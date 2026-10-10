"""Structural guards for snapshot evolution, archives and current documentation."""
from pathlib import Path
import importlib.util
import hashlib
import json
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('cleanup_guards', ROOT/'repository_cleanup.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

class CleanupEvolutionTests(unittest.TestCase):
    def test_protected_environment_identity_conflict_requires_review(self):
        documents={'model/environment.json':{'accepted_model_version':'previous'},'candidate/formal/environment.json':{'accepted_model_version':'current'}}
        self.assertEqual(engine.environment_reviews(documents,{'current_accepted_version':'current'}),['model/environment.json'])

    def test_current_snapshot_with_frozen_candidate_diff_is_validated(self):
        _, _, documents, _, _ = engine.inventory(ROOT)
        engine.verify_snapshot(ROOT, engine.discover(ROOT, documents), documents)

    def test_unknown_snapshot_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); snapshot = root/'versions/accepted/test'
            snapshot.mkdir(parents=True)
            (snapshot/'unregistered.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError, 'Unknown snapshot member'):
                engine.verify_snapshot(root, {'current_accepted_version':'test','current_q':'Q001'}, {})

    def test_frozen_diff_cannot_be_mismatched(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); snapshot = root/'versions/accepted/test'
            snapshot.mkdir(parents=True); (root/'candidate').mkdir()
            (snapshot/'candidate_diff.json').write_text('{}')
            (root/'candidate/candidate_diff.json').write_text('{"changed":true}')
            with self.assertRaisesRegex(RuntimeError, 'snapshot mismatch'):
                engine.verify_snapshot(root, {'current_accepted_version':'test','current_q':'Q001'}, {})

    def test_archive_requires_original_reachable_git_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git','init','-q',str(root)],check=True)
            original = root/'REPORT.md'; original.write_text('Historical installer path\n')
            subprocess.run(['git','add','.'],cwd=root,check=True)
            subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.org','commit','-qm','Historical input'],cwd=root,check=True)
            head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
            archive = 'provenance/cleanup/archive/REPORT.md'
            (root/archive).parent.mkdir(parents=True); original.rename(root/archive)
            index = 'provenance/cleanup/archive_manifest.json'
            document = {'head_before':head,'archives':[{'old_path':'REPORT.md','new_path':archive,'sha256':hashlib.sha256((root/archive).read_bytes()).hexdigest()}]}
            self.assertTrue(engine.historical_reference(root,archive,{index:document}))
            (root/archive).write_text('Altered report')
            self.assertFalse(engine.historical_reference(root,archive,{index:document}))
            document['head_before'] = '0'*40
            self.assertFalse(engine.historical_reference(root,archive,{index:document}))

    def test_current_readme_range_follows_canonical_accepted_boundary(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'README.md').write_text('AUTHORIZED:\nQ001–Q002\n')
            state = {'accepted':{},'current_q':'Q003','current_q_boundary':'Q001-Q003','current_accepted_version':'test','current_formal_model':'test'}
            updates = engine.metadata_updates(root,{'README.md':{}},{},state)
            self.assertIn('AUTHORIZED:\nQ001–Q003',updates['README.md'])

    def test_optional_motor_reader_allows_archive_but_live_dependency_blocks_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git','init','-q',str(root)],check=True)
            (root/'README.md').write_text('Historical baseline')
            subprocess.run(['git','add','.'],cwd=root,check=True)
            subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.org','commit','-qm','Baseline'],cwd=root,check=True)
            head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
            record = {'TARGET_REPO':'Morfindien/bubbleverse-model','SCIENTIFIC_CHANGE':False,'COMMIT_STATUS':'LOCAL_COMMITTED_REMOTE_PUBLICATION_BLOCKED','HEAD_BEFORE':head}
            report_name='REPOSITORY_'+'CLEANUP_REPORT.json'
            (root/report_name).write_text(json.dumps(record))
            (root/'repository_cleanup.py').write_text('optional = '+repr(report_name)+'\n')
            subprocess.run(['git','add','.'],cwd=root,check=True)
            entries,_,documents,_,_ = engine.inventory(root)
            self.assertEqual(len(engine.root_archives(root,entries,documents)),1)
            (root/'ACTIVE.md').write_text('Required: '+report_name)
            subprocess.run(['git','add','.'],cwd=root,check=True)
            entries,_,documents,_,_ = engine.inventory(root)
            self.assertEqual(engine.root_archives(root,entries,documents),[])

if __name__ == '__main__':
    unittest.main()
