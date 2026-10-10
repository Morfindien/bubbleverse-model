#!/usr/bin/env python3
"""Read-only Q045 technical-evidence admission and physical-inference firewall."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[2]
FINAL_PIN='f6a214d6ed8b58619a27f0f40df4bfbfe892056b4eb0985f24e662fa5fe0ed26'
ARTIFACT_PIN='75cb18ca3c124f90aaa890147aea4f39656ca78b17d6a2d24f5e9a94836c1e08'
MODEL_INPUT='bba3528250b3d56c451bf5ca363b0d75120acb03'
SOURCE_INPUT='a9a5777b5923f32930cd9c84a49227ba36249326'
REVIEWED={'constraints':'019d8218d11f0c5e3a788b4b804764b4b04a2d5c9271eb3d92ad1a7524de24d4','domain_of_validity':'7eb2297dc215eba223586ac93f696696e6c2dc3cfb4d201af70f45473e1b6f5c','limitations':'3ae29bf342eddbba4cb882df112d8a30c90d41646800d5f5049ab51d950b6174','robustness':'24f0d724888b0e3a8f44ddce11c493826d2235b611ddf0d400aef575e11efffb','uncertainty':'d6bc20f5e1942bc7b376d4ebaeef52d4ed620d576a74e9a8a64732627907e23d'}
SOURCE_INVENTORY_PIN='8703da4f7c6ca72b90b3522beb1f73e74cb9588b8c3b88095664dc8d54fa0cc4'
PROTECTED_INPUT_PIN='c72db6ff5184620e062b98283852c46c6590c107e3551228fc24d323f1ebb024'
LAYERS={'observations':'observations','constraints':'constraints','mechanisms':'mechanisms','predictions':'predictions','contradictions':'contradictions','robustness':'items'}
FORMAL={'parameters':'parameters','benchmarks':'benchmarks','equations':'equations','assumptions':'assumptions','uncertainty':'uncertainties','domain_of_validity':'domains','limitations':'limitations'}
def run_tests(root=ROOT,candidate=False):
 root=Path(root);layer=root/('candidate' if candidate else 'accepted');formal=root/('candidate/formal' if candidate else 'model');evidence=root/('candidate/evidence' if candidate else 'evidence');src=evidence/'sources/Q045';old=root/'versions/accepted/v0.6';rows=[]
 def load(p):return json.loads(p.read_text())
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 def req(c,m):
  if not c:raise AssertionError(m)
 def gate(name,fn):
  try:rows.append({'id':'Q045_'+name,'status':'PASS','detail':fn()})
  except Exception as e:rows.append({'id':'Q045_'+name,'status':'FAIL','detail':f'{type(e).__name__}: {e}'})
 prov=load(root/'candidate/Q045_PROVENANCE.json');c=load(root/'candidate/candidate_state.json');s=load(layer/('candidate_state.json' if candidate else 'model_state.json'))
 def sequence():
  a=load(root/'accepted/model_state.json');ev=load(evidence/'evidence_registry.json')
  req(c['target_q']==c['current_q']==c['q_access_end']=='Q045','candidate identity')
  req(c['previous_accepted_q']=='Q044' and c['previous_accepted_model_version']=='v0.6','Q sequence gap')
  req(c['candidate_model_version']=='v0.7' and c['candidate_revision']=='R000007','candidate revision')
  req(a['current_q']==('Q044' if candidate else 'Q045') and a['accepted_model_version']==('v0.6' if candidate else 'v0.7'),'accepted identity')
  req(ev['q_access_end']==ev['current_q']=='Q045' and load(old/'model_state.json')['current_q']=='Q044','evidence/baseline boundary')
  return 'Q044/v0.6 -> Q045/v0.7; no skipped Q'
 gate('SEQUENCE_GATE',sequence)
 def sources():
  inventory=prov['source_files'];req(hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()==SOURCE_INVENTORY_PIN,'source inventory retargeted');req(len(inventory)==25 and len({x['path'] for x in inventory})==25,'missing, duplicate or extra source')
  for row in inventory:
   p=root/row['path']
   if candidate and row['path'].startswith('evidence/'):p=root/'candidate'/row['path']
   req(p.is_file() and p.name==row['archived_name'] and sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],'source changed: '+row['path'])
   req(row['scientific_ingestion'] or row['path'].startswith('provenance/input_archives/Q045/'),'raw source entered evidence')
  req(sha(src/'q045_reference_history_final_v2.json')==FINAL_PIN,'original workflow final changed')
  req(sha(root/'provenance/input_archives/Q045/workflow_artifact.zip')==ARTIFACT_PIN,'original artifact changed')
  d=load(src/'q045_reference_history_final_v2.json')
  req(len(d['derived_files_sha256'])==12,'derived inventory')
  for name,digest in d['derived_files_sha256'].items():req(sha(src/name)==digest,'derived product differs: '+name)
  req(sha(src/'q045_reference_history_contract_v2.json')==d['config_sha256'],'execution contract mismatch')
  return {'source_files':25,'derived_hashes':12,'original_final_and_artifact_pins':'PASS'}
 gate('SOURCE_HASH_GATE',sources)
 def qualification():
  d=load(src/'q045_reference_history_final_v2.json');u=load(evidence/'q_updates/Q045.json')
  req(d['q']=='Q-045' and d['program_id']=='Q045-REFHIST-V2','execution identity')
  req(d['reference_truth_gate']=='UNQUALIFIED' and d['final_result_gate']=='UNRESOLVED' and d['reference_error_bound'] is None,'physical qualification overstated')
  req(d['actual_computed_scientific_result']=='NOT_YET_COMPUTED' and d['new_theory_evaluations']==0 and d['execution_mode']=='OFFLINE_ARTIFACT_REANALYSIS_ONLY','physical computation invented')
  req(d['preserved_original_final']['reference_treatments_executed']==[],'isolated treatments invented')
  for obj in [d,c,s,prov,u]:req(obj['production_restart_authorized'] is False,'production authorized')
  req(c['physical_model_change'] is s['physical_model_change'] is False,'physical model changed')
  for obj in [c,s]:
   req(obj['q045_reference_truth_gate']=='UNQUALIFIED' and obj['q045_final_result_gate']=='UNRESOLVED' and obj['q045_investigation_status']=='CLOSED_INCONCLUSIVE_PHYSICAL_MATERIALITY' and obj['q045_result']=='R-Q045-REFHIST-INGESTION-002','mirrored physical qualification overstated')
  req(u['reference_truth_gate']=='UNQUALIFIED' and u['final_result_gate']=='UNRESOLVED' and u['physical_model_change'] is False,'summary physical qualification overstated')
  req(prov['full_physical_reference_qualified'] is False and prov['native_or_history_solver_rerun'] is False and prov['source_repository_modified'] is False,'provenance physical qualification overstated')
  req(prov['original_post_run_closure_journal_unavailable'] is True and prov['closure_authority']=='OPERATOR_AUTHORIZED_Q045_MANUSCRIPT_EXCERPT' and prov['source_manuscript_commit'] is None,'closure availability/origin overstated')
  for obj in [c,s]:req(obj['source_repository_commit']==SOURCE_INPUT and obj['input_documents']==prov['source_files'],'state provenance retargeted')
  req(u['result']=='CLOSED_INCONCLUSIVE_PHYSICAL_MATERIALITY' and u['original_closure_ingestion_file_available'] is False and u['reported_closure_journal_hash_verified'] is False,'source gap concealed')
  text=(src/'q_journal_authorized.txt').read_text();req('CLOSED' in text and 'R-Q045-REFHIST-INGESTION-002' in text and 'UNQUALIFIED' in text and 'UNRESOLVED' in text,'closure authority unavailable')
  entries=[x for x in load(evidence/'evidence_registry.json')['entries'] if x.get('q_id')=='Q045']
  req(len(entries)==5,'Q045 evidence count')
  mapping={'EVD-Q045-RECOVERY':('q045_reference_history_final_v2.json',SOURCE_INPUT,'ORIGINAL_WORKFLOW_RESULT'),'EVD-Q045-QJOURNAL':('q_journal_authorized.txt',None,'OPERATOR_MANUSCRIPT_EXCERPT'),'EVD-Q045-APPENDICES':('appendices_authorized.txt',None,'OPERATOR_MANUSCRIPT_EXCERPT'),'EVD-Q045-MAINBOOK':('main_book_authorized.txt',None,'OPERATOR_MANUSCRIPT_EXCERPT'),'EVD-Q045-REMOTE-RUN':('remote_execution_receipt.json',SOURCE_INPUT,'LIVE_REMOTE_VERIFICATION')}
  req({e['evidence_id'] for e in entries}==set(mapping),'duplicate or replaced evidence identity')
  for e in entries:
   filename,origin,role=mapping[e['evidence_id']]
   req(e['source']=='evidence/sources/Q045/'+filename and e['source_repository_commit']==origin and e['role']==role,'evidence identity/source/origin retargeted')
   req(all(e[k] is False for k in ['physical_falsification','actual_computed_cosmological_result','new_scientific_inference','production_restart_authorized','independent_cosmological_evidence']),'technical evidence elevated into physics')
   req(e['sha256']==sha(evidence/e['source'].removeprefix('evidence/')),'evidence reference changed')
  return 'Technical recovery and manuscript closure admitted; physical reference/materiality unqualified'
 gate('QUALIFICATION_GATE',qualification)
 def diagnostic():
  d=load(src/'q045_reference_history_final_v2.json');records=d['recovered_records'];parents={'camspec-lcdm','camspec-ede_n3','hillipop-lcdm','hillipop-ede_n3'}
  req(len(records)==8 and {r['job_id'] for r in records}=={p+'-L'+str(i) for p in parents for i in [1,2]},'worker coverage')
  req(d['job_completeness']=={'gate':'PASS','missing':[],'unknown':[],'duplicates':[]} and d['errors']==[] and d['execution_status']=='COMPLETE' and d['history_diagnostic_gate']=='PASS_COMPONENT_ONLY','technical diagnostic qualification')
  req(sum(r['original_status']=='FAILED' and r['original_error']=='ValueError: UNCHANGED_PHYSICAL_NORMALIZATION YHe' for r in records)==2,'original failure history lost')
  req(set(d['history_comparisons'])==parents,'four history comparisons missing')
  for r in records:
   req(r['recovery_status']=='COMPLETE' and len(r['analysis']['effective_precision_changed'])==9,'joint-refinement scope')
   req(r['analysis']['reference_truth_gate']=='UNQUALIFIED' and r['analysis']['reference_error_bound'] is None,'worker physical-reference overstatement')
   w=load(src/'recovered_workers'/(r['job_id']+'.json'))
   req(w['analysis']==r['analysis'] and w['original_status']==r['original_status'],'worker/final aggregation mismatch')
  for p in parents:
   seq=d['history_comparisons'][p]['scalar_sequences']['actual_tau'];v=seq['values'];delta=[v[0]-v[1],v[1]-v[2]]
   req(seq['level_differences']==delta and delta[0]*delta[1]<0,'tau reversal changed')
   req(seq['observed_order'] is None and seq['empirical_remaining_estimate'] is None and seq['estimate_status']=='EMPIRICAL_NOT_A_BOUND','reversal became an error enclosure')
  req(d['original_native_evaluations_started']==8 and d['original_evaluations_inherited']==8 and d['evaluations_consumed_total']==16 and d['remaining_budget']==36,'evaluation accounting altered')
  return {'workers':8,'grids':4,'accepted_tau_reversals':4,'simultaneous_controls':9,'new_theory_evaluations':0,'fresh_solver_rerun':False}
 gate('DIAGNOSTIC_GATE',diagnostic)
 def regression():
  for n,key in {**LAYERS,**FORMAL}.items():
   before=load(old/(n+'.json'))[key];after=load((layer if n in LAYERS else formal)/(n+'.json'))[key]
   req(after[:len(before)]==before,'inherited definitions changed: '+n)
   if n not in REVIEWED:req(after==before,'unauthorized scientific addition: '+n)
  for n in ['input_schema','output_schema','result_registry','external_catalog_registry']:
   before=load(old/(n+'.json'));after=load(formal/(n+'.json'))
   if 'q_access_end' in before:before.pop('q_access_end');after.pop('q_access_end')
   req(after==before,'public capability changed: '+n)
  prev=load(old/'evidence_registry.json')['entries'];req(load(evidence/'evidence_registry.json')['entries'][:len(prev)]==prev,'evidence history changed')
  return 'All prior science, physical values, predictions, contradictions and public interfaces preserved'
 gate('REGRESSION_GATE',regression)
 def diff():
  d=load(root/'candidate/candidate_diff.json');actual={}
  for n,key in {**LAYERS,**FORMAL}.items():
   before=load(old/(n+'.json'))[key];after=load((layer if n in LAYERS else formal)/(n+'.json'))[key];tail=after[len(before):]
   actual[n]=[r['id'] for r in tail]
   if n in REVIEWED:req(hashlib.sha256(json.dumps(tail,sort_keys=True,separators=(',',':')).encode()).hexdigest()==REVIEWED[n],'reviewed definition altered: '+n)
   else:req(not tail,'unauthorized addition: '+n)
  req([x['id'] for x in d['added']]==sum([actual[n] for n in ['constraints','robustness']],[]),'layer diff mismatch')
  for field,n in [('new_uncertainties','uncertainty'),('new_validity_domains','domain_of_validity'),('new_limitations','limitations')]:req(d[field]==actual[n],'formal diff mismatch')
  req(all(d[k]==[] for k in ['new_parameters','new_equations','new_assumptions','new_benchmarks','new_calculations','new_domains','superseded','resolved_contradictions']) and d['physical_model_change'] is False,'unjustified expansion')
  return 'Exact traceable additions; no new calculation, fundamental equation or physical inference'
 gate('MODEL_DIFF_GATE',diff)
 def references():
  eids={e['evidence_id'] for e in load(evidence/'evidence_registry.json')['entries']}
  for base in [layer,formal]:
   for p in base.glob('*.json'):
    def walk(v):
     if isinstance(v,dict):
      if 'evidence_refs' in v:req(set(v['evidence_refs'])<=eids,'unresolved evidence reference')
      for x in v.values():walk(x)
     elif isinstance(v,list):
      for x in v:walk(x)
    walk(load(p))
  req(load(formal/'model_manifest.json')['evidence_refs']==load(old/'model_manifest.json')['evidence_refs']+['EVD-Q045-RECOVERY','EVD-Q045-QJOURNAL','EVD-Q045-APPENDICES','EVD-Q045-MAINBOOK','EVD-Q045-REMOTE-RUN'],'formal evidence mismatch')
  return 'Evidence references resolve; existing equations, assumptions, units and schemas preserved'
 gate('REFERENCE_GATE',references)
 def firewall():
  count=0
  for base in [layer,formal,evidence]:
   for p in base.rglob('*'):
    if p.is_file() and p.suffix in {'.json','.txt','.md','.py','.c'}:
     req(not any(int(x)>45 for x in re.findall(r'\bQ-?0*([0-9]{1,5})\b',p.read_text(),re.I)),'future scientific origin: '+str(p));count+=1
  req(all(row['scientific_ingestion'] or row['path'].startswith('provenance/input_archives/Q045/') for row in prov['source_files']),'raw archive entered scientific evidence')
  return {'scanned_files':count,'maximum_q':45,'mixed_boundary_manuscripts':'BOUNDED_EXCERPTS_ONLY'}
 gate('FIREWALL_GATE',firewall)
 def immutable():
  req(hashlib.sha256(json.dumps(prov['protected_input_hashes'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==PROTECTED_INPUT_PIN,'protected input inventory changed')
  for rel,digest in prov['protected_input_hashes'].items():
   if not candidate and (rel.startswith(('accepted/','model/')) or rel in ['evidence/evidence_registry.json','release/MODEL_RELEASE_HANDOFF.json','release/MODEL_RELEASE_HANDOFF.md']):continue
   req(sha(root/rel)==digest,'protected input changed: '+rel)
  if not candidate:
   snap=root/'versions/accepted/v0.7';frozen=load(root/'provenance/Q045_SNAPSHOT_MANIFEST.json')
   req({p.name for p in snap.iterdir() if p.is_file()}==set(frozen['sha256']),'snapshot inventory')
   for name,digest in frozen['sha256'].items():req(sha(snap/name)==digest,'frozen snapshot changed')
   for base in [layer,formal]:
    for p in base.iterdir():
     if p.is_file():req(sha(p)==sha(snap/p.name),'live/snapshot mismatch')
   req(sha(evidence/'evidence_registry.json')==sha(snap/'evidence_registry.json'),'evidence snapshot mismatch')
  return 'Accepted immutable before promotion; all prior snapshots protected; current live/frozen match'
 gate('IMMUTABILITY_GATE',immutable)
 def remote():
  r=load(src/'remote_execution_receipt.json');req(r['id']==38042718814 and r['head_sha']==SOURCE_INPUT and r['conclusion']=='success' and r['status']=='completed' and r['run_attempt']==1,'run provenance')
  req(len(r['jobs'])==1 and r['jobs'][0]['id']==114186014990 and r['jobs'][0]['conclusion']=='success','job identity')
  req(r['artifacts'][0]['id']==11665884089 and r['artifacts'][0]['digest']=='sha256:'+ARTIFACT_PIN and r['artifacts'][0]['size_in_bytes']==4541261,'artifact provenance')
  req(prov['model_input_commit']==MODEL_INPUT and prov['source_repository_inspection_commit']==SOURCE_INPUT and prov['source_manuscript_commit'] is None,'source/Word identity fabricated')
  subprocess.run(['git','cat-file','-e',MODEL_INPUT+'^{commit}'],cwd=root,check=True,capture_output=True)
  return 'Live run/job/artifact identity matches pinned original; real reachable model input'
 gate('PROVENANCE_GATE',remote)
 passed=sum(r['status']=='PASS' for r in rows)
 return {'artifact_type':'Q045_MODEL_UPDATE_VALIDATION','target_q':'Q045','mode':'CANDIDATE' if candidate else 'CURRENT_ACCEPTED','tests':rows,'tests_total':len(rows),'tests_passed':passed,'all_green':passed==len(rows),'non_destructive':True}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',action='store_true');args=ap.parse_args();r=run_tests(candidate=args.candidate)
 for row in r['tests']:print(f"{row['id']}={row['status']} {row['detail']}")
 print(f"Q045_MODEL_TESTS={r['tests_passed']}/{r['tests_total']}");raise SystemExit(0 if r['all_green'] else 1)
