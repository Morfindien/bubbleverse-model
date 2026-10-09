"""Historical Q042 gates must survive a valid controlled boundary extension."""
import json
import tempfile
import unittest
from pathlib import Path
from q042_model_validate import run_tests

ROOT = Path(__file__).resolve().parents[2]


class Q042HistoricalSequence(unittest.TestCase):
    def test_frozen_q042_sequence_passes_with_current_q043(self):
        # Only the sequence check needs these files; other absent gates may fail.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = {
                'candidate/candidate_state.json': {'current_q':'Q043','q_access_end':'Q043'},
                'accepted/model_state.json': {'current_q':'Q043','q_access_end':'Q043','accepted_model_version':'v0.5'},
                'evidence/evidence_registry.json': {'current_q':'Q043','q_access_end':'Q043'},
                'provenance/archive/Q042/candidate_state.json': {'current_q':'Q042','q_access_end':'Q042','previous_accepted_q':'Q041'},
                'versions/accepted/v0.4/model_state.json': {'current_q':'Q042','q_access_end':'Q042','accepted_model_version':'v0.4'},
            }
            for relative,data in paths.items():
                p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data))
            rows={x['id']:x for x in run_tests(root)['tests']}
            self.assertEqual(rows['Q_SEQUENCE_GATE']['status'],'PASS',rows['Q_SEQUENCE_GATE'])
            p=root/'evidence/evidence_registry.json';p.write_text(json.dumps({'current_q':'Q042','q_access_end':'Q042'}))
            rows={x['id']:x for x in run_tests(root)['tests']}
            self.assertEqual(rows['Q_SEQUENCE_GATE']['status'],'FAIL')


if __name__ == '__main__':
    unittest.main()
