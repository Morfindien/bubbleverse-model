"""Real failure injection for scoped Q044 model admission."""
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Q044Guards(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)/'model'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('.git','__pycache__','run-output'))
        gitdir=(ROOT/'.git').resolve()
        if gitdir.is_file():gitdir=Path(gitdir.read_text().split(':',1)[1].strip())
        (self.root/'.git').write_text('gitdir: '+str(gitdir)+'\n')

    def result(self):
        path = ROOT/'tests/programs/q044_model_validate.py'
        self.assertTrue(path.exists(), 'Q044 admission has no validator')
        spec = importlib.util.spec_from_file_location('q044_validator', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.run_tests(self.root, candidate=json.loads((self.root/'accepted/model_state.json').read_text())['current_q'] == 'Q043')

    def active_path(self, relative):
        active=int(json.loads((self.root/'accepted/model_state.json').read_text())['current_q'][1:])
        pending=int(json.loads((self.root/'candidate/candidate_state.json').read_text())['current_q'][1:])
        if active>44 or pending>44:
            if relative in ['candidate/candidate_state.json','candidate/candidate_diff.json']:
                return self.root/'provenance/archive/Q044'/Path(relative).name
            if relative=='candidate/evidence/evidence_registry.json':
                return self.root/'versions/accepted/v0.6/evidence_registry.json'
            if relative.startswith('candidate/formal/') or relative in ['candidate/robustness.json','candidate/observations.json','candidate/predictions.json','candidate/mechanisms.json','candidate/contradictions.json']:
                return self.root/'versions/accepted/v0.6'/Path(relative).name
            if relative.startswith('candidate/evidence/'):
                return self.root/relative.removeprefix('candidate/')
        if json.loads((self.root/'accepted/model_state.json').read_text())['current_q'] == 'Q044':
            relative = relative.replace('candidate/formal/', 'model/').replace('candidate/evidence/', 'evidence/')
            if relative in ['candidate/robustness.json', 'candidate/observations.json', 'candidate/predictions.json', 'candidate/mechanisms.json', 'candidate/contradictions.json']:
                relative = relative.replace('candidate/', 'accepted/')
        return self.root/relative

    def mutate(self, relative, change, gate):
        path = self.active_path(relative)
        before = path.read_bytes()
        try:
            data = json.loads(before);change(data);path.write_text(json.dumps(data))
            rows = {x['id']:x for x in self.result()['tests']}
            self.assertEqual(rows[gate]['status'], 'FAIL', rows[gate])
        finally:
            path.write_bytes(before)

    def test_scoped_admission_passes(self):
        result = self.result();self.assertTrue(result['all_green'], result)

    def test_production_authorization_rejected(self):
        self.mutate('candidate/candidate_state.json', lambda x:x.update(production_restart_authorized=True), 'QUALIFICATION_GATE')

    def test_physical_parameter_change_rejected(self):
        self.mutate('candidate/formal/parameters.json', lambda x:x['parameters'][0].update(value=999), 'REGRESSION_GATE')

    def test_support_loss_rejected(self):
        self.mutate('candidate/evidence/sources/Q044/Q044_SPLINE_RESULT.json', lambda x:x['trials'][0]['support_cells'].pop(), 'COMPONENT_AGGREGATION_GATE')

    def test_hull_tampering_rejected(self):
        self.mutate('candidate/evidence/sources/Q044/Q044_SPLINE_RESULT.json', lambda x:x['trials'][0]['support_hull_bounds'].__setitem__(0,0), 'COMPONENT_AGGREGATION_GATE')

    def test_future_science_rejected(self):
        self.mutate('candidate/robustness.json', lambda x:x['items'].append({'id':'INJECTION','finding':'Q'+str(45).zfill(3)+' evidence'}), 'Q_FIREWALL_GATE')

    def test_empty_source_inventory_rejected(self):
        self.mutate('candidate/Q044_PROVENANCE.json', lambda x:x.update(source_files=[]), 'SOURCE_HASH_GATE')

    def test_invented_physical_result_rejected(self):
        def change(x):
            next(e for e in x['entries'] if e['evidence_id']=='EVD-Q044-COMPONENT')['actual_computed_cosmological_result']=True
        self.mutate('candidate/evidence/evidence_registry.json', change, 'QUALIFICATION_GATE')

    def test_references_must_resolve(self):
        self.mutate('candidate/formal/equations.json', lambda x:x['equations'][-1].update(assumption_refs=['MISSING']), 'FORMAL_REFERENCE_GATE')

    def test_prior_snapshot_immutable(self):
        self.mutate('versions/accepted/v0.5/model_state.json', lambda x:x.update(injected=True), 'ACCEPTED_IMMUTABILITY_GATE')

    def test_unsupported_physical_prediction_rejected(self):
        self.mutate('candidate/predictions.json', lambda x:x['predictions'].append({'id':'UNSUPPORTED-PHYSICS','statement':'Q044 establishes a physical model preference.', 'physical_falsification':True,'status':'CONFIRMED'}), 'MODEL_DIFF_GATE')

    def test_unlisted_robustness_addition_rejected(self):
        self.mutate('candidate/robustness.json', lambda x:x['items'].append({'id':'UNLISTED','finding':'unqualified'}), 'MODEL_DIFF_GATE')

    def test_diff_omission_rejected(self):
        self.mutate('candidate/candidate_diff.json', lambda x:x['added'].pop(), 'MODEL_DIFF_GATE')

    def test_same_id_physical_overstatement_rejected(self):
        self.mutate('candidate/robustness.json', lambda x:x['items'][-1].update(finding='Physical model preference established by Q044.'), 'MODEL_DIFF_GATE')

    def test_read_only_validation(self):
        paths=[p for b in ['accepted','candidate','model','evidence','versions','release'] for p in (self.root/b).rglob('*') if p.is_file()]
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        self.result()
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


if __name__ == '__main__':
    unittest.main()
