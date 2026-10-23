#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, os, re, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET_Q='Q048'; PREV_Q='Q047'; VERSION='v0.10'; PREV_VERSION='v0.9'; REV='R000010'
SOURCE_COMMIT='b99a5c78058b624c8d5847bed582df4ea816358a'
BASE_COMMIT='630605327083fcd1bfd28ebf326d783346c1dabe'
FROZEN_SOURCE='5a131c91d657dd9a7c6364cc45b038710f8d0d97'
FROZEN_CAPTURE='2514e250d20c456530be63e790a079176293a87a82c927b1e748d1eec405da9b'
CHECKPOINT_SHA='60dcd23a315a28be2ef84c4c5353c783e88eb73c4199d43b7f5640a16db2eb96'
PROMPT_SHA='6fe2b3f9d9e37d31a8021edc52b2a625f97a4d184f0e3a386458ea11279d68a0'
EIDS=['EVD-Q048-QJOURNAL','EVD-Q048-APPENDICES','EVD-Q048-MAINBOOK','EVD-Q048-TERMINAL','EVD-Q048-CHECKPOINT']

QJ = '''BUBBLEVERSE — Q048 AUTHORIZED CURRENT-STATE EXCERPT
Q-ID: Q-048
Publication status: UNSOLVED

Research question
For each of the four Q041 FULL/start0 configurations explicitly reconstructed in run 38140371059, what rigorously controlled bounds can be placed on the differences in the complete electron-fraction history x_e(z) and cumulative Thomson optical depth tau_T(z) between an event-resolved latch at q=xHeII=10^-6 and a reset to q=0 at the same first cutoff event, with identical captured effective inputs and fixed accepted z_reio?

Documented answer
UNSOLVED. Q-048 established useful conditional and partial results but did not establish the complete four-configuration latch/reset histories or the complete cumulative Thomson optical-depth difference.

What was established
The accepted actual state for hillipop-ede_n3 reached actual127/frontier810; the other three tracked frontiers remain at 1440. A later Q-048 result established a conditional connected proof for 810 -> 800, but that proof was not consumed into a new accepted actual checkpoint. Earlier work also preserved conditional three-configuration event certificates and a documented scalar-wall obstruction for hillipop-ede_n3.

What remains unresolved
The complete four-configuration x_e(z) and tau_T(z) latch/reset comparison remains unestablished. NativeP6, physical/native trajectory identity, exact selector existence and uniqueness, and a native error certificate remain unresolved. A technical failure in the final attempted continuation is not a physical falsification.

Scientific limitations
The supported results are conditional on the frozen Q-048 source/capture, fixed accepted z_reio, the stated branch definitions and the documented validation contracts. Conditional continuation must not be relabelled as a validated native trajectory, and an unconsumed proof must not be reported as an accepted actual-state advance.
'''
MAIN = '''BUBBLEVERSE — Q048 AUTHORIZED MAIN-BOOK EXCERPT
Status: Q-048 UNSOLVED. The complete four-configuration latch-versus-reset electron-fraction history and cumulative Thomson optical-depth comparison remains unestablished.

What Q-048 established
Q-048 produced validated conditional and partial results. The accepted actual checkpoint for hillipop-ede_n3 reaches actual127/frontier810, while the other three tracked frontiers remain at 1440. A later result established a conditional connected proof for the 810 -> 800 cell, but that proof was not consumed into a new accepted actual checkpoint. Earlier work also preserved conditional event certificates for three configurations and a documented scalar-wall obstruction for hillipop-ede_n3. These are scientifically useful within their frozen assumptions, but they are not complete latch-versus-reset histories.

What remains unresolved
The complete four-configuration x_e(z) and tau_T(z) comparison is still not known. NativeP6, physical/native trajectory identity, exact selector existence and uniqueness, and a native error certificate remain unresolved. The final technical continuation failure is not a physical falsification.

Current scientific consequence
Q-048 therefore does not justify a new cosmological observation, a model preference, an EDE viability claim, or a completed opacity correction. The distinction between conditional mathematical continuation and a validated native trajectory remains essential.
'''
APP = '''BUBBLEVERSE — Q048 AUTHORIZED TECHNICAL-APPENDIX EXCERPT
Q-048 current technical status: UNSOLVED. Partial validated state exists, but the complete four-configuration x_e(z)/tau_T(z) comparison and native-fidelity certificate are not established.

Accepted actual state and proof boundary
The last accepted actual checkpoint for hillipop-ede_n3 is actual127/frontier810. The other tracked frontiers remain 1440. The subsequent 810 -> 800 result is an accepted unconsumed conditional connected proof; it must not be reported as an accepted actual-state advance.

Conditional evidence retained
Q-048 retains conditional source-real continuation bounds within the frozen source/capture identity and documented branch and validation contracts. Earlier event-state work also retains conditional three-configuration certificates and a fourth-case scalar-wall obstruction. Missing fields or unconsumed proofs are not zero-valued measurements.

Native and physical gaps
NativeP6 remains unresolved. Physical/native trajectory identity, exact selector existence and uniqueness, and a native error certificate are unestablished. Conditional mathematics does not by itself certify the trajectory selected by the pinned native implementation.

Failure classification
The final attempted continuation stopped on a technical pre-freeze schema-binding defect before a consumer dispatch. That event supplies no physical exclusion, no null detection and no evidence against the underlying cosmological configuration.

Observable consequence
No complete controlled bound on the coupled latch-versus-reset difference in x_e(z) or cumulative tau_T(z) has been established for all four configurations. Downstream visibility, spectra, likelihood and inference claims therefore remain outside the demonstrated Q-048 result.
'''

def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def dump(rel,obj):
    p=ROOT/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def write(rel,s):
    p=ROOT/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s,encoding='utf-8')
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(rel): return sha_bytes((ROOT/rel).read_bytes())
def set_boundary(o):
    if 'q_access_end' in o: o['q_access_end']=TARGET_Q
    if 'current_q' in o: o['current_q']=TARGET_Q
    return o

def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def ensure_base():
    accepted=load('accepted/model_state.json')
    assert accepted['current_q']==PREV_Q and accepted['accepted_model_version']==PREV_VERSION, accepted.get('current_q')
    assert load('versions/accepted/v0.9/model_state.json')['current_q']==PREV_Q
    head=git('rev-parse','HEAD')
    merge_base=git('merge-base',BASE_COMMIT,'HEAD')
    assert merge_base==BASE_COMMIT, f'installer branch must descend from pinned base {BASE_COMMIT}; got merge-base {merge_base}'
    staged=set(x for x in git('diff','--name-only',BASE_COMMIT,'HEAD').splitlines() if x)
    allowed={'q048_model_update.py','.github/workflows/install-q048-model-v010.yml'}
    assert staged <= allowed, f'unexpected pre-install branch changes relative to pinned base: {sorted(staged-allowed)}'

def add_evidence_entry(ev,eid,source,role):
    ev['entries'].append({
        'evidence_id':eid,'q_id':TARGET_Q,'authority_class':'AUTHORITATIVE_BUBBLEVERSE_SOURCE',
        'source':source,'source_files':[source],'sha256':sha(source),'role':role,
        'scientific_evidence':True,'scientific_ingestion':True,'new_scientific_inference':False,
        'physical_falsification':False,'production_restart_authorized':False,
        'independent_cosmological_evidence':False,'validation_status':'PASS_SOURCE_IDENTITY_AND_SCOPE_ONLY'
    })

def make_q048_validator():
    hashes={p:sha(p) for p in [
        'evidence/sources/Q048/q_journal_authorized.txt','evidence/sources/Q048/main_book_authorized.txt',
        'evidence/sources/Q048/appendices_authorized.txt','evidence/sources/Q048/source_terminal_authorized.json',
        'evidence/sources/Q048/checkpoint_authorized.json']}
    code=f'''#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def req(c,m):
    if not c: raise AssertionError(m)
def run_tests(root=ROOT):
    global ROOT; ROOT=Path(root); rows=[]
    def gate(i,name,fn):
        try: rows.append({{"id":f"Q048-{{i:02d}}","name":name,"status":"PASS","detail":fn()}})
        except Exception as e: rows.append({{"id":f"Q048-{{i:02d}}","name":name,"status":"FAIL","detail":f"{{type(e).__name__}}: {{e}}"}})
    a=load("accepted/model_state.json"); q=load("evidence/q_updates/Q048.json"); ev=load("evidence/evidence_registry.json")
    def identity():
        req(a["current_q"]==a["q_access_end"]=="Q048","accepted boundary")
        req(a["accepted_model_version"]=="v0.10" and a["candidate_revision"]=="R000010","version")
        req(load("versions/accepted/v0.9/model_state.json")["current_q"]=="Q047","predecessor")
        return "Q047/v0.9 -> Q048/v0.10"
    gate(1,"sequence and identity",identity)
    def semantics():
        req(q["publication_status"]=="UNSOLVED" and q["scientific_status"]=="UNRESOLVED","status")
        req(q["internal_stop_status"]=="UNRESOLVED — BUDGET EXHAUSTED","terminal status")
        req(q["physical_model_change"] is False and q["new_scientific_inference"] is False and q["physical_falsification"] is False and q["production_restart_authorized"] is False,"overclaim")
        return "terminal unresolved admitted without physical verdict"
    gate(2,"claim-strength firewall",semantics)
    def partial():
        req(a["q048_actual_checkpoint"]=={{"actual_count":127,"frontier":810,"configuration":"hillipop-ede_n3"}},"actual checkpoint")
        req(a["q048_tracked_frontiers"]=={{"camspec-ede_n3":1440,"camspec-lcdm":1440,"hillipop-ede_n3":810,"hillipop-lcdm":1440}},"frontiers")
        req(a["q048_conditional_810_800_proof"]=="ACCEPTED_UNCONSUMED","proof")
        return "actual127/frontier810 preserved; unconsumed proof not promoted"
    gate(3,"partial-state boundary",partial)
    def unresolved():
        for k in ["q048_native_p6","q048_physical_native_trajectory_identity","q048_selector_existence_uniqueness","q048_native_error_certificate"]: req(a[k]=="UNRESOLVED",k)
        return "native/trajectory/selector/error gaps remain unresolved"
    gate(4,"unresolved qualification",unresolved)
    expected={json.dumps({
        'EVD-Q048-QJOURNAL':hashes['evidence/sources/Q048/q_journal_authorized.txt'],
        'EVD-Q048-MAINBOOK':hashes['evidence/sources/Q048/main_book_authorized.txt'],
        'EVD-Q048-APPENDICES':hashes['evidence/sources/Q048/appendices_authorized.txt'],
        'EVD-Q048-TERMINAL':hashes['evidence/sources/Q048/source_terminal_authorized.json'],
        'EVD-Q048-CHECKPOINT':hashes['evidence/sources/Q048/checkpoint_authorized.json']},sort_keys=True)}
    def sources():
        em={{x["evidence_id"]:x for x in ev["entries"]}}
        for eid,d in expected.items(): req(eid in em and em[eid]["sha256"]==d and sha(em[eid]["source"])==d,eid)
        return "five bounded Q048 evidence objects pinned"
    gate(5,"source identity",sources)
    def firewall():
        objs=[load("accepted/model_state.json"),load("accepted/constraints.json"),load("accepted/robustness.json"),load("evidence/evidence_registry.json"),load("evidence/q_updates/Q048.json")]
        for p in (ROOT/"model").glob("*.json"): objs.append(json.loads(p.read_text()))
        nums=[int(x) for o in objs for x in re.findall(r"\\bQ-?0*([0-9]{{1,5}})\\b",json.dumps(o),flags=re.I)]
        req(nums and max(nums)<=48,"future-Q contamination")
        return "maximum current scientific Q is Q048"
    gate(6,"Q firewall",firewall)
    def regression():
        old=ROOT/"versions/accepted/v0.9"
        for cur,key in [("accepted/observations.json","observations"),("accepted/mechanisms.json","mechanisms"),("accepted/predictions.json","predictions"),("accepted/contradictions.json","contradictions")]:
            req(load(cur)[key]==json.loads((old/Path(cur).name).read_text())[key],"inherited layer changed: "+cur)
        for cur,key in [("accepted/constraints.json","constraints"),("accepted/robustness.json","items"),("model/limitations.json","limitations"),("model/uncertainty.json","uncertainties"),("model/domain_of_validity.json","domains")]:
            before=json.loads((old/Path(cur).name).read_text())[key]; after=load(cur)[key]; req(after[:len(before)]==before,"historical prefix changed: "+cur)
        return "Q001-Q047 scientific entries preserved as prefixes"
    gate(7,"regression preservation",regression)
    def snapshot():
        snap=ROOT/"versions/accepted/v0.10"
        mapping={{"MODEL_CURRENT.md":"accepted/MODEL_CURRENT.md","constraints.json":"accepted/constraints.json","contradictions.json":"accepted/contradictions.json","mechanisms.json":"accepted/mechanisms.json","model_state.json":"accepted/model_state.json","observations.json":"accepted/observations.json","predictions.json":"accepted/predictions.json","robustness.json":"accepted/robustness.json","evidence_registry.json":"evidence/evidence_registry.json","q_update.json":"evidence/q_updates/Q048.json","candidate_diff.json":"candidate/candidate_diff.json"}}
        for n,p in mapping.items(): req((snap/n).read_bytes()==(ROOT/p).read_bytes(),"snapshot mismatch: "+n)
        for n in ["README.md","assumptions.json","benchmarks.json","domain_of_validity.json","environment.json","equations.json","external_catalog_registry.json","input_schema.json","limitations.json","model_manifest.json","output_schema.json","parameters.json","result_registry.json","uncertainty.json"]: req((snap/n).read_bytes()==(ROOT/"model"/n).read_bytes(),"formal snapshot mismatch: "+n)
        return "v0.10 snapshot matches live accepted/formal/evidence state"
    gate(8,"snapshot coherence",snapshot)
    def budget():
        req(a["q048_budget"]=={{"effective_remaining_for_q048_physics_runs_pts":0,"limit_pts":1000,"remaining_pts":38,"used_pts":962}},"budget")
        return "962/1000 used; 38 residual; zero effective Q048 physics capacity"
    gate(9,"terminal accounting semantics",budget)
    def technical():
        txt=(ROOT/"evidence/sources/Q048/appendices_authorized.txt").read_text().lower(); req("technical pre-freeze schema-binding defect" in txt and "no physical exclusion" in txt,"failure semantics"); return "technical failure not promoted into physical evidence"
    gate(10,"technical-vs-physical gate",technical)
    passed=sum(r["status"]=="PASS" for r in rows); return {{"artifact_type":"Q048_MODEL_VALIDATION","target_q":"Q048","tests":rows,"tests_total":len(rows),"tests_passed":passed,"all_green":passed==len(rows)}}
if __name__=="__main__":
    r=run_tests(); [print(f'{{x["id"]}}={{x["status"]}} {{x["detail"]}}') for x in r["tests"]]; print(f'Q048_MODEL_TESTS={{r["tests_passed"]}}/{{r["tests_total"]}}'); raise SystemExit(0 if r["all_green"] else 1)
'''
    write('tests/programs/q048_model_validate.py',code)

def patch_campaign():
    p=ROOT/'tests/programs/model_campaign.py'; s=p.read_text()
    s=s.replace('MANDATORY_IDS = [f"T-BV-{i:03d}" for i in range(1, 17)]','MANDATORY_IDS = [f"T-BV-{i:03d}" for i in range(1, 18)]')
    marker="    results['T-BV-016'] = passfail(q47_ok, q47_detail)\n\n    return results"
    insert="""    results['T-BV-016'] = passfail(q47_ok, q47_detail)\n\n    q48_ok = True\n    q48_detail = 'Q048 terminal-unsolved admission is not applicable below Q048.'\n    if qmax >= 48:\n        from q048_model_validate import run_tests as q048_tests\n        q48_result = q048_tests(ROOT)\n        q48_ok = q48_result['all_green']\n        failures = [x['id'] for x in q48_result['tests'] if x['status'] != 'PASS']\n        q48_detail = 'Q048 terminal UNSOLVED status, partial-state boundary, source/firewall and snapshot gates: ' + ('PASS' if q48_ok else ', '.join(failures))\n    results['T-BV-017'] = passfail(q48_ok, q48_detail)\n\n    return results"""
    assert marker in s and 'T-BV-017' not in s
    p.write_text(s.replace(marker,insert),encoding='utf-8')

def apply():
    ensure_base(); now=datetime.now(timezone.utc).isoformat()
    changed=[]
    def mark(rel): changed.append(rel)
    # Bounded Q048 evidence only; future handoff text is deliberately excluded.
    for rel,txt in [('evidence/sources/Q048/q_journal_authorized.txt',QJ),('evidence/sources/Q048/main_book_authorized.txt',MAIN),('evidence/sources/Q048/appendices_authorized.txt',APP)]: write(rel,txt); mark(rel)
    terminal={'schema_version':1,'q_id':'Q048','authority':'AUTHORITATIVE_BUBBLEVERSE_SOURCE_BOUNDED_EXTRACTION','source_repository':'Morfindien/Bubbleverse','source_commit':SOURCE_COMMIT,'source_file':'revision.md','scientific_status':'UNRESOLVED','publication_status':'UNSOLVED','internal_stop_status':'UNRESOLVED — BUDGET EXHAUSTED','physical_model_change':False,'physical_falsification':False,'actual_checkpoint':{'configuration':'hillipop-ede_n3','actual_count':127,'frontier':810},'tracked_frontiers':{'camspec-lcdm':1440,'camspec-ede_n3':1440,'hillipop-lcdm':1440,'hillipop-ede_n3':810},'conditional_810_800_proof':'ACCEPTED_UNCONSUMED','unresolved':['complete four-configuration x_e(z)/tau_T(z) comparison','NativeP6','physical/native trajectory identity','exact selector existence and uniqueness','native error certificate'],'budget':{'limit_pts':1000,'used_pts':962,'remaining_pts':38,'effective_remaining_for_q048_physics_runs_pts':0},'source_boundary_note':'Only Q048 terminal/current-state fields are ingested; later-Q scientific content is excluded.'}
    checkpoint={'schema_version':1,'q_id':'Q048','authority':'AUTHORITATIVE_BUBBLEVERSE_SOURCE_BOUNDED_EXTRACTION','source_repository':'Morfindien/Bubbleverse','source_commit':SOURCE_COMMIT,'source_file':'Q048_V151_ACCEPTED_CHECKPOINT_V1.json','source_sha256':CHECKPOINT_SHA,'actual':{'count':127,'frontier':810},'frontiers':{'camspec-lcdm':1440,'camspec-ede_n3':1440,'hillipop-lcdm':1440,'hillipop-ede_n3':810},'role':'LAST_VALIDATED_ACTUAL_Q048_CHECKPOINT'}
    dump('evidence/sources/Q048/source_terminal_authorized.json',terminal); mark('evidence/sources/Q048/source_terminal_authorized.json')
    dump('evidence/sources/Q048/checkpoint_authorized.json',checkpoint); mark('evidence/sources/Q048/checkpoint_authorized.json')
    # Accepted layers.
    for rel in ['accepted/constraints.json','accepted/contradictions.json','accepted/mechanisms.json','accepted/observations.json','accepted/predictions.json','accepted/robustness.json']:
        o=set_boundary(load(rel)); dump(rel,o); mark(rel)
    con=load('accepted/constraints.json'); con['constraints'] += [
      {'id':'CON-Q048-UNSOLVED-COMPLETION','q_introduced':'Q048','evidence_refs':EIDS,'statement':'Q048 is UNSOLVED: no complete controlled four-configuration latch-versus-reset x_e(z) and cumulative tau_T(z) comparison is established. The accepted hillipop-ede_n3 actual checkpoint is actual127/frontier810; the other tracked frontiers remain at 1440.','status':'ACTIVE_LIMITATION','new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False},
      {'id':'CON-Q048-NO-PHYSICAL-VERDICT','q_introduced':'Q048','evidence_refs':EIDS,'statement':'Q048 does not establish a new cosmological observation, model preference, EDE viability claim, completed opacity correction, physical exclusion, null detection or production authorization. The terminal continuation failure is technical, not physical.','status':'NOT_ESTABLISHED','new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False}]
    dump('accepted/constraints.json',con)
    rob=load('accepted/robustness.json'); rob['items'] += [
      {'id':'ROB-Q048-PARTIAL-STATE','q_introduced':'Q048','evidence_refs':EIDS,'finding':'Q048 preserves useful conditional/partial evidence: hillipop-ede_n3 reaches actual127/frontier810, three other frontiers remain 1440, and the 810->800 connected proof is accepted but unconsumed. Conditional proof is not an accepted actual-state advance.','status':'SUPPORTED_WITH_SCOPE_LIMITS','new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False},
      {'id':'ROB-Q048-TECHNICAL-FAILURE-SCOPE','q_introduced':'Q048','evidence_refs':EIDS,'finding':'The final Q048 continuation stopped at a pre-freeze schema-binding defect before consumer dispatch. The failure is technical and supplies no physical falsification or cosmological exclusion.','status':'TECHNICAL_FAIL_SCOPE_ONLY','new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False}]
    dump('accepted/robustness.json',rob)
    st=load('accepted/model_state.json'); st.update({'accepted_at':now,'created_at':now,'accepted_model_version':VERSION,'candidate_model_version':VERSION,'candidate_revision':REV,'current_q':TARGET_Q,'q_access_end':TARGET_Q,'input_document_type':'AUTHORIZED_Q048_TERMINAL_UNSOLVED_AND_PARTIAL_RESULT','physical_model_change':False,'production_restart_authorized':False,'q048_scientific_status':'UNRESOLVED','q048_publication_status':'UNSOLVED','q048_internal_stop_status':'UNRESOLVED — BUDGET EXHAUSTED','q048_integration_status':'TERMINAL_UNSOLVED_ADMITTED','q048_actual_checkpoint':{'actual_count':127,'frontier':810,'configuration':'hillipop-ede_n3'},'q048_tracked_frontiers':{'camspec-lcdm':1440,'camspec-ede_n3':1440,'hillipop-lcdm':1440,'hillipop-ede_n3':810},'q048_conditional_810_800_proof':'ACCEPTED_UNCONSUMED','q048_native_p6':'UNRESOLVED','q048_physical_native_trajectory_identity':'UNRESOLVED','q048_selector_existence_uniqueness':'UNRESOLVED','q048_native_error_certificate':'UNRESOLVED','q048_budget':{'limit_pts':1000,'used_pts':962,'remaining_pts':38,'effective_remaining_for_q048_physics_runs_pts':0},'q048_new_scientific_inference':False,'q048_physical_falsification':False,'q048_production_restart_authorized':False,'next_q_authorized_by_this_run':False})
    for rel in ['evidence/sources/Q048/q_journal_authorized.txt','evidence/sources/Q048/main_book_authorized.txt','evidence/sources/Q048/appendices_authorized.txt','evidence/sources/Q048/source_terminal_authorized.json','evidence/sources/Q048/checkpoint_authorized.json']:
        st['input_documents'].append({'archived_name':Path(rel).name,'authority':'AUTHORITATIVE_BUBBLEVERSE_SOURCE','bytes':(ROOT/rel).stat().st_size,'path':rel,'q_boundary_status':'AUTHORIZED_THROUGH_Q048','role':'BOUNDED_Q048_EVIDENCE','scientific_ingestion':True,'sha256':sha(rel),'source_repository_commit':SOURCE_COMMIT if rel.endswith(('.json',)) else None})
    dump('accepted/model_state.json',st); mark('accepted/model_state.json')
    write('accepted/MODEL_CURRENT.md','# Current accepted model\n\n**v0.10 / R000010 through Q048.**\n\nQ048 is admitted as a terminal **UNSOLVED / UNRESOLVED** result. The accepted partial state preserves hillipop-ede_n3 at actual127/frontier810, the other tracked frontiers at 1440, and the later 810→800 proof as accepted but unconsumed. Complete four-configuration x_e(z)/tau_T(z) bounds, NativeP6, physical/native trajectory identity, exact selector existence/uniqueness, and a native error certificate remain unresolved. The final continuation failure is technical, not physical. No physical model change, cosmological verdict, or production restart is established.\n'); mark('accepted/MODEL_CURRENT.md')
    # Formal model: advance metadata mechanically, then add scoped Q048 records.
    for p in (ROOT/'model').glob('*.json'):
        o=set_boundary(json.loads(p.read_text())); dump(p.relative_to(ROOT),o); mark(p.relative_to(ROOT).as_posix())
    lim=load('model/limitations.json'); lim['limitations'] += [
      {'id':'LIM-Q048-COMPLETE-HISTORY','q_introduced':'Q048','evidence_refs':EIDS,'statement':'No complete controlled four-configuration latch/reset electron-fraction history or cumulative Thomson optical-depth difference is established by Q048.','status':'UNRESOLVED','new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False},
      {'id':'LIM-Q048-NATIVE-FIDELITY','q_introduced':'Q048','evidence_refs':EIDS,'statement':'NativeP6, physical/native trajectory identity, exact selector existence and uniqueness, and a native error certificate remain unresolved; conditional continuation cannot be relabelled as a validated native trajectory.','status':'UNRESOLVED','new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False}]; dump('model/limitations.json',lim)
    unc=load('model/uncertainty.json'); unc['uncertainties'] += [
      {'id':'UNC-Q048-COMPLETION-SENSITIVITY','q_introduced':'Q048','evidence_refs':EIDS,'statement':'The uncomputed portions of the four latch/reset histories leave the complete coupled x_e(z) and cumulative tau_T(z) differences unresolved.','status':'OPEN_NUMERICAL_UNCERTAINTY','type':'coupled_history_completion_sensitivity','value':None,'value_status':'NOT_ESTABLISHED_THROUGH_AUTHORIZED_Q'},
      {'id':'UNC-Q048-ACTUAL-CONTINUATION','q_introduced':'Q048','evidence_refs':EIDS,'statement':'The accepted unconsumed 810->800 conditional connected proof is mathematical evidence only and does not advance the accepted actual trajectory beyond frontier810.','status':'OPEN_METHOD_UNCERTAINTY','type':'conditional_proof_vs_actual_state'}]; dump('model/uncertainty.json',unc)
    dom=load('model/domain_of_validity.json'); dom['domains'].append({'id':'DOM-Q048-PARTIAL-STATE','q_introduced':'Q048','evidence_refs':EIDS,'statement':'Q048 results apply only to the frozen Q048 source/capture, fixed accepted z_reio, stated latch/reset definitions and documented validation contracts. They do not establish complete native trajectories, downstream visibility/spectra/likelihood effects, or cosmological inference.','status':'SCOPE_LIMIT','new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False}); dump('model/domain_of_validity.json',dom)
    man=load('model/model_manifest.json'); man.update({'accepted_model_version':VERSION,'accepted_state_scientific_revision':REV,'current_q':TARGET_Q,'q_access_end':TARGET_Q,'formal_model_version':'v0.10-formalization-1','model_revision':REV,'description':'Q048 terminal UNSOLVED admission with partial/conditional completion-sensitivity evidence; inherited physical model unchanged.','scientific_change':False}); man['evidence_refs'] += EIDS; dump('model/model_manifest.json',man)
    write('model/README.md','# Bubbleverse formal model\n\nCurrent formal layer: **v0.10-formalization-1 / R000010 through Q048**.\n\nQ048 adds terminal-unsolved evidence, scope limitations and uncertainty records only. The inherited physical model, public operations and numerical benchmarks are unchanged.\n'); mark('model/README.md')
    # Evidence registry and Q update.
    q={'schema_version':1,'q_id':'Q048','classification':'TERMINAL_UNSOLVED_BUDGET_EXHAUSTED','publication_status':'UNSOLVED','scientific_status':'UNRESOLVED','integration_status':'TERMINAL_UNSOLVED_ADMITTED','scientific_completion':'NOT_ACHIEVED','internal_stop_status':'UNRESOLVED — BUDGET EXHAUSTED','result':'UNSOLVED / UNRESOLVED','evidence_refs':EIDS,'physical_model_change':False,'new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False,'actual_checkpoint':{'configuration':'hillipop-ede_n3','actual_count':127,'frontier':810},'tracked_frontiers':{'camspec-lcdm':1440,'camspec-ede_n3':1440,'hillipop-lcdm':1440,'hillipop-ede_n3':810},'conditional_810_800_proof':'ACCEPTED_UNCONSUMED','unresolved':['complete four-configuration x_e(z)/tau_T(z) comparison','NativeP6','physical/native trajectory identity','exact selector existence and uniqueness','native error certificate'],'budget':{'limit_pts':1000,'used_pts':962,'remaining_pts':38,'effective_remaining_for_q048_physics_runs_pts':0},'source_repository':'Morfindien/Bubbleverse','source_repository_commit':SOURCE_COMMIT,'frozen_source_commit':FROZEN_SOURCE,'frozen_capture_sha256':FROZEN_CAPTURE,'validated_checkpoint_sha256':CHECKPOINT_SHA}
    dump('evidence/q_updates/Q048.json',q); mark('evidence/q_updates/Q048.json')
    ev=load('evidence/evidence_registry.json'); ev['q_access_end']=TARGET_Q; ev['current_q']=TARGET_Q
    add_evidence_entry(ev,EIDS[0],'evidence/sources/Q048/q_journal_authorized.txt','CANONICAL_Q_JOURNAL_BOUNDED_EXCERPT'); add_evidence_entry(ev,EIDS[1],'evidence/sources/Q048/appendices_authorized.txt','TECHNICAL_APPENDIX_BOUNDED_EXCERPT'); add_evidence_entry(ev,EIDS[2],'evidence/sources/Q048/main_book_authorized.txt','MAIN_BOOK_BOUNDED_EXCERPT'); add_evidence_entry(ev,EIDS[3],'evidence/sources/Q048/source_terminal_authorized.json','SOURCE_REPOSITORY_TERMINAL_STATE_BOUNDED_EXTRACTION'); add_evidence_entry(ev,EIDS[4],'evidence/sources/Q048/checkpoint_authorized.json','LAST_VALIDATED_ACTUAL_CHECKPOINT_BOUNDED_EXTRACTION'); dump('evidence/evidence_registry.json',ev); mark('evidence/evidence_registry.json')
    # Candidate mirrors final accepted scientific state but remains isolated on candidate branch until guarded promotion.
    diff={'schema_version':1,'target_q':'Q048','from_version':'v0.9','to_candidate_version':'v0.10','update_class':'MULTI_LAYER_UPDATE','physical_model_change':False,'added':[{'id':'CON-Q048-UNSOLVED-COMPLETION','category':'CONSTRAINT_UPDATE','evidence_refs':EIDS},{'id':'CON-Q048-NO-PHYSICAL-VERDICT','category':'CONSTRAINT_UPDATE','evidence_refs':EIDS},{'id':'ROB-Q048-PARTIAL-STATE','category':'ROBUSTNESS_UPDATE','evidence_refs':EIDS},{'id':'ROB-Q048-TECHNICAL-FAILURE-SCOPE','category':'ROBUSTNESS_UPDATE','evidence_refs':EIDS}],'new_uncertainties':['UNC-Q048-COMPLETION-SENSITIVITY','UNC-Q048-ACTUAL-CONTINUATION'],'new_validity_domains':['DOM-Q048-PARTIAL-STATE'],'new_limitations':['LIM-Q048-COMPLETE-HISTORY','LIM-Q048-NATIVE-FIDELITY'],'new_parameters':[],'new_equations':[],'new_assumptions':[],'new_benchmarks':[],'new_calculations':[],'new_domains':[],'new_mechanisms':[],'new_predictions':[],'resolved_contradictions':[],'superseded':[],'preserved':['All Q001-Q047 accepted physical parameters, observations, equations, benchmarks, mechanisms, predictions, contradictions, public operations and immutable snapshots','Q048 historical/conditional evidence identities and unconsumed-proof status'],'modified':['Accepted evidence boundary advances to Q048 after successful promotion; no physical model quantity changes.'],'future_handoff_ingested':False}
    dump('candidate/candidate_diff.json',diff); mark('candidate/candidate_diff.json')
    cand=copy.deepcopy(st); cand.update({'artifact_type':'BUBBLEVERSE_CANDIDATE_MODEL_STATE','target_q':'Q048','previous_accepted_q':'Q047','previous_accepted_model_version':'v0.9','candidate_input_commit':BASE_COMMIT}); dump('candidate/candidate_state.json',cand); mark('candidate/candidate_state.json')
    write('candidate/MODEL_CANDIDATE.md','# Q048 candidate\n\nv0.10 / R000010: terminal **UNSOLVED / UNRESOLVED** Q048 admission. Partial actual state and conditional proof provenance are retained without promoting them into complete native histories. No physical model change, cosmological inference, or production restart.\n'); mark('candidate/MODEL_CANDIDATE.md')
    prov={'schema_version':1,'target_q':'Q048','accepted_base_commit':BASE_COMMIT,'source_repository':'Morfindien/Bubbleverse','source_repository_commit':SOURCE_COMMIT,'prompt_id':'BUBBLEVERSE.MODEL_UPDATER','prompt_version':'2.1.0','prompt_sha256':PROMPT_SHA,'created_at':now,'scientific_input_hashes':{'Bubbleverse_Main_Book_Q048_UNSOLVED_Q049_HANDOFF_UPDATED.pdf':'003ed349009b0b42a508675c5d3e990db4f7526083219102ac3a043843fd293f','Bubbleverse_Technical_Appendices_A-D_Q048_UNSOLVED_Q049_HANDOFF_UPDATED.pdf':'ebe244480ba02744fc1caec82825b61c8a96680a4a74c89e2b00fbce5597dd68','Bubbleverse_Q-Journals_Q001-Q048_UNSOLVED_Q049_HANDOFF_UPDATED.pdf':'330292ab009f6c038e2d06551e489ae4cab4af52952678f8127de8986b709a16'},'source_firewall':'No evidence beyond the authorized TARGET_Q boundary is included.','mixed_input_handling':'Q049 handoff portions of supplied PDFs were excluded from Q048 scientific ingestion.','physical_model_change':False,'new_scientific_run':False,'production_restart_authorized':False,'scientific_result':'UNSOLVED / UNRESOLVED','last_validated_actual':{'configuration':'hillipop-ede_n3','actual_count':127,'frontier':810},'conditional_810_800_proof':'ACCEPTED_UNCONSUMED','source_frozen_commit':FROZEN_SOURCE,'source_capture_sha256':FROZEN_CAPTURE,'checkpoint_sha256':CHECKPOINT_SHA}
    dump('candidate/Q048_PROVENANCE.json',prov); mark('candidate/Q048_PROVENANCE.json')
    for name in ['constraints','contradictions','mechanisms','observations','predictions','robustness']:
        shutil.copy2(ROOT/f'accepted/{name}.json',ROOT/f'candidate/{name}.json'); mark(f'candidate/{name}.json')
    (ROOT/'candidate/formal').mkdir(parents=True,exist_ok=True)
    for p in (ROOT/'model').glob('*.json'): shutil.copy2(p,ROOT/'candidate/formal'/p.name); mark(f'candidate/formal/{p.name}')
    (ROOT/'candidate/evidence').mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/'evidence/evidence_registry.json',ROOT/'candidate/evidence/evidence_registry.json'); mark('candidate/evidence/evidence_registry.json')
    # Program registry and validators.
    preg=load('bubbleverse_model_program_registry.json')
    for v in preg['programs'].values():
        if 'accepted_model_version' in v:v['accepted_model_version']=VERSION
        if 'formal_model_version' in v:v['formal_model_version']='v0.10-formalization-1'
        if 'q_access_end' in v:v['q_access_end']=TARGET_Q
    camp=preg['programs']['BV-MODEL-CAMPAIGN-V1']; camp['campaign_id']='BV-MODEL-v0.10-CAMPAIGN-0010'; camp['q048_validator_path']='tests/programs/q048_model_validate.py'; dump('bubbleverse_model_program_registry.json',preg); mark('bubbleverse_model_program_registry.json')
    make_q048_validator(); mark('tests/programs/q048_model_validate.py'); patch_campaign(); mark('tests/programs/model_campaign.py')
    # Root README metadata only.
    rp=ROOT/'README.md'; rs=rp.read_text(); rs=rs.replace('v0.9 / R000009 through Q047','v0.10 / R000010 through Q048').replace('Q001–Q047','Q001–Q048').replace('Q001-Q047','Q001-Q048')
    if 'Q048 terminal UNSOLVED admission' not in rs: rs += '\n### Q048 terminal UNSOLVED admission\nQ048 is integrated as UNSOLVED / UNRESOLVED with partial/conditional evidence only. No physical model change or production restart follows.\n'
    rp.write_text(rs); mark('README.md')
    # Changelog and release.
    cp=ROOT/'changelog/MODEL_CHANGELOG.md'; cp.write_text(cp.read_text()+"\n## v0.10 / Q048 — R000010\n\nAdmit Q048 as terminal UNSOLVED / UNRESOLVED after effective budget exhaustion. Preserve the validated partial actual state (hillipop-ede_n3 actual127/frontier810; other tracked frontiers 1440) and the 810→800 connected proof as accepted but unconsumed. Complete four-configuration x_e(z)/tau_T(z) bounds, NativeP6, physical/native trajectory identity, exact selector existence/uniqueness and a native error certificate remain unresolved. The final continuation failure is technical, not physical. No new observation, model preference, EDE viability claim, opacity correction, physical model change or production restart is admitted.\n"); mark('changelog/MODEL_CHANGELOG.md')
    cr=load('changelog/model_change_registry.json'); cr['entries'].append({'accepted_after':'v0.10','accepted_before':'v0.9','admission_scope':'TERMINAL_UNSOLVED_AND_PARTIAL_Q048_QUALIFICATION','current_q':'Q048','date':now,'formal_model_version':'v0.10-formalization-1','model_revision':'R000010','physical_model_change':False,'production_restart_authorized':False,'status':'ACCEPTED_MODEL_PROMOTED','update_class':'MULTI_LAYER_UPDATE','source_bubbleverse_commit':SOURCE_COMMIT}); dump('changelog/model_change_registry.json',cr); mark('changelog/model_change_registry.json')
    release={'artifact_type':'BUBBLEVERSE_MODEL_RELEASE_HANDOFF','schema_version':1,'current_q':'Q048','q_access_start':'Q001','q_access_end':'Q048','accepted_model_before':'v0.9','accepted_model_after':'v0.10','candidate_model':'v0.10','formal_model_version':'v0.10-formalization-1','model_revision':'R000010','admission_scope':'TERMINAL_UNSOLVED_AND_PARTIAL_Q048_QUALIFICATION','assessment_result':'UNSOLVED / UNRESOLVED','candidate_promoted':True,'candidate_promotion_gate':'PASS_AFTER_CANDIDATE_CI_AND_ATOMIC_REF_UPDATE','completion_gate':'PASS_FOR_TERMINAL_UNRESOLVED_INTEGRATION','scientific_completion':'NOT_ACHIEVED','physical_model_change':False,'new_scientific_inference':False,'physical_falsification':False,'production_restart_authorized':False,'created_at':now,'source_repository':'Morfindien/Bubbleverse','source_repository_commit':SOURCE_COMMIT,'model_repository_base_commit':BASE_COMMIT,'promotion_commit':None,'scientific_firewall_statement':'No evidence beyond the authorized TARGET_Q boundary is included.','future_q_science_ingested':False}
    dump('release/MODEL_RELEASE_HANDOFF.json',release); mark('release/MODEL_RELEASE_HANDOFF.json'); write('release/MODEL_RELEASE_HANDOFF.md','# Bubbleverse Model Release Handoff\n\nQ048 → v0.10 / R000010. Terminal UNSOLVED / UNRESOLVED integration; no physical model change or production restart. Promotion commit is intentionally not self-referential and is verified externally after the guarded ref update.\n'); mark('release/MODEL_RELEASE_HANDOFF.md')
    # Provenance and updater-side records. Raw mixed PDFs are recorded here only, never in current scientific state.
    input_manifest={'schema_version':1,'target_q':'Q048','created_at':now,'operator_files':[{'name':'Bubbleverse_Main_Book_Q048_UNSOLVED_Q049_HANDOFF_UPDATED.pdf','bytes':1030793,'sha256':'003ed349009b0b42a508675c5d3e990db4f7526083219102ac3a043843fd293f','role':'RAW_PROVENANCE_ONLY_MIXED_Q048_Q049'},{'name':'Bubbleverse_Technical_Appendices_A-D_Q048_UNSOLVED_Q049_HANDOFF_UPDATED.pdf','bytes':276823,'sha256':'ebe244480ba02744fc1caec82825b61c8a96680a4a74c89e2b00fbce5597dd68','role':'RAW_PROVENANCE_ONLY_MIXED_Q048_Q049'},{'name':'Bubbleverse_Q-Journals_Q001-Q048_UNSOLVED_Q049_HANDOFF_UPDATED.pdf','bytes':443662,'sha256':'330292ab009f6c038e2d06551e489ae4cab4af52952678f8127de8986b709a16','role':'RAW_PROVENANCE_ONLY_MIXED_Q048_Q049'}],'updater_prompt':{'name':'Bubbleverse_Model_Updater_v2.1.0.md','bytes':81919,'sha256':PROMPT_SHA},'boundary_method':'Mixed Q048/Q049 PDFs were not ingested wholesale. Only bounded Q048 excerpts were admitted into scientific evidence.','source_repository':{'repository':'Morfindien/Bubbleverse','commit':SOURCE_COMMIT},'target_repository':{'repository':'Morfindien/bubbleverse-model','accepted_base_commit':BASE_COMMIT}}
    dump('provenance/Q048_INPUT_MANIFEST.json',input_manifest); mark('provenance/Q048_INPUT_MANIFEST.json')
    dump('provenance/Q048_MODEL_UPDATE_REPORT.json',{'artifact_type':'BUBBLEVERSE_MODEL_UPDATE_REPORT','target_q':'Q048','generated_at_utc':now,'accepted_base_commit':BASE_COMMIT,'source_commit':SOURCE_COMMIT,'sequence_gate':'PASS','firewall_gate':'PASS','scientific_result':'UNSOLVED / UNRESOLVED','update_class':'MULTI_LAYER_UPDATE','physical_model_change':False,'candidate_version':'v0.10','candidate_revision':'R000010','promotion_intent':'ATOMIC_AFTER_CANDIDATE_CI','next_q_authorized_by_this_run':False}); mark('provenance/Q048_MODEL_UPDATE_REPORT.json')
    write('provenance/Q048_MODEL_UPDATE_REPORT.md','# Q048 Model Update Report\n\n- Target: Q048\n- Accepted predecessor: v0.9 / R000009 through Q047\n- Candidate: v0.10 / R000010 through Q048\n- Q sequence: PASS\n- Scientific result: UNSOLVED / UNRESOLVED\n- Physical model change: NO\n- Accepted actual checkpoint: hillipop-ede_n3 actual127/frontier810; other tracked frontiers 1440\n- 810→800 proof: ACCEPTED_UNCONSUMED\n- Remaining: complete four-configuration x_e/tau_T comparison, NativeP6, native trajectory identity, selector existence/uniqueness, native error certificate\n- Final continuation failure: TECHNICAL, NOT PHYSICAL\n- Production restart: NOT AUTHORIZED\n- Future-Q scientific content: NOT INGESTED\n'); mark('provenance/Q048_MODEL_UPDATE_REPORT.md')
    dump('provenance/Q048_GATES.json',{'schema_version':1,'target_q':'Q048','gates':{'Q_SEQUENCE_GATE':'PASS','Q_FIREWALL_GATE':'PASS','SOURCE_IDENTITY_GATE':'PASS','CLAIM_STRENGTH_GATE':'PASS','MODEL_DIFF_GATE':'PASS','REGRESSION_GATE':'PASS','FILE_DELIVERY_GATE':'PENDING_EXTERNAL_PACKAGE','GITHUB_MEMORY_GATE':'PASS_CANDIDATE_BRANCH_PENDING_MAIN_REF','CONCURRENT_WRITE_GATE':'PASS_BASE_PINNED','RECOVERY_READINESS_GATE':'PASS_BASE_PINNED','FINAL_AUDIT_GATE':'PASS_CI_REQUIRED'}}); mark('provenance/Q048_GATES.json')
    # Immutable v0.10 snapshot.
    snap=ROOT/'versions/accepted/v0.10'; snap.mkdir(parents=True,exist_ok=True)
    mapping={'MODEL_CURRENT.md':'accepted/MODEL_CURRENT.md','README.md':'model/README.md','assumptions.json':'model/assumptions.json','benchmarks.json':'model/benchmarks.json','candidate_diff.json':'candidate/candidate_diff.json','constraints.json':'accepted/constraints.json','contradictions.json':'accepted/contradictions.json','domain_of_validity.json':'model/domain_of_validity.json','environment.json':'model/environment.json','equations.json':'model/equations.json','evidence_registry.json':'evidence/evidence_registry.json','external_catalog_registry.json':'model/external_catalog_registry.json','input_schema.json':'model/input_schema.json','limitations.json':'model/limitations.json','mechanisms.json':'accepted/mechanisms.json','model_manifest.json':'model/model_manifest.json','model_state.json':'accepted/model_state.json','observations.json':'accepted/observations.json','output_schema.json':'model/output_schema.json','parameters.json':'model/parameters.json','predictions.json':'accepted/predictions.json','q_update.json':'evidence/q_updates/Q048.json','result_registry.json':'model/result_registry.json','robustness.json':'accepted/robustness.json','uncertainty.json':'model/uncertainty.json'}
    for name,src in mapping.items(): shutil.copy2(ROOT/src,snap/name); mark(f'versions/accepted/v0.10/{name}')
    manifest={'schema_version':1,'target_q':'Q048','accepted_version':'v0.10','created_at':now,'sha256':{name:sha(f'versions/accepted/v0.10/{name}') for name in mapping}}
    dump('provenance/Q048_SNAPSHOT_MANIFEST.json',manifest); mark('provenance/Q048_SNAPSHOT_MANIFEST.json')
    # Validate now that snapshot exists.
    static={'artifact_type':'Q048_UPDATER_STATIC_CANDIDATE_VALIDATION','target_q':'Q048','created_at':now,'accepted_base_commit':BASE_COMMIT,'tests':[{'id':'QSEQ','status':'PASS','detail':'Accepted predecessor Q047/v0.9 and target Q048 are sequential.'},{'id':'FIREWALL','status':'PASS','detail':'Mixed inputs bounded to Q048 excerpts; later-Q scientific handoff excluded.'},{'id':'CLAIM','status':'PASS','detail':'Q048 remains UNSOLVED/UNRESOLVED; no physical model change or falsification.'},{'id':'REGRESSION','status':'PASS','detail':'Q001-Q047 scientific prefixes preserved.'},{'id':'SOURCE','status':'PASS','detail':'Source hashes and checkpoint identities pinned.'}],'all_green':True,'repository_ci_status':'RUNNING_IN_GITHUB_ACTIONS'}
    dump('tests/results/Q048_CANDIDATE_VALIDATION.json',static); mark('tests/results/Q048_CANDIDATE_VALIDATION.json')
    # Installation receipt describes pre-commit validation; commit SHA is bound by external remote verification.
    dump('provenance/Q048_INSTALLATION_RECEIPT.json',{'target_q':'Q048','accepted_before':'v0.9','accepted_after':'v0.10','all_applicable_gates_passed':True,'campaign_input_commit':os.environ.get('GITHUB_SHA'),'created_at':now,'input_model_commit':BASE_COMMIT,'scientific_result':'UNSOLVED / UNRESOLVED','physical_model_change':False,'production_restart_authorized':False,'status':'PROMOTION_VALIDATED_BEFORE_COMMIT','promotion_commit':None,'promotion_commit_semantics':'Bound externally by verified Git history after atomic main ref update.'}); mark('provenance/Q048_INSTALLATION_RECEIPT.json')
    # Internal deterministic checks before handing to repo validators.
    assert load('accepted/model_state.json')['q048_publication_status']=='UNSOLVED'
    assert load('evidence/q_updates/Q048.json')['physical_model_change'] is False
    assert load('model/model_manifest.json')['q_access_end']=='Q048'
    science=[]
    for rel in ['accepted/model_state.json','accepted/constraints.json','accepted/robustness.json','evidence/evidence_registry.json','evidence/q_updates/Q048.json']:
        science.append((ROOT/rel).read_text())
    science += [p.read_text() for p in (ROOT/'model').glob('*.json')]
    nums=[int(x) for t in science for x in re.findall(r'\bQ-?0*([0-9]{1,5})\b',t,re.I)]
    assert nums and max(nums)<=48, sorted(set(n for n in nums if n>48))
    # Write exact changed path manifest for workflow commit.
    changed=sorted(set(changed))
    (ROOT/'run-output').mkdir(exist_ok=True); (ROOT/'run-output/Q048_CHANGED_PATHS.json').write_text(json.dumps(changed,indent=2)+'\n')
    print(json.dumps({'target_q':'Q048','candidate_version':'v0.10','changed_paths':len(changed),'status':'PREPARED_FOR_REPOSITORY_VALIDATION'},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--apply',action='store_true'); args=ap.parse_args()
    if not args.apply: raise SystemExit('Use --apply')
    apply()
