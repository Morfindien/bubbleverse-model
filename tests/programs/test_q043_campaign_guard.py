"""Q043 integrity must participate in the existing public validation campaign."""
import importlib.util
import json
import unittest
from guard_fixture import isolated_repository
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('campaign',ROOT/'tests/programs/model_campaign.py')
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)


class Q043CampaignGuard(unittest.TestCase):
    def setUp(self):
        self.root=isolated_repository(self,ROOT)
        campaign.ROOT=self.root

    def test_q043_is_a_mandatory_campaign_gate(self):
        self.assertIn('T-BV-012', campaign.MANDATORY_IDS)

    def test_production_claim_fails_current_public_campaign(self):
        if json.loads((self.root/'accepted/model_state.json').read_text())['current_q'] not in ['Q043','Q044']:
            self.skipTest('Q043 campaign requires the projected or promoted Q043 state')
        path = self.root/'evidence/evidence_registry.json'
        before = path.read_bytes()
        try:
            data=json.loads(before)
            entry=next(x for x in data['entries'] if x['evidence_id']=='EVD-Q043-RESULT')
            entry['production_restart_authorized']=True
            path.write_text(json.dumps(data))
            self.assertEqual(campaign.audit()['T-BV-012'][0],'FAIL')
        finally:
            path.write_bytes(before)


if __name__ == '__main__':
    unittest.main()
