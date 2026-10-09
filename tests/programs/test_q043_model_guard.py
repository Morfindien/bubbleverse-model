"""Failure-injection tests for Q043 admission, using real candidate evidence."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validator():
    path = ROOT / 'tests/programs/q043_model_validate.py'
    if not path.exists():
        raise AssertionError('Q043 has no validator; admission must not pass')
    spec = importlib.util.spec_from_file_location('q043_validator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Q043Guards(unittest.TestCase):
    def result(self):
        accepted = json.loads((ROOT/'accepted/model_state.json').read_text())
        return validator().run_tests(ROOT, candidate=accepted['current_q'] == 'Q042')

    def mutate(self, relative, change, gate):
        if json.loads((ROOT/'accepted/model_state.json').read_text())['current_q'] == 'Q043':
            relative = relative.replace('candidate/formal/', 'model/').replace('candidate/evidence/', 'evidence/')
            if relative in ['candidate/robustness.json','candidate/predictions.json']:
                relative = relative.replace('candidate/', 'accepted/')
            if relative == 'candidate/candidate_state.json' and gate == 'Q043_QUALIFICATION_GATE':
                relative = 'accepted/model_state.json'
        path = ROOT / relative
        original = path.read_bytes()
        try:
            data = json.loads(original)
            change(data)
            path.write_text(json.dumps(data))
            rows = {x['id']: x for x in self.result()['tests']}
            self.assertEqual(rows[gate]['status'], 'FAIL', rows)
        finally:
            path.write_bytes(original)

    def test_valid_candidate_passes(self):
        result = self.result()
        self.assertTrue(result['all_green'], result)

    def test_production_authorization_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d: d.update(production_restart_authorized=True), 'Q043_QUALIFICATION_GATE')

    def test_gap_in_sequence_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda d: d.update(previous_accepted_q='Q041'), 'Q043_SEQUENCE_GATE')

    def test_future_evidence_rejected(self):
        self.mutate('candidate/robustness.json', lambda d: d['items'].append({'id': 'INJECTION', 'finding': 'Q044 result'}), 'Q043_FIREWALL_GATE')

    def test_physical_parameter_change_rejected(self):
        self.mutate('candidate/formal/parameters.json', lambda d: d['parameters'][0].update(value=999), 'Q043_PHYSICAL_PRESERVATION_GATE')

    def test_original_prediction_change_rejected(self):
        self.mutate('candidate/predictions.json', lambda d: d['predictions'][0].update(statement='rewritten prediction'), 'Q043_PREDICTION_CONTRADICTION_GATE')

    def test_claiming_remote_sync_in_source_rejected(self):
        self.mutate('candidate/evidence/sources/Q043/integration_result.json', lambda d: d.update(remote_sync='PERFORMED'), 'Q043_SOURCE_HASH_GATE')

    def test_inherited_source_loss_rejected(self):
        self.mutate('candidate/evidence/sources/Q042/ingestion_decision.json', lambda d: d['source_register'].pop(), 'Q043_SOURCE_CONTINUITY_GATE')

    def test_old_snapshot_mutation_rejected(self):
        self.mutate('versions/accepted/v0.4/model_state.json', lambda d: d.update(current_q='Q041'), 'Q043_ACCEPTED_IMMUTABILITY_GATE')

    def test_tests_do_not_write_scientific_state(self):
        import hashlib
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for b in ['candidate', 'accepted', 'model', 'evidence', 'versions', 'release'] for p in (ROOT/b).rglob('*') if p.is_file()}
        self.result()
        after = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
