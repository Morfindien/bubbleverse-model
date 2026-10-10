#!/usr/bin/env python3
"""Read-only scoped Q044 admission, regression and snapshot checks."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE_NAMES={'Q044_SPLINE_INGESTION_RESULT.json','Q044_ENDPOINT_SOURCE_EVIDENCE.json','Q044_SPLINE_VALIDATE.py','Q044_SPLINE_RESULT.json','Q044_SPLINE_INPUTS.json','Q044_SPLINE_CHECKS.json','Q044_SPLINE_ADJOINT.py','Q044_NATIVE_REPLAY.c','Q044_V29_RECOVERY.json','q042_interval_v29.py','cumulative_journal_original.md','cumulative_journal_authorized.md','q_journal.pdf','appendices.pdf','main_book.pdf','q_journal_authorized.txt','appendices_authorized.txt','main_book_authorized.txt'}
PINNED={'Q044_SPLINE_INGESTION_RESULT.json':'9382cb198ab7d519f377e41f29fb8dad3339bde067e3ee16194536cd52e2b7ec','Q044_SPLINE_RESULT.json':'25638274b3898d97f63d1ecbb06739797396659d02270ab80e37d4bdf5b2354e','Q044_SPLINE_INPUTS.json':'f26da12d32eb40c2ae7a8ff618180bb3e495b5f3d183a16f65c09ff97f98fa0c','Q044_SPLINE_CHECKS.json':'5300cd20e40c2ff43ee48ec1a0ad1b9ef487639bd2aa2fae7d1ce9911861948f'}

# Frozen reviewed Q044 additions, independent of mutable candidate metadata.
REVIEWED_ADDITION_SHA256={'observations': 'a3ba3977795ca58a95b6afe3f2362e84772e60624a05799e106722c8e58bb428', 'constraints': '01f14daf888d01b56cf7697cd65561f2be2950f76579715f0a4c504189e77bc0', 'mechanisms': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', 'predictions': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', 'contradictions': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', 'robustness': 'c410b8f6102c984b5cf8a6197d20ccea4ba308f87e5d7d9eba47c05ed8835dd7', 'parameters': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', 'benchmarks': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', 'equations': '8961ec8ffe764d343bbf167cb9ae05182f0cd5ea80b59630b15df33274711668', 'assumptions': '5dbcdbc47f5a94751337b0177b9db0ed98c069e6715a28294f1816f6be5830b1', 'uncertainty': 'fe568613177f2c8c3b487c905265531a007fd61fc05c16e7b98eec2f522aa43e', 'domain_of_validity': '9cdaf956db047ab4ba05d6f6e6c372ec29c7b24c1506ddf8e8c2ef5461983d7d', 'limitations': '0e5c5457796f2f99c72ce0035685bf0b4baf559306d39185f054620ed6aa2528'}

def run_tests(root=ROOT,candidate=False):
    root=Path(root);layer=root/('candidate' if candidate else 'accepted');formal=root/('candidate/formal' if candidate else 'model');evidence=root/('candidate/evidence' if candidate else 'evidence');src=evidence/'sources/Q044';old=root/'versions/accepted/v0.5';rows=[]
    def load(p):return json.loads(p.read_text())
    def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def require(c,m):
        if not c:raise AssertionError(m)
    def gate(name,fn):
        try:rows.append({'id':name,'status':'PASS','detail':fn()})
        except Exception as exc:rows.append({'id':name,'status':'FAIL','detail':f'{type(exc).__name__}: {exc}'})
    provenance=load(root/'candidate/Q044_PROVENANCE.json')
    def sequence():
        c=load(root/'candidate/candidate_state.json');a=load(root/'accepted/model_state.json');e=load(evidence/'evidence_registry.json')
        require(c['target_q']==c['current_q']==c['q_access_end']=='Q044','candidate boundary')
        require(c['previous_accepted_q']=='Q043' and c['previous_accepted_model_version']=='v0.5','sequence gap')
        require(c['candidate_model_version']=='v0.6' and c['candidate_revision']=='R000006','candidate identity')
        require(a['current_q']==a['q_access_end']==('Q043' if candidate else 'Q044'),'accepted boundary')
        require(a['accepted_model_version']==('v0.5' if candidate else 'v0.6'),'accepted version')
        require(e['current_q']==e['q_access_end']=='Q044','evidence boundary')
        return 'Q043/v0.5 -> Q044/v0.6; no missing question'
    gate('Q_SEQUENCE_GATE',sequence)
    def source_hashes():
        inventory=provenance['source_files'];names=[x['archived_name'] for x in inventory]
        require(len(names)==len(SOURCE_NAMES) and set(names)==SOURCE_NAMES,'source inventory missing, duplicated or retargeted')
        for s in inventory:
            p=root/s['path']
            if s['path'].startswith('evidence/') and candidate:p=root/'candidate'/s['path']
            require(p.name==s['archived_name'] and digest(p)==s['sha256'] and p.stat().st_size==s['bytes'],'source bytes changed: '+s['archived_name'])
        for name,sha in PINNED.items():require(digest(src/name)==sha,'original pinned authority changed: '+name)
        ing=load(src/'Q044_SPLINE_INGESTION_RESULT.json')
        for row in ing['audit']['inputs']:
            p=src/row['file']
            if p.exists():require(digest(p)==row['sha256'],'declared reproduction input mismatch')
        checks=load(src/'Q044_SPLINE_CHECKS.json')
        for name,sha in checks['hashes'].items():require(digest(src/name)==sha,'original validation dependency mismatch')
        return {'hashed_sources':len(inventory),'original_pins_verified':len(PINNED)}
    gate('SOURCE_HASH_GATE',source_hashes)
    def qualification():
        ing=load(src/'Q044_SPLINE_INGESTION_RESULT.json');component=load(src/'Q044_SPLINE_RESULT.json');c=load(root/'candidate/candidate_state.json');state=load(layer/('candidate_state.json' if candidate else 'model_state.json'))
        require(ing['q']==component['q']=='Q044','source identity')
        require(ing['final_answer']=='INCONCLUSIVE / INSUFFICIENT_SCIENTIFIC_QUALIFICATION' and ing['scientific_contract_class']=='NOT_AVAILABLE','closure overstatement')
        require(component['result_type']=='CONDITIONAL_MATHEMATICAL_COMPONENT_RESULT' and component['inference_adequacy']=='UNDETERMINED' and component['binary64_native_rounding_error']=='NOT CERTIFIED' and component['complete_V31_history_recovered'] is False,'component qualification lost')
        for d in [c,state,ing,component,provenance,load(evidence/'q_updates/Q044.json')]:require(d['production_restart_authorized'] is False,'production authorized')
        require(c['physical_model_change'] is state['physical_model_change'] is False,'physical model changed')
        entries=[e for e in load(evidence/'evidence_registry.json')['entries'] if e.get('q_id')=='Q044']
        require(len(entries)==8 and len({x['evidence_id'] for x in entries})==8,'Q044 evidence inventory')
        for e in entries:
            require(all(e[k] is False for k in ['physical_falsification','actual_computed_cosmological_result','production_restart_authorized','independent_cosmological_evidence','native_binary_rounding_certified','new_scientific_inference']),'internal component elevated into physics')
            require(e['sha256']==digest(evidence/e['source'].removeprefix('evidence/')),'evidence hash retargeted')
        require(provenance['independent_component_program_rerun'] is False and provenance['native_C_replay_rerun'] is False,'historical diagnostics claimed as fresh replay')
        return 'Conditional component accepted; downstream inference unavailable; no physical verdict or production'
    gate('QUALIFICATION_GATE',qualification)
    def aggregation():
        inputs=load(src/'Q044_SPLINE_INPUTS.json');result=load(src/'Q044_SPLINE_RESULT.json');checks=load(src/'Q044_SPLINE_CHECKS.json');ing=load(src/'Q044_SPLINE_INGESTION_RESULT.json');obs=next(o for o in load(layer/'observations.json')['observations'] if o['id']=='OBS-Q044-SUPPORT-HULLS-001')
        require(len(result['trials'])==len(inputs['trials_certificate'])==2,'trial count')
        count=0
        for cert,t,reported in zip(inputs['trials_certificate'],result['trials'],obs['trials']):
            cells=t['support_cells'];indices=[c['support'] for c in cells]
            require(cert['trial']==t['trial']==reported['trial'],'trial identity')
            require(indices==cert['candidate_indices'] and len(indices)==len(set(indices))==t['support_count'],'support coverage')
            require(all(c['N']==max(3,c['support']) and all(math.isfinite(v) for v in c['tau_bounds']) and c['tau_bounds'][0]<=c['tau_bounds'][1] for c in cells),'native support semantics/finite ordered intervals')
            hull=[min(c['tau_bounds'][0] for c in cells),max(c['tau_bounds'][1] for c in cells)]
            require(hull==t['support_hull_bounds']==reported['bounds'] and hull[1]-hull[0]==t['width']==reported['width'],'hull aggregation')
            require(reported['support_count']==len(cells),'registered support count')
            count+=len(cells)
        require(count==3140 and checks['rational_checks']['exact_rational_fixture_cases']==64 and len(checks['native_replay_cases'])==18,'original diagnostic counts')
        require(ing['independent_program_or_C_replay_rerun_in_this_ingestion'] is False,'historical source altered')
        return {'support_cells_verified':count,'recorded_rational_fixtures':64,'recorded_native_diagnostics':18,'fresh_component_replay':False}
    gate('COMPONENT_AGGREGATION_GATE',aggregation)
    def regression():
        for n,key in [('parameters','parameters'),('benchmarks','benchmarks')]:require(load(formal/(n+'.json'))[key]==load(old/(n+'.json'))[key],'cosmological values changed')
        for n,key in [('observations','observations'),('constraints','constraints'),('mechanisms','mechanisms'),('predictions','predictions'),('contradictions','contradictions'),('robustness','items')]:
            before=load(old/(n+'.json'))[key];after=load(layer/(n+'.json'))[key];require(after[:len(before)]==before,'inherited scientific history changed: '+n)
        for n,key in [('equations','equations'),('assumptions','assumptions'),('uncertainty','uncertainties'),('domain_of_validity','domains'),('limitations','limitations')]:
            before=load(old/(n+'.json'))[key];after=load(formal/(n+'.json'))[key];require(after[:len(before)]==before,'inherited formal state changed: '+n)
        for n in ['input_schema','output_schema','result_registry','external_catalog_registry']:
            before=load(old/(n+'.json'));after=load(formal/(n+'.json'))
            if n in ['result_registry','external_catalog_registry']:
                require(after['q_access_end']=='Q044','public registry boundary')
                before.pop('q_access_end');after.pop('q_access_end')
            require(after==before,'public operation changed: '+n)
        before=load(old/'evidence_registry.json')['entries'];require(load(evidence/'evidence_registry.json')['entries'][:len(before)]==before,'inherited evidence changed')
        return 'Physical parameters, all original histories and public operations preserved; traceable scoped additions only'
    gate('REGRESSION_GATE',regression)
    def model_diff():
        diff=load(root/'candidate/candidate_diff.json');actual={}
        expected={'observations':['OBS-Q044-SUPPORT-HULLS-001'],'constraints':['CON-Q044-NO-DOWNSTREAM-001'],'mechanisms':[],'predictions':[],'contradictions':[],'robustness':['ROB-Q044-COMPONENT-001','ROB-Q044-CLOSURE-001'],'parameters':[],'benchmarks':[],'equations':['EQ-Q044-SUPPORT-ADJOINT'],'assumptions':['ASSUMP-Q044-FIXED-KNOTS','ASSUMP-Q044-SOURCE-RAILS','ASSUMP-Q044-REAL-ARITHMETIC'],'uncertainty':['UNC-Q044-NATIVE-ROUNDING','UNC-Q044-PHYSICAL-CORRELATION'],'domain_of_validity':['DOM-Q044-SUPPORT-COMPONENT'],'limitations':['LIM-Q044-COMPLETE-HISTORY','LIM-Q044-DOWNSTREAM-QUALIFICATION']}
        keys={'robustness':'items','uncertainty':'uncertainties','domain_of_validity':'domains'}
        layer_names=['observations','constraints','mechanisms','predictions','contradictions','robustness']
        for n,ids in expected.items():
            key=keys.get(n,n);before=load(old/(n+'.json'))[key];after=load((layer if n in layer_names else formal)/(n+'.json'))[key]
            tail=after[len(before):];actual[n]=[x['id'] for x in tail]
            require(actual[n]==ids,'unauthorized scientific additions: '+n)
            require(hashlib.sha256(json.dumps(tail,sort_keys=True,separators=(',',':')).encode()).hexdigest()==REVIEWED_ADDITION_SHA256[n],'reviewed scientific definition altered: '+n)
            for obj in tail:
                for flag in ['physical_falsification','actual_computed_cosmological_result','production_restart_authorized','independent_cosmological_evidence','new_scientific_inference']:
                    require(obj.get(flag,False) is False,'unsupported physical qualification: '+n)
        require([x['id'] for x in diff['added']]==sum([actual[n] for n in layer_names],[]),'candidate diff does not enumerate all layer additions')
        for field,n in [('new_equations','equations'),('new_assumptions','assumptions'),('new_uncertainties','uncertainty'),('new_validity_domains','domain_of_validity'),('new_limitations','limitations'),('new_parameters','parameters'),('new_benchmarks','benchmarks')]:require(diff[field]==actual[n],'formal diff mismatch: '+field)
        require(diff['physical_model_change'] is False and diff['new_calculations']==diff['new_domains']==diff['superseded']==diff['resolved_contradictions']==[],'unauthorized capability or scientific revision')
        return 'Exact authorized additions agree with diff; physical histories and predictions admit no new claims'
    gate('MODEL_DIFF_GATE',model_diff)
    def references():
        eids={e['evidence_id'] for e in load(evidence/'evidence_registry.json')['entries']};ass={a['id'] for a in load(formal/'assumptions.json')['assumptions']};domains={d['id'] for d in load(formal/'domain_of_validity.json')['domains']}
        for base in [layer,formal]:
            for p in base.glob('*.json'):
                def walk(x):
                    if isinstance(x,dict):
                        if 'evidence_refs' in x:require(set(x['evidence_refs'])<=eids,'unresolved evidence reference')
                        if 'assumption_refs' in x:require(set(x['assumption_refs'])<=ass,'unresolved assumption reference')
                        for v in x.values():walk(v)
                    elif isinstance(x,list):
                        for v in x:walk(v)
                walk(load(p))
        eq=next(e for e in load(formal/'equations.json')['equations'] if e['id']=='EQ-Q044-SUPPORT-ADJOINT')
        require(eq['domain_ref'] in domains and eq['implementation_operation'] is None,'unqualified public calculation/domain')
        require(len(eq['assumption_refs'])==3 and eq['units']=='dimensionless','component units/conditions')
        require(load(formal/'model_manifest.json')['evidence_refs'][-8:]==[x['evidence_id'] for x in load(evidence/'evidence_registry.json')['entries'][-8:]],'manifest evidence diff')
        return 'Scoped equation, units, assumptions, evidence and validity references resolve'
    gate('FORMAL_REFERENCE_GATE',references)
    def firewall():
        scanned=0
        for base in [layer,formal,evidence]:
            for p in base.rglob('*'):
                if p.is_file() and p.suffix in {'.json','.md','.txt','.py','.c'}:
                    require(not any(int(x)>44 for x in re.findall(r'\bQ-?0*([0-9]{1,5})\b',p.read_text(),re.I)),'unauthorized scientific origin in '+str(p))
                    scanned+=1
        for s in provenance['source_files']:
            if not s['scientific_ingestion']:require(s['path'].startswith('provenance/input_archives/Q044/'),'quarantine leaks into science')
        return {'scanned_files':scanned,'maximum_authorized_q':44,'mixed_boundary_originals':'HASHED_PROVENANCE_ONLY'}
    gate('Q_FIREWALL_GATE',firewall)
    def continuity():
        original=(root/'provenance/input_archives/Q044/cumulative_journal_original.md').read_bytes();marker='# PRESERVED INCOMING JOURNAL — HISTORICAL VERSION\n'.encode();tail=(src/'cumulative_journal_authorized.md').read_bytes()
        require(original.split(marker,1)[1]==tail,'authorized journal bytes changed')
        inherited=load(evidence/'sources/Q043/integration_result.json')['original_91_source_register']
        blocks=[json.loads(b) for b in re.findall(r'```json\s*\n(.*?)\n```',tail.decode(),re.S)]
        require(any(b==inherited for b in blocks),'91-object inherited register missing')
        source=load(evidence/'sources/Q042/ingestion_decision.json');maps={'inherited_claim_maps':source['inherited_claim_maps'],'new_claim_to_source_map':source['new_claim_to_source_map']}
        require(any(isinstance(b,dict) and all(b.get(k)==v for k,v in maps.items()) for b in blocks),'inherited claim maps missing')
        return 'Exact authorized journal tail, 91 source objects and original claim maps preserved'
    gate('SOURCE_CONTINUITY_GATE',continuity)
    def immutable():
        for rel,sha in provenance['protected_input_hashes'].items():
            if not candidate and (rel.startswith(('accepted/','model/')) or rel in ['evidence/evidence_registry.json','release/MODEL_RELEASE_HANDOFF.json','release/MODEL_RELEASE_HANDOFF.md']):continue
            require(digest(root/rel)==sha,'protected prior input mutated: '+rel)
        if not candidate:
            snap=root/'versions/accepted/v0.6';frozen=load(root/'provenance/Q044_SNAPSHOT_MANIFEST.json')
            require(set(p.name for p in snap.iterdir() if p.is_file())==set(frozen['sha256']),'snapshot inventory changed')
            for name,sha in frozen['sha256'].items():require(digest(snap/name)==sha,'snapshot mutated: '+name)
            for base in [layer,formal]:
                for p in base.iterdir():
                    if p.is_file():require(digest(p)==digest(snap/p.name),'live/frozen mismatch')
        return 'Accepted untouched before promotion; previous and current snapshots immutable'
    gate('ACCEPTED_IMMUTABILITY_GATE',immutable)
    def git_identity():
        subprocess.run(['git','cat-file','-e',provenance['model_input_commit']+'^{commit}'],cwd=root,check=True,capture_output=True)
        require(provenance['source_repository_inspection_commit']=='72cf9e92fc794c122f593a77b6a555e6e97f6a2e' and provenance['source_manuscript_commit'] is None,'manuscript falsely attributed to source commit')
        return 'Reachable real model input; separate real source inspection pin; no fabricated manuscript commit'
    gate('REAL_COMMIT_PROVENANCE_GATE',git_identity)
    passed=sum(r['status']=='PASS' for r in rows)
    return {'artifact_type':'Q044_MODEL_UPDATE_VALIDATION','target_q':'Q044','mode':'CANDIDATE' if candidate else 'CURRENT_ACCEPTED','tests':rows,'tests_total':len(rows),'tests_passed':passed,'all_green':passed==len(rows),'non_destructive':True}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',action='store_true');args=ap.parse_args();r=run_tests(candidate=args.candidate)
    for row in r['tests']:print(f"{row['id']}={row['status']} {row['detail']}")
    print(f"Q044_MODEL_TESTS={r['tests_passed']}/{r['tests_total']}")
    raise SystemExit(0 if r['all_green'] else 1)
