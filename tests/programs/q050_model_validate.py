#!/usr/bin/env python3
"""Bounded Q050 admission and scope validation. No new scientific solver run."""
import hashlib,json,re,sys,subprocess
from pathlib import Path
from q050_contract_validate import check_certificate,mutation_campaign
ROOT=Path(__file__).resolve().parents[2]
def run_tests(root=ROOT):
 root=Path(root);rows=[]
 def load(p):return json.loads((root/p).read_text())
 def sha(p):return hashlib.sha256((root/p).read_bytes()).hexdigest()
 def req(v,m):
  if not v:raise AssertionError(m)
 def gate(name,fn):
  try:rows.append({'id':'Q050-'+name,'status':'PASS','detail':fn()})
  except Exception as e:rows.append({'id':'Q050-'+name,'status':'FAIL','detail':str(e)})
 q=load('evidence/q_updates/Q050.json');a=load('accepted/model_state.json')
 def identity():
  req(a['current_q']==a['q_access_end']==a['processed_through_q']=='Q050','current identity')
  req(a['accepted_model_version']=='v0.12' and a['model_revision']=='R000012','version')
  req(load('versions/accepted/v0.11/model_state.json')['current_q']=='Q049','predecessor')
  req(q['publication_status']=='CLOSED' and q['scientific_status']=='RESOLVED_WITHIN_SCOPE','closure')
  req(a==load('candidate/candidate_state.json'),'candidate/accepted mismatch')
  return 'Sequential Q049/v0.11 -> Q050/v0.12, original bounded closure'
 gate('identity',identity)
 def sources():
  ev={x['evidence_id']:x for x in load('evidence/evidence_registry.json')['entries']}
  for x in load('provenance/Q050_INPUT_MANIFEST.json')['inputs']:
   req(sha(x['source'])==x['sha256'],'changed source '+x['source']);req(ev[x['evidence_id']]==x,'evidence binding')
  req(sha('evidence/sources/Q050/Q050_GLOBAL_LITERAL_SELECTOR_EXTENSION_CERTIFICATE_V1.json')=='14f281a158e57cf2052ec05b5af6685e341155a9a09d90c241476c746556dacb','original certificate bytes')
  req(all(e in ev for e in q['evidence_refs']),'dangling evidence')
  return 'Exact original certificate and every registered bounded evidence object verified'
 gate('sources',sources)
 def contract():
  c=load('evidence/sources/Q050/Q050_GLOBAL_LITERAL_SELECTOR_EXTENSION_CERTIFICATE_V1.json');t=load('provenance/input_archives/Q050/Q050_NEXT_MATHEMATICS_TASK_GLOBAL_LITERAL_SELECTOR_EXTENSION_V1.json');v=check_certificate(c,t);m=mutation_campaign(c,t)
  req(v['status']=='PASS','contract checks failed');req(len(m)==7 and all(x['status']=='REJECTED' and x['input_changed'] and x['failed_checks'] for x in m),'mutation control not executed/rejected')
  add=load('provenance/Q050_CONTRACT_VALIDATION_ADDENDUM_V2.json')
  req(add['checks']==v['checks'] and add['mutation_controls']==m,'addendum is stale')
  req(add['checker_sha256']==sha('tests/programs/q050_contract_validate.py'),'checker identity')
  return '13 explicit contract checks; seven distinct mutated inputs actually checked and rejected; not independent theorem proof'
 gate('contract',contract)
 def scope():
  req(q['existence_proved_within_scope'] is True and q['conditional_on_fixed_admitted_background'] is True,'existence scope')
  for k in ['uniqueness_proved','background_existence_proved','cosmological_reachability_proved','native_fidelity_proved','small_effect_established','new_observation','physical_model_change','production_restart_authorized','next_q_authorized']:req(q[k] is False,'overclaim '+k)
  req(q['domain_z']==[0,810] and q['held_helium_q']==['1/1000000','0'],'domain')
  req(a['physical_model_change'] is False and a['production_restart_authorized'] is False and a['next_q_authorized_by_this_run'] is False,'state overclaim')
  return 'Conditional existence only; uniqueness/native/smallness/background existence remain unestablished'
 gate('scope',scope)
 def inheritance():
  old=root/'versions/accepted/v0.11'
  for p,key in [('accepted/observations.json','observations'),('accepted/mechanisms.json','mechanisms'),('accepted/predictions.json','predictions'),('accepted/contradictions.json','contradictions'),('model/parameters.json','parameters'),('model/equations.json','equations'),('model/benchmarks.json','benchmarks')]:req(load(p)[key]==json.loads((old/Path(p).name).read_text())[key],'scientific quantity changed '+p)
  for p,key in [('accepted/constraints.json','constraints'),('accepted/robustness.json','items'),('model/assumptions.json','assumptions'),('model/limitations.json','limitations'),('model/uncertainty.json','uncertainties'),('model/domain_of_validity.json','domains'),('evidence/evidence_registry.json','entries')]:
   before=json.loads((old/Path(p).name).read_text())[key];req(load(p)[key][:len(before)]==before,'historical prefix changed '+p)
  b=json.loads((old/'model_state.json').read_text())
  for k,v in b.items():
   if k.startswith('q048_') or k.startswith('q049_'):req(a[k]==v,'historical state changed '+k)
  req(load('evidence/q_updates/Q049.json')==json.loads((old/'q_update.json').read_text()),'Q049 historical result altered')
  return 'Prior scientific entries, Q048 debt and Q049 original record preserved exactly'
 gate('inheritance',inheritance)
 def references():
  ev={x['evidence_id'] for x in load('evidence/evidence_registry.json')['entries']};ass={x['id'] for x in load('model/assumptions.json')['assumptions']};eq={x['id'] for x in load('model/equations.json')['equations']}
  def walk(o):
   if isinstance(o,dict):
    for k,v in o.items():
     if k=='evidence_refs':req(set(v)<=ev,'evidence ref')
     if k=='assumption_refs':req(set(v)<=ass,'assumption ref')
     if k=='equation_refs':req(set(v)<=eq,'equation ref')
     walk(v)
   elif isinstance(o,list):
    for v in o:walk(v)
  for folder in ['accepted','model']:
   for p in (root/folder).glob('*.json'):walk(json.loads(p.read_text()))
  return 'Evidence, assumption and equation references resolve'
 gate('references',references)
 def firewall():
  paths=list((root/'accepted').glob('*.json'))+list((root/'model').glob('*.json'))+[root/'evidence/evidence_registry.json',root/'evidence/q_updates/Q050.json']
  for p in paths:
   ns=[int(n) for n in re.findall(r'\bQ-?0*([0-9]{1,5})\b',p.read_text(),re.I)];req(not ns or max(ns)<=50,'future-Q scientific state '+str(p))
  return 'Current scientific projections contain no later Q identifiers; raw source routing metadata is not admitted science'
 gate('firewall',firewall)
 def snapshot():
  snap=root/'versions/accepted/v0.12';m=load('provenance/Q050_SNAPSHOT_MANIFEST.json')['sha256'];req({p.name for p in snap.iterdir() if p.is_file()}==set(m),'snapshot inventory')
  for name,h in m.items():
   req(sha('versions/accepted/v0.12/'+name)==h,'snapshot changed '+name)
   paths=[root/'accepted'/name,root/'model'/name]
   if name=='model_state.json':paths.append(root/'candidate/candidate_state.json')
   if name=='candidate_diff.json':paths.append(root/'candidate/candidate_diff.json')
   if name=='evidence_registry.json':paths.append(root/'evidence/evidence_registry.json')
   if name=='q_update.json':paths.append(root/'evidence/q_updates/Q050.json')
   for p in paths:
    if p.is_file():req(p.read_bytes()==(snap/name).read_bytes(),'live/snapshot mismatch '+name)
  return 'New frozen snapshot matches exact proposed accepted/formal/evidence tree'
 gate('snapshot',snapshot)
 passed=sum(x['status']=='PASS' for x in rows);return {'artifact_type':'Q050_MODEL_VALIDATION','tests':rows,'tests_total':len(rows),'tests_passed':passed,'all_green':passed==len(rows)}
if __name__=='__main__':
 r=run_tests();print(json.dumps(r,indent=2));raise SystemExit(0 if r['all_green'] else 1)
