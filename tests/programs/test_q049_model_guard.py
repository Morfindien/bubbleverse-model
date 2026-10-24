"""Behavior guards: admission must reject corrupted evidence and scientific overclaims."""
import importlib, json, shutil, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/programs'))

class Q049Guards(unittest.TestCase):
    def test_current_environment_registry_match_accepted_model(self):
        state=json.loads((ROOT/'accepted/model_state.json').read_text())
        env=json.loads((ROOT/'model/environment.json').read_text())
        self.assertEqual(env['accepted_model_version'],state['accepted_model_version'])
        self.assertEqual(env['source_bubbleverse_commit'],state['source_repository_commit'])
        registry=json.loads((ROOT/'bubbleverse_model_program_registry.json').read_text())
        for item in registry['programs'].values():
            self.assertEqual(item['accepted_model_version'],state['accepted_model_version'])
            self.assertEqual(item['q_access_end'],state['q_access_end'])

    def test_campaign_validates_q049_and_preserved_q048(self):
        import model_campaign
        rows=model_campaign.audit()
        self.assertIn('T-BV-018',rows,'Q049 admission must participate in public campaign')
        self.assertTrue(all(v[0]=='PASS' for v in rows.values()),rows)

    def test_q048_historical_view_passes_after_q049_admission(self):
        import q048_model_validate
        result=q048_model_validate.run_tests(ROOT)
        self.assertTrue(result['all_green'],result)

    def mutation(self,mutate):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'repo'
            shutil.copytree(ROOT,target,ignore=shutil.ignore_patterns('.git','__pycache__'))
            mutate(target)
            module=importlib.import_module('q049_model_validate')
            result=module.run_tests(target)
            self.assertFalse(result['all_green'],result)

    def test_corrupted_original_certificate_rejected(self):
        self.mutation(lambda r:(r/'evidence/sources/Q049/Q049_V2_GLOBAL_BOUND_RESULT.json').write_text('{}'))

    def test_understated_cap_rejected(self):
        def change(r):
            p=r/'evidence/q_updates/Q049.json';d=json.loads(p.read_text());d['bound_dimensionless']='0.000001';p.write_text(json.dumps(d))
        self.mutation(change)

    def test_existence_and_small_effect_overclaims_rejected(self):
        for key in ['existence_proved','uniqueness_proved','native_fidelity_proved','small_effect_established']:
            with self.subTest(key=key):
                def change(r):
                    p=r/'evidence/q_updates/Q049.json';d=json.loads(p.read_text());d[key]=True;p.write_text(json.dumps(d))
                self.mutation(change)

if __name__=='__main__':unittest.main()
