#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def load(rel): return json.loads((ROOT/rel).read_text(encoding="utf-8"))
def main():
    tests={}
    def gate(n,c,d): tests[n]={"status":"PASS" if c else "FAIL","detail":d}
    state=load("accepted/model_state.json"); ev=load("evidence/evidence_registry.json")
    obs=load("accepted/observations.json"); pred=load("accepted/predictions.json")
    ctr=load("accepted/contradictions.json"); rob=load("accepted/robustness.json")
    unc=load("model/uncertainty.json"); dom=load("model/domain_of_validity.json"); lim=load("model/limitations.json")
    eids={x.get("evidence_id"):x for x in ev["entries"]}; oids={x.get("id"):x for x in obs["observations"]}
    pids={x.get("id"):x for x in pred["predictions"]}; cids={x.get("id"):x for x in ctr["contradictions"]}
    rids={x.get("id"):x for x in rob["items"]}; uids={x.get("id"):x for x in unc["uncertainties"]}
    dids={x.get("id"):x for x in dom["domains"]}; lids={x.get("id"):x for x in lim["limitations"]}
    q41=eids.get("EVD-Q041-PORTABILITY-V19",{})
    gate("Q_SEQUENCE_GATE",state.get("current_q")=="Q041" and state.get("q_access_end")=="Q041","Accepted state ends exactly at Q041.")
    gate("SOURCE_RESULT_GATE",q41.get("scientific_classification")=="NO_SCIENTIFIC_RESULT" and q41.get("outcome_type")=="CONTROLLED_NO_SCIENTIFIC_RESULT" and q41.get("technical_failure") is False and q41.get("actual_computed_result") is False and q41.get("validation_status")=="PASS","Authoritative V19 final state is valid controlled no-science.")
    gate("ARTIFACT_IDENTITY_GATE",q41.get("artifact_sha256")=="2284518ecbaaf1ff0d0093977827d5162ec29549ba2b81880f266c250311ca2b" and q41.get("final_result_sha256")=="0062874ed3529004f46cfb542a708d5b8e8dde55d1b4fd1c2ac7c394e6c8be79" and q41.get("final_tests_sha256")=="95fe1e63c78033de8559f609f0d8a1f4d48ee1b4123f3bb8f845b3ac6e5797ab","Artifact identities match authorized result.")
    gate("OBSERVATION_GATE",oids.get("OBS-Q041-PORTABILITY-V19-001",{}).get("scientific_falsification") is False,"Non-convergence is not physical falsification.")
    hist=pids.get("PRED-EDE-PORTABILITY-001",{}).get("history",[])
    gate("PREDICTION_GATE",pids.get("PRED-EDE-PORTABILITY-001",{}).get("status")=="OPEN" and any(x.get("q")=="Q041" and x.get("status")=="INCONCLUSIVE_COMPUTATIONAL_ATTEMPT" for x in hist),"Portability prediction remains open with Q041 history.")
    gate("CONTRADICTION_GATE",cids.get("CTR-PLANCK-IMPL-001",{}).get("status")=="OPEN_NARROWED","Implementation contradiction remains open/narrowed.")
    gate("ROBUSTNESS_GATE",rids.get("ROB-Q041-CONTROLLED-NOSCIENCE-001",{}).get("status")=="ACTIVE" and rids.get("ROB-Q041-CONTRACT-SCOPE-001",{}).get("status")=="ACTIVE","Q041 robustness safeguards are active.")
    gate("FORMAL_SCOPE_GATE","UNC-Q041-POSTERIOR-CONVERGENCE" in uids and "DOM-Q041-PORTABILITY-V19" in dids and "LIM-Q041-DOWNSTREAM-PORTABILITY" in lids and "LIM-Q041-CONTRACT-SCOPE" in lids,"Q041 uncertainty/domain/limitations formalized.")
    gate("PHYSICAL_MODEL_GATE",not any(x.get("id","").startswith("PAR-Q041") for x in load("model/parameters.json")["parameters"]) and not any(x.get("id","").startswith("EQ-Q041") for x in load("model/equations.json")["equations"]),"No unsupported Q041 parameter/equation added.")
    text=" ".join(p.read_text(encoding="utf-8") for base in [ROOT/"accepted",ROOT/"candidate",ROOT/"model",ROOT/"evidence"] for p in base.rglob("*.json"))
    highs=[int(x) for x in re.findall(r"\bQ-?0*([0-9]{1,5})\b",text,flags=re.I) if int(x)>41]
    gate("Q_FIREWALL_GATE",not highs,"No scientific JSON exceeds Q041.")
    passed=sum(x["status"]=="PASS" for x in tests.values())
    for k,v in tests.items(): print(f"{k}={v['status']} {v['detail']}")
    print(f"Q041_MODEL_TESTS={passed}/{len(tests)}")
    return 0 if passed==len(tests) else 1
if __name__=="__main__": raise SystemExit(main())
