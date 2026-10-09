#!/usr/bin/env python3
"""Non-destructive Q042 closure and evidence-scope validator."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def run_tests(root=ROOT, candidate=False):
    root = Path(root)
    layer = root / ('candidate' if candidate else 'accepted')
    formal = root / ('candidate/formal' if candidate else 'model')
    evidence = root / ('candidate/evidence' if candidate else 'evidence')
    rows = []
    def gate(name, fn):
        try:
            detail = fn()
            rows.append({'id': name, 'status': 'PASS', 'detail': detail})
        except Exception as exc:
            rows.append({'id': name, 'status': 'FAIL', 'detail': f'{type(exc).__name__}: {exc}'})
    def load(p): return json.loads(p.read_text(encoding='utf-8'))
    def require(value, message):
        if not value: raise AssertionError(message)
    def items(path, key): return {x['id']: x for x in load(path)[key]}
    def sequence():
        s = load(root/'candidate/candidate_state.json')
        a = load(root/'accepted/model_state.json')
        active_q = a['current_q']
        if not candidate and int(active_q[1:]) > 42:
            s = load(root/'provenance/archive/Q042/candidate_state.json')
            a = load(root/'versions/accepted/v0.4/model_state.json')
        require(s.get('current_q') == 'Q042' and s.get('q_access_end') == 'Q042', 'Q042 candidate missing')
        require(a.get('current_q') == ('Q041' if candidate else 'Q042'), 'accepted sequence mismatch')
        require(s.get('previous_accepted_q') == 'Q041', 'sequence gap')
        require(a.get('accepted_model_version') == ('v0.3' if candidate else 'v0.4'), 'version mismatch')
        e = load(evidence/'evidence_registry.json')
        evidence_q = 'Q042' if candidate else active_q
        require(e.get('current_q') == evidence_q and e.get('q_access_end') == evidence_q, 'evidence boundary mismatch')
        return 'Q041 -> Q042 exact historical sequence; active evidence boundary matches accepted'
    gate('Q_SEQUENCE_GATE', sequence)
    def sources():
        p=load(root/'candidate/Q042_PROVENANCE.json')
        for x in p['source_files']:
            actual=evidence/'sources/Q042'/x['archived_name']
            require(hashlib.sha256(actual.read_bytes()).hexdigest() == x['sha256'], f"source hash mismatch: {x['archived_name']}")
        return {'verified_source_files':len(p['source_files'])}
    gate('SOURCE_HASH_GATE', sources)
    def continuity():
        d=load(evidence/'sources/Q042/ingestion_decision.json')
        a=load(evidence/'sources/Q042/ingestion_audit.json')
        require(d['source_register'] == a['source_register'], 'source objects changed')
        ids=[x['id'] for x in d['source_register']]
        require(len(ids)==91 and len(set(ids))==91, '91-source continuity/uniqueness')
        require(d['inherited_claim_maps']==a['inherited_claim_maps'], 'inherited claim maps changed')
        require(d['new_claim_to_source_map']==a['new_claim_to_source_map'], 'new claim map mismatch')
        return {'source_objects':91, 'claim_maps_preserved':True}
    gate('SOURCE_CONTINUITY_GATE', continuity)
    def closure():
        d=load(evidence/'sources/Q042/ingestion_decision.json')
        ev={x['evidence_id']:x for x in load(evidence/'evidence_registry.json')['entries']}
        e=ev['EVD-Q042-CLOSURE-001']
        require(d['gates']['Q_COMPLETION_GATE']=='PASS_DOCUMENTED_INCONCLUSIVE_EPISTEMIC_CLOSURE','closure source mismatch')
        require(e['status']=='CLOSED_INCONCLUSIVE_GENERAL_FEASIBILITY','closure not preserved')
        require(e['physical_falsification'] is False and e['actual_computed_cosmological_result'] is False,'manufactured physical verdict')
        require(e['reference_truth']=='BLOCKED' and e['numerical_final_result']=='UNRESOLVED','qualification invented')
        require(e['production_restart_authorized'] is False,'production restart')
        require(d['new_tau_values']==0 and d['production_restart_authorized'] is False,'source not no-tau closure')
        return 'Closed investigation; unresolved reference/numerical result; no physical verdict'
    gate('CLOSURE_QUALIFICATION_GATE', closure)
    def certificate():
        c=load(evidence/'sources/Q042/functional_cap_certificate.json')
        k=load(evidence/'sources/Q042/functional_cap_checks.json')
        require(c['cap']==32 and len(k)==8 and all(v is True for v in k.values()),'certificate checks/cap')
        require(c['new_tau_values']==0 and c['new_trajectories']==0,'new execution claimed')
        require({p['trial'] for p in c['proof']}=={'UPPER','LOWER'},'trial set')
        for p in c['proof']:
            exact=lambda h: Fraction.from_float(float.fromhex(h))
            m=exact(p['minimum_upper_bound']['binary64_hex_bounds'][1])
            tail=exact(p['tail_xe_source_bound']['binary64_hex_bounds'][0])
            require(tail>m, 'missing tail can lower the threshold')
            witness=p['33_witnesses']; inds={w['index'] for w in witness}
            require(len(witness)==33 and len(inds)==33,'33 distinct witnesses required')
            require(c['excluded_final_index'] not in inds,'excluded final source node used')
            require(all(exact(w['xe_source_bounds']['binary64_hex_bounds'][0])<=m for w in witness),'exact witness inequality')
            require(p['candidate_count']==len(p['candidate_indices']) and p['candidate_count']>32,'candidate support cap')
            require(p['arithmetic_evidence']['direction_violations']==0,'directed export violation')
            require(p['actual_tau_status']=='NOT COMPUTED' and p['actual_functional_pipeline_status']=='NOT_EXECUTED','conditional result promoted into actual tau')
        return 'Exact-dyadic retained-witness/tail inequalities checked; conditional policy failure only'
    gate('CONDITIONAL_CERTIFICATE_GATE', certificate)
    def physical_preservation():
        for name,key in [('parameters.json','parameters'),('equations.json','equations'),('benchmarks.json','benchmarks')]:
            old=load(root/'versions/accepted/v0.3'/name)[key]
            new=load(formal/name)[key]
            require(old==new,f'unsupported physical/calculation change in {name}')
        require(load(layer/'mechanisms.json')['mechanisms']==load(root/'versions/accepted/v0.3/mechanisms.json')['mechanisms'],'mechanism rescue/destruction')
        return 'Parameters, equations, benchmarks and mechanisms unchanged'
    gate('PHYSICAL_MODEL_PRESERVATION_GATE', physical_preservation)
    def history():
        p=items(layer/'predictions.json','predictions')
        old=items(root/'versions/accepted/v0.3/predictions.json','predictions')
        for pid,entry in old.items():
            require(pid in p,'prediction removed')
            require(p[pid]['statement']==entry['statement'],'prediction rewritten after outcome')
            require(p[pid].get('history',[])[:len(entry.get('history',[]))]==entry.get('history',[]),'prediction history overwritten')
        require(p['PRED-EDE-PORTABILITY-001']['status']=='OPEN','portability verdict invented')
        require(any(x.get('q')=='Q042' and x.get('status')=='INCONCLUSIVE_FEASIBILITY_INVESTIGATION' for x in p['PRED-EDE-PORTABILITY-001']['history']),'Q042 history absent')
        c=items(layer/'contradictions.json','contradictions')
        require(c['CTR-PLANCK-IMPL-001']['status']=='OPEN_NARROWED' and c['CTR-H0-001']['status']=='OPEN','contradiction forced closed')
        return 'Original predictions and open contradictions preserved'
    gate('PREDICTION_CONTRADICTION_GATE', history)
    def scope():
        require('ASSUMP-Q042-FROZEN-INTERVAL-POLICY' in items(formal/'assumptions.json','assumptions'),'conditional assumptions missing')
        require('DOM-Q042-CONDITIONAL-FEASIBILITY' in items(formal/'domain_of_validity.json','domains'),'domain missing')
        u=items(formal/'uncertainty.json','uncertainties')
        require({'UNC-Q042-REFERENCE-QUALIFICATION','UNC-Q042-KILLED-TAIL'}<=set(u),'uncertainty missing')
        l=items(formal/'limitations.json','limitations')
        require({'LIM-Q042-REFERENCE','LIM-Q042-GENERAL-FEASIBILITY','LIM-Q042-NO-PRODUCTION'}<=set(l),'scope limitations missing')
        return 'Frozen construction, missing accuracy budgets, partial history and no restart explicit'
    gate('FORMAL_SCOPE_GATE', scope)
    def firewall():
        max_q = 42 if candidate else int(load(root/'accepted/model_state.json')['q_access_end'][1:])
        for base in [layer,formal,evidence]:
            for path in base.rglob('*'):
                if path.is_file() and path.suffix in {'.json','.md','.txt'}:
                    nums=[int(x) for x in re.findall(r'\bQ-?0*([0-9]{1,5})\b',path.read_text(encoding='utf-8'),re.I)]
                    require(not any(n>max_q for n in nums), f'boundary contamination: {path}')
        return f'No scientific evidence beyond accepted Q{max_q:03d}; Q042 source identity remains hashed'
    gate('Q_FIREWALL_GATE', firewall)
    def immutable():
        p=load(root/'candidate/Q042_PROVENANCE.json')
        expected=p['protected_input_hashes']
        for rel,sha in expected.items():
            if rel.startswith('accepted/') and not candidate: continue
            require(hashlib.sha256((root/rel).read_bytes()).hexdigest()==sha,f'protected input mutated: {rel}')
        return {'protected_input_files':len(expected),'accepted_checked_before_promotion':candidate}
    gate('ACCEPTED_IMMUTABILITY_GATE', immutable)
    def refs():
        p=load(root/'candidate/Q042_PROVENANCE.json')
        subprocess.run(['git','cat-file','-e',p['model_input_commit']+'^{commit}'],cwd=root,check=True,capture_output=True)
        return {'reachable_model_input_commit':p['model_input_commit']}
    gate('REAL_COMMIT_PROVENANCE_GATE', refs)
    passed=sum(x['status']=='PASS' for x in rows)
    return {'artifact_type':'Q042_MODEL_UPDATE_VALIDATION','target_q':'Q042','mode':'CANDIDATE' if candidate else 'CURRENT_ACCEPTED','tests':rows,'tests_total':len(rows),'tests_passed':passed,'all_green':passed==len(rows),'non_destructive':True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',action='store_true');ap.add_argument('--root',type=Path,default=ROOT)
    args=ap.parse_args();r=run_tests(args.root,args.candidate)
    for x in r['tests']:print(f"{x['id']}={x['status']} {x['detail']}")
    print(f"Q042_MODEL_TESTS={r['tests_passed']}/{r['tests_total']}")
    return 0 if r['all_green'] else 1
if __name__=='__main__':raise SystemExit(main())
