import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class ContractTests(unittest.TestCase):
 def setUp(self):
  self.cert=json.loads((ROOT/'evidence/sources/Q050/Q050_GLOBAL_LITERAL_SELECTOR_EXTENSION_CERTIFICATE_V1.json').read_text())
  self.task=json.loads((ROOT/'provenance/input_archives/Q050/Q050_NEXT_MATHEMATICS_TASK_GLOBAL_LITERAL_SELECTOR_EXTENSION_V1.json').read_text())
 def check(self,cert):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);(t/'c').write_text(json.dumps(cert));(t/'t').write_text(json.dumps(self.task))
   x=subprocess.run([sys.executable,str(ROOT/'tests/programs/q050_contract_validate.py'),str(t/'c'),str(t/'t')],capture_output=True,text=True)
   return json.loads(x.stdout)
 def test_original_is_admitted_within_contract(self):self.assertEqual(self.check(self.cert)['status'],'PASS')
 def test_missing_regularity_component_rejected(self):
  self.cert['global_components'].pop('GLOBAL_1_AWAY_FROM_INTERFACE');self.assertEqual(self.check(self.cert)['status'],'FAIL')
 def test_missing_pion_gate_rejected(self):
  self.cert['inherited_local_gates']['pion_hmla_swift']['status']='UNRESOLVED';self.assertEqual(self.check(self.cert)['status'],'FAIL')
 def test_missing_tangent_certificate_rejected(self):
  self.cert['inherited_local_gates']['peebles_ratio_exact_tangent']['certificate']='NOT_ESTABLISHED';self.assertEqual(self.check(self.cert)['status'],'FAIL')
 def test_unbounded_zeno_reason_rejected(self):
  self.cert['global_components']['GLOBAL_4_ZENO_ACCUMULATION']['reason']='Branch fields may be unbounded.';self.assertEqual(self.check(self.cert)['status'],'FAIL')
 def test_missing_endpoint_restart_rejected(self):
  self.cert['maximal_extension_theorem']['proof_skeleton']=[];self.assertEqual(self.check(self.cert)['status'],'FAIL')
 def test_missing_hydrogen_safety_rejected(self):
  self.cert['global_components']['GLOBAL_3_INVARIANT_CONTINUATION']['reason']='No bound away from native singularity supplied.';self.assertEqual(self.check(self.cert)['status'],'FAIL')
 def test_convexified_selector_rejected(self):
  self.cert['claim_firewall']=[s for s in self.cert['claim_firewall'] if 'convexification' not in s];self.assertEqual(self.check(self.cert)['status'],'FAIL')
 def test_changed_question_rejected(self):
  self.cert['question_sha256']='0'*64;self.assertEqual(self.check(self.cert)['status'],'FAIL')
if __name__=='__main__':unittest.main()
