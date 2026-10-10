"""Structural cleanup guards; scientific inputs stay unchanged."""
from pathlib import Path
import importlib.util, json, shutil, subprocess, tempfile, unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('cleanup_under_test',ROOT/'repository_cleanup.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)

class CompletedBundleInstallerTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory(prefix='cleanup-guard-')
        self.repo=Path(self.folder.name)/'repo'
        subprocess.run(['git','clone','--quiet','--branch','main',str(ROOT),str(self.repo)],check=True,capture_output=True)
        self.q=json.loads((self.repo/'accepted/model_state.json').read_text())['current_q']
        self.workflow='.github/workflows/'+self.q.lower()+'-install-model.yml'
        self.bundle=self.q+'_model_update.bundle'
        self.guide=self.q+'_INSTALL_ACTIONS.md'
        self.receipt='provenance/'+self.q+'_REMOTE_INSTALLATION_RECEIPT.json'
        self.cohort={self.workflow,self.bundle,self.guide}
        if not (self.repo/self.workflow).exists():
            revision=subprocess.check_output(['git','rev-list','-1','HEAD','--',self.receipt],cwd=self.repo,text=True).strip()
            if not revision:self.skipTest('No historical bundle installation receipt in this model state')
            subprocess.run(['git','checkout','--quiet','--detach',revision],cwd=self.repo,check=True)

    def tearDown(self):self.folder.cleanup()

    def audit(self):return engine.audit(self.repo)[0]

    def keep(self,report):
        self.assertFalse(self.cohort & set(report['planned_deletions']))
        rows={e['path']:e for e in report['repository_map']}
        for p in self.cohort:self.assertEqual(rows[p]['classification'],'REVIEW_REQUIRED')

    def test_completed_bundle_cohort_is_safe_delete(self):
        r=self.audit();self.assertTrue(self.cohort <= set(r['planned_deletions']))
        self.assertNotIn(self.receipt,r['planned_deletions'])
        self.assertFalse(any(p.startswith(engine.PROTECTED) for p in r['planned_deletions']))

    def test_missing_successful_receipt_keeps_cohort(self):
        (self.repo/self.receipt).unlink();self.keep(self.audit())

    def test_tampered_bundle_keeps_cohort(self):
        with (self.repo/self.bundle).open('ab') as f:f.write(b'changed')
        self.keep(self.audit())

    def test_live_dependency_keeps_cohort(self):
        p=self.repo/'ACTIVE_INSTALL_DEPENDENCY.md';p.write_text('Required file: '+self.bundle+'\n')
        subprocess.run(['git','add',p.name],cwd=self.repo,check=True)
        self.keep(self.audit())

    def test_unreachable_promotion_keeps_cohort(self):
        p=self.repo/self.receipt;o=json.loads(p.read_text());o['promotion_commit']='0'*40
        p.write_text(json.dumps(o));self.keep(self.audit())

    def test_current_publication_documentation_uses_verified_receipt(self):
        r,updates=engine.audit(self.repo)
        self.assertIn('README.md',updates)
        self.assertIn(self.receipt,updates['README.md'])
        self.assertNotIn('no successful remote installation receipt exists',updates['README.md'])

if __name__=='__main__':unittest.main()
