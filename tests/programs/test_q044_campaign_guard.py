import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from q043_model_validate import run_tests

ROOT=Path(__file__).resolve().parents[2]

class Q044CampaignGuard(unittest.TestCase):
    def test_q044_is_mandatory(self):
        spec=importlib.util.spec_from_file_location('campaign',ROOT/'tests/programs/model_campaign.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertIn('T-BV-013',module.MANDATORY_IDS)

    def test_historical_q043_sequence_after_extension(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            paths={'accepted/model_state.json':{'current_q':'Q044','q_access_end':'Q044','accepted_model_version':'v0.6'},'candidate/Q043_PROVENANCE.json':{},'versions/accepted/v0.5/model_state.json':{'current_q':'Q043','q_access_end':'Q043','accepted_model_version':'v0.5'},'versions/accepted/v0.5/evidence_registry.json':{'current_q':'Q043','q_access_end':'Q043'},'versions/accepted/v0.4/model_state.json':{'current_q':'Q042'},'provenance/archive/Q043/candidate_state.json':{'previous_accepted_q':'Q042','previous_accepted_model_version':'v0.4','current_q':'Q043','q_access_end':'Q043','target_q':'Q043','candidate_model_version':'v0.5','candidate_revision':'R000005'}}
            for rel,obj in paths.items():p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj))
            rows={r['id']:r for r in run_tests(root)['tests']}
            self.assertEqual(rows['Q043_SEQUENCE_GATE']['status'],'PASS',rows['Q043_SEQUENCE_GATE'])

    def test_historical_snapshot_survives_live_q044_state(self):
        path=ROOT/'accepted/model_state.json';before=path.read_bytes()
        try:
            state=json.loads(before);state.update(current_q='Q044',q_access_end='Q044',accepted_model_version='v0.6',model_revision='R000006')
            path.write_text(json.dumps(state))
            rows={r['id']:r for r in run_tests(ROOT)['tests']}
            self.assertEqual(rows['Q043_ACCEPTED_IMMUTABILITY_GATE']['status'],'PASS',rows['Q043_ACCEPTED_IMMUTABILITY_GATE'])
        finally:path.write_bytes(before)

if __name__=='__main__':unittest.main()
