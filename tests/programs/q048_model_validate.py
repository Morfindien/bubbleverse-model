#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HISTORICAL=False
def load(p):
    mapped=p
    if HISTORICAL:
        if p.startswith("accepted/") or p.startswith("model/") or p=="evidence/evidence_registry.json": mapped="versions/accepted/v0.10/"+Path(p).name
        elif p=="candidate/candidate_diff.json": mapped="versions/accepted/v0.10/candidate_diff.json"
    return json.loads((ROOT/mapped).read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def req(c,m):
    if not c: raise AssertionError(m)
def run_tests(root=ROOT):
    global ROOT,HISTORICAL; ROOT=Path(root); rows=[]
    active=json.loads((ROOT/"accepted/model_state.json").read_text())["current_q"]
    HISTORICAL=int(active[1:])>48
    def gate(i,name,fn):
        try: rows.append({"id":f"Q048-{i:02d}","name":name,"status":"PASS","detail":fn()})
        except Exception as e: rows.append({"id":f"Q048-{i:02d}","name":name,"status":"FAIL","detail":f"{type(e).__name__}: {e}"})
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
        req(a["q048_actual_checkpoint"]=={"actual_count":127,"frontier":810,"configuration":"hillipop-ede_n3"},"actual checkpoint")
        req(a["q048_tracked_frontiers"]=={"camspec-ede_n3":1440,"camspec-lcdm":1440,"hillipop-ede_n3":810,"hillipop-lcdm":1440},"frontiers")
        req(a["q048_conditional_810_800_proof"]=="ACCEPTED_UNCONSUMED","proof")
        return "actual127/frontier810 preserved; unconsumed proof not promoted"
    gate(3,"partial-state boundary",partial)
    def unresolved():
        for k in ["q048_native_p6","q048_physical_native_trajectory_identity","q048_selector_existence_uniqueness","q048_native_error_certificate"]: req(a[k]=="UNRESOLVED",k)
        return "native/trajectory/selector/error gaps remain unresolved"
    gate(4,"unresolved qualification",unresolved)
    expected={"EVD-Q048-APPENDICES": "5d4e24c14622f8b346c4da310d4f4e0380eaa2009499ff2ed93d9426e0a6c783", "EVD-Q048-CHECKPOINT": "fd5e4ad69792a6316f03bd42c883dd41fbe16b5138ed4dd04944317b41609f78", "EVD-Q048-MAINBOOK": "b022563d6058fe5d93681073a696708193e06791a6455f5de8352c0c3328ce88", "EVD-Q048-QJOURNAL": "a247141ecc0cac4134a1f6fc888b4c60ccecf24f6d1a2ec6c4acdf78a467f669", "EVD-Q048-TERMINAL": "a5e2427aabe467c6028a4cea3eca16ab55b4779850ac52f864f7c718cc5070d1"}
    def sources():
        em={x["evidence_id"]:x for x in ev["entries"]}
        for eid,d in expected.items(): req(eid in em and em[eid]["sha256"]==d and sha(em[eid]["source"])==d,eid)
        return "five bounded Q048 evidence objects pinned"
    gate(5,"source identity",sources)
    def firewall():
        objs=[load("accepted/model_state.json"),load("accepted/constraints.json"),load("accepted/robustness.json"),load("evidence/evidence_registry.json"),load("evidence/q_updates/Q048.json")]
        for p in (ROOT/"model").glob("*.json"): objs.append(load(str(p.relative_to(ROOT))))
        nums=[int(x) for o in objs for x in re.findall(r"\bQ-?0*([0-9]{1,5})\b",json.dumps(o),flags=re.I)]
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
        if HISTORICAL:
            frozen=json.loads((ROOT/"provenance/Q048_SNAPSHOT_MANIFEST.json").read_text())
            req({p.name for p in snap.iterdir() if p.is_file()}==set(frozen["sha256"]),"historical snapshot inventory")
            for name,digest in frozen["sha256"].items(): req(sha(str((snap/name).relative_to(ROOT)))==digest,"historical snapshot mismatch: "+name)
            return "Q048 frozen v0.10 snapshot inventory and every digest verified independently of later live state"
        mapping={"MODEL_CURRENT.md":"accepted/MODEL_CURRENT.md","constraints.json":"accepted/constraints.json","contradictions.json":"accepted/contradictions.json","mechanisms.json":"accepted/mechanisms.json","model_state.json":"accepted/model_state.json","observations.json":"accepted/observations.json","predictions.json":"accepted/predictions.json","robustness.json":"accepted/robustness.json","evidence_registry.json":"evidence/evidence_registry.json","q_update.json":"evidence/q_updates/Q048.json","candidate_diff.json":"candidate/candidate_diff.json"}
        for n,p in mapping.items(): req((snap/n).read_bytes()==(ROOT/p).read_bytes(),"snapshot mismatch: "+n)
        for n in ["README.md","assumptions.json","benchmarks.json","domain_of_validity.json","environment.json","equations.json","external_catalog_registry.json","input_schema.json","limitations.json","model_manifest.json","output_schema.json","parameters.json","result_registry.json","uncertainty.json"]: req((snap/n).read_bytes()==(ROOT/"model"/n).read_bytes(),"formal snapshot mismatch: "+n)
        return "v0.10 snapshot matches live accepted/formal/evidence state"
    gate(8,"snapshot coherence",snapshot)
    def budget():
        req(a["q048_budget"]=={"effective_remaining_for_q048_physics_runs_pts":0,"limit_pts":1000,"remaining_pts":38,"used_pts":962},"budget")
        return "962/1000 used; 38 residual; zero effective Q048 physics capacity"
    gate(9,"terminal accounting semantics",budget)
    def technical():
        txt=(ROOT/"evidence/sources/Q048/appendices_authorized.txt").read_text().lower(); req("technical pre-freeze schema-binding defect" in txt and "no physical exclusion" in txt,"failure semantics"); return "technical failure not promoted into physical evidence"
    gate(10,"technical-vs-physical gate",technical)
    passed=sum(r["status"]=="PASS" for r in rows); return {"artifact_type":"Q048_MODEL_VALIDATION","target_q":"Q048","tests":rows,"tests_total":len(rows),"tests_passed":passed,"all_green":passed==len(rows)}
if __name__=="__main__":
    r=run_tests(); [print(f'{x["id"]}={x["status"]} {x["detail"]}') for x in r["tests"]]; print(f'Q048_MODEL_TESTS={r["tests_passed"]}/{r["tests_total"]}'); raise SystemExit(0 if r["all_green"] else 1)
