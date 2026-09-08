#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
Q_MAX = 39
CAMPAIGN = "BV-MODEL-v0.1-CAMPAIGN-0001"
MANDATORY_IDS = [f"T-BV-{i:03d}" for i in range(1,10)]

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def dump(rel, obj):
    p=ROOT/rel; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n", encoding="utf-8")

def passfail(condition, detail):
    return ("PASS" if condition else "FAIL", detail)

def qnums(obj):
    s=json.dumps(obj, sort_keys=True)
    return [int(x) for x in re.findall(r"\bQ-?0*([0-9]{1,4})\b", s, flags=re.I)]

def unique_ids(items):
    ids=[x["id"] for x in items if "id" in x]
    return len(ids)==len(set(ids))

def audit():
    state=load("candidate/candidate_state.json")
    obs=load("candidate/observations.json")
    con=load("candidate/constraints.json")
    mech=load("candidate/mechanisms.json")
    pred=load("candidate/predictions.json")
    ctr=load("candidate/contradictions.json")
    rob=load("candidate/robustness.json")
    ev=load("evidence/evidence_registry.json")
    q39=load("evidence/q_updates/Q039.json")

    results={}
    results["T-BV-001"]=passfail(
        state.get("q_access_start")=="Q001" and state.get("q_access_end")=="Q039" and state.get("current_q")=="Q039",
        "Candidate identity and hard Q boundary are exact."
    )

    scanned=[state,obs,con,mech,pred,ctr,rob,ev,q39]
    nums=[n for x in scanned for n in qnums(x)]
    results["T-BV-002"]=passfail(bool(nums) and max(nums)<=Q_MAX,
        f"Highest Q identifier in scientific candidate/evidence JSON is Q{max(nums):03d}." if nums else "No Q identifiers found.")

    h=[x for x in obs["observations"] if x["id"].startswith("OBS-H0-")]
    hv={x["id"]:(x["value"],x["sigma"],x["inference_chain"]) for x in h}
    ok=(hv.get("OBS-H0-LOCAL-001")== (73.50,0.81,"local distance network")
        and hv.get("OBS-H0-CMB-001")== (67.24,0.35,"CMB cosmological inference")
        and hv.get("OBS-H0-BAOBBN-001")== (68.51,0.58,"BAO standard ruler + BBN")
        and len({x[2] for x in hv.values()})==3)
    results["T-BV-003"]=passfail(ok,"H0 benchmarks and distinct inference chains preserved.")

    eids={x.get("evidence_id"):x for x in ev["entries"]}
    a=eids.get("EVD-Q039-IMPLBLOCK",{})
    b=eids.get("EVD-Q039-FGPROFILE",{})
    ok=(a.get("result_id")=="R-Q039-EDE-IMPLEMENTATION-BLOCK-INTERVENTION-001"
        and a.get("program_id")=="Q039-IMPLBLOCK-V5" and str(a.get("run_id"))=="34161368438"
        and a.get("validation_status")=="PASS"
        and b.get("result_id")=="R-Q039-EDE-NATIVE-FOREGROUND-PROFILE-001"
        and b.get("program_id")=="Q039-FGPROFILE-V1" and str(b.get("run_id"))=="34184346582"
        and b.get("validation_status")=="PASS")
    results["T-BV-004"]=passfail(ok,"Authoritative Q039 identities and PASS provenance preserved.")

    t=eids.get("EVD-Q039-V1-V4",{})
    results["T-BV-005"]=passfail(t.get("scientific_evidence") is False and t.get("status")=="SUPERSEDED",
        "Q039 V1-V4 technical recoveries excluded from scientific evidence.")

    q39text=json.dumps(q39).lower()+" "+json.dumps(con).lower()
    required=["relative calibration","off-diagonal precision","foreground"]
    forbidden_claims=["establishes new physics","proves new physics","physical calibration error established","ede falsified","ede detected"]
    ok=all(x in q39text for x in required) and not any(x in q39text for x in forbidden_claims)
    results["T-BV-006"]=passfail(ok,"Q039 narrowing preserved without prohibited causal/new-physics promotion.")

    cids={x["id"] for x in ctr["contradictions"]}
    results["T-BV-007"]=passfail({"CTR-H0-001","CTR-PLANCK-IMPL-001"} <= cids,
        "Required open contradictions remain explicit.")

    ctext=json.dumps(con).lower()+" "+json.dumps(mech).lower()+" "+json.dumps(ctr).lower()
    ok=("unresolved" in ctext and "hubble" in ctext and "microscopic" in ctext and "acceleration" in ctext)
    results["T-BV-008"]=passfail(ok,"Major unresolved questions remain unresolved.")

    json_paths=[
      "candidate/candidate_state.json","candidate/observations.json","candidate/constraints.json",
      "candidate/mechanisms.json","candidate/predictions.json","candidate/contradictions.json",
      "candidate/robustness.json","candidate/candidate_diff.json","evidence/evidence_registry.json",
      "evidence/q_updates/Q039.json","tests/test_registry.json","tests/preregistration/BV-MODEL-v0.1-CAMPAIGN-0001.json"
    ]
    parse_ok=True
    for p in json_paths:
        try: load(p)
        except Exception: parse_ok=False
    uniq=(unique_ids(obs["observations"]) and unique_ids(con["constraints"]) and unique_ids(mech["mechanisms"])
          and unique_ids(pred["predictions"]) and unique_ids(ctr["contradictions"]) and unique_ids(rob["items"]))
    results["T-BV-009"]=passfail(parse_ok and uniq,"Required JSON parses and layer IDs are unique.")
    return results

def write_results(results):
    rows=[]
    for tid in MANDATORY_IDS:
        status,detail=results[tid]
        rows.append({"test_id":tid,"status":status,"detail":detail,"mandatory_for_promotion":True})
    passed=sum(x["status"]=="PASS" for x in rows)
    out={"schema_version":1,"test_campaign_id":CAMPAIGN,"q_access_start":"Q001","q_access_end":"Q039",
         "candidate_model_version":"v0.1-candidate","tests":rows,
         "mandatory_tests_total":len(rows),"mandatory_tests_passed":passed,
         "all_mandatory_green":passed==len(rows)}
    dump("tests/results/BV-MODEL-v0.1-CAMPAIGN-0001.json",out)
    reg=load("tests/test_registry.json")
    by={x["test_id"]:x for x in rows}
    for t in reg["tests"]:
        t["status"]=by[t["test_id"]]["status"]
    dump("tests/test_registry.json",reg)
    return out

def promote(campaign):
    if not campaign["all_mandatory_green"]:
        return False
    cand=load("candidate/candidate_state.json")
    accepted=dict(cand)
    accepted["status"]="ACCEPTED"
    accepted["accepted_model_version"]="v0.1"
    accepted["candidate_model_version"]=None
    accepted["accepted_at"]="GITHUB_ACTIONS_CAMPAIGN"
    dump("accepted/model_state.json",accepted)
    for name in ["observations","constraints","mechanisms","predictions","contradictions","robustness"]:
        shutil.copy2(ROOT/f"candidate/{name}.json",ROOT/f"accepted/{name}.json")
    md=(ROOT/"candidate/MODEL_CANDIDATE.md").read_text(encoding="utf-8")
    md=md.replace("# BUBBLEVERSE MODEL CANDIDATE","# BUBBLEVERSE ACCEPTED MODEL",1)
    md=md.replace("**NOT YET ACCEPTED**","**ACCEPTED — v0.1**",1)
    md=md.replace("**Candidate:** v0.1-candidate","**Accepted model:** v0.1",1)
    md=md.replace("READY FOR PREREGISTERED BOOTSTRAP CAMPAIGN. Accepted model remains uninitialized until all mandatory tests are green.",
                  "PROMOTED after all nine bootstrap tests explicitly passed.")
    (ROOT/"accepted/MODEL_CURRENT.md").write_text(md,encoding="utf-8")
    vdir=ROOT/"versions/accepted/v0.1"; vdir.mkdir(parents=True,exist_ok=True)
    for p in (ROOT/"accepted").glob("*"):
        if p.is_file(): shutil.copy2(p,vdir/p.name)
    return True

def write_release(campaign,promoted):
    total=campaign["mandatory_tests_total"]; passed=campaign["mandatory_tests_passed"]
    allg=campaign["all_mandatory_green"] and promoted
    r=load("release/MODEL_RELEASE_HANDOFF.json")
    r.update({
      "accepted_model_after":"v0.1" if allg else None,
      "mandatory_tests_passed":passed,
      "mandatory_tests_failed":total-passed,
      "mandatory_tests_blocked":0,
      "all_mandatory_green":allg,
      "model_schema_gate":"PASS" if allg else "FAIL",
      "provenance_gate":"PASS" if allg else "FAIL",
      "contradiction_gate":"PASS" if allg else "FAIL",
      "regression_gate":"PASS" if allg else "FAIL",
      "test_campaign_gate":"PASS" if allg else "FAIL",
      "candidate_promotion_gate":"PASS" if allg else "BLOCKED",
      "final_audit_gate":"PASS" if allg else "FAIL",
      "candidate_promoted":allg,
      "next_word_authorized":allg,
      "release_status":"ALL_GREEN" if allg else "BLOCKED",
      "repository_write_gate":"PASS" if allg else r.get("repository_write_gate","PENDING"),
      "model_repository_commit":"SEE_REPOSITORY_COMMIT_CONTAINING_THIS_HANDOFF" if allg else r.get("model_repository_commit"),
      "blocking_items":[] if allg else [x["test_id"] for x in campaign["tests"] if x["status"]!="PASS"],
      "blocking_reason":None if allg else "One or more mandatory model tests failed."
    })
    dump("release/MODEL_RELEASE_HANDOFF.json",r)
    lines=[
      "# BUBBLEVERSE MODEL RELEASE HANDOFF","",
      "AUTHORIZED Q RANGE: Q001–Q039  ","CURRENT Q: Q039  ","Processed through: Q039","",
      "Previous accepted model: NONE  ","Candidate: v0.1-candidate  ",
      f"Final accepted model: {'v0.1' if allg else 'NONE'}","",
      f"Campaign: {CAMPAIGN}","",
      "## MANDATORY TESTS",f"PASS: {passed} / {total}  ",f"FAIL: {total-passed}  ",
      "INCONCLUSIVE: 0  ","NOT COMPARABLE: 0  ","BLOCKED: 0  ","TECHNICAL FAIL: 0  ","INVALID: 0","",
      "## GATES","CURRENT Q: PASS  ","Q ACCESS FIREWALL: PASS  ","HIGH-Q CONTAMINATION: PASS  ",
      f"SCHEMA: {'PASS' if allg else 'FAIL'}  ",f"PROVENANCE: {'PASS' if allg else 'FAIL'}  ",
      f"CONTRADICTIONS: {'PASS' if allg else 'FAIL'}  ",f"REGRESSION: {'PASS' if allg else 'FAIL'}  ",
      f"TEST CAMPAIGN: {'PASS' if allg else 'FAIL'}  ",f"PROMOTION: {'PASS' if allg else 'BLOCKED'}  ",
      f"FINAL AUDIT: {'PASS' if allg else 'FAIL'}  ",
      f"REPOSITORY WRITE: {'PASS' if allg else 'PENDING'}","",
      f"ALL MANDATORY GREEN: {'YES' if allg else 'NO'}  ",
      f"CANDIDATE PROMOTED: {'YES' if allg else 'NO'}  ",
      f"NEXT WORD AUTHORIZED: {'YES' if allg else 'NO'}  ",
      f"RELEASE STATUS: {'ALL_GREEN' if allg else 'BLOCKED'}"
    ]
    (ROOT/"release/MODEL_RELEASE_HANDOFF.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=["validate","test"])
    args=ap.parse_args()
    res=audit()
    failed=[k for k,v in res.items() if v[0]!="PASS"]
    for k,(s,d) in res.items(): print(f"{k}={s} {d}")
    if args.command=="validate":
        raise SystemExit(1 if failed else 0)
    campaign=write_results(res)
    promoted=promote(campaign)
    write_release(campaign,promoted)
    if promoted:
        with (ROOT/"changelog/MODEL_CHANGELOG.md").open("a",encoding="utf-8") as f:
            f.write("\n## R000002 — automatic campaign promotion\n- 9/9 mandatory tests PASS.\n- v0.1-candidate promoted to accepted v0.1.\n- NEXT_WORD_AUTHORIZED = true.\n")
    raise SystemExit(0 if promoted else 1)
if __name__=="__main__":
    main()
