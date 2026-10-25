#!/usr/bin/env python3
"""Versioned model-side proof-contract addendum, not an independent theorem prover."""
import copy,json,math,sys
from fractions import Fraction
from pathlib import Path
COMPONENTS=('GLOBAL_1_AWAY_FROM_INTERFACE','GLOBAL_2_ALL_LOCAL_GATES','GLOBAL_3_INVARIANT_CONTINUATION','GLOBAL_4_ZENO_ACCUMULATION','GLOBAL_5_REIONIZATION_FIXED_TIME')
def check_certificate(c,t):
 rows=[]
 def check(name,fn):
  try:ok=bool(fn())
  except (KeyError,TypeError,ValueError,ZeroDivisionError):ok=False
  rows.append({'id':name,'status':'PASS' if ok else 'FAIL'})
 def text(k):return c['global_components'][k]['reason'].lower()
 check('identity',lambda:c['task_id']==t['task_id'] and c['question_sha256']==t['question_sha256'] and c['exact_question']==t['exact_question'] and c['current_q']==c['target_q']=='Q050')
 check('closure',lambda:c['answer']=='YES' and c['q050_closure']['completion_gate']=='SATISFIED' and c['q050_closure']['workflow_state']=='CLOSED')
 check('exact_five_components',lambda:set(c['global_components'])==set(COMPONENTS) and all(c['global_components'][k]['status']=='PASS' and c['global_components'][k]['reason'] for k in COMPONENTS))
 check('regularity_and_denominators',lambda:all(s in text(COMPONENTS[0]) for s in ('locally lipschitz','positive','denominators')))
 check('pion_local_gate',lambda:c['inherited_local_gates']['pion_hmla_swift']['status'].startswith('CLEARED') and 'literal' in c['inherited_local_gates']['pion_hmla_swift']['literal_local_lemma'])
 check('peebles_tangent',lambda:c['inherited_local_gates']['peebles_ratio_exact_tangent']['status']=='CLEARED' and c['inherited_local_gates']['peebles_ratio_exact_tangent']['certificate'].startswith('v_uu < -1/10') and c['inherited_local_gates']['peebles_ratio_exact_tangent']['equality_arm']=='PEEBLES')
 check('hydrogen_and_thermal_safety',lambda:all(s in text(COMPONENTS[2]) for s in ('hstar<1','compact','a-priori')) and Fraction(c['global_components'][COMPONENTS[2]]['global_v_lower_exact'])==Fraction(49,40550) and math.isclose(c['global_components'][COMPONENTS[2]]['global_v_lower_decimal'],49/40550,rel_tol=1e-14))
 check('bounded_zeno_restart',lambda:all(s in text(COMPONENTS[3]) for s in ('uniformly bounded','lipschitz','limit','restarts','maximality')))
 check('maximal_endpoint_restart',lambda:len(c['maximal_extension_theorem']['proof_skeleton'])>=6 and any('local existence' in s.lower() and 'extends' in s.lower() for s in c['maximal_extension_theorem']['proof_skeleton']) and c['maximal_extension_theorem']['z0_reached'] is True)
 check('fixed_time_dispatch',lambda:all(s in text(COMPONENTS[4]) for s in ('bounded','affine','caratheodory','fixed-time')))
 check('threshold_order',lambda:0<c['threshold_separation']['reionization_start_decimal']<c['threshold_separation']['TR_MIN_forced_peebles_decimal']<c['threshold_separation']['peebles_tangent_upper_decimal']<c['threshold_separation']['swift_fit_lower_1775K_decimal']<810)
 check('initial_domain_and_two_arms',lambda:set(c['state']['q_values'])=={'1/1000000','0'} and Fraction(c['state']['initial_domain']['h_upper'])<1 and Fraction(c['state']['initial_domain']['v_lower'])>0)
 check('claim_firewall',lambda:any('uniqueness is not claimed' in s for s in c['claim_firewall']) and any(s.startswith('No selector smoothing, convexification') for s in c['claim_firewall']) and any(s.startswith('No native/P6') for s in c['claim_firewall']) and any('existence is not proved here' in s for s in c['claim_firewall']))
 return {'status':'PASS' if all(x['status']=='PASS' for x in rows) else 'FAIL','checks':rows}
def mutation_campaign(c,t):
 changes=[('drop_global1_regular',lambda m:m['global_components'].pop(COMPONENTS[0])),('drop_pion_local_gate',lambda m:m['inherited_local_gates']['pion_hmla_swift'].update(status='UNRESOLVED')),('drop_peebles_tangent',lambda m:m['inherited_local_gates']['peebles_ratio_exact_tangent'].update(certificate='NOT_ESTABLISHED')),('allow_unbounded_field_at_zeno',lambda m:m['global_components'][COMPONENTS[3]].update(reason='Fields may be unbounded.')),('remove_endpoint_restart',lambda m:m['maximal_extension_theorem'].update(proof_skeleton=[])),('allow_h_to_reach_native_singularity',lambda m:m['global_components'][COMPONENTS[2]].update(reason='No hydrogen safety bound.')),('convexify_selector',lambda m:m.update(claim_firewall=[s for s in m['claim_firewall'] if 'convexification' not in s]))]
 rows=[]
 for name,mutate in changes:
  m=copy.deepcopy(c);mutate(m);result=check_certificate(m,t)
  rows.append({'id':name,'input_changed':m!=c,'status':'REJECTED' if result['status']=='FAIL' else 'ACCEPTED','failed_checks':[x['id'] for x in result['checks'] if x['status']=='FAIL']})
 return rows
if __name__=='__main__':
 c=json.loads(Path(sys.argv[1]).read_text());t=json.loads(Path(sys.argv[2]).read_text());r=check_certificate(c,t);r['mutation_controls']=mutation_campaign(c,t) if r['status']=='PASS' else [];r['limited_semantics']='Checks explicit proof-contract coverage and scope. Does not establish underlying analytical premises or independently prove the theorem.'
 r['mutations_executed']=len(r['mutation_controls']);r['mutations_rejected']=sum(x['status']=='REJECTED' for x in r['mutation_controls']);r['status']='PASS' if r['status']=='PASS' and r['mutations_rejected']==7 else 'FAIL';print(json.dumps(r,indent=2));raise SystemExit(0 if r['status']=='PASS' else 1)
