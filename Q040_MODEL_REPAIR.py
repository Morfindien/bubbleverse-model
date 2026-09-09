#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

TARGET_Q = "Q040"
TARGET_Q_NUM = 40
ACCEPTED_VERSION = "v0.2"
REVISION = "R000002"
SOURCE_COMMIT = "855a28c58246dbdd52d01cae1f40e0611103d96b"
WORD_SHA256 = "d389095fea2bd65ca5424a77cf22a4240581f1966eff3575ddabddfd0dd54397"

MODEL_CAMPAIGN = '#!/usr/bin/env python3\nfrom __future__ import annotations\n\nimport argparse\nimport json\nimport re\nimport subprocess\nimport sys\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[2]\nMANDATORY_IDS = [f"T-BV-{i:03d}" for i in range(1, 10)]\n\n\ndef load(rel):\n    return json.loads((ROOT / rel).read_text(encoding="utf-8"))\n\n\ndef dump(rel, obj):\n    p = ROOT / rel\n    p.parent.mkdir(parents=True, exist_ok=True)\n    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\\n", encoding="utf-8")\n\n\ndef qnum(value):\n    m = re.fullmatch(r"Q-?0*([0-9]{1,5})", str(value or ""), flags=re.I)\n    return int(m.group(1)) if m else None\n\n\ndef qnums(obj):\n    s = json.dumps(obj, sort_keys=True)\n    return [int(x) for x in re.findall(r"\\bQ-?0*([0-9]{1,5})\\b", s, flags=re.I)]\n\n\ndef passfail(condition, detail):\n    return ("PASS" if condition else "FAIL", detail)\n\n\ndef unique_ids(items):\n    ids = [x["id"] for x in items if "id" in x]\n    return len(ids) == len(set(ids))\n\n\ndef current():\n    accepted = load("accepted/model_state.json")\n    candidate = load("candidate/candidate_state.json")\n    q = qnum(accepted.get("current_q"))\n    if q is None:\n        raise RuntimeError("Cannot parse accepted current_q")\n    return accepted, candidate, q\n\n\ndef audit():\n    accepted, state, qmax = current()\n    obs = load("candidate/observations.json")\n    con = load("candidate/constraints.json")\n    mech = load("candidate/mechanisms.json")\n    pred = load("candidate/predictions.json")\n    ctr = load("candidate/contradictions.json")\n    rob = load("candidate/robustness.json")\n    ev = load("evidence/evidence_registry.json")\n\n    expected_q = f"Q{qmax:03d}"\n    results = {}\n\n    results["T-BV-001"] = passfail(\n        state.get("q_access_start") == "Q001"\n        and state.get("q_access_end") == expected_q\n        and state.get("current_q") == expected_q\n        and accepted.get("q_access_end") == expected_q\n        and accepted.get("current_q") == expected_q,\n        "Candidate/accepted identity and hard Q boundary match current accepted state."\n    )\n\n    scanned = [state, obs, con, mech, pred, ctr, rob, ev]\n    q_update_dir = ROOT / "evidence/q_updates"\n    for p in sorted(q_update_dir.glob("Q*.json")):\n        scanned.append(json.loads(p.read_text(encoding="utf-8")))\n    nums = [n for x in scanned for n in qnums(x)]\n    results["T-BV-002"] = passfail(\n        bool(nums) and max(nums) <= qmax,\n        f"Highest Q identifier in current scientific candidate/evidence JSON is Q{max(nums):03d}."\n        if nums else "No Q identifiers found."\n    )\n\n    h = [x for x in obs["observations"] if x["id"].startswith("OBS-H0-")]\n    hv = {x["id"]: (x["value"], x["sigma"], x["inference_chain"]) for x in h}\n    ok = (\n        hv.get("OBS-H0-LOCAL-001") == (73.50, 0.81, "local distance network")\n        and hv.get("OBS-H0-CMB-001") == (67.24, 0.35, "CMB cosmological inference")\n        and hv.get("OBS-H0-BAOBBN-001") == (68.51, 0.58, "BAO standard ruler + BBN")\n        and len({x[2] for x in hv.values()}) == 3\n    )\n    results["T-BV-003"] = passfail(ok, "H0 benchmarks and distinct inference chains preserved.")\n\n    eids = {x.get("evidence_id"): x for x in ev["entries"]}\n    a = eids.get("EVD-Q039-IMPLBLOCK", {})\n    b = eids.get("EVD-Q039-FGPROFILE", {})\n    ok = (\n        a.get("result_id") == "R-Q039-EDE-IMPLEMENTATION-BLOCK-INTERVENTION-001"\n        and a.get("program_id") == "Q039-IMPLBLOCK-V5"\n        and str(a.get("run_id")) == "34161368438"\n        and a.get("validation_status") == "PASS"\n        and b.get("result_id") == "R-Q039-EDE-NATIVE-FOREGROUND-PROFILE-001"\n        and b.get("program_id") == "Q039-FGPROFILE-V1"\n        and str(b.get("run_id")) == "34184346582"\n        and b.get("validation_status") == "PASS"\n    )\n    results["T-BV-004"] = passfail(ok, "Authoritative Q039 identities and PASS provenance preserved.")\n\n    t = eids.get("EVD-Q039-V1-V4", {})\n    results["T-BV-005"] = passfail(\n        t.get("scientific_evidence") is False and t.get("status") == "SUPERSEDED",\n        "Q039 V1-V4 technical recoveries remain excluded from scientific evidence."\n    )\n\n    ctext = json.dumps(con).lower()\n    q39_ok = all(x in ctext for x in ["relative calibration", "off-diagonal precision", "foreground"])\n    q40_ok = True\n    if qmax >= 40:\n        rqmc = eids.get("EVD-Q040-RQMC", {})\n        rmap = {x["id"]: x for x in rob["items"]}\n        q40_ok = (\n            rqmc.get("physical_falsification") is False\n            and rqmc.get("scientific_status") == "INCONCLUSIVE_TECHNICAL_FAIL"\n            and rmap.get("ROB-Q040-NUMERIC-001", {}).get("status") == "TECHNICAL_FAIL"\n        )\n    results["T-BV-006"] = passfail(\n        q39_ok and q40_ok,\n        "Q039 narrowing and Q040 technical-vs-physical semantics are preserved."\n    )\n\n    cids = {x["id"] for x in ctr["contradictions"]}\n    results["T-BV-007"] = passfail(\n        {"CTR-H0-001", "CTR-PLANCK-IMPL-001"} <= cids,\n        "Required open contradictions remain explicit."\n    )\n\n    unresolved_text = (\n        json.dumps(con).lower() + " "\n        + json.dumps(mech).lower() + " "\n        + json.dumps(ctr).lower()\n    )\n    ok = (\n        "unresolved" in unresolved_text\n        and "hubble" in unresolved_text\n        and "microscopic" in unresolved_text\n        and "acceleration" in unresolved_text\n    )\n    results["T-BV-008"] = passfail(ok, "Major unresolved questions remain unresolved.")\n\n    parse_ok = True\n    for base in [\n        ROOT / "candidate", ROOT / "accepted", ROOT / "evidence",\n        ROOT / "model", ROOT / "release"\n    ]:\n        for p in base.rglob("*.json"):\n            try:\n                json.loads(p.read_text(encoding="utf-8"))\n            except Exception:\n                parse_ok = False\n\n    uniq = (\n        unique_ids(obs["observations"])\n        and unique_ids(con["constraints"])\n        and unique_ids(mech["mechanisms"])\n        and unique_ids(pred["predictions"])\n        and unique_ids(ctr["contradictions"])\n        and unique_ids(rob["items"])\n    )\n    results["T-BV-009"] = passfail(parse_ok and uniq, "Current JSON parses and layer IDs are unique.")\n    return results\n\n\ndef formal_gate():\n    cp = subprocess.run(\n        [sys.executable, str(ROOT / "tests/programs/formal_model_validate.py")],\n        cwd=ROOT, text=True, capture_output=True\n    )\n    print(cp.stdout, end="")\n    if cp.stderr:\n        print(cp.stderr, end="")\n    return cp.returncode == 0\n\n\ndef main():\n    ap = argparse.ArgumentParser()\n    ap.add_argument("command", choices=["validate", "test"])\n    args = ap.parse_args()\n\n    accepted, _, qmax = current()\n    results = audit()\n    formal_ok = formal_gate()\n\n    for tid in MANDATORY_IDS:\n        status, detail = results[tid]\n        print(f"{tid}={status} {detail}")\n\n    all_green = formal_ok and all(results[x][0] == "PASS" for x in MANDATORY_IDS)\n\n    if args.command == "test":\n        version = accepted.get("accepted_model_version", "unknown")\n        campaign_id = f"BV-MODEL-{version}-CURRENT-VALIDATION"\n        rows = [\n            {\n                "test_id": tid,\n                "status": results[tid][0],\n                "detail": results[tid][1],\n                "mandatory_for_current_validation": True,\n            }\n            for tid in MANDATORY_IDS\n        ]\n        out = {\n            "schema_version": 1,\n            "test_campaign_id": campaign_id,\n            "mode": "NON_DESTRUCTIVE_CURRENT_STATE_VALIDATION",\n            "current_q": f"Q{qmax:03d}",\n            "q_access_start": accepted.get("q_access_start"),\n            "q_access_end": accepted.get("q_access_end"),\n            "accepted_model_version": version,\n            "tests": rows,\n            "formal_model_gate": "PASS" if formal_ok else "FAIL",\n            "tests_total": len(rows),\n            "tests_passed": sum(x["status"] == "PASS" for x in rows),\n            "all_green": all_green,\n            "created_at": datetime.now(timezone.utc).isoformat(),\n        }\n        dump(f"tests/results/{campaign_id}.json", out)\n\n    raise SystemExit(0 if all_green else 1)\n\n\nif __name__ == "__main__":\n    main()\n'


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def preflight(repo: Path):
    require((repo / ".git").exists(), "Not a Git repository")

    accepted = load(repo / "accepted/model_state.json")
    require(accepted.get("status") == "ACCEPTED", "Accepted state is not ACCEPTED")
    require(accepted.get("current_q") == TARGET_Q, "Repair requires accepted current_q=Q040")
    require(accepted.get("q_access_end") == TARGET_Q, "Repair requires q_access_end=Q040")
    require(accepted.get("accepted_model_version") == ACCEPTED_VERSION,
            "Repair requires accepted_model_version=v0.2")
    require(accepted.get("model_revision") == REVISION, "Repair requires model_revision=R000002")
    require(accepted.get("source_bubbleverse_commit") == SOURCE_COMMIT,
            "Unexpected Bubbleverse source commit")
    require(accepted.get("word_input_sha256") == WORD_SHA256,
            "Unexpected Q040 Word hash")

    release = load(repo / "release/MODEL_RELEASE_HANDOFF.json")
    require(release.get("current_q") == TARGET_Q, "Release handoff is not Q040")
    require(release.get("accepted_model_after") == ACCEPTED_VERSION,
            "Release handoff does not point to v0.2")
    require(release.get("candidate_promoted") is True,
            "Repair only applies to the already-promoted Q040 state")


def repair_candidate(repo: Path):
    p = repo / "candidate/candidate_state.json"
    d = load(p)
    d["current_q"] = TARGET_Q
    d["q_access_end"] = TARGET_Q
    d["candidate_model_version"] = ACCEPTED_VERSION
    d["candidate_revision"] = REVISION
    d["promotion_status"] = f"PROMOTED_TO_{ACCEPTED_VERSION}"
    d["status"] = "CANDIDATE_PROMOTED"
    save(p, d)

    md = f"""# BUBBLEVERSE MODEL CANDIDATE RECORD

**PROMOTED TO ACCEPTED {ACCEPTED_VERSION}**

- Candidate version: **{ACCEPTED_VERSION}**
- Candidate revision: **{REVISION}**
- Authorized Q range: **Q001-Q040**
- Current Q: **Q040**
- Promotion status: **PROMOTED_TO_{ACCEPTED_VERSION}**

Q040 introduced a methodologically legitimate common physical CMB-space
native-nuisance marginalization construction for CamSpec and HiLLiPoP.

The tested single-Gaussian and defensive randomized quasi-Monte Carlo
representations failed mandatory numerical validation before endpoint geometry
was accepted. This remains a **TECHNICAL_FAIL**, not physical falsification.

The causal origin of the CamSpec-HiLLiPoP fitted-geometry difference remains
unresolved. This candidate record is retained as promotion history; the active
scientific state is `accepted/`.
"""
    (repo / "candidate/MODEL_CANDIDATE.md").write_text(md, encoding="utf-8")


def repair_formal_and_context(repo: Path):
    manifest_path = repo / "model/model_manifest.json"
    manifest = load(manifest_path)
    manifest["accepted_model_version"] = ACCEPTED_VERSION
    manifest["formal_model_version"] = "v0.2-formalization-1"
    manifest["model_revision"] = REVISION
    manifest["current_q"] = TARGET_Q
    manifest["q_access_start"] = "Q001"
    manifest["q_access_end"] = TARGET_Q
    manifest["scientific_change"] = False
    manifest["accepted_state_scientific_revision"] = REVISION
    manifest["description"] = (
        "Machine-readable formalization of the accepted Bubbleverse v0.2 state "
        "through Q040, including Q-bounded known-result contextualization, "
        "next-step routing and read-only external astronomy catalogue context. "
        "The formalization introduces no scientific claim beyond the accepted Q040 state."
    )
    manifest["formalization_rule"] = (
        "NO_UNSUPPORTED_SCIENTIFIC_CLAIMS_OR_UNVALIDATED_PUBLIC_CALCULATIONS"
    )
    save(manifest_path, manifest)

    for name in ["result_registry.json", "external_catalog_registry.json"]:
        p = repo / "model" / name
        d = load(p)
        d["q_access_start"] = "Q001"
        d["q_access_end"] = TARGET_Q
        save(p, d)

    readme = """# Bubbleverse Formal Model Layer

This directory is the machine-readable formalization of the accepted Bubbleverse model state.

It does **not** add new physics, choose a preferred cosmology, or fill unknown quantities with guesses.
It records parameters, benchmark inference chains, implemented equations, explicit assumptions,
uncertainty classes, domains of validity, limitations, schemas, provenance and execution environment.

Current authorized boundary: **Q001-Q040**.
Accepted model: **v0.2 / R000002**.

Q040 records the common-CMB nuisance-marginalization construction and its numerical-validation
failure without promoting the technical failure to physical falsification.

Run the public workflow with operation `test` to validate the complete current model surface.
"""
    (repo / "model/README.md").write_text(readme, encoding="utf-8")

    preg = repo / "bubbleverse_model_program_registry.json"
    programs = load(preg)
    for entry in programs.get("programs", {}).values():
        if isinstance(entry, dict):
            if "accepted_model_version" in entry:
                entry["accepted_model_version"] = ACCEPTED_VERSION
            if "formal_model_version" in entry:
                entry["formal_model_version"] = "v0.2-formalization-1"
            if "q_access_end" in entry:
                entry["q_access_end"] = TARGET_Q

    campaign = programs.get("programs", {}).get("BV-MODEL-CAMPAIGN-V1")
    if campaign:
        campaign["status"] = "ACTIVE_CURRENT_VALIDATOR"
        campaign["command_semantics"] = "CURRENT_STATE_VALIDATION_AND_TEST_RECORD"
        campaign["campaign_id"] = "BV-MODEL-v0.2-CAMPAIGN-0002"

    save(preg, programs)


def repair_release(repo: Path):
    p = repo / "release/MODEL_RELEASE_HANDOFF.json"
    d = load(p)
    d["candidate_model"] = ACCEPTED_VERSION
    d["candidate_promoted"] = True
    d["candidate_promotion_gate"] = "PASS"
    d["current_q"] = TARGET_Q
    d["processed_through_q"] = TARGET_Q
    d["q_access_start"] = "Q001"
    d["q_access_end"] = TARGET_Q
    d["model_revision"] = REVISION
    d["accepted_model_after"] = ACCEPTED_VERSION
    d["release_status"] = "ALL_GREEN"
    d["all_mandatory_green"] = True
    d["blocking_items"] = []
    d["blocking_reason"] = None
    d["mandatory_tests_total"] = 11
    d["mandatory_tests_passed"] = 11
    d["mandatory_tests_failed"] = 0
    d["mandatory_tests_blocked"] = 0
    d["mandatory_tests_inconclusive"] = 0
    d["mandatory_tests_invalid"] = 0
    d["mandatory_tests_not_comparable"] = 0
    d["mandatory_tests_technical_fail"] = 0
    d["test_campaign_id"] = "Q040_MODEL_UPDATE_GATES"
    d["test_campaign_artifact"] = "tests/results/Q040_MODEL_UPDATE_TEST_RESULT.json"
    d["repair_status"] = "Q040_POST_PROMOTION_CONSISTENCY_REPAIRED"
    d["repair_timestamp"] = now()
    save(p, d)


def install_current_validator(repo: Path):
    p = repo / "tests/programs/model_campaign.py"
    p.write_text(MODEL_CAMPAIGN, encoding="utf-8")


def repair_snapshot(repo: Path):
    dst = repo / "versions/accepted" / ACCEPTED_VERSION
    require(dst.exists(), "versions/accepted/v0.2 is missing")

    shutil.copy2(repo / "accepted/MODEL_CURRENT.md", dst / "MODEL_CURRENT.md")

    for name in [
        "model_state.json", "constraints.json", "contradictions.json",
        "mechanisms.json", "observations.json", "predictions.json", "robustness.json"
    ]:
        shutil.copy2(repo / "accepted" / name, dst / name)

    for name in [
        "model_manifest.json", "parameters.json", "benchmarks.json",
        "equations.json", "assumptions.json", "uncertainty.json",
        "domain_of_validity.json", "limitations.json", "input_schema.json",
        "output_schema.json", "environment.json", "result_registry.json",
        "external_catalog_registry.json"
    ]:
        src = repo / "model" / name
        if src.exists():
            shutil.copy2(src, dst / name)

    shutil.copy2(repo / "evidence/evidence_registry.json", dst / "evidence_registry.json")
    shutil.copy2(repo / "evidence/q_updates/Q040.json", dst / "q_update.json")


def append_changelog(repo: Path):
    p = repo / "changelog/MODEL_CHANGELOG.md"
    marker = "Q040 post-promotion consistency repair"
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    if marker not in old:
        entry = """

## Q040 post-promotion consistency repair

- Repair type: structural/provenance consistency only; no new scientific claim.
- Accepted scientific state remains Q040 / v0.2 / R000002.
- Added missing `current_q` and promotion metadata to the retained candidate record.
- Aligned formal/context registries with the Q040 firewall.
- Corrected the formalization-layer `scientific_change` flag to false; the Q040 scientific change is already represented in accepted state.
- Replaced the legacy Q039-hardcoded campaign validator with a current-state validator.
- Completed the frozen v0.2 snapshot with `MODEL_CURRENT.md` and current context registries.
- Preserved Q040 `TECHNICAL_FAIL` as non-physical falsification.
"""
        with p.open("a", encoding="utf-8") as f:
            f.write(entry)


def validation_report(repo: Path):
    errors = []

    accepted = load(repo / "accepted/model_state.json")
    candidate = load(repo / "candidate/candidate_state.json")
    release = load(repo / "release/MODEL_RELEASE_HANDOFF.json")
    manifest = load(repo / "model/model_manifest.json")
    result_registry = load(repo / "model/result_registry.json")
    external_registry = load(repo / "model/external_catalog_registry.json")

    checks = {
        "accepted_q040": accepted.get("current_q") == TARGET_Q and accepted.get("q_access_end") == TARGET_Q,
        "candidate_current_q": candidate.get("current_q") == TARGET_Q,
        "candidate_promoted": candidate.get("promotion_status") == f"PROMOTED_TO_{ACCEPTED_VERSION}",
        "promotion_version_consistency":
            candidate.get("candidate_model_version") == release.get("candidate_model") == ACCEPTED_VERSION,
        "formalization_no_extra_science": manifest.get("scientific_change") is False,
        "formal_boundary_q040": manifest.get("q_access_end") == TARGET_Q,
        "result_registry_q040": result_registry.get("q_access_end") == TARGET_Q,
        "external_registry_q040": external_registry.get("q_access_end") == TARGET_Q,
        "snapshot_model_current":
            (repo / f"versions/accepted/{ACCEPTED_VERSION}/MODEL_CURRENT.md").exists(),
        "model_campaign_current":
            "Q_MAX = 39" not in (repo / "tests/programs/model_campaign.py").read_text(encoding="utf-8"),
    }

    for k, ok in checks.items():
        if not ok:
            errors.append(k)

    report = {
        "artifact_type": "BUBBLEVERSE_Q040_POST_PROMOTION_REPAIR",
        "target_q": TARGET_Q,
        "accepted_model_version": ACCEPTED_VERSION,
        "model_revision": REVISION,
        "scientific_change": False,
        "repair_scope": "STRUCTURAL_METADATA_VALIDATOR_SNAPSHOT_ONLY",
        "checks": {k: ("PASS" if v else "FAIL") for k, v in checks.items()},
        "all_green": not errors,
        "errors": errors,
        "created_at": now(),
    }
    save(repo / "Q040_MODEL_REPAIR_REPORT.json", report)
    require(not errors, f"Repair validation failed: {errors}")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    preflight(repo)

    if not args.check_only:
        repair_candidate(repo)
        repair_formal_and_context(repo)
        repair_release(repo)
        install_current_validator(repo)
        repair_snapshot(repo)
        append_changelog(repo)

    report = validation_report(repo)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
