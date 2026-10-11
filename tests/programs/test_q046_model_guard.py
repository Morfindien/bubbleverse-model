"""Scope, source-integrity and rollback tests for Q046 assessment admission."""
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from guard_fixture import isolated_repository

ROOT = Path(__file__).resolve().parents[2]

class Q046Guards(unittest.TestCase):
    def setUp(self):
        self.root = isolated_repository(self, ROOT)

    def result(self):
        path = ROOT / 'tests/programs/q046_model_validate.py'
        self.assertTrue(path.exists(), 'Q046 needs a scope-limited admission validator')
        spec = importlib.util.spec_from_file_location('q046_guard', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        candidate = json.loads((self.root/'accepted/model_state.json').read_text())['current_q'] == 'Q045'
        return module.run_tests(self.root, candidate=candidate)

    def path(self, relative):
        if json.loads((self.root/'accepted/model_state.json').read_text())['current_q'] == 'Q046':
            relative = relative.replace('candidate/formal/', 'model/').replace('candidate/evidence/', 'evidence/')
            if relative in ['candidate/constraints.json', 'candidate/robustness.json']:
                relative = relative.replace('candidate/', 'accepted/')
        return self.root / relative

    def mutate(self, relative, change, gate):
        p = self.path(relative)
        obj = json.loads(p.read_text()); change(obj); p.write_text(json.dumps(obj))
        rows = {row['id']: row for row in self.result()['tests']}
        self.assertEqual(rows[gate]['status'], 'FAIL', rows[gate])

    def test_documented_insufficient_qualification_is_admissible(self):
        result = self.result()
        self.assertTrue(result['all_green'], result)

    def test_physical_comparison_claim_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(q046_physical_reference_qualified=True), 'Q046_QUALIFICATION_GATE')

    def test_case_id_fabrication_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(q046_canonical_case_id='INVENTED'), 'Q046_QUALIFICATION_GATE')

    def test_result_id_fabrication_rejected(self):
        self.mutate('candidate/evidence/q_updates/Q046.json', lambda d:d.update(canonical_result_id='INVENTED'), 'Q046_QUALIFICATION_GATE')

    def test_production_authorization_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(production_restart_authorized=True), 'Q046_QUALIFICATION_GATE')

    def test_physical_parameter_mutation_rejected(self):
        self.mutate('candidate/formal/parameters.json', lambda d:d['parameters'][0].update(value=999), 'Q046_REGRESSION_GATE')

    def test_document_source_corruption_rejected(self):
        p = self.path('candidate/evidence/sources/Q046/q_journal_authorized.txt')
        p.write_text(p.read_text()+' altered source')
        rows = {row['id']:row for row in self.result()['tests']}
        self.assertEqual(rows['Q046_SOURCE_HASH_GATE']['status'], 'FAIL')

    def test_evidence_source_retarget_rejected(self):
        def change(d):
            entry = next(e for e in d['entries'] if e['evidence_id']=='EVD-Q046-QJOURNAL')
            other = next(e for e in d['entries'] if e['evidence_id']=='EVD-Q046-MAINBOOK')
            entry.update(source=other['source'], sha256=other['sha256'])
        self.mutate('candidate/evidence/evidence_registry.json', change, 'Q046_SOURCE_HASH_GATE')

    def test_unreviewed_same_id_overstatement_rejected(self):
        self.mutate('candidate/robustness.json', lambda d:d['items'][-1].update(finding='Physical CLASS_EDE bias established.'), 'Q046_MODEL_DIFF_GATE')

    def test_future_origin_rejected(self):
        self.mutate('candidate/robustness.json', lambda d:d['items'].append({'id':'INJECTED','finding':'Q'+str(46+1).zfill(3)+' scientific source'}), 'Q046_FIREWALL_GATE')

    def test_missing_diff_entry_rejected(self):
        self.mutate('candidate/candidate_diff.json', lambda d:d.update(new_limitations=[]), 'Q046_MODEL_DIFF_GATE')

    def test_frozen_baseline_mutation_rejected(self):
        self.mutate('versions/accepted/v0.7/model_state.json', lambda d:d.update(injected=True), 'Q046_IMMUTABILITY_GATE')

    def test_manuscript_commit_fabrication_rejected(self):
        def change(d):
            next(e for e in d['entries'] if e['evidence_id']=='EVD-Q046-QJOURNAL')['source_repository_commit']='5db94b20610d9e3e2eb765f39ce426f078ae385d'
        self.mutate('candidate/evidence/evidence_registry.json', change, 'Q046_SOURCE_HASH_GATE')

    def test_validator_is_read_only(self):
        files=[p for name in ['accepted','candidate','model','evidence','versions','release'] for p in (self.root/name).rglob('*') if p.is_file()]
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        self.result()
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

    def test_q046_gate_is_mandatory_in_healthcheck(self):
        spec=importlib.util.spec_from_file_location('campaign', ROOT/'tests/programs/model_campaign.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.assertIn('T-BV-015', module.MANDATORY_IDS)

if __name__ == '__main__':
    unittest.main()
