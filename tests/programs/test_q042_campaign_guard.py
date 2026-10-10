"""Integration checks: changing Q042 qualification state must fail the public campaign."""
import importlib.util
import json
import unittest
from guard_fixture import isolated_repository
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('campaign',ROOT/'tests/programs/model_campaign.py')
campaign=importlib.util.module_from_spec(spec);spec.loader.exec_module(campaign)

class QualificationGuardTests(unittest.TestCase):
    def setUp(self):
        self.root=isolated_repository(self,ROOT)
        campaign.ROOT=self.root

    def test_valid_closure_participates_in_current_campaign(self):
        checks=campaign.audit()
        self.assertIn('T-BV-011',checks,'Q042 is not tested by the current public campaign')
        self.assertEqual(checks['T-BV-011'][0],'PASS')

    def test_production_authorization_is_rejected(self):
        path=self.root/'evidence/evidence_registry.json';before=path.read_bytes()
        try:
            data=json.loads(before)
            closure=next(x for x in data['entries'] if x['evidence_id']=='EVD-Q042-CLOSURE-001')
            closure['production_restart_authorized']=True
            path.write_text(json.dumps(data))
            self.assertIn('T-BV-011',campaign.audit())
            self.assertEqual(campaign.audit()['T-BV-011'][0],'FAIL')
        finally:path.write_bytes(before)

    def test_physical_falsification_is_rejected(self):
        path=self.root/'evidence/evidence_registry.json';before=path.read_bytes()
        try:
            data=json.loads(before)
            closure=next(x for x in data['entries'] if x['evidence_id']=='EVD-Q042-CLOSURE-001')
            closure['physical_falsification']=True
            path.write_text(json.dumps(data))
            self.assertIn('T-BV-011',campaign.audit())
            self.assertEqual(campaign.audit()['T-BV-011'][0],'FAIL')
        finally:path.write_bytes(before)

    def test_stale_evidence_current_q_is_rejected(self):
        path=self.root/'evidence/evidence_registry.json';before=path.read_bytes()
        try:
            data=json.loads(before);data['current_q']='Q041'
            path.write_text(json.dumps(data))
            self.assertEqual(campaign.audit()['T-BV-011'][0],'FAIL')
        finally:path.write_bytes(before)

if __name__=='__main__':unittest.main()
