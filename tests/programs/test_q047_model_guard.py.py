"""Scope, source-integrity and rollback tests for Q047 assessment admission."""
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from guard_fixture import isolated_repository

ROOT = Path(__file__).resolve().parents[2]

class Q047Guards(unittest.TestCase):
    def setUp(self):
        self.root = isolated_repository(self, ROOT)

    def result(self):
        path = ROOT / 'tests/programs/q047_model_validate.py'
        self.assertTrue(path.exists(), 'Q047 needs a scope-limited admission validator')
        spec = importlib.util.spec_from_file_location('q047_guard', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        candidate = json.loads((self.root/'accepted/model_state.json').read_text())['current_q'] == 'Q046'
        return module.run_tests(self.root, candidate=candidate)

    def path(self, relative):
        active = int(json.loads((self.root/'accepted/model_state.json').read_text())['current_q'][1:])
        pending = int(json.loads((self.root/'candidate/candidate_state.json').read_text())['current_q'][1:])

        # Once the repository has advanced beyond Q047, q047_model_validate.py
        # validates the frozen v0.9/Q047 historical surface. Failure-injection
        # tests must mutate those same historical inputs, not the live Q048
        # candidate/accepted surface.
        if active > 47 or pending > 47:
            if relative in ['candidate/candidate_state.json', 'candidate/candidate_diff.json']:
                relative = 'provenance/archive/Q047/' + Path(relative).name
            elif relative == 'candidate/evidence/evidence_registry.json':
                relative = 'versions/accepted/v0.9/evidence_registry.json'
            elif relative.startswith('candidate/formal/'):
                relative = 'versions/accepted/v0.9/' + Path(relative).name
            elif relative in ['candidate/constraints.json', 'candidate/robustness.json']:
                relative = 'versions/accepted/v0.9/' + Path(relative).name
            elif relative.startswith('candidate/evidence/'):
                relative = relative.replace('candidate/evidence/', 'evidence/', 1)

        elif active == 47:
            relative = relative.replace('candidate/formal/', 'model/').replace('candidate/evidence/', 'evidence/')
            if relative in ['candidate/constraints.json', 'candidate/robustness.json']:
                relative = relative.replace('candidate/', 'accepted/')

        return self.root / relative

    def mutate(self, relative, change, gate):
        p = self.path(relative)
        obj = json.loads(p.read_text()); change(obj); p.write_text(json.dumps(obj))
        rows = {row['id']: row for row in self.result()['tests']}
        self.assertEqual(rows[gate]['status'], 'FAIL', rows[gate])

    def test_documented_inconclusive_closure_is_admissible(self):
        result = self.result()
        self.assertTrue(result['all_green'], result)

    def test_physical_comparison_claim_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(q047_physical_reference_qualified=True), 'Q047_QUALIFICATION_GATE')

    def test_case_id_fabrication_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(q047_canonical_case_id='INVENTED'), 'Q047_QUALIFICATION_GATE')

    def test_result_id_fabrication_rejected(self):
        self.mutate('candidate/evidence/q_updates/Q047.json', lambda d:d.update(canonical_result_id='INVENTED'), 'Q047_QUALIFICATION_GATE')

    def test_production_authorization_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(production_restart_authorized=True), 'Q047_QUALIFICATION_GATE')

    def test_physical_parameter_mutation_rejected(self):
        self.mutate('candidate/formal/parameters.json', lambda d:d['parameters'][0].update(value=999), 'Q047_REGRESSION_GATE')

    def test_document_source_corruption_rejected(self):
        p = self.path('candidate/evidence/sources/Q047/q_journal_authorized.txt')
        p.write_text(p.read_text()+' altered source')
        rows = {row['id']:row for row in self.result()['tests']}
        self.assertEqual(rows['Q047_SOURCE_HASH_GATE']['status'], 'FAIL')

    def test_evidence_source_retarget_rejected(self):
        def change(d):
            entry = next(e for e in d['entries'] if e['evidence_id']=='EVD-Q047-QJOURNAL')
            other = next(e for e in d['entries'] if e['evidence_id']=='EVD-Q047-MAINBOOK')
            entry.update(source=other['source'], sha256=other['sha256'])
        self.mutate('candidate/evidence/evidence_registry.json', change, 'Q047_SOURCE_HASH_GATE')

    def test_unreviewed_same_id_overstatement_rejected(self):
        self.mutate('candidate/robustness.json', lambda d:d['items'][-1].update(finding='Physical CLASS_EDE bias established.'), 'Q047_MODEL_DIFF_GATE')

    def test_future_origin_rejected(self):
        self.mutate('candidate/robustness.json', lambda d:d['items'].append({'id':'INJECTED','finding':'Q'+str(47+1).zfill(3)+' scientific source'}), 'Q047_FIREWALL_GATE')

    def test_missing_diff_entry_rejected(self):
        self.mutate('candidate/candidate_diff.json', lambda d:d.update(new_limitations=[]), 'Q047_MODEL_DIFF_GATE')

    def test_frozen_baseline_mutation_rejected(self):
        self.mutate('versions/accepted/v0.8/model_state.json', lambda d:d.update(injected=True), 'Q047_IMMUTABILITY_GATE')

    def test_manuscript_commit_fabrication_rejected(self):
        def change(d):
            next(e for e in d['entries'] if e['evidence_id']=='EVD-Q047-QJOURNAL')['source_repository_commit']='5db94b20610d9e3e2eb765f39ce426f078ae385d'
        self.mutate('candidate/evidence/evidence_registry.json', change, 'Q047_SOURCE_HASH_GATE')

    def test_validator_is_read_only(self):
        files=[p for name in ['accepted','candidate','model','evidence','versions','release'] for p in (self.root/name).rglob('*') if p.is_file()]
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        self.result()
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

    def test_q047_gate_is_mandatory_in_healthcheck(self):
        spec=importlib.util.spec_from_file_location('campaign', ROOT/'tests/programs/model_campaign.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.assertIn('T-BV-016', module.MANDATORY_IDS)

    def test_historical_identity_upgrade_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(q047_historical_state_identity_gate='PASS'), 'Q047_QUALIFICATION_GATE')

    def test_closure_does_not_set_physical_final_gate(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(q047_final_result_gate='PASS'), 'Q047_QUALIFICATION_GATE')

    def test_source_run_identity_retarget_rejected(self):
        self.mutate('candidate/Q047_PROVENANCE.json', lambda d:d.update(source_run_id='INVENTED'), 'Q047_RECONSTRUCTION_GATE')

    def test_proposed_result_identity_preserved(self):
        self.mutate('candidate/candidate_state.json', lambda d:d.update(q047_source_result_ids=[]), 'Q047_QUALIFICATION_GATE')

if __name__ == '__main__':
    unittest.main()
