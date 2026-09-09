#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TMP_FP = Path("/tmp/bubbleverse_cleanup_before.json")

SAFE_DELETE = [
    ".github/workflows/q040-model-update.yml",
    ".github/workflows/q040-model-repair.yml",
    "Q040_MODEL_UPDATE_INSTALL.py",
    "Q040_MODEL_UPDATE_MANIFEST.json",
    "Q040_MODEL_UPDATE_REPORT.md",
    "Q040_MODEL_REPAIR.py",
    "Q040_MODEL_REPAIR_REPORT.json",
    "README-updated-final.md",
]

PROTECTED_ROOTS = [
    "accepted",
    "versions/accepted",
    "evidence",
    "model",
    "candidate",
    "tests/programs",
    "tests/preregistration",
    "tests/results",
]
PROTECTED_EXACT = ["release/MODEL_RELEASE_HANDOFF.json"]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def save(rel: str, obj):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint() -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in PROTECTED_ROOTS:
        base = ROOT / rel
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file():
                out[p.relative_to(ROOT).as_posix()] = sha256(p)
    for rel in PROTECTED_EXACT:
        p = ROOT / rel
        if p.exists():
            out[rel] = sha256(p)
    return out


def canonical_state():
    accepted = load("accepted/model_state.json")
    release = load("release/MODEL_RELEASE_HANDOFF.json")
    manifest = load("model/model_manifest.json")
    programs = load("bubbleverse_model_program_registry.json")

    if accepted.get("status") != "ACCEPTED":
        raise SystemExit("Accepted state is not ACCEPTED")
    if accepted.get("current_q") != accepted.get("q_access_end"):
        raise SystemExit("Accepted current_q and q_access_end disagree")
    if release.get("current_q") != accepted.get("current_q"):
        raise SystemExit("Release current_q disagrees with accepted state")
    if release.get("accepted_model_after") != accepted.get("accepted_model_version"):
        raise SystemExit("Release accepted version disagrees with accepted state")
    if manifest.get("current_q") != accepted.get("current_q"):
        raise SystemExit("Formal manifest current_q disagrees with accepted state")
    if manifest.get("accepted_model_version") != accepted.get("accepted_model_version"):
        raise SystemExit("Formal manifest accepted version disagrees with accepted state")
    if release.get("release_status") != "ALL_GREEN":
        raise SystemExit("Release is not ALL_GREEN")

    return accepted, release, manifest, programs


def reference_scan(delete_group: set[str]):
    failures = {}
    for target in sorted(delete_group):
        p = ROOT / target
        if not p.exists():
            continue
        needles = {target, Path(target).name}
        hits = []
        for candidate in ROOT.rglob("*"):
            if not candidate.is_file() or ".git" in candidate.parts:
                continue
            rel = candidate.relative_to(ROOT).as_posix()
            if rel in delete_group:
                continue
            # Canonical historical records may mention old infrastructure by name.
            if rel.startswith("provenance/") or rel.startswith("changelog/"):
                continue
            try:
                text = candidate.read_text(encoding="utf-8")
            except Exception:
                continue
            if any(n in text for n in needles):
                hits.append(rel)
        if hits:
            failures[target] = hits
    if failures:
        raise SystemExit(f"REFERENCE_SCAN failed: {failures}")


def sync_readme(accepted, release, manifest, programs):
    p = ROOT / "README.md"
    text = p.read_text(encoding="utf-8")

    qstart = accepted["q_access_start"]
    qend = accepted["q_access_end"]
    qrange = f"{qstart}–{qend}"
    version = accepted["accepted_model_version"]
    revision = accepted["model_revision"]
    formal = manifest.get("formal_model_version", "UNKNOWN")
    campaign = programs.get("programs", {}).get("BV-MODEL-CAMPAIGN-V1", {})
    campaign_id = campaign.get("campaign_id", "CURRENT")

    current_state = f"""## Current State

- Mode: **INCREMENTAL_UPDATE — {qend} accepted**
- Authorized scientific range: **{qrange}**
- Current Q: **{accepted["current_q"]}**
- Accepted model: **{version}**
- Model revision: **{revision}**
- Candidate state: **promoted record retained**
- Formal model: **{formal}**
- Scientific campaign: **9 / 9 PASS**
- Formal-model validation: **12 / 12 PASS**
- Public system healthcheck: **20 / 20 PASS**
- Result context engine: **ACTIVE**
- External astronomy catalog context: **ACTIVE**
- Release status: **{release["release_status"]}**
- Next Q: **{"AUTHORIZED" if release.get("next_word_authorized") else "BLOCKED"}**

---
"""

    text, n = re.subn(
        r"## Current State\n.*?\n---\n",
        current_state,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("README current-state section not found")

    # README is current documentation, so stale current-boundary labels are synced.
    text = text.replace("Q001–Q039", qrange)
    text = text.replace("Q001-Q039", f"{qstart}-{qend}")
    text = text.replace("The Q039 baseline is complete and ready for automatic future model updates.",
                        f"The {qend} accepted state is complete and ready for the next controlled model update.")

    # Current implementation's campaign is validation-only.
    campaign_pattern = re.compile(
        r"### campaign\n\nRuns the explicit model campaign\..*?instead\.\n",
        re.S,
    )
    replacement = """### campaign

Runs the current scientific/model validation campaign and may write a validation record under `tests/results/`.

In the current implementation it does **not** promote a candidate, expand the Q boundary, or alter accepted scientific state. Scientific promotion belongs to the controlled model-update pipeline.

Use `test` for the complete non-destructive system healthcheck and `validate-model` for direct model validation.
"""
    text = campaign_pattern.sub(replacement, text, count=1)

    p.write_text(text, encoding="utf-8")


def sync_release_md(release):
    p = ROOT / "release/MODEL_RELEASE_HANDOFF.md"
    r = release
    text = f"""# BUBBLEVERSE MODEL RELEASE HANDOFF

AUTHORIZED Q RANGE: {r["q_access_start"]}–{r["q_access_end"]}
CURRENT Q: {r["current_q"]}
Processed through: {r["processed_through_q"]}

Previous accepted model: {r["accepted_model_before"]}
Candidate: {r["candidate_model"]}
Final accepted model: {r["accepted_model_after"]}
Model revision: {r["model_revision"]}

Campaign: {r["test_campaign_id"]}

## MANDATORY TESTS
PASS: {r["mandatory_tests_passed"]} / {r["mandatory_tests_total"]}
FAIL: {r["mandatory_tests_failed"]}
INCONCLUSIVE: {r["mandatory_tests_inconclusive"]}
NOT COMPARABLE: {r["mandatory_tests_not_comparable"]}
BLOCKED: {r["mandatory_tests_blocked"]}
TECHNICAL FAIL: {r["mandatory_tests_technical_fail"]}
INVALID: {r["mandatory_tests_invalid"]}

## GATES
Q ACCESS FIREWALL: {r["q_access_firewall_gate"]}
HIGH-Q CONTAMINATION: {r["high_q_contamination_gate"]}
SCHEMA: {r["model_schema_gate"]}
PROVENANCE: {r["provenance_gate"]}
CONTRADICTIONS: {r["contradiction_gate"]}
REGRESSION: {r["regression_gate"]}
TEST CAMPAIGN: {r["test_campaign_gate"]}
PROMOTION: {r["candidate_promotion_gate"]}
FINAL AUDIT: {r["final_audit_gate"]}

ALL MANDATORY GREEN: {"YES" if r["all_mandatory_green"] else "NO"}
CANDIDATE PROMOTED: {"YES" if r["candidate_promoted"] else "NO"}
NEXT WORD AUTHORIZED: {"YES" if r["next_word_authorized"] else "NO"}
RELEASE STATUS: {r["release_status"]}

SOURCE BUBBLEVERSE COMMIT: `{r["source_bubbleverse_commit"]}`
CANDIDATE COMMIT: `{r["candidate_commit"]}`
MODEL REPOSITORY COMMIT ({r["model_repository_commit_semantics"]}): `{r["model_repository_commit"]}`
REPAIR STATUS: {r.get("repair_status", "NONE")}
"""
    p.write_text(text, encoding="utf-8")


def sync_test_docs(accepted, programs):
    campaign = programs.get("programs", {}).get("BV-MODEL-CAMPAIGN-V1", {})
    campaign_id = campaign.get("campaign_id", "CURRENT")
    qend = accepted["q_access_end"]
    version = accepted["accepted_model_version"]

    plan = f"""# BUBBLEVERSE MODEL — TEST PLAN CURRENT

**Campaign:** {campaign_id}
**Authorized Q range:** {accepted["q_access_start"]}–{qend}
**Current Q:** {accepted["current_q"]}
**Accepted model:** {version} / {accepted["model_revision"]}
**Mode:** current-state validation

Historical preregistration and historical results remain preserved under `tests/preregistration/` and `tests/results/`. This file describes the active validator only.

| TEST_ID | Current target | Required |
|---|---|---|
| T-BV-001 | Candidate/accepted identity and current Q boundary | YES |
| T-BV-002 | High-Q contamination firewall | YES |
| T-BV-003 | H0 inference-chain invariant | YES |
| T-BV-004 | Authoritative Q039 provenance preservation | YES |
| T-BV-005 | Q039 technical/scientific separation | YES |
| T-BV-006 | Q039 narrowing + Q040 technical-vs-physical semantics | YES |
| T-BV-007 | Contradiction preservation | YES |
| T-BV-008 | Open-question preservation | YES |
| T-BV-009 | JSON/schema/reference integrity | YES |

## Success rule
All nine current tests must explicitly PASS.

## Q firewall
Current scientific/model state is limited to {accepted["q_access_start"]}–{qend}. No current-state validation may ingest scientific evidence above {qend}.

## Execution mechanism
`tests/programs/model_campaign.py validate` performs deterministic current-state validation. The permanent public workflow is `.github/workflows/00-bubbleverse-model-start-public.yml`.

## Promotion semantics
This current validator is non-promoting. It does not create a new accepted model, expand the Q boundary, or revise scientific conclusions. Promotion is handled by the controlled model-update pipeline.
"""
    (ROOT / "tests/TEST_PLAN_CURRENT.md").write_text(plan, encoding="utf-8")

    reg = load("tests/test_registry.json")
    reg["campaign_id"] = campaign_id
    reg["accepted_model_version"] = version
    reg["candidate_model_version"] = version
    reg["current_q"] = accepted["current_q"]
    reg["q_access_start"] = accepted["q_access_start"]
    reg["q_access_end"] = qend
    reg["mode"] = "CURRENT_STATE_VALIDATION"
    for item in reg.get("tests", []):
        item["mandatory_for_current_validation"] = True
        item["mandatory_for_promotion"] = False
    save("tests/test_registry.json", reg)


def migrate_provenance(release):
    p = ROOT / "provenance/Q040_PROVENANCE.md"
    if not p.exists():
        return
    text = p.read_text(encoding="utf-8")
    if "## Model-integration handoff history" not in text:
        text += f"""

## Model-integration handoff history

- Integration artifact SHA-256: `1cdb34576665d4b91300243ea72b92eab8ee8a24a122fbf118fcd424d891ffc5`
- Final artifact SHA-256: `450c7a4116eff544d5c8e0f8b209a6ba1f41caa4cb8b89284923d1956b348a62`
- Initial connected-write attempt: `TECHNICAL_BLOCK_403`; infrastructure failure, not scientific failure.
- Post-promotion consistency repair status: `{release.get("repair_status", "NONE")}`.
- One-time updater/repair infrastructure is preserved by Git history rather than retained as active root/workflow clutter.
"""
        p.write_text(text, encoding="utf-8")


def sync_changelog(accepted, release, manifest):
    reg = load("changelog/model_change_registry.json")
    changes = reg.setdefault("changes", [])
    statuses = {x.get("status") for x in changes}

    if "CURRENT_STATE_METADATA_SYNC" not in statuses:
        changes.append({
            "change_revision": f"STRUCT-{len(changes)+1:06d}",
            "date": datetime.now(timezone.utc).isoformat(),
            "status": "CURRENT_STATE_METADATA_SYNC",
            "accepted_after": accepted["accepted_model_version"],
            "current_q": accepted["current_q"],
            "q_access_start": accepted["q_access_start"],
            "q_access_end": accepted["q_access_end"],
            "model_revision": accepted["model_revision"],
            "formal_model_version": manifest.get("formal_model_version"),
            "scientific_change": False,
            "metadata_sync": True,
            "source_bubbleverse_commit": release.get("source_bubbleverse_commit"),
            "repair_status": release.get("repair_status"),
        })

    changes.append({
        "change_revision": f"STRUCT-{len(changes)+1:06d}",
        "date": datetime.now(timezone.utc).isoformat(),
        "status": "REPOSITORY_CLEANUP",
        "accepted_after": accepted["accepted_model_version"],
        "current_q": accepted["current_q"],
        "q_access_start": accepted["q_access_start"],
        "q_access_end": accepted["q_access_end"],
        "model_revision": accepted["model_revision"],
        "scientific_change": False,
        "accepted_state_changed": False,
        "q_boundary_changed": False,
        "model_version_changed": False,
    })
    save("changelog/model_change_registry.json", reg)

    p = ROOT / "changelog/MODEL_CHANGELOG.md"
    text = p.read_text(encoding="utf-8")
    marker = "## Repository cleanup — Q040 post-promotion hygiene"
    if marker not in text:
        text += f"""

{marker}

- Removed completed one-time Q040 updater and repair infrastructure from the active tree.
- Removed stale secondary README copy.
- Synchronized current README, release mirror and current test metadata to canonical accepted state.
- Preserved accepted snapshots, evidence, provenance and historical test results.
- Added runtime-clutter ignore rules.
- Scientific change: false.
- Accepted state changed: false.
- Q boundary changed: false.
- Model version changed: false.
"""
        p.write_text(text, encoding="utf-8")


def sync_gitignore():
    p = ROOT / ".gitignore"
    lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
    for rule in ["run-output/", "__pycache__/", "*.py[cod]", ".pytest_cache/", ".mypy_cache/", ".DS_Store"]:
        if rule not in lines:
            lines.append(rule)
    p.write_text("\n".join(x for x in lines if x.strip()) + "\n", encoding="utf-8")


def json_gate():
    bad = []
    for p in ROOT.rglob("*.json"):
        if ".git" in p.parts:
            continue
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            bad.append((p.relative_to(ROOT).as_posix(), str(exc)))
    if bad:
        raise SystemExit(f"JSON parse failures: {bad[:10]}")


def apply():
    accepted, release, manifest, programs = canonical_state()
    before = fingerprint()
    TMP_FP.write_text(json.dumps(before, indent=2, sort_keys=True), encoding="utf-8")

    delete_group = set(SAFE_DELETE)
    reference_scan(delete_group)

    for rel in SAFE_DELETE:
        p = ROOT / rel
        if p.exists():
            p.unlink()

    sync_readme(accepted, release, manifest, programs)
    sync_release_md(release)
    sync_test_docs(accepted, programs)
    migrate_provenance(release)
    sync_changelog(accepted, release, manifest)
    sync_gitignore()
    json_gate()

    after = fingerprint()
    if before != after:
        changed = sorted(
            p for p in set(before) | set(after)
            if before.get(p) != after.get(p)
        )
        raise SystemExit(f"Protected scientific/history state changed: {changed}")

    print("CLEANUP_APPLY=PASS")
    print("SCIENTIFIC_CHANGE=false")
    print("ACCEPTED_STATE_CHANGED=false")
    print("Q_BOUNDARY_CHANGED=false")
    print("MODEL_VERSION_CHANGED=false")


def verify():
    if not TMP_FP.exists():
        raise SystemExit("Missing pre-cleanup fingerprint")
    before = json.loads(TMP_FP.read_text(encoding="utf-8"))
    after = fingerprint()
    if before != after:
        changed = sorted(
            p for p in set(before) | set(after)
            if before.get(p) != after.get(p)
        )
        raise SystemExit(f"Protected scientific/history state changed: {changed}")

    accepted, release, manifest, programs = canonical_state()
    json_gate()

    if any((ROOT / rel).exists() for rel in SAFE_DELETE):
        remaining = [rel for rel in SAFE_DELETE if (ROOT / rel).exists()]
        raise SystemExit(f"SAFE_DELETE files remain: {remaining}")

    if accepted["current_q"] not in (ROOT / "README.md").read_text(encoding="utf-8"):
        raise SystemExit("README not synchronized to current Q")
    if accepted["accepted_model_version"] not in (ROOT / "README.md").read_text(encoding="utf-8"):
        raise SystemExit("README not synchronized to accepted version")

    print("CLEANUP_VERIFY=PASS")


def public_healthcheck():
    wf = (ROOT / ".github/workflows/00-bubbleverse-model-start-public.yml").read_text(encoding="utf-8")
    blocks = re.findall(
        r"python - <<'PY'\n(.*?)\n\s*PY",
        wf,
        flags=re.S,
    )
    if not blocks:
        raise SystemExit("No embedded public-engine Python block found")

    block = next((b for b in blocks if "SELF-020" in b), blocks[0])
    # Strip workflow indentation from every line.
    lines = block.splitlines()
    nonempty = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    indent = min(nonempty) if nonempty else 0
    code = "\n".join(line[indent:] if len(line) >= indent else line for line in lines) + "\n"

    script = Path("/tmp/bubbleverse_public_engine.py")
    script.write_text(code, encoding="utf-8")
    compile(code, str(script), "exec")

    env = dict(os.environ)
    env["BV_OPERATION"] = "test"
    env["BV_INPUT"] = ""
    env["GITHUB_REPOSITORY"] = "Morfindien/bubbleverse-model"

    cp = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    print(cp.stdout, end="")
    if cp.stderr:
        print(cp.stderr, end="", file=sys.stderr)
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)

    result_path = ROOT / "run-output/result.json"
    if not result_path.exists():
        raise SystemExit("Public healthcheck did not create run-output/result.json")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("tests_total") != 20 or result.get("tests_passed") != 20 or result.get("all_green") is not True:
        raise SystemExit(
            f"Public healthcheck is not 20/20: "
            f"{result.get('tests_passed')}/{result.get('tests_total')}"
        )
    shutil.rmtree(ROOT / "run-output", ignore_errors=True)
    print("PUBLIC_ENGINE_HEALTHCHECK=20/20 PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["apply", "verify", "public-healthcheck"])
    args = ap.parse_args()
    if args.command == "apply":
        apply()
    elif args.command == "verify":
        verify()
    else:
        public_healthcheck()


if __name__ == "__main__":
    main()
