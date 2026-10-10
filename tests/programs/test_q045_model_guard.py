"""Reject physically overstated or damaged Q045 admission using real inputs."""
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class Q045Guards(unittest.TestCase):
    def setUp(self):
        from guard_fixture import isolated_repository
        self.root=isolated_repository(self,ROOT)
    def result(self):
        path=ROOT/'tests/programs/q045_model_validate.py'
        self.assertTrue(path.exists(),'Q045 admission requires a validator')
        spec=importlib.util.spec_from_file_location('q045',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        return mod.run_tests(self.root,candidate=json.loads((self.root/'accepted/model_state.json').read_text())['current_q']=='Q044')
    def path(self,rel):
        if json.loads((self.root/'accepted/model_state.json').read_text())['current_q']=='Q045':
            rel=rel.replace('candidate/formal/','model/').replace('candidate/evidence/','evidence/')
            if rel.startswith('candidate/') and rel.split('/')[-1] in ['robustness.json','constraints.json']:rel=rel.replace('candidate/','accepted/')
        return self.root/rel
    def mutate(self,rel,change,gate):
        p=self.path(rel);d=json.loads(p.read_text());change(d);p.write_text(json.dumps(d))
        rows={r['id']:r for r in self.result()['tests']};self.assertEqual(rows[gate]['status'],'FAIL',rows[gate])
    def test_scoped_candidate_passes(self):self.assertTrue(self.result()['all_green'],self.result())
    def test_qualified_reference_rejected(self):
        self.mutate('candidate/evidence/sources/Q045/q045_reference_history_final_v2.json',lambda d:d.update(reference_truth_gate='PASS'),'Q045_QUALIFICATION_GATE')
    def test_production_rejected(self):
        self.mutate('candidate/candidate_state.json',lambda d:d.update(production_restart_authorized=True),'Q045_QUALIFICATION_GATE')
    def test_invented_physical_parameter_rejected(self):
        self.mutate('candidate/formal/parameters.json',lambda d:d['parameters'][0].update(value=999),'Q045_REGRESSION_GATE')
    def test_source_loss_rejected(self):
        self.mutate('candidate/Q045_PROVENANCE.json',lambda d:d.update(source_files=[]),'Q045_SOURCE_HASH_GATE')
    def test_tau_sequence_tampering_rejected(self):
        self.mutate('candidate/evidence/sources/Q045/q045_reference_history_final_v2.json',lambda d:d['history_comparisons']['camspec-lcdm']['scalar_sequences']['actual_tau']['values'].__setitem__(1,0),'Q045_DIAGNOSTIC_GATE')
    def test_future_science_rejected(self):
        self.mutate('candidate/robustness.json',lambda d:d['items'].append({'id':'INJECT','finding':'Q'+str(46).zfill(3)+' source'}),'Q045_FIREWALL_GATE')
    def test_overstated_same_id_rejected(self):
        self.mutate('candidate/robustness.json',lambda d:d['items'][-1].update(finding='Physical bias established.'),'Q045_MODEL_DIFF_GATE')
    def test_previous_snapshot_mutation_rejected(self):
        self.mutate('versions/accepted/v0.6/model_state.json',lambda d:d.update(injected=True),'Q045_IMMUTABILITY_GATE')
    def test_derived_grid_tampering_rejected(self):
        p=self.path('candidate/evidence/sources/Q045/camspec-lcdm_common_grid.tsv');p.write_bytes(p.read_bytes()+b'0\n')
        rows={r['id']:r for r in self.result()['tests']};self.assertEqual(rows['Q045_SOURCE_HASH_GATE']['status'],'FAIL')
    def test_candidate_reference_qualification_rejected(self):
        self.mutate('candidate/candidate_state.json',lambda d:d.update(q045_reference_truth_gate='QUALIFIED'),'Q045_QUALIFICATION_GATE')
    def test_summary_final_result_overstatement_rejected(self):
        self.mutate('candidate/evidence/q_updates/Q045.json',lambda d:d.update(final_result_gate='PASS'),'Q045_QUALIFICATION_GATE')
    def test_provenance_physical_qualification_rejected(self):
        self.mutate('candidate/Q045_PROVENANCE.json',lambda d:d.update(full_physical_reference_qualified=True),'Q045_QUALIFICATION_GATE')
    def test_valid_hash_source_retarget_rejected(self):
        def change(d):
            entries={e['evidence_id']:e for e in d['entries']}
            entries['EVD-Q045-RECOVERY'].update(source=entries['EVD-Q045-MAINBOOK']['source'],sha256=entries['EVD-Q045-MAINBOOK']['sha256'])
        self.mutate('candidate/evidence/evidence_registry.json',change,'Q045_QUALIFICATION_GATE')
    def test_manuscript_commit_fabrication_rejected(self):
        def change(d):
            next(e for e in d['entries'] if e['evidence_id']=='EVD-Q045-QJOURNAL')['source_repository_commit']='a9a5777b5923f32930cd9c84a49227ba36249326'
        self.mutate('candidate/evidence/evidence_registry.json',change,'Q045_QUALIFICATION_GATE')
    def test_prior_evidence_update_tampering_rejected(self):
        self.mutate('evidence/q_updates/Q044.json',lambda d:d.update(result='FALSIFIED'),'Q045_IMMUTABILITY_GATE')
    def test_read_only(self):
        files=[p for n in ['accepted','candidate','model','evidence','versions','release'] for p in (self.root/n).rglob('*') if p.is_file()]
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files};self.result()
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
if __name__=='__main__':unittest.main()
