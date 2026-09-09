#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANDATORY_IDS = [f"T-BV-{i:03d}" for i in range(1, 10)]


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def dump(rel, obj):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def qnum(value):
    m = re.fullmatch(r"Q-?0*([0-9]{1,5})", str(value or ""), flags=re.I)
    return int(m.group(1)) if m else None


def qnums(obj):
    s = json.dumps(obj, sort_keys=True)
    return [int(x) for x in re.findall(r"\bQ-?0*([0-9]{1,5})\b", s, flags=re.I)]


def passfail(condition, detail):
    return ("PASS" if condition else "FAIL", detail)


def unique_ids(items):
    ids = [x["id"] for x in items if "id" in x]
    return len(ids) == len(set(ids))


def current():
    accepted = load("accepted/model_state.json")
    candidate = load("candidate/candidate_state.json")
    q = qnum(accepted.get("current_q"))
    if q is None:
        raise RuntimeError("Cannot parse accepted current_q")
    return accepted, candidate, q


def audit():
    accepted, state, qmax = current()
    obs = load("candidate/observations.json")
    con = load("candidate/constraints.json")
    mech = load("candidate/mechanisms.json")
    pred = load("candidate/predictions.json")
    ctr = load("candidate/contradictions.json")
    rob = load("candidate/robustness.json")
    ev = load("evidence/evidence_registry.json")

    expected_q = f"Q{qmax:03d}"
    results = {}

    results["T-BV-001"] = passfail(
        state.get("q_access_start") == "Q001"
        and state.get("q_access_end") == expected_q
        and state.get("current_q") == expected_q
        and accepted.get("q_access_end") == expected_q
        and accepted.get("current_q") == expected_q,
        "Candidate/accepted identity and hard Q boundary match current accepted state."
    )

    scanned = [state, obs, con, mech, pred, ctr, rob, ev]
    q_update_dir = ROOT / "evidence/q_updates"
    for p in sorted(q_update_dir.glob("Q*.json")):
        scanned.append(json.loads(p.read_text(encoding="utf-8")))
    nums = [n for x in scanned for n in qnums(x)]
    results["T-BV-002"] = passfail(
        bool(nums) and max(nums) <= qmax,
        f"Highest Q identifier in current scientific candidate/evidence JSON is Q{max(nums):03d}."
        if nums else "No Q identifiers found."
    )

    h = [x for x in obs["observations"] if x["id"].startswith("OBS-H0-")]
    hv = {x["id"]: (x["value"], x["sigma"], x["inference_chain"]) for x in h}
    ok = (
        hv.get("OBS-H0-LOCAL-001") == (73.50, 0.81, "local distance network")
        and hv.get("OBS-H0-CMB-001") == (67.24, 0.35, "CMB cosmological inference")
        and hv.get("OBS-H0-BAOBBN-001") == (68.51, 0.58, "BAO standard ruler + BBN")
        and len({x[2] for x in hv.values()}) == 3
    )
    results["T-BV-003"] = passfail(ok, "H0 benchmarks and distinct inference chains preserved.")

    eids = {x.get("evidence_id"): x for x in ev["entries"]}
    a = eids.get("EVD-Q039-IMPLBLOCK", {})
    b = eids.get("EVD-Q039-FGPROFILE", {})
    ok = (
        a.get("result_id") == "R-Q039-EDE-IMPLEMENTATION-BLOCK-INTERVENTION-001"
        and a.get("program_id") == "Q039-IMPLBLOCK-V5"
        and str(a.get("run_id")) == "34161368438"
        and a.get("validation_status") == "PASS"
        and b.get("result_id") == "R-Q039-EDE-NATIVE-FOREGROUND-PROFILE-001"
        and b.get("program_id") == "Q039-FGPROFILE-V1"
        and str(b.get("run_id")) == "34184346582"
        and b.get("validation_status") == "PASS"
    )
    results["T-BV-004"] = passfail(ok, "Authoritative Q039 identities and PASS provenance preserved.")

    t = eids.get("EVD-Q039-V1-V4", {})
    results["T-BV-005"] = passfail(
        t.get("scientific_evidence") is False and t.get("status") == "SUPERSEDED",
        "Q039 V1-V4 technical recoveries remain excluded from scientific evidence."
    )

    ctext = json.dumps(con).lower()
    q39_ok = (("relative calibration" in ctext or "relative-calibration" in ctext) and ("off-diagonal precision" in ctext or "off diagonal precision" in ctext) and "foreground" in ctext)
    q40_ok = True
    if qmax >= 40:
        rqmc = eids.get("EVD-Q040-RQMC", {})
        rmap = {x["id"]: x for x in rob["items"]}
        q40_ok = (
            rqmc.get("physical_falsification") is False
            and rqmc.get("scientific_status") == "INCONCLUSIVE_TECHNICAL_FAIL"
            and rmap.get("ROB-Q040-NUMERIC-001", {}).get("status") == "TECHNICAL_FAIL"
        )
    results["T-BV-006"] = passfail(
        q39_ok and q40_ok,
        "Q039 narrowing and Q040 technical-vs-physical semantics are preserved."
    )

    cids = {x["id"] for x in ctr["contradictions"]}
    results["T-BV-007"] = passfail(
        {"CTR-H0-001", "CTR-PLANCK-IMPL-001"} <= cids,
        "Required open contradictions remain explicit."
    )

    unresolved_text = (
        json.dumps(con).lower() + " "
        + json.dumps(mech).lower() + " "
        + json.dumps(ctr).lower()
    )
    ok = (
        "unresolved" in unresolved_text
        and "hubble" in unresolved_text
        and "microscopic" in unresolved_text
        and "acceleration" in unresolved_text
    )
    results["T-BV-008"] = passfail(ok, "Major unresolved questions remain unresolved.")

    parse_ok = True
    for base in [
        ROOT / "candidate", ROOT / "accepted", ROOT / "evidence",
        ROOT / "model", ROOT / "release"
    ]:
        for p in base.rglob("*.json"):
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                parse_ok = False

    uniq = (
        unique_ids(obs["observations"])
        and unique_ids(con["constraints"])
        and unique_ids(mech["mechanisms"])
        and unique_ids(pred["predictions"])
        and unique_ids(ctr["contradictions"])
        and unique_ids(rob["items"])
    )
    results["T-BV-009"] = passfail(parse_ok and uniq, "Current JSON parses and layer IDs are unique.")
    return results


def formal_gate():
    cp = subprocess.run(
        [sys.executable, str(ROOT / "tests/programs/formal_model_validate.py")],
        cwd=ROOT, text=True, capture_output=True
    )
    print(cp.stdout, end="")
    if cp.stderr:
        print(cp.stderr, end="")
    return cp.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["validate", "test"])
    args = ap.parse_args()

    accepted, _, qmax = current()
    results = audit()
    formal_ok = formal_gate()

    for tid in MANDATORY_IDS:
        status, detail = results[tid]
        print(f"{tid}={status} {detail}")

    all_green = formal_ok and all(results[x][0] == "PASS" for x in MANDATORY_IDS)

    if args.command == "test":
        version = accepted.get("accepted_model_version", "unknown")
        campaign_id = f"BV-MODEL-{version}-CURRENT-VALIDATION"
        rows = [
            {
                "test_id": tid,
                "status": results[tid][0],
                "detail": results[tid][1],
                "mandatory_for_current_validation": True,
            }
            for tid in MANDATORY_IDS
        ]
        out = {
            "schema_version": 1,
            "test_campaign_id": campaign_id,
            "mode": "NON_DESTRUCTIVE_CURRENT_STATE_VALIDATION",
            "current_q": f"Q{qmax:03d}",
            "q_access_start": accepted.get("q_access_start"),
            "q_access_end": accepted.get("q_access_end"),
            "accepted_model_version": version,
            "tests": rows,
            "formal_model_gate": "PASS" if formal_ok else "FAIL",
            "tests_total": len(rows),
            "tests_passed": sum(x["status"] == "PASS" for x in rows),
            "all_green": all_green,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        dump(f"tests/results/{campaign_id}.json", out)

    raise SystemExit(0 if all_green else 1)


if __name__ == "__main__":
    main()
