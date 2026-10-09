#!/usr/bin/env python3
"""Dynamically audit and clean Bubbleverse infrastructure; never pushes or promotes."""
from __future__ import annotations
import argparse,ast,collections,hashlib,json,os,re,subprocess,sys,tempfile,textwrap
from pathlib import Path
from datetime import datetime,timezone
UPLOADS={'repository_cleanup.py','.github/workflows/repository-cleanup-current.yml','REPOSITORY_CLEANUP.md'}
PROTECTED=('accepted/','candidate/','model/','evidence/','provenance/','release/','tests/results/','tests/preregistration/','versions/accepted/','changelog/')
HISTORICAL=('versions/accepted/','provenance/','tests/results/','tests/preregistration/','changelog/','docs/superpowers/')
SUSPICIOUS=re.compile(r'(?:-\d+\.|_copy\.| copy\.|backup|final-final|final2|duplicate|(?:^|[_.-])(?:old|new|temp|tmp)(?:[_.-]|$))',re.I)

def command(repo,args,env=None):
 cp=subprocess.run(args,cwd=repo,text=True,capture_output=True,env=env)
 if cp.returncode:raise RuntimeError('Command failed: '+' '.join(map(str,args))+'\n'+cp.stdout+cp.stderr)
 return cp.stdout.strip()
def git(repo,*args):return command(repo,['git',*args])
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def file_bytes(p):return os.readlink(p).encode() if p.is_symlink() else p.read_bytes()
def digest(p):return sha_bytes(file_bytes(p))
def q_number(q):
 m=re.fullmatch(r'Q-?0*(\d+)',str(q),re.I)
 if not m:raise RuntimeError('Unresolved Q identity: '+str(q))
 return int(m[1])
def clean(repo):
 for row in git(repo,'status','--porcelain','--untracked-files=all').splitlines():
  if row.startswith('?? ') and row[3:] in UPLOADS and (repo/row[3:]).is_file() and not (repo/row[3:]).is_symlink():continue
  raise RuntimeError('Uncommitted operator changes: '+row)
def default_branch(repo):
 configured=os.environ.get('BV_DEFAULT_BRANCH')
 if configured:return configured
 try:ref=git(repo,'symbolic-ref','refs/remotes/origin/HEAD')
 except RuntimeError:
  remote=git(repo,'ls-remote','--symref','origin','HEAD')
  match=re.search(r'(?m)^ref: refs/heads/([^\t]+)\tHEAD$',remote)
  if not match:raise RuntimeError('Remote default branch cannot be discovered')
  return match[1]
 return ref.removeprefix('refs/remotes/origin/')
def repository(path,target='Morfindien/bubbleverse-model'):
 root=Path(git(path,'rev-parse','--show-toplevel')).resolve()
 url=git(root,'config','--get','remote.origin.url').lower().rstrip('/').removesuffix('.git')
 target=target.lower()
 if url not in {'https://github.com/'+target,'git@github.com:'+target,'ssh://git@github.com/'+target}:raise RuntimeError('Cleanup target must be '+target)
 branch=default_branch(root)
 if git(root,'branch','--show-current')!=branch:raise RuntimeError('Select the default branch '+branch+' before cleanup')
 clean(root);return root

def inventory(repo):
 entries={};texts={};jsons={};parse_errors=[]
 raw=subprocess.check_output(['git','ls-files','-s','-z'],cwd=repo)
 for row in raw.split(b'\0'):
  if not row:continue
  meta,path=row.split(b'\t',1);mode,blob,stage=meta.decode().split();name=path.decode();p=repo/name
  if stage!='0':raise RuntimeError('Unmerged index: '+name)
  if mode=='160000':
   entries[name]={'path':name,'mode':mode,'git_blob_sha':blob,'sha256':None,'size':None,'classification':'UNKNOWN','reason':'Submodule kept; nested repository is outside this transaction','references':[],'referenced_by':[]};continue
  if not p.exists() and not p.is_symlink():continue
  b=file_bytes(p);e={'path':name,'mode':mode,'git_blob_sha':blob,'sha256':sha_bytes(b),'size':len(b),'role':name.split('/')[0] if '/' in name else 'ROOT','protection_level':'IMMUTABLE_SNAPSHOT' if name.startswith('versions/accepted/') else 'PROTECTED' if name.startswith(PROTECTED) else 'STRUCTURAL','classification':'KEEP_HISTORICAL' if name.startswith(HISTORICAL) else 'KEEP_ACTIVE','reason':'Registered structural/scientific role retained','references':[],'referenced_by':[]};entries[name]=e
  if mode!='100644' and mode!='100755':continue
  try:s=b.decode('utf-8')
  except UnicodeDecodeError:continue
  # Pure encoded payload lines cannot contain repository filenames with extensions.
  # Their complete bytes remain hashed and their Python syntax is still parsed.
  texts[name]=re.sub(r'(?m)^[A-Za-z0-9+/=]{80,}$','',s) if name.endswith('.py') else s
  try:
   if name.endswith('.json'):jsons[name]=json.loads(s)
   elif name.endswith('.py'):ast.parse(s)
  except (ValueError,SyntaxError) as exc:parse_errors.append({'path':name,'error':str(exc)})
 full=re.compile('|'.join(map(re.escape,sorted(entries,key=len,reverse=True)))) if entries else None
 basenames=collections.defaultdict(list)
 for p in entries:basenames[Path(p).name].append(p)
 bare=re.compile('|'.join(map(re.escape,sorted(basenames,key=len,reverse=True)))) if basenames else None
 for p,s in texts.items():
  refs=set(m.group(0) for m in full.finditer(s)) if full else set()
  if bare:
   for m in bare.finditer(s):
    name=m.group(0);relative=(Path(p).parent/name).as_posix()
    if relative in entries:refs.add(relative)
    elif len(basenames[name])==1:refs.add(basenames[name][0])
  if p.endswith('.py'):
   try:
    for node in ast.walk(ast.parse(s)):
     modules=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module] if isinstance(node,ast.ImportFrom) and node.module else []
     for module in modules:
      name=module.rsplit('.',1)[-1]+'.py'
      refs.update(basenames.get(name,[]))
   except SyntaxError:pass
  entries[p]['references']=sorted(refs-{p})
  for ref in refs-{p}:entries[ref]['referenced_by'].append(p)
 groups=collections.defaultdict(list)
 for p,e in entries.items():
  if e['sha256']:groups[e['sha256']].append(p)
 duplicates=[{'sha256':h,'paths':ps,'action':'KEEP_UNLESS_POSITIVE_ACCIDENTAL_DUPLICATE_PROOF'} for h,ps in groups.items() if len(ps)>1]
 return entries,texts,jsons,parse_errors,duplicates

def discover(repo,jsons):
 accepted=jsons.get('accepted/model_state.json');manifest=jsons.get('model/model_manifest.json');registry=jsons.get('bubbleverse_model_program_registry.json')
 if not accepted or not manifest or registry is None:raise RuntimeError('Canonical accepted/formal/program metadata is unavailable; no safe cleanup')
 current=accepted.get('current_q') or accepted.get('q_access_end');q_number(current)
 version=accepted.get('accepted_model_version')
 if not version:raise RuntimeError('Accepted version is unresolved')
 programs=registry.get('programs',{})
 if isinstance(programs,list):programs={str(i):p for i,p in enumerate(programs)}
 validators={};workflow=jsons.get('model/environment.json',{}).get('public_workflow')
 for pid,item in programs.items():
  if not isinstance(item,dict) or not str(item.get('status','')).startswith('ACTIVE'):continue
  for key,value in item.items():
   if key.endswith('_validator_path') or key=='validator_path':
    m=re.fullmatch(r'q(\d+)_validator_path',key,re.I)
    if m and int(m[1])!=q_number(current):continue
    validators[value]=[]
  if item.get('validation_command')=='validate' and item.get('path'):validators[item['path']]=['validate']
  if workflow is None and 'test' in item.get('public_workflow_operations',[]) and item.get('workflow_id'):workflow='.github/workflows/'+item['workflow_id']
 if not validators or not workflow:raise RuntimeError('Registered current validators/public healthcheck cannot be discovered safely')
 return {'accepted':accepted,'manifest':manifest,'programs':programs,'validators':validators,'public_workflow':workflow,'current_q':current,'current_q_boundary':str(accepted.get('q_access_start','Q001'))+'-'+str(accepted.get('q_access_end',current)),'current_accepted_version':version,'current_formal_model':manifest.get('formal_model_version'),'current_candidate_state':jsons.get('candidate/candidate_state.json',{}).get('status'),'current_release_state':jsons.get('release/MODEL_RELEASE_HANDOFF.json',{}).get('release_status')}

def validate(repo,work):
 entries,_,jsons,errors,_=inventory(repo);before={p:e['sha256'] for p,e in entries.items()};state=discover(repo,jsons);result={}
 relevant=[x for x in errors if x['path'].startswith(PROTECTED) or x['path'].startswith('tests/programs/') or x['path']=='bubbleverse_model_program_registry.json']
 if relevant:raise RuntimeError('Canonical parse failure: '+json.dumps(relevant))
 result['CANONICAL_JSON_PYTHON_PARSE']='PASS'
 accepted=state['accepted'];manifest=state['manifest']
 for key in ['accepted_model_version','q_access_start','q_access_end','current_q']:
  if key in manifest and manifest[key]!=accepted.get(key):raise RuntimeError('Accepted/formal metadata mismatch: '+key)
 result['CURRENT_METADATA']='PASS'
 for path,args in state['validators'].items():
  if path not in entries or not path.endswith('.py'):raise RuntimeError('Invalid registered validator path: '+str(path))
  out=command(repo,[sys.executable,str(repo/path),*args]);result[path]='PASS'
  (work/(Path(path).name+'.log')).write_text(out+'\n')
 workflow=state['public_workflow']
 if workflow not in entries:raise RuntimeError('Registered public workflow is missing: '+workflow)
 match=re.search(r"(?m)^([ ]*)python - <<'PY'\n(.*?)^\1PY\s*$",(repo/workflow).read_text(),re.S)
 if not match:raise RuntimeError('Registered healthcheck format is unresolved; keep files and inspect')
 engine=work/'public-healthcheck.py';engine.write_text(textwrap.dedent(match.group(2)))
 command(repo,[sys.executable,str(engine)],env={**os.environ,'BV_OPERATION':'test','BV_INPUT':''})
 output=jsons.get('model/output_schema.json',{}).get('primary_artifact')
 if not output:raise RuntimeError('Registered public healthcheck output path is unresolved')
 health=load(repo/output)
 if not health.get('all_green'):raise RuntimeError('Public healthcheck failed')
 result['PUBLIC_HEALTHCHECK']={'status':'PASS','passed':health.get('tests_passed'),'total':health.get('tests_total')}
 snapshot=repo/'versions/accepted'/state['current_accepted_version']
 if not snapshot.is_dir():raise RuntimeError('Current immutable accepted snapshot is missing')
 release=jsons.get('release/MODEL_RELEASE_HANDOFF.json',{})
 for frozen in snapshot.rglob('*'):
  if not frozen.is_file():continue
  name=frozen.name;relative=frozen.relative_to(snapshot).as_posix()
  if relative.startswith(('accepted/','model/','evidence/')):live=repo/relative
  elif name=='TEST_RESULT.json':live=repo/release.get('test_campaign_artifact','tests/results/'+state['current_q']+'_MODEL_UPDATE_TEST_RESULT.json')
  elif name=='evidence_registry.json':live=repo/'evidence/evidence_registry.json'
  elif name=='q_update.json':live=repo/'evidence/q_updates'/(state['current_q']+'.json')
  elif (repo/'accepted'/relative).is_file():live=repo/'accepted'/relative
  elif (repo/'model'/relative).is_file():live=repo/'model'/relative
  else:raise RuntimeError('Unknown snapshot member; cannot verify safely: '+relative)
  if file_bytes(frozen)!=file_bytes(live):raise RuntimeError('Accepted snapshot mismatch: '+relative)
 result['ACCEPTED_SNAPSHOT_MATCH']='PASS'
 for pid,item in state['programs'].items():
  if not isinstance(item,dict) or not str(item.get('status','')).startswith('ACTIVE'):continue
  for key,value in item.items():
   if (key.endswith('_path') or key in {'path','implementation'}) and isinstance(value,str) and '/' in value and value not in entries:raise RuntimeError('Missing active registered path: '+pid+'/'+key)
  if item.get('workflow_id') and '.github/workflows/'+item['workflow_id'] not in entries:raise RuntimeError('Missing active registered workflow: '+pid)
 result['ACTIVE_REGISTRY_PATHS']='PASS'
 for key in ['promotion_commit','verified_remote_publication_commit']:
  commit=release.get(key)
  if commit:
   if not re.fullmatch(r'[0-9a-fA-F]{40}',commit):raise RuntimeError('Invalid real Git provenance: '+key)
   git(repo,'cat-file','-e',commit+'^{commit}');git(repo,'merge-base','--is-ancestor',commit,'HEAD')
 result['REGISTERED_GIT_PROVENANCE']='PASS'
 regression=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests/programs','-p','test*.py'],cwd=repo,text=True,capture_output=True)
 regression_log=regression.stdout+regression.stderr;(work/'regressions.log').write_text(regression_log)
 if regression.returncode:raise RuntimeError('Regression tests failed:\n'+regression_log)
 count=re.search(r'Ran (\d+) tests?',regression_log)
 result['REGRESSION_TESTS']={'status':'PASS','tests_run':int(count[1]) if count else None}
 after=inventory(repo)[0]
 if before!={p:e['sha256'] for p,e in after.items()}:raise RuntimeError('A validation modified tracked repository files')
 result['NON_DESTRUCTIVE']='PASS';return result

def verified_installation_receipt(repo,q,receipt,state):
 if not isinstance(receipt,dict) or receipt.get('target_q')!=q or receipt.get('stop_state')!='PROMOTED' or receipt.get('remote_promotion_verified') is not True:raise RuntimeError('A verified successful remote installation receipt is missing')
 if q_number(q)>q_number(state['current_q']):raise RuntimeError('Installation lies beyond the current accepted boundary')
 version=receipt.get('accepted_version')
 if not isinstance(version,str) or '/' in version or version in {'','.','..'} or not (repo/'versions/accepted'/version).is_dir():raise RuntimeError('Installed immutable snapshot is missing')
 for key in ['baseline_commit','initial_main_commit','package_commit','promotion_commit']:
  commit=receipt.get(key)
  if not isinstance(commit,str) or not re.fullmatch(r'[0-9a-fA-F]{40}',commit):raise RuntimeError('Missing real installation Git identity: '+key)
  git(repo,'cat-file','-e',commit+'^{commit}');git(repo,'merge-base','--is-ancestor',commit,'HEAD')
 installed=json.loads(git(repo,'show',receipt['promotion_commit']+':accepted/model_state.json'))
 if installed.get('current_q')!=q or installed.get('accepted_model_version')!=version:raise RuntimeError('Promotion commit does not contain the claimed installed state')
 return receipt

def bundle_installers(repo,entries,jsons,state):
 rows=[]
 for workflow in entries:
  m=re.fullmatch(r'\.github/workflows/(q\d+)-install-model\.yml',workflow,re.I)
  if not m:continue
  q=m[1].upper();bundle=q+'_model_update.bundle';guide=q+'_INSTALL_ACTIONS.md'
  cohort={p for p in [workflow,bundle,guide] if p in entries};receipt_path='provenance/'+q+'_REMOTE_INSTALLATION_RECEIPT.json';reason=None
  try:
   receipt=verified_installation_receipt(repo,q,jsons.get(receipt_path),state)
   if bundle not in entries:raise RuntimeError('Bundle payload is unavailable for a complete history audit')
   if any(entries[p]['mode'] not in {'100644','100755'} for p in cohort):raise RuntimeError('Installation artifact is not a regular file')
   if digest(repo/bundle)!=receipt.get('bundle_sha256'):raise RuntimeError('Bundle differs from the successful installation receipt')
   git(repo,'bundle','verify',bundle)
   for line in git(repo,'bundle','list-heads',bundle).splitlines():
    commit=line.split()[0];git(repo,'cat-file','-e',commit+'^{commit}');git(repo,'merge-base','--is-ancestor',commit,'HEAD')
   for p in cohort:
    original=subprocess.check_output(['git','show',receipt['initial_main_commit']+':'+p],cwd=repo)
    if git(repo,'rev-parse',receipt['initial_main_commit']+':'+p)!=entries[p]['git_blob_sha'] or digest(repo/p)!=sha_bytes(original):
     raise RuntimeError('Installation artifact changed after verified input: '+p)
   inbound={ref for p in cohort for ref in entries[p]['referenced_by'] if ref not in cohort and not (ref.startswith('provenance/cleanup/') and jsons.get(ref,{}).get('reference_scope')=='HISTORICAL_GIT_OBJECTS_AT_HEAD_BEFORE')}
   if inbound:raise RuntimeError('Retained files depend on installer artifacts: '+', '.join(sorted(inbound)))
  except (RuntimeError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as exc:reason=str(exc)
  rows.append({'q':q,'cohort':cohort,'receipt_path':receipt_path,'reason':reason})
 return rows

def metadata_updates(repo,entries,jsons,state):
 changes={};accepted=state['accepted'];q=state['current_q'];boundary=state['current_q_boundary'];version=state['current_accepted_version'];revision=accepted.get('model_revision');formal=state['current_formal_model']
 replacements=[(r'(Current authorized boundary: \*\*)[^*]+(\*\*)',boundary),(r'(Accepted model: \*\*)[^*]+(\*\*)',version+(' / '+revision if revision else '')),(r'(Formal model: \*\*)[^*]+(\*\*)',formal),(r'(- Authorized scientific range: \*\*)[^*]+(\*\*)',boundary.replace('-','–')),(r'(- Accepted model: \*\*)[^*]+(\*\*)',version+(' / '+revision if revision else ''))]
 for path in ['README.md','model/README.md']:
  if path not in entries:continue
  original=(repo/path).read_text();s=original
  for pattern,value in replacements:
   if value is not None:s=re.sub(pattern,lambda m:m[1]+value+m[2],s)
  if s!=original:changes[path]=s
 # A later installation receipt augments the immutable historical preparation report.
 receipt_path='provenance/'+q+'_REMOTE_INSTALLATION_RECEIPT.json'
 try:
  receipt=verified_installation_receipt(repo,q,jsons.get(receipt_path),state)
  if receipt['accepted_version']!=version:raise RuntimeError('Receipt is for another accepted version')
 except (RuntimeError,ValueError,KeyError,TypeError):receipt=None
 if receipt and 'README.md' in entries:
  original=(repo/'README.md').read_text();s=changes.get('README.md',original)
  s=re.sub(r'(?m)^- (?:Local candidate promotion|Repository installation): .*$',f'- Repository installation: **VERIFIED**; remote accepted model **{version} / {revision} through {q}**. Historical local-preparation reports are preserved.',s)
  s=re.sub(r'(?m)^- Publication status: .*$',f'- Publication status: `{receipt_path}`. `release/MODEL_RELEASE_HANDOFF.json` preserves the earlier preparation-time publication status.',s)
  if s!=original:changes['README.md']=s
 registry=jsons.get('tests/test_registry.json');path='tests/test_registry.json'
 if registry and path in entries:
  new=json.loads(json.dumps(registry))
  for item in new.get('tests',[]):
   text=item.get('why_test_matters','')
   if text.startswith('Accepted/candidate identity must match '):item['why_test_matters']=f'Accepted/candidate identity must match {boundary} / CURRENT_Q {q}.'
   elif text.startswith('Scientific candidate/evidence JSON must contain no Q identifier above '):item['why_test_matters']=f'Scientific candidate/evidence JSON must contain no Q identifier above {q}.'
  if new!=registry:changes[path]=json.dumps(new,indent=2,sort_keys=True)+'\n'
 path='tests/TEST_PLAN_CURRENT.md'
 if registry and path in entries:
  original=(repo/path).read_text();s=original
  fields={'Campaign':registry.get('campaign_id'),'Authorized Q range':boundary.replace('-','–'),'Current Q':q,'Accepted model':version}
  for key,value in fields.items():
   if value is not None:s=re.sub(r'(?m)^(\*\*'+re.escape(key)+r':\*\* )[^\n]+',lambda m:m[1]+value+'  ',s)
  rows=registry.get('tests',[])
  if '| TEST_ID | Current target | Required |' in s:
   table='| TEST_ID | Current target | Required |\n|---|---|---|\n'+''.join('| '+t['test_id']+' | '+t.get('target_component','Registered current test').replace('|','/')+' | '+('YES' if t.get('mandatory_for_current_validation') else 'NO')+' |\n' for t in rows)
   s=re.sub(r'\| TEST_ID \| Current target \| Required \|\n(?:\|[^\n]*\n)+',lambda _:table,s,count=1)
  s=re.sub(r'All (?:ten|eleven|\d+) current scientific/regression tests and all formal-model tests must PASS\.',f'All {len(rows)} current registered tests and all formal-model tests must PASS.',s)
  s=re.sub(r'The current scientific/model state is limited to Q\d+[-–]Q\d+\.',f'The current scientific/model state is limited to {boundary.replace("-","–")}.',s)
  if s!=original:changes[path]=s
 return changes

def audit(repo):
 entries,texts,jsons,errors,duplicates=inventory(repo);state=discover(repo,jsons);deletions=set();decisions=[]
 for row in bundle_installers(repo,entries,jsons,state):
  for p in row['cohort']:
   if row['reason']:entries[p].update(classification='REVIEW_REQUIRED',reason=row['reason'])
   else:
    deletions.add(p)
    entries[p].update(classification='SAFE_DELETE',reason='Completed bundle installation; exact input artifacts, successful receipt, immutable target and all bundled Git heads preserved',canonical_alternative=row['receipt_path'],change_class='OBSOLETE_WORKFLOW_REMOVAL' if p.endswith('.yml') else 'INSTALLER_REMOVAL')
 # An installer is completed only with a persisted, verified receipt and reachable commits.
 for path in entries:
  match=re.fullmatch(r'install_(q\d+)_model\.py',path,re.I)
  if not match:continue
  q=match[1].upper();number=q_number(q);workflow='.github/workflows/install-'+q.lower()+'-model.yml';guide='INSTALL_'+q+'.md';cohort={p for p in [path,workflow,guide] if p in entries};reason=None
  receipt=jsons.get('release/'+q+'_INSTALLATION_RESULT.json')
  if not receipt or receipt.get('target_q')!=q or not receipt.get('remote_promotion_verified') or q_number(state['current_q'])<number:reason='Installation completion is not verified through the current accepted boundary'
  elif any(entries[p]['mode'] not in {'100644','100755'} for p in cohort):reason='Installer cohort contains a non-regular file'
  elif not (repo/'versions/accepted'/str(receipt.get('accepted_version',''))).is_dir():reason='Installer target snapshot is missing'
  else:
   for key in ['installation_input_commit','promotion_commit','verified_remote_publication_commit']:
    commit=receipt.get(key)
    try:
     if not commit or not re.fullmatch(r'[0-9a-fA-F]{40}',commit):raise RuntimeError('Missing commit')
     git(repo,'cat-file','-e',commit+'^{commit}');git(repo,'merge-base','--is-ancestor',commit,'HEAD')
    except RuntimeError:reason='Installer completion Git provenance is unresolved';break
   if reason is None:
    for p in cohort:
     try:blob=git(repo,'rev-parse',receipt['installation_input_commit']+':'+p)
     except RuntimeError:reason='Installed artifact has no verified original Git blob';break
     if blob!=entries[p]['git_blob_sha']:reason='Installer artifact changed after its verified installation';break
  inbound={ref for p in cohort for ref in entries[p]['referenced_by'] if ref not in cohort and not (ref.startswith('provenance/cleanup/') and jsons.get(ref,{}).get('reference_scope')=='HISTORICAL_GIT_OBJECTS_AT_HEAD_BEFORE')}
  if inbound:reason='Retained files still depend on the installer cohort: '+', '.join(sorted(inbound))
  if reason:
   for p in cohort:entries[p].update(classification='REVIEW_REQUIRED',reason=reason)
  else:
   deletions.update(cohort)
   for p in cohort:entries[p].update(classification='SAFE_DELETE',reason='Completed one-time installer; verified receipt, immutable target and real Git history retained',canonical_alternative='release/'+q+'_INSTALLATION_RESULT.json',change_class='OBSOLETE_WORKFLOW_REMOVAL' if p.endswith('.yml') else 'INSTALLER_REMOVAL')
 # Exact duplicate-name accidents and source-reproducible compiled caches only.
 for p,e in entries.items():
  if p in deletions or p.startswith(PROTECTED) or p in UPLOADS:continue
  refs=set(e['referenced_by'])-deletions;regular=e['mode'] in {'100644','100755'}
  name=Path(p).name;canonical=re.sub(r'(?:-\d+|_copy(?:-\d+)?| copy(?: \(\d+\))?| \(\d+\))(?=\.[^.]+$)','',name,flags=re.I)
  alternatives=[other for other,x in entries.items() if Path(other).name==canonical and other!=p and x['sha256']==e['sha256'] and other not in deletions]
  if canonical!=name and len(alternatives)==1 and not refs and regular:
   e.update(classification='SAFE_DELETE',reason='Exact unreferenced duplicate-name accident with one retained canonical alternative',canonical_alternative=alternatives[0],change_class='DUPLICATE_REMOVAL');deletions.add(p)
  elif p.endswith('.pyc') and '/__pycache__/' in '/'+p and not refs and regular:
   source=(Path(p).parent.parent/(name.split('.')[0]+'.py')).as_posix()
   if source in entries:e.update(classification='SAFE_DELETE',reason='Reproducible compiled cache; tracked Python source retained',canonical_alternative=source,change_class='TEMPORARY_FILE_REMOVAL');deletions.add(p)
  elif name=='.DS_Store' and not refs and regular:e.update(classification='SAFE_DELETE',reason='Finder directory metadata without scientific role or dependencies',canonical_alternative=None,change_class='TEMPORARY_FILE_REMOVAL');deletions.add(p)
  elif SUSPICIOUS.search(p) or re.search(r'(?:^|/)(?:run-output|__pycache__|\.pytest_cache)/',p):e.update(classification='REVIEW_REQUIRED',reason='Suspicious name/output without positive verified redundancy; retained')
 for error in errors:
  if not error['path'].startswith(PROTECTED):entries[error['path']].update(classification='UNKNOWN',reason='Unparseable file retained: '+error['error']);deletions.discard(error['path'])
 updates=metadata_updates(repo,entries,jsons,state)
 for p in updates:entries[p].update(classification='UPDATE',reason='Synchronize only current documentation/descriptive metadata with canonical machine state',change_class='DOCUMENTATION_SYNC')
 if any(p.endswith('.pyc') for p in deletions):
  ignore=(repo/'.gitignore').read_text() if '.gitignore' in entries else ''
  if '*.py[cod]' not in ignore and '*.pyc' not in ignore:updates['.gitignore']=ignore.rstrip()+'\n__pycache__/\n*.py[cod]\n'
 for p in deletions:
  e=entries[p];inbound={ref for ref in set(e['referenced_by'])-deletions if not (ref.startswith('provenance/cleanup/') and jsons.get(ref,{}).get('reference_scope')=='HISTORICAL_GIT_OBJECTS_AT_HEAD_BEFORE')}
  if inbound:raise RuntimeError('Deletion creates live dependencies: '+p)
  e['delete_gate']={'FILE_EXISTS':'PASS','CANONICAL_ALTERNATIVE':'PASS' if e.get('canonical_alternative') else 'NOT_APPLICABLE','REFERENCE_SCAN':'PASS_ATOMIC_COHORT','PROVENANCE_PRESERVED':'PASS_GIT_BLOB_AT_INPUT_HEAD','ACCEPTED_MODEL_PROTECTION':'PASS','VERSION_SNAPSHOT_PROTECTION':'PASS','TEST_HISTORY_PROTECTION':'PASS','SCIENTIFIC_CHANGE':False,'DELETE_CLASSIFICATION':'SAFE_DELETE','BASELINE_VALIDATION':'PENDING'}
 report={'schema_version':2,'target_repo':git(repo,'config','--get','remote.origin.url'),'date_time':datetime.now(timezone.utc).isoformat(),'default_branch':default_branch(repo),'head_before':git(repo,'rev-parse','HEAD'),'current_q_boundary':state['current_q_boundary'],'current_accepted_version':state['current_accepted_version'],'current_candidate_state':state['current_candidate_state'],'current_formal_model':state['current_formal_model'],'current_release_state':state['current_release_state'],'files_scanned':len(entries),'repository_map':list(entries.values()),'duplicate_groups':duplicates,'parse_observations':errors,'review_required':[p for p,e in entries.items() if e['classification']=='REVIEW_REQUIRED'],'unknown':[p for p,e in entries.items() if e['classification']=='UNKNOWN'],'planned_deletions':sorted(deletions),'planned_updates':sorted(updates),'archive_moves':[],'scientific_change':False,'accepted_state_changed':False,'q_boundary_changed':False,'model_version_changed':False}
 return report,updates

def cleanup(repo,mode):
 input_head=git(repo,'rev-parse','HEAD');branch=default_branch(repo)
 with tempfile.TemporaryDirectory(prefix='bubbleverse-cleanup-') as folder:
  work=Path(folder);stage=work/'validated-tree';git(repo,'worktree','add','--quiet','--detach',str(stage),input_head)
  try:
   report,updates=audit(stage);report['mode']=mode;report['pre_cleanup_tests']=validate(stage,work)
   for e in report['repository_map']:
    if 'delete_gate' in e:e['delete_gate']['BASELINE_VALIDATION']='PASS'
   deletions=report['planned_deletions'];actions=bool(deletions or updates);before={p:e['sha256'] for p,e in inventory(stage)[0].items()};protected={p:h for p,h in before.items() if p not in set(deletions)|set(updates)}
   report.update(protected_files_verified=len(protected),accepted_snapshot_files=sum(p.startswith('versions/accepted/') for p in protected),removed_files=[],updated_files=[],push_performed=False,head_after=input_head)
   if mode=='AUDIT':report['cleanup_status']='AUDIT_ONLY'
   elif not actions:report['cleanup_status']='PARTIAL_CLEAN' if report['review_required'] or report['unknown'] else 'CLEAN'
   else:
    for p in deletions:
     if digest(stage/p)!=before[p]:raise RuntimeError('Delete input changed: '+p)
     (stage/p).unlink()
    for p,s in updates.items():(stage/p).write_text(s,encoding='utf-8')
    report['post_cleanup_tests']=validate(stage,work)
    after=inventory(stage)[0]
    for p,h in protected.items():
     if p not in after or after[p]['sha256']!=h:raise RuntimeError('Protected file changed: '+p)
    if set(after)!=set(before)-set(deletions)|set(updates):raise RuntimeError('Unexpected structural tree change')
    # Re-audit the resulting tree rather than using a stale incoming plan.
    post,remaining=audit(stage)
    if remaining or post['planned_deletions']:raise RuntimeError('Cleanup did not converge; no caller files changed')
    report['cleanup_status']='PARTIAL_CLEAN' if post['review_required'] or post['unknown'] else 'CLEANED';report['removed_files']=deletions;report['updated_files']=sorted(updates);report['review_required']=post['review_required'];report['unknown']=post['unknown'];report['protected_hashes']=protected
    receipt=stage/'provenance/cleanup'/('cleanup_'+input_head+'.json');receipt.parent.mkdir(parents=True,exist_ok=True)
    historical=dict(report);historical['reference_scope']='HISTORICAL_GIT_OBJECTS_AT_HEAD_BEFORE';historical['publication_status']='LOCAL_COMMIT_OPERATOR_PUSH_REQUIRED';receipt.write_text(json.dumps(historical,indent=2,sort_keys=True)+'\n')
    targets=deletions+list(updates)+[receipt.relative_to(stage).as_posix()]
    git(stage,'add','-A','--',*targets)
    changed=set(git(stage,'diff','--cached','--name-only').splitlines())
    if changed!=set(targets):raise RuntimeError('Unexpected staged diff')
    git(stage,'-c','user.name=Bubbleverse Repository Cleanup','-c','user.email=repository-cleanup@users.noreply.github.com','commit','--quiet','-m','Repository cleanup: remove verified clutter and sync current documentation')
    final=git(stage,'rev-parse','HEAD');clean(repo)
    if git(repo,'branch','--show-current')!=branch or git(repo,'rev-parse','HEAD')!=input_head:raise RuntimeError('Operator branch or HEAD changed during validation; no cleanup applied')
    caller={p:e['sha256'] for p,e in inventory(repo)[0].items()}
    if caller!=before:raise RuntimeError('Operator files changed during validation; no cleanup applied')
    git(repo,'merge','--ff-only',final);report['head_after']=final;report['cleanup_receipt']=receipt.relative_to(stage).as_posix()
   clean(repo)
   if git(repo,'branch','--show-current')!=branch or git(repo,'rev-parse','HEAD')!=report['head_after']:raise RuntimeError('Operator branch or HEAD changed during validation')
   return report
  finally:git(repo,'worktree','remove','--force',str(stage))

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,default=Path.cwd());parser.add_argument('--target-repo',default='Morfindien/bubbleverse-model');parser.add_argument('--mode',choices=['AUDIT','CLEAN'],default='CLEAN');parser.add_argument('--report',type=Path);args=parser.parse_args()
 try:
  report=cleanup(repository(args.repo,args.target_repo),args.mode)
  if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
  summary={k:v for k,v in report.items() if k not in {'repository_map','protected_hashes','duplicate_groups'}};print(json.dumps(summary,indent=2));return 0
 except Exception as exc:print('CLEANUP_BLOCKED: '+str(exc),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
