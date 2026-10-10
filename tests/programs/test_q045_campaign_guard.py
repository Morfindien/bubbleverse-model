import unittest
from pathlib import Path
import importlib.util
from guard_fixture import isolated_repository
from q044_model_validate import run_tests
ROOT=Path(__file__).resolve().parents[2]
class Q045CampaignGuard(unittest.TestCase):
    def test_q045_gate_is_mandatory(self):
        spec=importlib.util.spec_from_file_location('campaign',ROOT/'tests/programs/model_campaign.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertIn('T-BV-014',m.MANDATORY_IDS)
    def test_q044_history_remains_fully_validated(self):
        root=isolated_repository(self,ROOT);r=run_tests(root)
        self.assertEqual(r['tests_total'],11);self.assertTrue(r['all_green'],r)
if __name__=='__main__':unittest.main()
