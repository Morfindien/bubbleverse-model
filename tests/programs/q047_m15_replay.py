"""Replay the existing, pinned Q047 rational audit on preserved input bytes."""
import hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path

CODE_SHA256_PLACEHOLDER = '48338ea8077f32c2babb5ebf032a136c916955f31e762620603b62ac0a820607'

def replay(source_root):
 source_root=Path(source_root)
 code=source_root/'q047_m15_exact_audit_v1.py'
 if hashlib.sha256(code.read_bytes()).hexdigest()!=CODE_SHA256_PLACEHOLDER:
  raise AssertionError('Refuse to execute an unreviewed M15 audit')
 with tempfile.TemporaryDirectory(prefix='q047-rational-replay-') as temp:
  work=Path(temp);(work/'upload').mkdir();(work/'q047_math_work').mkdir()
  expected=json.loads((source_root/'Q047_M15_EXACT_AUDIT_V1.json').read_text())
  files=[]
  for case,row in expected['cases'].items():
   p=source_root/f'Q047_RECONSTRUCTION_STATE_{case}_V1.json'
   if hashlib.sha256(p.read_bytes()).hexdigest()!=row['state_sha256']:raise AssertionError('Captured state identity changed')
   shutil.copyfile(p,work/'upload'/p.name)
   for name in ['accepted_initial_hex.json','effective_background_hex.json','source_objects/source/background.c','source_objects/include/common.h']:
    raw=source_root/case/name
    files.append({'artifact_relative_path':'q047_reconstructed/'+case+'/'+name,'local_path':str(raw.resolve()),'sha256':hashlib.sha256(raw.read_bytes()).hexdigest()})
  (work/'upload/Q047_RAW_EVIDENCE_INDEX_V1.json').write_text(json.dumps({'files':files}))
  shutil.copyfile(code,work/'q047_math_work'/code.name)
  result=subprocess.run([sys.executable,str(work/'q047_math_work'/code.name)],text=True,capture_output=True,timeout=60)
  if result.returncode:raise AssertionError('Q047 existing exact audit failed: '+result.stderr[-2000:])
  actual=json.loads((work/'q047_math_work/Q047_M15_EXACT_AUDIT_V1.json').read_text())
  for obj in [actual,expected]:
   obj.pop('checked_utc');obj.pop('runtime')
  if actual!=expected:raise AssertionError('Rational replay differs beyond timestamp/runtime')
 return {'status':'PASS','method':'Existing source audit reproduced exactly except timestamp/runtime','scope':'NEW_RECONSTRUCTION finite arithmetic only','native_solver_executions':0}
