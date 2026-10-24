#!/usr/bin/env python3
"""Read-only Q049 admission; does not re-execute historical producer/verifier runs."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[2]
CERT_SHA='c7b32ce22a1b61063d6c5e936df15d0b8d97579037fd1bb167ca0ac62d5455e8'
VERIFIER_SHA='830ba5beeec0693f3aa08ea7f441abf41777933a99f11f29be434cd8914cf9e1'

def run_tests(root=ROOT):
    root=Path(root); rows=[]
    def load(p):return json.loads((root/p).read_text())
    def sha(p):return hashlib.sha256((root/p).read_bytes()).hexdigest()
    def req(value,message):
        if not value:raise AssertionError(message)
    def gate(name,fn):
        try:rows.append({'id':'Q049-'+name,'status':'PASS','detail':fn()})
        except Exception as e:rows.append({'id':'Q049-'+name,'status':'FAIL','detail':f'{type(e).__name__}: {e}'})
    def identity():
        a=load('accepted/model_state.json');q=load('evidence/q_updates/Q049.json')
        req(a['current_q']==a['q_access_end']==a['processed_through_q']=='Q049','Q049 identity')
        req(a['accepted_model_version']=='v0.11' and a['model_revision']=='R000011','model version')
        req(load('versions/accepted/v0.10/model_state.json')['current_q']=='Q048','predecessor')
        req(q['publication_status']=='CLOSED' and q['scientific_status']=='CONDITIONALLY_SUPPORTED','closure scope')
        req(q['source_canonical_id_status']=='LOCAL_ID_CANONICAL_WRITEBACK_UNVERIFIED','source identity overclaim')
        return 'Sequential Q049 closure under explicit conditional scope; source local IDs preserved'
    gate('identity',identity)
    def scope():
        q=load('evidence/q_updates/Q049.json')
        req(q['bound_dimensionless']=='46.67050453' and q['domain_z']==[0,810] and q['configuration']=='hillipop-ede_n3','cap/domain')
        req(q['conditional_on_existing_continuations'] is True,'existence condition removed')
        for k in ['existence_proved','uniqueness_proved','native_fidelity_proved','small_effect_established','physical_model_change','production_restart_authorized','new_observation','next_q_authorized']:req(q[k] is False,'overclaim: '+k)
        req(q['actual_difference_value'] is None and q['actual_difference_sign'] is None,'actual effect fabricated')
        a=load('accepted/model_state.json')
        req(a['physical_model_change'] is False and a['production_restart_authorized'] is False and a['next_q_authorized_by_this_run'] is False,'state overclaim')
        c=next(x for x in load('accepted/constraints.json')['constraints'] if x['id']=='CON-Q049-CONDITIONAL-TAIL-CAP')
        req(c['value']=='46.67050453' and c['units']=='dimensionless' and c['evidence_grade']=='CONDITIONAL' and c['epistemic_type']=='DERIVED','constraint semantics')
        return 'No smallness, sign, positive effect floor, existence, uniqueness, native or downstream inference is admitted'
    gate('scope',scope)
    def sources():
        manifest=load('provenance/Q049_INPUT_MANIFEST.json');ev=load('evidence/evidence_registry.json')['entries'];em={x['evidence_id']:x for x in ev}
        req(len(em)==len(ev),'duplicate evidence IDs')
        for row in manifest['inputs']:
            req(sha(row['path'])==row['sha256'],'input bytes changed: '+row['path'])
            req(em[row['evidence_id']]['sha256']==row['sha256'] and em[row['evidence_id']]['source']==row['path'],'evidence binding')
        req(sha('evidence/sources/Q049/Q049_V2_GLOBAL_BOUND_RESULT.json')==CERT_SHA,'original producer digest')
        req(sha('evidence/sources/Q049/Q049_V2_INDEPENDENT_VERIFICATION.json')==VERIFIER_SHA,'original verifier digest')
        for eid in load('evidence/q_updates/Q049.json')['evidence_refs']:req(eid in em,'dangling evidence reference')
        return 'All seven bounded source objects match exact registered SHA256; producer/verifier match journal-published identities'
    gate('sources',sources)
    def exact_certificate():
        p=load('evidence/sources/Q049/Q049_V2_GLOBAL_BOUND_RESULT.json');v=load('evidence/sources/Q049/Q049_V2_INDEPENDENT_VERIFICATION.json')
        req(p['check_count']==len(p['checks'])==46 and all(x is True for x in p['checks'].values()),'producer historical check inventory')
        req(v['check_count']==len(v['checks'])==33 and v['status']=='PASS' and all(x is True for x in v['checks'].values()),'verifier historical check inventory')
        cap=Fraction('46.67050453');lo=Fraction(p['bound_formula_enclosure_lo']);hi=Fraction(p['bound_formula_enclosure_hi'])
        req(0<lo<=hi<=cap and Fraction(v['independent_upper_rational'])<=cap,'invalid outward rounding')
        req(Fraction(p['safe_decimal_upper'])==cap and Fraction(p['absolute_delta_tau_upper_exact'])==hi,'certificate cap mismatch')
        req(Fraction(p['swift_denominator_global_lower'])>0 and Fraction(v['independent_swift_denominator_lower'])>0,'denominator positivity')
        req(Fraction(p['pointwise_delta_xe_cap'])==Fraction(1000001,1000000),'electron envelope')
        req(Fraction(p['thermal_ratio_lower_global'])==Fraction(49,40550),'thermal floor')
        req(v['producer_result_sha256']==CERT_SHA,'verifier source binding')
        req(p['no_IVP'] is True and p['no_native'] is True and p['V154_consumed'] is False,'historical execution semantics')
        return 'Stored 46/33 checks inspected, not re-executed; exact rational upper endpoints lie below safe decimal cap'
    gate('exact-certificate',exact_certificate)
    def inheritance():
        old=root/'versions/accepted/v0.10'
        for cur,key in [('accepted/observations.json','observations'),('accepted/mechanisms.json','mechanisms'),('accepted/predictions.json','predictions'),('accepted/contradictions.json','contradictions'),('model/parameters.json','parameters'),('model/benchmarks.json','benchmarks')]:
            req(load(cur)[key]==json.loads((old/Path(cur).name).read_text())[key],'inherited quantity changed: '+cur)
        for cur,key in [('accepted/constraints.json','constraints'),('accepted/robustness.json','items'),('model/assumptions.json','assumptions'),('model/equations.json','equations'),('model/uncertainty.json','uncertainties'),('model/domain_of_validity.json','domains'),('model/limitations.json','limitations'),('evidence/evidence_registry.json','entries')]:
            before=json.loads((old/Path(cur).name).read_text())[key];req(load(cur)[key][:len(before)]==before,'historical entry changed: '+cur)
        a=load('accepted/model_state.json');b=json.loads((old/'model_state.json').read_text())
        for k in b:
            if k.startswith('q048_'):req(a[k]==b[k],'Q048 historical state changed: '+k)
        for name in ['input_schema.json','output_schema.json','result_registry.json','external_catalog_registry.json']:
            before=json.loads((old/name).read_text());after=load('model/'+name);before.pop('q_access_end',None);after.pop('q_access_end',None);req(before==after,'public interface changed: '+name)
        return 'All inherited scientific entries, Q048 state and public operations preserved'
    gate('inheritance',inheritance)
    def references():
        ev={x['evidence_id'] for x in load('evidence/evidence_registry.json')['entries']}
        assumptions={x['id'] for x in load('model/assumptions.json')['assumptions']}
        eqs={x['id'] for x in load('model/equations.json')['equations']}
        for folder in ['accepted','model']:
            for path in (root/folder).glob('*.json'):
                d=json.loads(path.read_text())
                def walk(o):
                    if isinstance(o,dict):
                        for k,v in o.items():
                            if k=='evidence_refs':req(all(i in ev for i in v),'dangling evidence')
                            if k=='assumption_refs':req(all(i in assumptions for i in v),'dangling assumption')
                            if k=='equation_refs':req(all(i in eqs for i in v),'dangling equation')
                            walk(v)
                    elif isinstance(o,list):
                        for v in o:walk(v)
                walk(d)
        return 'Evidence, assumption and equation references resolve; documented equation has no new public operation'
    gate('references',references)
    def firewall():
        paths=list((root/'accepted').glob('*.json'))+list((root/'model').glob('*.json'))+[root/'evidence/evidence_registry.json',root/'evidence/q_updates/Q049.json']+list((root/'evidence/sources/Q049').glob('*'))
        for p in paths:
            nums=[int(x) for x in re.findall(r'\bQ-?0*([0-9]{1,5})\b',p.read_text(),flags=re.I)]
            req(not nums or max(nums)<=49,'boundary contamination: '+str(p.relative_to(root)))
        return 'Current scientific state and bounded source text contain no later scientific Q identifiers'
    gate('firewall',firewall)
    def snapshot():
        frozen=load('provenance/Q049_SNAPSHOT_MANIFEST.json');snap=root/'versions/accepted/v0.11'
        req({p.name for p in snap.iterdir() if p.is_file()}==set(frozen['sha256']),'snapshot inventory')
        for name,digest in frozen['sha256'].items():
            req(hashlib.sha256((snap/name).read_bytes()).hexdigest()==digest,'snapshot hash: '+name)
            candidates=[root/'accepted'/name,root/'model'/name]
            if name=='model_state.json':candidates.append(root/'candidate/candidate_state.json')
            if name=='candidate_diff.json':candidates.append(root/'candidate/candidate_diff.json')
            if name=='evidence_registry.json':candidates.append(root/'evidence/evidence_registry.json')
            if name=='q_update.json':candidates.append(root/'evidence/q_updates/Q049.json')
            for p in candidates:
                if p.is_file():req(p.read_bytes()==(snap/name).read_bytes(),'live snapshot mismatch: '+str(p))
        return 'Frozen v0.11 inventory and live scientific/formal state agree exactly'
    gate('snapshot',snapshot)
    passed=sum(r['status']=='PASS' for r in rows)
    return {'artifact_type':'Q049_MODEL_VALIDATION','target_q':'Q049','tests':rows,'tests_total':len(rows),'tests_passed':passed,'all_green':passed==len(rows)}

if __name__=='__main__':
    r=run_tests()
    for row in r['tests']:print(row['id']+'='+row['status']+' '+row['detail'])
    print('Q049_MODEL_TESTS='+str(r['tests_passed'])+'/'+str(r['tests_total']))
    raise SystemExit(0 if r['all_green'] else 1)
