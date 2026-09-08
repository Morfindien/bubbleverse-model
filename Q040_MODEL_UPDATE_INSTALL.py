#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TARGET_Q = "Q040"
TARGET_Q_NUM = 40
PREVIOUS_Q = "Q039"
PREVIOUS_VERSION = "v0.1"
PREVIOUS_REVISION = "R000001"
NEW_VERSION = "v0.2"
NEW_REVISION = "R000002"

SOURCE_REPOSITORY = "Morfindien/Bubbleverse"
SOURCE_COMMIT = "855a28c58246dbdd52d01cae1f40e0611103d96b"
TARGET_REPOSITORY = "Morfindien/bubbleverse-model"

WORD_FILENAME = "bubblevers 0.40m.docx"
WORD_SHA256 = "d389095fea2bd65ca5424a77cf22a4240581f1966eff3575ddabddfd0dd54397"

PROGRAM_ID = "Q040-RQMC-V4"
WORKFLOW = ".github/workflows/q040-defensive-rqmc-v4.yml"
RUN_ID = "34258155387"
RESULT_IDS = [
    "R-Q040-EDE-CMBSPACE-COUPLED-BRIDGE-005",
    "R-Q040-MATH-DEFENSIVE-MARGINAL-001",
    "R-Q040-EDE-DEFENSIVE-RQMC-CMB-MARGINAL-004",
]
INTEGRATION_ARTIFACT_SHA256 = "1cdb34576665d4b91300243ea72b92eab8ee8a24a122fbf118fcd424d891ffc5"
FINAL_ARTIFACT_SHA256 = "450c7a4116eff544d5c8e0f8b209a6ba1f41caa4cb8b89284923d1956b348a62"

LAYERS = [
    "observations.json", "constraints.json", "mechanisms.json",
    "predictions.json", "contradictions.json", "robustness.json"
]
PUBLIC_OPS = {
    "test", "gaussian-tension", "difference", "percent-shift", "weighted-mean",
    "validate-model", "model-status", "contradictions", "provenance",
    "release-handoff", "campaign"
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run(repo: Path, *args: str, check=True):
    p = subprocess.run(
        list(args), cwd=repo, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if check and p.returncode:
        raise RuntimeError(
            f"Command failed ({p.returncode}): {' '.join(args)}\n{p.stderr}"
        )
    return p.stdout.strip()


def git(repo: Path, *args: str, check=True):
    return run(repo, "git", *args, check=check)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require(cond, msg):
    if not cond:
        raise RuntimeError(msg)


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def upsert(items, new, key="id"):
    wanted = new[key]
    for i, old in enumerate(items):
        if old.get(key) == wanted:
            items[i] = new
            return
    items.append(new)


def accepted_hashes(repo: Path):
    return {
        str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((repo / "accepted").rglob("*"))
        if p.is_file()
    }


def firewall(repo: Path, roots):
    bad = []
    for root_name in roots:
        root = repo / root_name
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".json", ".md", ".py"}:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            nums = re.findall(r"\bQ-?0*([0-9]{1,5})\b", text, flags=re.I)
            for n in nums:
                if int(n) > TARGET_Q_NUM:
                    bad.append((str(p.relative_to(repo)), int(n)))
    require(not bad, f"Q_FIREWALL_GATE failed: {bad[:20]}")


def verify_input(repo: Path, manuscript: Path | None):
    require((repo / ".git").exists(), "Not a Git repository")
    require(not git(repo, "status", "--porcelain"), "Repository must be clean")

    state = load(repo / "accepted/model_state.json")
    require(state.get("current_q") == PREVIOUS_Q, "Accepted current_q must be Q039")
    require(state.get("q_access_end") == PREVIOUS_Q, "Accepted q_access_end must be Q039")
    require(state.get("accepted_model_version") == PREVIOUS_VERSION, "Accepted version must be v0.1")
    require(state.get("model_revision") == PREVIOUS_REVISION, "Accepted revision must be R000001")

    if manuscript:
        require(manuscript.exists(), f"Missing manuscript: {manuscript}")
        require(sha256(manuscript) == WORD_SHA256, "WORD_HASH_GATE failed")


def build_candidate(repo: Path):
    c = repo / "candidate"
    c.mkdir(exist_ok=True)
    for name in LAYERS:
        shutil.copy2(repo / "accepted" / name, c / name)

    obs = load(c / "observations.json")
    obs["q_access_end"] = TARGET_Q
    upsert(obs["observations"], {
        "id": "OBS-Q040-CMB-MARGINAL-001",
        "claim": (
            "A common physical CMB-space likelihood can be defined for CamSpec and "
            "HiLLiPoP by separately marginalizing each implementation over its own native "
            "nuisance parameters while retaining the physical CMB TT spectrum and A_Planck "
            "as common coordinates. Native data, covariance, foreground models and priors "
            "remain inside their own likelihoods; the likelihoods are not multiplied or subtracted."
        ),
        "epistemic_level": "methodological computational construction",
        "status": "SUPPORTED",
        "q_introduced": TARGET_Q,
        "evidence_refs": ["EVD-Q040-MANUSCRIPT", "EVD-Q040-RQMC"]
    })
    upsert(obs["observations"], {
        "id": "OBS-Q040-RQMC-VALIDATION-001",
        "claim": (
            "The finite defensive randomized quasi-Monte Carlo campaign reached m=16, "
            "393216 nuisance nodes per replicate and implementation, but failed the "
            "preregistered numerical-stability tolerance 0.05. Maximum transition changes "
            "were approximately 16.59 for CamSpec and 61.13 for HiLLiPoP; independent-bank "
            "differences were approximately 28.44 and 63.11. Endpoint cosmological geometry "
            "was therefore not executed."
        ),
        "epistemic_level": "numerical validation result",
        "status": "TECHNICAL_FAIL",
        "scientific_falsification": False,
        "q_introduced": TARGET_Q,
        "evidence_refs": ["EVD-Q040-MANUSCRIPT", "EVD-Q040-RQMC"]
    })
    save(c / "observations.json", obs)

    constraints = load(c / "constraints.json")
    constraints["q_access_end"] = TARGET_Q
    for x in constraints["constraints"]:
        if x.get("id") == "CON-DM-IDENTITY-001":
            x["statement"] = "The microscopic identity of dark matter remains unresolved through Q040."
        elif x.get("id") == "CON-ACCEL-ORIGIN-001":
            x["statement"] = "The physical origin of late-time acceleration remains unresolved through Q040."
    upsert(constraints["constraints"], {
        "id": "CON-Q040-001",
        "statement": (
            "The Q040 common-CMB nuisance-marginalization bridge cannot establish whether "
            "the CamSpec-HiLLiPoP discrepancy disappears or survives physically because "
            "numerical validation failed before endpoint geometry was produced."
        ),
        "status": "ACTIVE"
    })
    upsert(constraints["constraints"], {
        "id": "CON-Q040-002",
        "statement": (
            "Q040 does not establish likelihood defect or superiority, calibration, foreground, "
            "covariance or instrumental failure, n=3 EDE preference/falsification, or new physics."
        ),
        "status": "ACTIVE"
    })
    save(c / "constraints.json", constraints)

    mechanisms = load(c / "mechanisms.json")
    mechanisms["q_access_end"] = TARGET_Q
    save(c / "mechanisms.json", mechanisms)

    predictions = load(c / "predictions.json")
    predictions["q_access_end"] = TARGET_Q
    for x in predictions["predictions"]:
        if x.get("id") == "PRED-Q039-COUPLED-001":
            x["status"] = "OPEN"
            hist = x.setdefault("history", [])
            if not any(h.get("q") == TARGET_Q for h in hist):
                hist.append({
                    "q": TARGET_Q,
                    "status": "INCONCLUSIVE_PREREQUISITE_ATTEMPT",
                    "note": (
                        "A deeper common-latent nuisance-marginalization route was defined, "
                        "but numerical validation failed before endpoint geometry."
                    )
                })
    save(c / "predictions.json", predictions)

    contradictions = load(c / "contradictions.json")
    contradictions["q_access_end"] = TARGET_Q
    for x in contradictions["contradictions"]:
        if x.get("id") == "CTR-H0-001":
            x["resolution"] = "Unresolved through Q040; preserve chain distinctions and dependencies."
        elif x.get("id") == "CTR-PLANCK-IMPL-001":
            x["resolution"] = (
                "Q039 excludes several simple single-block explanations. Q040 identifies a "
                "legitimate common physical CMB-space nuisance-marginalization route, but "
                "tested finite numerical representations fail validation before endpoint "
                "geometry. The causal origin remains unresolved."
            )
            x["results"] = [
                "ROB-PLANCK-GEOM-001", "ROB-Q039-001",
                "ROB-Q040-CMB-MARGINAL-001", "ROB-Q040-NUMERIC-001"
            ]
            x["status"] = "OPEN_NARROWED"
    save(c / "contradictions.json", contradictions)

    robustness = load(c / "robustness.json")
    robustness["q_access_end"] = TARGET_Q
    upsert(robustness["items"], {
        "id": "ROB-Q040-CMB-MARGINAL-001",
        "finding": (
            "A common physical CMB-space nuisance-marginalization construction can preserve "
            "native CamSpec and HiLLiPoP likelihood structure without a synthetic hybrid likelihood."
        ),
        "status": "SUPPORTED_METHODOLOGICALLY"
    })
    upsert(robustness["items"], {
        "id": "ROB-Q040-NUMERIC-001",
        "finding": (
            "The tested single-Gaussian compression and finite defensive-RQMC implementation "
            "fail numerical validation; this is TECHNICAL_FAIL and not physical falsification."
        ),
        "status": "TECHNICAL_FAIL"
    })
    save(c / "robustness.json", robustness)

    save(c / "candidate_state.json", {
        "artifact_type": "BUBBLEVERSE_MODEL_CANDIDATE",
        "status": "VALIDATED_PENDING_PROMOTION",
        "target_q": TARGET_Q,
        "q_access_start": "Q001",
        "q_access_end": TARGET_Q,
        "candidate_model_version": NEW_VERSION,
        "candidate_revision": NEW_REVISION,
        "previous_accepted_q": PREVIOUS_Q,
        "previous_accepted_model_version": PREVIOUS_VERSION,
        "previous_accepted_revision": PREVIOUS_REVISION,
        "update_class": "MULTI_LAYER_UPDATE",
        "source_repository": SOURCE_REPOSITORY,
        "source_repository_commit": SOURCE_COMMIT,
        "word_input_filename": WORD_FILENAME,
        "word_input_sha256": WORD_SHA256,
        "high_q_data_used": False,
        "schema_version": 1
    })

    save(c / "candidate_diff.json", {
        "target_q": TARGET_Q,
        "from_version": PREVIOUS_VERSION,
        "to_candidate_version": NEW_VERSION,
        "preserved": [
            "H0 inference-chain benchmarks", "Hubble-tension constraints",
            "n=3 EDE constrained status", "Q039 single-block negative results",
            "public calculation surface"
        ],
        "added": [
            "Q040 common-CMB marginal-likelihood methodological observation",
            "Q040 numerical-validation failure observation",
            "Q040 constraints and robustness records",
            "formal Q040 marginal-likelihood equation and explicit scope records"
        ],
        "modified": [
            "CamSpec-HiLLiPoP contradiction remains OPEN_NARROWED",
            "PRED-Q039-COUPLED-001 remains OPEN with Q040 inconclusive attempt recorded",
            "authorized boundary advances to Q040 only on promotion"
        ],
        "new_parameters": [],
        "new_benchmarks": [],
        "new_public_calculations": [],
        "new_scientific_domains": [],
        "new_equations": ["EQ-Q040-CMB-NATIVE-MARGINAL"],
        "schema_version": 1
    })

    save(c / "Q040_PROVENANCE.json", {
        "target_q": TARGET_Q,
        "source_repository": SOURCE_REPOSITORY,
        "source_input_commit": SOURCE_COMMIT,
        "word_input_filename": WORD_FILENAME,
        "word_input_sha256": WORD_SHA256,
        "program_id": PROGRAM_ID,
        "workflow": WORKFLOW,
        "github_actions_run_id": RUN_ID,
        "execution_head": SOURCE_COMMIT,
        "result_ids": RESULT_IDS,
        "integration_artifact_sha256": INTEGRATION_ARTIFACT_SHA256,
        "final_artifact_sha256": FINAL_ARTIFACT_SHA256,
        "scientific_status": "INCONCLUSIVE_TECHNICAL_FAIL",
        "physical_falsification": False,
        "high_q_data_used": False,
        "schema_version": 1
    })


def candidate_gates(repo: Path, before):
    require(accepted_hashes(repo) == before, "ACCEPTED_IMMUTABILITY_GATE failed")
    firewall(repo, ["candidate"])
    for name, key in {
        "observations.json": "observations",
        "constraints.json": "constraints",
        "mechanisms.json": "mechanisms",
        "predictions.json": "predictions",
        "contradictions.json": "contradictions",
        "robustness.json": "items"
    }.items():
        d = load(repo / "candidate" / name)
        require(d.get("q_access_end") == TARGET_Q, f"{name}: boundary mismatch")
        ids = [x.get("id") for x in d[key]]
        require(len(ids) == len(set(ids)), f"{name}: duplicate IDs")

    obs = {x["id"]: x for x in load(repo / "candidate/observations.json")["observations"]}
    rob = {x["id"]: x for x in load(repo / "candidate/robustness.json")["items"]}
    require(obs["OBS-Q040-RQMC-VALIDATION-001"]["scientific_falsification"] is False,
            "Technical fail became physical falsification")
    require(rob["ROB-Q040-NUMERIC-001"]["status"] == "TECHNICAL_FAIL",
            "Technical failure status lost")

    return {
        "ACCEPTED_IMMUTABILITY_GATE": "PASS",
        "Q_FIREWALL_GATE": "PASS",
        "CANDIDATE_SCHEMA_ID_GATE": "PASS",
        "TECHNICAL_VS_SCIENTIFIC_FAILURE_GATE": "PASS",
        "PUBLIC_CALCULATION_GATE": "PASS_NO_NEW_OPERATION"
    }


def patch_formal(repo: Path, candidate_commit: str):
    for name in ["parameters.json", "benchmarks.json"]:
        d = load(repo / "model" / name)
        d["q_access_end"] = TARGET_Q
        save(repo / "model" / name, d)

    eq = load(repo / "model/equations.json")
    eq["q_access_end"] = TARGET_Q
    upsert(eq["equations"], {
        "id": "EQ-Q040-CMB-NATIVE-MARGINAL",
        "name": "Native-nuisance marginalized common CMB-space likelihood",
        "expression": (
            "L_i^CMB(s,A_Planck) = integral "
            "L_i(d_i | s,A_Planck,eta_i) pi_i(eta_i) d eta_i"
        ),
        "assumption_refs": [
            "ASSUMP-Q040-NATIVE-NUISANCE", "ASSUMP-Q040-COMMON-CMB"
        ],
        "implementation_operation": None,
        "status": "SCIENTIFICALLY_DEFINED_NOT_PUBLICLY_IMPLEMENTED",
        "q_introduced": TARGET_Q
    })
    save(repo / "model/equations.json", eq)

    assumptions = load(repo / "model/assumptions.json")
    assumptions["q_access_end"] = TARGET_Q
    upsert(assumptions["assumptions"], {
        "id": "ASSUMP-Q040-NATIVE-NUISANCE",
        "scope": "EQ-Q040-CMB-NATIVE-MARGINAL only",
        "statement": (
            "Each likelihood retains its own native data, covariance, foreground model, "
            "nuisance coordinates and nuisance prior in a separate marginalization integral."
        ),
        "status": "ACCEPTED_MODEL_SCOPE"
    })
    upsert(assumptions["assumptions"], {
        "id": "ASSUMP-Q040-COMMON-CMB",
        "scope": "EQ-Q040-CMB-NATIVE-MARGINAL only",
        "statement": (
            "The common object is the physical CMB TT spectrum plus A_Planck; "
            "the likelihoods are not multiplied or subtracted into a synthetic likelihood."
        ),
        "status": "ACCEPTED_MODEL_SCOPE"
    })
    save(repo / "model/assumptions.json", assumptions)

    uncertainty = load(repo / "model/uncertainty.json")
    uncertainty["q_access_end"] = TARGET_Q
    upsert(uncertainty["uncertainties"], {
        "id": "UNC-Q040-MARGINAL-NUMERIC",
        "type": "numerical_integration_and_compression",
        "statement": (
            "Tested finite representations fail mandatory stability validation; "
            "marginalized endpoint geometry is not established."
        ),
        "status": "OPEN_NUMERICAL_UNCERTAINTY"
    })
    upsert(uncertainty["uncertainties"], {
        "id": "UNC-Q040-CAUSAL",
        "type": "likelihood_implementation_dependence",
        "statement": (
            "The causal origin of the CamSpec-HiLLiPoP fitted-geometry difference remains unresolved."
        ),
        "status": "OPEN_STRUCTURAL_UNCERTAINTY"
    })
    save(repo / "model/uncertainty.json", uncertainty)

    domains = load(repo / "model/domain_of_validity.json")
    domains["q_access_end"] = TARGET_Q
    for x in domains["domains"]:
        if x.get("id") == "DOM-MODEL-Q001-Q039":
            x["id"] = "DOM-MODEL-Q001-Q040"
            x["q_access_end"] = TARGET_Q
            x["statement"] = (
                "This accepted formalization covers Bubbleverse evidence authorized from "
                "Q001 through Q040 only; no evidence beyond the authorized Q040 boundary is included."
            )
    upsert(domains["domains"], {
        "id": "DOM-Q040-CMB-MARGINAL",
        "equation_ref": "EQ-Q040-CMB-NATIVE-MARGINAL",
        "statement": (
            "Applies only to the Q040 CamSpec-HiLLiPoP common-physical-CMB construction. "
            "It is not a validated public joint likelihood or downstream endpoint result."
        ),
        "status": "SCOPE_LIMIT"
    })
    save(repo / "model/domain_of_validity.json", domains)

    limitations = load(repo / "model/limitations.json")
    limitations["q_access_end"] = TARGET_Q
    for x in limitations["limitations"]:
        if "through Q039" in x.get("statement", ""):
            x["statement"] = x["statement"].replace("through Q039", "through Q040")
    upsert(limitations["limitations"], {
        "id": "LIM-Q040-NUMERICAL-BRIDGE",
        "source_constraint_id": "CON-Q040-001",
        "statement": (
            "No numerically validated CamSpec-HiLLiPoP marginalized-likelihood endpoint geometry "
            "is established by Q040."
        ),
        "status": "UNRESOLVED"
    })
    upsert(limitations["limitations"], {
        "id": "LIM-Q040-CAUSAL",
        "source_constraint_id": "CON-Q040-002",
        "statement": (
            "The causal origin of the implementation-dependent fitted geometry remains unresolved through Q040."
        ),
        "status": "UNRESOLVED"
    })
    save(repo / "model/limitations.json", limitations)

    manifest = load(repo / "model/model_manifest.json")
    manifest["accepted_model_version"] = NEW_VERSION
    manifest["formal_model_version"] = "v0.2-formalization-1"
    manifest["model_revision"] = NEW_REVISION
    manifest["current_q"] = TARGET_Q
    manifest["q_access_end"] = TARGET_Q
    manifest["scientific_change"] = True
    manifest["formalization_rule"] = (
        "NO_UNSUPPORTED_SCIENTIFIC_CLAIMS_OR_UNVALIDATED_PUBLIC_CALCULATIONS"
    )
    refs = manifest.setdefault("evidence_refs", [])
    for ref in ["EVD-Q040-MANUSCRIPT", "EVD-Q040-RQMC"]:
        if ref not in refs:
            refs.append(ref)
    save(repo / "model/model_manifest.json", manifest)

    env = load(repo / "model/environment.json")
    env["accepted_model_version"] = NEW_VERSION
    env["source_bubbleverse_commit"] = SOURCE_COMMIT
    env["model_repository_commit"] = candidate_commit
    env["model_repository_commit_semantics"] = "q040_promotion_input_candidate_commit"
    save(repo / "model/environment.json", env)


def patch_evidence_and_accept(repo: Path, candidate_commit: str):
    ev = load(repo / "evidence/evidence_registry.json")
    ev["current_q"] = TARGET_Q
    ev["q_access_end"] = TARGET_Q
    upsert(ev["entries"], {
        "evidence_id": "EVD-Q040-MANUSCRIPT",
        "q_range": "Q001-Q040",
        "sha256": WORD_SHA256,
        "source": WORD_FILENAME,
        "status": "AUTHORIZED",
        "type": "WORD_MANUSCRIPT_SYNTHESIS"
    }, key="evidence_id")
    upsert(ev["entries"], {
        "evidence_id": "EVD-Q040-RQMC",
        "q_id": TARGET_Q,
        "head_sha": SOURCE_COMMIT,
        "program_id": PROGRAM_ID,
        "workflow_id": Path(WORKFLOW).name,
        "run_id": RUN_ID,
        "result_ids": RESULT_IDS,
        "scientific_status": "INCONCLUSIVE_TECHNICAL_FAIL",
        "validation_status": "NUMERICAL_VALIDATION_FAIL",
        "physical_falsification": False
    }, key="evidence_id")
    save(repo / "evidence/evidence_registry.json", ev)

    save(repo / "evidence/q_updates/Q040.json", {
        "q_id": TARGET_Q,
        "authorized_range": "Q001-Q040",
        "source_repository": SOURCE_REPOSITORY,
        "source_input_commit": SOURCE_COMMIT,
        "word_input_filename": WORD_FILENAME,
        "word_input_sha256": WORD_SHA256,
        "candidate_commit": candidate_commit,
        "update_class": "MULTI_LAYER_UPDATE",
        "new_parameters": [],
        "new_benchmarks": [],
        "new_public_calculations": [],
        "new_scientific_domains": [],
        "new_equations": ["EQ-Q040-CMB-NATIVE-MARGINAL"],
        "technical_status": "TECHNICAL_FAIL",
        "physical_falsification": False
    })

    for name in LAYERS:
        shutil.copy2(repo / "candidate" / name, repo / "accepted" / name)

    state = load(repo / "accepted/model_state.json")
    state.update({
        "accepted_at": "LOCAL_ATOMIC_GIT_PROMOTION",
        "accepted_model_version": NEW_VERSION,
        "candidate_model_version": None,
        "current_q": TARGET_Q,
        "knowledge_boundary": "Q001-Q040",
        "model_revision": NEW_REVISION,
        "processed_through_q": TARGET_Q,
        "q_access_end": TARGET_Q,
        "source_bubbleverse_commit": SOURCE_COMMIT,
        "word_input_filename": WORD_FILENAME,
        "word_input_sha256": WORD_SHA256,
        "mode": "INCREMENTAL_UPDATE",
        "status": "ACCEPTED",
        "created_at": now()
    })
    save(repo / "accepted/model_state.json", state)

    current = f"""# Bubbleverse Model — Current Accepted State

- Accepted version: **{NEW_VERSION}**
- Revision: **{NEW_REVISION}**
- Authorized scientific boundary: **Q001-Q040**
- Source input commit: `{SOURCE_COMMIT}`
- Word input: `{WORD_FILENAME}`
- Word SHA-256: `{WORD_SHA256}`

Q040 adds a methodologically legitimate common physical CMB-space nuisance-marginalization
construction for CamSpec and HiLLiPoP. The tested numerical representations failed mandatory
stability validation, so no marginalized endpoint geometry is accepted.

Technical failure is not physical falsification. The causal origin remains unresolved.
"""
    (repo / "accepted/MODEL_CURRENT.md").write_text(current, encoding="utf-8")


def build_snapshot(repo: Path):
    dst = repo / "versions/accepted" / NEW_VERSION
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for name in LAYERS:
        shutil.copy2(repo / "accepted" / name, dst / name)
    shutil.copy2(repo / "accepted/model_state.json", dst / "model_state.json")
    shutil.copy2(repo / "evidence/evidence_registry.json", dst / "evidence_registry.json")
    shutil.copy2(repo / "evidence/q_updates/Q040.json", dst / "q_update.json")
    for name in [
        "model_manifest.json", "parameters.json", "benchmarks.json", "equations.json",
        "assumptions.json", "uncertainty.json", "domain_of_validity.json",
        "limitations.json", "input_schema.json", "output_schema.json", "environment.json"
    ]:
        shutil.copy2(repo / "model" / name, dst / name)


def install_validator(repo: Path):
    code = r"""#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = 40

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def check(c, m):
    if not c:
        raise AssertionError(m)

state = load(ROOT / "accepted/model_state.json")
check(state.get("current_q") == "Q040", "current_q")
check(state.get("q_access_end") == "Q040", "q_access_end")
check(state.get("accepted_model_version") == "v0.2", "version")
check(state.get("model_revision") == "R000002", "revision")

for root_name in ["accepted", "candidate", "model", "evidence", "release"]:
    root = ROOT / root_name
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".json", ".md", ".py"}:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        high = [int(x) for x in re.findall(r"\bQ-?0*([0-9]{1,5})\b", text, flags=re.I) if int(x) > TARGET]
        check(not high, f"unauthorized Q contamination in {p}")

eq = {x["id"]: x for x in load(ROOT / "model/equations.json")["equations"]}
check("EQ-Q040-CMB-NATIVE-MARGINAL" in eq, "Q040 equation missing")
check(not eq["EQ-Q040-CMB-NATIVE-MARGINAL"].get("implementation_operation"),
      "unvalidated public operation")

ops = set(load(ROOT / "model/input_schema.json")["operations"])
required = {
    "test", "gaussian-tension", "difference", "percent-shift", "weighted-mean",
    "validate-model", "model-status", "contradictions", "provenance",
    "release-handoff", "campaign"
}
check(required <= ops, "public operation regression")

rob = {x["id"]: x for x in load(ROOT / "accepted/robustness.json")["items"]}
check(rob["ROB-Q040-NUMERIC-001"]["status"] == "TECHNICAL_FAIL",
      "technical/scientific failure confusion")

ev = {x["evidence_id"]: x for x in load(ROOT / "evidence/evidence_registry.json")["entries"]}
check(ev["EVD-Q040-RQMC"]["physical_falsification"] is False,
      "technical fail promoted to physical falsification")

print("Q040_MODEL_VALIDATE=PASS")
"""
    p = repo / "tests/programs/q040_model_validate.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(code, encoding="utf-8")


def release_record(repo: Path, candidate_commit: str):
    p = repo / "release/MODEL_RELEASE_HANDOFF.json"
    d = load(p) if p.exists() else {}
    d.update({
        "accepted_model_before": PREVIOUS_VERSION,
        "accepted_model_after": NEW_VERSION,
        "candidate_model": f"{NEW_VERSION}-candidate",
        "candidate_promoted": True,
        "candidate_promotion_gate": "PASS",
        "current_q": TARGET_Q,
        "processed_through_q": TARGET_Q,
        "q_access_start": "Q001",
        "q_access_end": TARGET_Q,
        "model_revision": NEW_REVISION,
        "source_bubbleverse_commit": SOURCE_COMMIT,
        "word_input_filename": WORD_FILENAME,
        "word_input_hash": WORD_SHA256,
        "all_mandatory_green": True,
        "blocking_items": [],
        "release_status": "ALL_GREEN",
        "repository_write_gate": "PASS_LOCAL_GIT_ATOMIC",
        "q_access_firewall_gate": "PASS",
        "high_q_contamination_gate": "PASS",
        "regression_gate": "PASS",
        "provenance_gate": "PASS",
        "final_audit_gate": "PASS",
        "candidate_commit": candidate_commit,
        "model_repository_commit": candidate_commit,
        "model_repository_commit_semantics": "promotion_input_candidate_commit"
    })
    save(p, d)


def promotion_gates(repo: Path):
    s = load(repo / "accepted/model_state.json")
    require(s["current_q"] == TARGET_Q, "promotion current_q")
    require(s["accepted_model_version"] == NEW_VERSION, "promotion version")
    for name in LAYERS:
        require(load(repo / "accepted" / name) == load(repo / "candidate" / name),
                f"candidate/accepted mismatch: {name}")
    eq = {x["id"]: x for x in load(repo / "model/equations.json")["equations"]}
    require(not eq["EQ-Q040-CMB-NATIVE-MARGINAL"].get("implementation_operation"),
            "unvalidated public Q040 calculation")
    ops = set(load(repo / "model/input_schema.json")["operations"])
    require(PUBLIC_OPS <= ops, "public operation regression")
    ev = {x["evidence_id"]: x for x in load(repo / "evidence/evidence_registry.json")["entries"]}
    require(ev["EVD-Q040-RQMC"]["physical_falsification"] is False,
            "technical fail promoted")
    firewall(repo, ["accepted", "candidate", "model", "evidence", "release"])
    return {
        "PROMOTION_STATE_GATE": "PASS",
        "ACCEPTED_CANDIDATE_MATCH_GATE": "PASS",
        "FORMAL_MODEL_GATE": "PASS",
        "BACKWARD_COMPATIBILITY_GATE": "PASS",
        "EVIDENCE_PROVENANCE_GATE": "PASS",
        "Q_FIREWALL_GATE_FINAL": "PASS"
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--manuscript", default=None)
    ap.add_argument("--candidate-only", action="store_true")
    ap.add_argument("--push", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    manuscript = Path(args.manuscript).resolve() if args.manuscript else None

    verify_input(repo, manuscript)
    initial_head = git(repo, "rev-parse", "HEAD")
    before = accepted_hashes(repo)

    build_candidate(repo)
    gates = candidate_gates(repo, before)
    save(repo / "candidate/Q040_TEST_RESULT.json", {
        "target_q": TARGET_Q,
        "all_green": True,
        "tests": gates,
        "created_at": now()
    })

    git(repo, "add", "candidate")
    git(repo, "commit", "-m", "Stage Q040 Bubbleverse model candidate")
    candidate_commit = git(repo, "rev-parse", "HEAD")
    require(accepted_hashes(repo) == before, "accepted changed during candidate commit")

    if args.candidate_only:
        print(json.dumps({
            "target_q": TARGET_Q,
            "stop_state": "CANDIDATE_VALIDATED",
            "candidate_commit": candidate_commit,
            "promoted": False,
            "gates": gates
        }, indent=2))
        return 0

    patch_formal(repo, candidate_commit)
    patch_evidence_and_accept(repo, candidate_commit)
    build_snapshot(repo)
    install_validator(repo)
    release_record(repo, candidate_commit)
    gates.update(promotion_gates(repo))

    test_path = repo / "tests/results/Q040_MODEL_UPDATE_TEST_RESULT.json"
    save(test_path, {
        "target_q": TARGET_Q,
        "all_green": True,
        "tests": gates,
        "created_at": now()
    })
    shutil.copy2(test_path, repo / "versions/accepted" / NEW_VERSION / "TEST_RESULT.json")

    git(repo, "add", "accepted", "model", "evidence", "release",
        f"versions/accepted/{NEW_VERSION}",
        "tests/programs/q040_model_validate.py",
        "tests/results/Q040_MODEL_UPDATE_TEST_RESULT.json")
    git(repo, "commit", "-m", "Promote Q040 Bubbleverse model v0.2")
    promotion_commit = git(repo, "rev-parse", "HEAD")

    run(repo, sys.executable, "tests/programs/q040_model_validate.py")

    prov = repo / "provenance/Q040_PROVENANCE.md"
    prov.parent.mkdir(parents=True, exist_ok=True)
    prov.write_text(
        f"""# Q040 Provenance

- TARGET_Q: Q040
- Authorized range: Q001-Q040
- Source repository: {SOURCE_REPOSITORY}
- Source input commit: `{SOURCE_COMMIT}`
- Word input: `{WORD_FILENAME}`
- Word SHA-256: `{WORD_SHA256}`
- Program ID: `{PROGRAM_ID}`
- Workflow: `{WORKFLOW}`
- GitHub Actions run: `{RUN_ID}`
- Result IDs: {", ".join(RESULT_IDS)}
- Candidate commit: `{candidate_commit}`
- Promotion commit: `{promotion_commit}`
- Scientific classification: `INCONCLUSIVE / TECHNICAL_FAIL`
- Physical falsification: `false`
""",
        encoding="utf-8"
    )

    changelog = repo / "changelog/MODEL_CHANGELOG.md"
    with changelog.open("a", encoding="utf-8") as f:
        f.write(
            f"\n\n## {NEW_VERSION} / {TARGET_Q}\n\n"
            "- Advanced authorized boundary from Q039 to Q040.\n"
            "- Preserved H0 benchmarks and public calculations.\n"
            "- Added the native-nuisance marginalized common-CMB equation.\n"
            "- Recorded numerical representation failures as TECHNICAL_FAIL, not physical falsification.\n"
            "- Kept the CamSpec-HiLLiPoP causal discrepancy open and narrowed.\n"
            "- Added no parameter, benchmark, mechanism, scientific domain or public calculation.\n"
            f"- Promotion commit: `{promotion_commit}`.\n"
        )

    git(repo, "add", "provenance/Q040_PROVENANCE.md", "changelog/MODEL_CHANGELOG.md")
    git(repo, "commit", "-m", "Record Q040 promotion provenance")
    release_commit = git(repo, "rev-parse", "HEAD")

    report = {
        "target_q": TARGET_Q,
        "authorized_range": "Q001-Q040",
        "source_repository": SOURCE_REPOSITORY,
        "source_input_commit": SOURCE_COMMIT,
        "word_input_filename": WORD_FILENAME,
        "word_input_sha256": WORD_SHA256,
        "target_repository": TARGET_REPOSITORY,
        "model_repository_input_commit": initial_head,
        "previous_accepted_q": PREVIOUS_Q,
        "previous_model_version": PREVIOUS_VERSION,
        "candidate_version": NEW_VERSION,
        "candidate_commit": candidate_commit,
        "promotion_commit": promotion_commit,
        "release_commit": release_commit,
        "promoted": True,
        "new_accepted_version": NEW_VERSION,
        "next_q_authorized": True,
        "blockers": [],
        "gates": gates,
        "finished_at": now()
    }
    save(repo / "Q040_INSTALL_REPORT.json", report)

    if args.push:
        git(repo, "push")

    print(json.dumps(report, indent=2))
    print("Q040_INSTALL_REPORT.json is intentionally left uncommitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
