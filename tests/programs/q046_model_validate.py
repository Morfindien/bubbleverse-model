#!/usr/bin/env python3
"""Read-only admission of the documented Q046 insufficient-qualification assessment."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path

REVIEWED={'constraints': '1da1469eee9c244bfdc03a0fe00829a7abc308578e63d0205e014036fc056cf3', 'robustness': '60fe1848fa60fe3349b4dcc00db187d3ceab2b50029d485b3d9e9ad62b43e9f7', 'uncertainty': '6dbc2c0de1d90a977a0d7f96c15cf038809a0e6374208ca9a671a45ac0bdb8d4', 'domain_of_validity': 'c25896c1dc128cd4880f34b60d3f5d5770754b4fde748db9400eec5de3afc6a2', 'limitations': '52f12082572217ea3222ea78156eeafc7a30d90f683afc36527792c1668a94f5'}
SOURCE_FILES=[{'path': 'evidence/sources/Q046/main_book_authorized.txt', 'archived_name': 'main_book_authorized.txt', 'bytes': 2056, 'sha256': '8407065237e663402aa2e8b6c06a27b29ed07d4194769d5354aa93289e2e120e', 'role': 'OPERATOR_MANUSCRIPT_EXCERPT', 'scientific_ingestion': True, 'authority': 'AUTHORITATIVE_BUBBLEVERSE_SOURCE', 'q_boundary_status': 'AUTHORIZED_THROUGH_Q046', 'source_repository_commit': None, 'parent_pdf_sha256': '288596246b670cfcc1a8d2de5051676035e42c7faba537cf1a96887740308779', 'parent_pdf_bytes': 1052495, 'parent_library_file_id': 'libfile_3f168493f1f081919a48ac0d3c2f242b', 'derivation': {'extractor': 'pdftotext -layout', 'line_start': 2044, 'stop_before_next_question_heading': True, 'whole_document_ingestion': False}}, {'path': 'evidence/sources/Q046/q_journal_authorized.txt', 'archived_name': 'q_journal_authorized.txt', 'bytes': 2764, 'sha256': 'e4285b03a878634cb9772364d0faef2975ca9d0a6c2211307cffeb0a50501e3e', 'role': 'OPERATOR_MANUSCRIPT_EXCERPT', 'scientific_ingestion': True, 'authority': 'AUTHORITATIVE_BUBBLEVERSE_SOURCE', 'q_boundary_status': 'AUTHORIZED_THROUGH_Q046', 'source_repository_commit': None, 'parent_pdf_sha256': 'd917929e0f4c5e1ef581be0e898e1f2be5a61269a78938cac7e869d1d9eafd75', 'parent_pdf_bytes': 463342, 'parent_library_file_id': 'libfile_2e6a89d632f8819187ae1be5446e72e3', 'derivation': {'extractor': 'pdftotext -layout', 'line_start': 4546, 'stop_before_next_question_heading': True, 'whole_document_ingestion': False}}, {'path': 'evidence/sources/Q046/appendices_authorized.txt', 'archived_name': 'appendices_authorized.txt', 'bytes': 2715, 'sha256': 'a99b7d0ad986ece8f6715099cbf2eec51300af567dab2483c664f55e54e43bdf', 'role': 'OPERATOR_MANUSCRIPT_EXCERPT', 'scientific_ingestion': True, 'authority': 'AUTHORITATIVE_BUBBLEVERSE_SOURCE', 'q_boundary_status': 'AUTHORIZED_THROUGH_Q046', 'source_repository_commit': None, 'parent_pdf_sha256': '43298a932b16d4aacfbca144c97b31f7d1d0e2d02fdae2728b366ab488adad6b', 'parent_pdf_bytes': 296406, 'parent_library_file_id': 'libfile_0c1bea1a168c8191a34321cd88f9b1c2', 'derivation': {'extractor': 'pdftotext -layout', 'line_start': 2222, 'stop_before_next_question_heading': True, 'whole_document_ingestion': False}}]
PROTECTED_INVENTORY_PIN='db0c7f0adeaf527882174bcfad096ea130738bbe54d05d449d6f936d1e3ea590'
ROOT=Path(__file__).resolve().parents[2]
BASE='5db94b20610d9e3e2eb765f39ce426f078ae385d'
EIDS=['EVD-Q046-QJOURNAL','EVD-Q046-APPENDICES','EVD-Q046-MAINBOOK']
LAYERS={'observations':'observations','constraints':'constraints','mechanisms':'mechanisms','predictions':'predictions','contradictions':'contradictions','robustness':'items'}
FORMAL={'parameters':'parameters','benchmarks':'benchmarks','equations':'equations','assumptions':'assumptions','uncertainty':'uncertainties','domain_of_validity':'domains','limitations':'limitations'}

def run_tests(root=ROOT,candidate=False):
 root=Path(root); layer=root/('candidate' if candidate else 'accepted');formal=root/('candidate/formal' if candidate else 'model');evidence=root/('candidate/evidence' if candidate else 'evidence');old=root/'versions/accepted/v0.7';rows=[]
 def rawload(p):return json.loads(p.read_text())
 active=int(rawload(root/'accepted/model_state.json')['current_q'][1:]);pending=int(rawload(root/'candidate/candidate_state.json')['current_q'][1:])
 historical=not candidate and (active>46 or pending>46)
 if historical:layer=formal=root/'versions/accepted/v0.8'
 def load(p):
  if historical:
   if p in [root/'candidate/candidate_state.json',root/'candidate/candidate_diff.json']:p=root/'provenance/archive/Q046'/p.name
   elif p==root/'accepted/model_state.json':p=layer/'model_state.json'
   elif p==evidence/'evidence_registry.json':p=layer/'evidence_registry.json'
  return rawload(p)
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 def req(c,m):
  if not c:raise AssertionError(m)
 def gate(name,fn):
  try:rows.append({'id':'Q046_'+name,'status':'PASS','detail':fn()})
  except Exception as e:rows.append({'id':'Q046_'+name,'status':'FAIL','detail':f'{type(e).__name__}: {e}'})
 c=load(root/'candidate/candidate_state.json');s=load(layer/('candidate_state.json' if candidate else 'model_state.json'));prov=load(root/'candidate/Q046_PROVENANCE.json');u=load(evidence/'q_updates/Q046.json')
 def sequence():
  a=load(root/'accepted/model_state.json');e=load(evidence/'evidence_registry.json')
  req(c['target_q']==c['current_q']==c['q_access_end']=='Q046','candidate boundary')
  req(c['previous_accepted_q']=='Q045' and c['previous_accepted_model_version']=='v0.7','missing accepted predecessor')
  req(c['candidate_model_version']=='v0.8' and c['candidate_revision']=='R000008','candidate version')
  req(a['current_q']==a['q_access_end']==('Q045' if candidate else 'Q046'),'accepted boundary')
  req(a['accepted_model_version']==('v0.7' if candidate else 'v0.8'),'accepted version')
  req(e['current_q']==e['q_access_end']=='Q046' and load(old/'model_state.json')['current_q']=='Q045','evidence or predecessor identity')
  return 'Q045/v0.7 -> Q046/v0.8; completed assessment only'
 gate('SEQUENCE_GATE',sequence)
 def sources():
  req(prov['source_files']==SOURCE_FILES,'source inventory retargeted')
  entries=[e for e in load(evidence/'evidence_registry.json')['entries'] if e.get('q_id')=='Q046']
  req(len(entries)==3 and {e['evidence_id'] for e in entries}==set(EIDS),'assessment evidence identity')
  for row in SOURCE_FILES:
   p=evidence/row['path'].removeprefix('evidence/')
   req(p.is_file() and sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],'source excerpt changed: '+row['path'])
   entry=next(e for e in entries if e['source']==row['path'])
   expected='EVD-Q046-'+{'q_journal_authorized.txt':'QJOURNAL','appendices_authorized.txt':'APPENDICES','main_book_authorized.txt':'MAINBOOK'}[p.name]
   req(entry['evidence_id']==expected and entry['sha256']==row['sha256'] and entry['source_repository_commit'] is None,'source authority retargeted')
   req(entry['role']=='OPERATOR_MANUSCRIPT_EXCERPT' and row['scientific_ingestion'] is True,'source authority class')
  req(prov['source_manuscript_commit'] is None,'fabricated repository manuscript commit')
  return 'Three independently hashed operator manuscript excerpts; original PDF identities pinned separately'
 gate('SOURCE_HASH_GATE',sources)
 def qualification():
  for obj in [c,s]:
   req(obj['q046_result']=='INSUFFICIENT QUALIFICATION' and obj['q046_investigation_status']=='COMPLETED_ASSESSMENT_INSUFFICIENT_QUALIFICATION','assessment conclusion overstated')
   req(obj['q046_admission_scope']=='DOCUMENTED_ASSESSMENT_AND_QUALIFICATION_LIMITATIONS_ONLY','admission scope')
   req(obj['q046_canonical_case_id'] is None and obj['q046_canonical_result_id'] is None and obj['q046_source_canonical_status']=='UNREGISTERED','source canonical identity fabricated')
   req(obj['q046_physical_reference_qualified'] is False and obj['q046_cosmological_event_certified'] is False and obj['q046_physical_materiality']=='UNKNOWN' and obj['q046_new_scientific_run'] is False,'unsupported physical qualification')
   req(obj['physical_model_change'] is False and obj['production_restart_authorized'] is False,'physical model or production changed')
  req(u['result']=='INSUFFICIENT QUALIFICATION' and u['canonical_case_id'] is None and u['canonical_result_id'] is None and u['canonical_source_status']=='UNREGISTERED','summary identity or result fabricated')
  req(u['physical_reference_qualified'] is False and u['cosmological_event_certified'] is False and u['physical_materiality']=='UNKNOWN' and u['new_scientific_run'] is False and u['production_restart_authorized'] is False,'summary qualification overstated')
  req(prov['canonical_case_id'] is None and prov['canonical_result_id'] is None and prov['canonical_source_status']=='UNREGISTERED' and prov['full_physical_reference_qualified'] is False and prov['new_scientific_run'] is False and prov['reported_conditional_math_independently_rederived'] is False,'provenance overclaim')
  for e in load(evidence/'evidence_registry.json')['entries']:
   if e.get('q_id')=='Q046':req(all(e[k] is False for k in ['new_scientific_inference','physical_falsification','production_restart_authorized','actual_computed_cosmological_result','independent_cosmological_evidence']) and e['canonical_case_id'] is None and e['canonical_result_id'] is None and e['scientific_run_id'] is None,'assessment elevated into physics or scientific run')
  return 'Insufficient qualification and unknown source CASE/RESULT identities are preserved; no positive physical result required or asserted'
 gate('QUALIFICATION_GATE',qualification)
 def regression():
  for n,key in {**LAYERS,**FORMAL}.items():
   before=load(old/(n+'.json'))[key];after=load((layer if n in LAYERS else formal)/(n+'.json'))[key]
   req(after[:len(before)]==before,'inherited scientific definition changed: '+n)
   if n not in REVIEWED:req(after==before,'unauthorized addition: '+n)
  for n in ['input_schema','output_schema','result_registry','external_catalog_registry']:
   before=load(old/(n+'.json'));after=load(formal/(n+'.json'));before.pop('q_access_end',None);after.pop('q_access_end',None)
   req(before==after,'public surface changed: '+n)
  previous=load(old/'evidence_registry.json')['entries'];req(load(evidence/'evidence_registry.json')['entries'][:len(previous)]==previous,'evidence history mutated')
  return 'All inherited scientific records, physical values, predictions, contradictions, evidence and public schemas preserved'
 gate('REGRESSION_GATE',regression)
 def diff():
  d=load(root/'candidate/candidate_diff.json');tails={}
  for n,key in {**LAYERS,**FORMAL}.items():
   before=load(old/(n+'.json'))[key];after=load((layer if n in LAYERS else formal)/(n+'.json'))[key];tail=after[len(before):];tails[n]=[x['id'] for x in tail]
   if n in REVIEWED:req(canonical(tail)==REVIEWED[n],'reviewed scope changed: '+n)
   else:req(not tail,'unreviewed addition: '+n)
  req(d['target_q']=='Q046' and d['from_version']=='v0.7' and d['to_candidate_version']=='v0.8','diff boundary')
  req([x['id'] for x in d['added']]==tails['constraints']+tails['robustness'],'scientific-layer diff incomplete')
  for field,n in [('new_uncertainties','uncertainty'),('new_validity_domains','domain_of_validity'),('new_limitations','limitations')]:req(d[field]==tails[n],'formal diff incomplete: '+field)
  req(all(not d[k] for k in ['new_parameters','new_equations','new_assumptions','new_benchmarks','new_calculations','new_domains','superseded','resolved_contradictions']) and d['physical_model_change'] is False,'unjustified capability growth')
  return 'Exact reviewed assessment/limitation additions; no fundamental equation or public calculation'
 gate('MODEL_DIFF_GATE',diff)
 def references():
  ev=load(evidence/'evidence_registry.json')['entries'];eids={e['evidence_id'] for e in ev};req(len(eids)==len(ev),'duplicate evidence identity')
  def walk(v):
   if isinstance(v,dict):
    if 'evidence_refs' in v:req(set(v['evidence_refs'])<=eids,'unresolved evidence reference')
    for x in v.values():walk(x)
   elif isinstance(v,list):
    for x in v:walk(x)
  for base in [layer,formal]:
   for p in base.glob('*.json'):walk(load(p))
  manifest=load(formal/'model_manifest.json');req(manifest['evidence_refs']==load(old/'model_manifest.json')['evidence_refs']+EIDS,'formal provenance not synchronized')
  for n,key in {**LAYERS,**FORMAL}.items():
   ids=[x['id'] for x in load((layer if n in LAYERS else formal)/(n+'.json'))[key]];req(len(ids)==len(set(ids)),'duplicate registry ID: '+n)
  return 'Evidence references and canonical model-record IDs resolve; source CASE/RESULT identity stays unknown'
 gate('REFERENCE_GATE',references)
 def firewall():
  bases=[layer,formal,evidence];count=0
  if historical:
   paths=list(layer.glob('*'))+list(formal.glob('*'))
   for p in evidence.rglob('*'):
    if p.name=='evidence_registry.json':continue
    token=re.search(r'/Q(\d{3})(?:/|\.json)',p.as_posix())
    if token and int(token[1])<=46:paths.append(p)
  else:paths=[p for base in bases for p in base.rglob('*')]
  for p in paths:
   if p.is_file() and p.suffix in ['.json','.txt','.md','.py','.c']:
    req(not any(int(x)>46 for x in re.findall(r'\bQ-?0*(\d{1,5})\b',p.read_text(),re.I)),'future scientific origin: '+str(p));count+=1
  return {'scanned_files':count,'maximum_scientific_q':46,'mixed_boundary_inputs':'BOUNDED_EXCERPTS_ONLY'}
 gate('FIREWALL_GATE',firewall)
 def immutable():
  req(canonical(prov['protected_input_hashes'])==PROTECTED_INVENTORY_PIN,'protected inventory retargeted')
  for rel,digest in prov['protected_input_hashes'].items():
   if not candidate and (rel.startswith(('accepted/','model/')) or rel in ['evidence/evidence_registry.json','release/MODEL_RELEASE_HANDOFF.json','release/MODEL_RELEASE_HANDOFF.md']):continue
   req(sha(root/rel)==digest,'protected input changed: '+rel)
  if not candidate:
   snap=root/'versions/accepted/v0.8';frozen=load(root/'provenance/Q046_SNAPSHOT_MANIFEST.json')
   req({p.name for p in snap.iterdir() if p.is_file()}==set(frozen['sha256']),'snapshot inventory')
   for name,digest in frozen['sha256'].items():req(sha(snap/name)==digest,'frozen snapshot mutated: '+name)
   if not historical:
    for base in [layer,formal]:
     for p in base.iterdir():
      if p.is_file():req(sha(p)==sha(snap/p.name),'live/snapshot mismatch: '+p.name)
    req(sha(evidence/'evidence_registry.json')==sha(snap/'evidence_registry.json'),'evidence live/snapshot mismatch')
  return 'Accepted state immutable before promotion; all previous snapshots protected; accepted snapshot checked after promotion'
 gate('IMMUTABILITY_GATE',immutable)
 def isolation():
  if not candidate:
   req(all(p.startswith('accepted/') for p in s['layers'].values()),'accepted scientific paths depend on candidate')
  req(not any(p.startswith('candidate/') for p in load(formal/'model_manifest.json')['source_layers']),'formal accepted-source path escapes')
  return 'Accepted scientific layer references do not depend on mutable candidate paths'
 gate('PATH_ISOLATION_GATE',isolation)
 def provenance():
  req(prov['model_input_commit']==BASE and c['candidate_input_commit']==BASE,'input Git provenance retargeted')
  subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=root,check=True,capture_output=True)
  req(c['input_documents'][-3:]==SOURCE_FILES,'state source lineage retargeted')
  return 'Real reachable model input; operator manuscripts have hashes and persistent original file identity, no fabricated repository commit'
 gate('PROVENANCE_GATE',provenance)
 passed=sum(x['status']=='PASS' for x in rows)
 return {'artifact_type':'Q046_MODEL_ASSESSMENT_ADMISSION_VALIDATION','target_q':'Q046','mode':'CANDIDATE' if candidate else 'CURRENT_OR_HISTORICAL_ACCEPTED','tests':rows,'tests_total':len(rows),'tests_passed':passed,'all_green':passed==len(rows),'non_destructive':True}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',action='store_true');args=ap.parse_args();result=run_tests(candidate=args.candidate)
 for row in result['tests']:print(f"{row['id']}={row['status']} {row['detail']}")
 print(f"Q046_MODEL_TESTS={result['tests_passed']}/{result['tests_total']}")
 raise SystemExit(0 if result['all_green'] else 1)
