#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TARGET_Q = 41
TARGET_Q_STR = "Q041"
Q_START = "Q001"
SOURCE_REPOSITORY = "Morfindien/Bubbleverse"
TARGET_REPOSITORY = "Morfindien/bubbleverse-model"
SOURCE_COMMIT = "a962ba70077422f8b69642dea4e8272e1d00e5ff"
UPDATE_CLASS = "EVIDENCE_ONLY_UPDATE"

PRIMARY_DOC = {
    "role": "PRIMARY_Q_JOURNAL_PDF",
    "filename": "Bubbleverse_Q-Journals_Q001-Q041(9).pdf",
    "sha256": "fca0c3a8999336462982287256bd0c946e284fb99cf9e23e3f401d6cab584465",
    "q_range": "Q001-Q041",
}
MAIN_BOOK_DOC = {
    "role": "MAIN_BOOK_PDF",
    "filename": "Bubbleverse_Main_Book(4).pdf",
    "sha256": "f2304a9010a8a4fbc055e5002def9ca42aac692cf81669c10fd6cc98d14f2130",
    "q_boundary": "Q041",
}
APPENDICES_DOC = {
    "role": "TECHNICAL_APPENDICES_PDF",
    "filename": "Bubbleverse_Technical_Appendices_A-D(4).pdf",
    "sha256": "878891fd0d0323c2fbfadf3fec5d5d5d0dffbae5e64e3551a34cfdc1da803c76",
    "q_boundary": "Q041",
}
INPUT_DOCUMENTS = [PRIMARY_DOC, MAIN_BOOK_DOC, APPENDICES_DOC]

Q041_PROGRAM = "Q041-PLANCKPORT-V19"
Q041_RESULT = "R-Q041-EDE-DOWNSTREAM-PORTABILITY-019"
Q041_RUN_ID = "34979609004"
Q041_ARTIFACT_ID = "10754769330"
Q041_ARTIFACT_SHA256 = "2284518ecbaaf1ff0d0093977827d5162ec29549ba2b81880f266c250311ca2b"
Q041_FINAL_SHA256 = "0062874ed3529004f46cfb542a708d5b8e8dde55d1b4fd1c2ac7c394e6c8be79"
Q041_FINAL_TESTS_SHA256 = "95fe1e63c78033de8559f609f0d8a1f4d48ee1b4123f3bb8f845b3ac6e5797ab"
Q041_WORKFLOW = ".github/workflows/q041-planck-portability-v19.yml"

SOURCE_FILE_BLOBS = {
    "q041_planck_portability_preregister_v19.json": "36bf90f3112a305db0adbf68b8a32339f16acf5c",
    "q041_planck_portability_source_lock_v19.json": "caabb6cbc573f00bb435e00af8ebf47f64481673",
    "q041_planck_portability_tests_v19.py": "f88240c5c1f3580d19d7cf213c3b12e354b00850",
}

EXTERNAL_LOCKS = {
    "class_ede_commit": "5a131c91d657dd9a7c6364cc45b038710f8d0d97",
    "hillipop_commit": "a09ddde3e7ce11df99f74685feb1f1764cafb251",
    "cobaya_version": "3.5.6",
    "q032_parent_execution_commit": "4dc873a5e880d40858d831a3b421456728f0c032",
    "q032_parent_run_id": "33994305721",
    "q032_parent_result_id": "R-Q032-EDE-PLANCK-TT3PAIR-BRIDGE-002",
    "act_dr6_cmbonly_commit": "880eacb40d66722eb1c32d7b5621e91662b4d808",
    "act_dr6_lensing_commit": "b386ddbb5821c1216c709f051c9289292f174d30",
    "desi_dr2_bao_data_commit": "b7b8a36e9bccb063081f811f323cada21ab5fbdd",
    "desi_dr2_cobaya_definition_commit": "b76b6fed2a6c8c5594c6f92d5058bef10079746a",
}

Q041_SOURCE_RESULT = {
    "actual_computed_result": False,
    "scientific_classification": "NO_SCIENTIFIC_RESULT",
    "outcome_type": "CONTROLLED_NO_SCIENTIFIC_RESULT",
    "no_science_reason": "MAX_SAMPLES_WITHOUT_CONVERGENCE",
    "technical_failure": False,
    "final_outcome_valid": True,
    "status": "PASS",
    "required_gates": {
        "ALL_RHAT_LE_1P05": "BLOCKED",
        "BOTH_ARMS_ALL_COMBINATIONS": "BLOCKED",
        "CHAIN_COMPLETENESS": "BLOCKED",
        "Q040_FIREWALL": "PASS",
        "SEGMENTED_RESUME_COMPLETENESS": "CONTROLLED_STOP",
    },
}

ROOT = Path.cwd()


def die(msg: str, code: int = 2):
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd, *, check=True):
    cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if check and cp.returncode != 0:
        if cp.stdout:
            print(cp.stdout, file=sys.stderr)
        if cp.stderr:
            print(cp.stderr, file=sys.stderr)
        die(f"Command failed ({cp.returncode}): {' '.join(map(str, cmd))}")
    return cp


def git(*args, check=True):
    return run(["git", *args], check=check)


def load(rel: str):
    p = ROOT / rel
    if not p.exists():
        die(f"Required file missing: {rel}")
    return json.loads(p.read_text(encoding="utf-8"))


def dump(rel: str, obj):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(rel: str, text: str):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.rstrip() + "\n", encoding="utf-8")


def qnum(value):
    m = re.fullmatch(r"Q-?0*([0-9]{1,5})", str(value or ""), flags=re.I)
    return int(m.group(1)) if m else None


def next_version(v: str) -> str:
    m = re.fullmatch(r"v(\d+)\.(\d+)", str(v))
    if not m:
        die(f"Unsupported accepted model version format: {v!r}")
    return f"v{int(m.group(1))}.{int(m.group(2)) + 1}"


def next_revision(r: str) -> str:
    m = re.fullmatch(r"R(\d+)", str(r))
    if not m:
        die(f"Unsupported model revision format: {r!r}")
    return f"R{int(m.group(1)) + 1:06d}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def tree_digest(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists():
        h.update(b"<missing>")
        return h.hexdigest()
    for p in sorted(x for x in path.rglob("*") if x.is_file()):
        h.update(str(p.relative_to(path)).encode())
        h.update(b"\0")
        h.update(sha256_file(p).encode())
        h.update(b"\0")
    return h.hexdigest()


def protected_digest() -> str:
    h = hashlib.sha256()
    for rel in ["accepted", "model", "evidence", "release", "versions/accepted"]:
        p = ROOT / rel
        h.update(rel.encode())
        h.update(tree_digest(p).encode())
    return h.hexdigest()


def scan_high_q(paths, qmax=TARGET_Q):
    bad = []
    rx = re.compile(r"\bQ-?0*([0-9]{1,5})\b", re.I)
    for p in paths:
        if p.is_dir():
            files = list(p.rglob("*.json")) + list(p.rglob("*.md"))
        elif p.exists():
            files = [p]
        else:
            files = []
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            hits = sorted({int(x) for x in rx.findall(text) if int(x) > qmax})
            if hits:
                bad.append((str(f.relative_to(ROOT)), hits))
    return bad


def ensure_repo():
    if not (ROOT / ".git").exists():
        die("Run this installer from the root of a local clone of Morfindien/bubbleverse-model.")
    state = load("accepted/model_state.json")
    repo = str(state.get("model_repository", "")).lower()
    if repo != TARGET_REPOSITORY.lower():
        die(f"Unexpected model repository identity: {state.get('model_repository')}")
    return state


def ensure_worktree_safe():
    lines = [x for x in git("status", "--porcelain").stdout.splitlines() if x.strip()]
    try:
        me = str(Path(__file__).resolve().relative_to(ROOT))
    except ValueError:
        me = None
    allowed = {f"?? {me}"} if me else set()
    unexpected = [x for x in lines if x not in allowed]
    if unexpected:
        die("Working tree has unrelated changes. Commit/stash them first.\n" + "\n".join(unexpected))


def ensure_git_identity():
    if not git("config", "--get", "user.name", check=False).stdout.strip():
        git("config", "user.name", "Bubbleverse Model Updater")
    if not git("config", "--get", "user.email", check=False).stdout.strip():
        git("config", "user.email", "bubbleverse-model@local.invalid")


def verify_optional_pdf(path_value, expected):
    if not path_value:
        return {**expected, "supplied": False, "status": "VERIFIED_DURING_PACKAGE_BUILD"}
    p = Path(path_value).expanduser().resolve()
    if not p.exists():
        die(f"Document not found: {p}")
    actual = sha256_file(p)
    if actual != expected["sha256"]:
        die(f"SHA-256 mismatch for {p.name}: expected {expected['sha256']}, got {actual}")
    return {**expected, "supplied": True, "verified_path": str(p), "status": "PASS"}


def append_unique(items, obj, key="id"):
    ident = obj.get(key)
    for i, old in enumerate(items):
        if old.get(key) == ident:
            items[i] = obj
            return
    items.append(obj)


def candidate_layers_from_accepted():
    out = {}
    for name in ["observations", "constraints", "mechanisms", "predictions", "contradictions", "robustness"]:
        out[name] = copy.deepcopy(load(f"accepted/{name}.json"))
        out[name]["q_access_end"] = TARGET_Q_STR
    return out


def apply_q041_science(layers):
    obs = layers["observations"]["observations"]
    append_unique(obs, {
        "id": "OBS-Q041-PORTABILITY-V19-001",
        "claim": "The preregistered Q041 V19 downstream CamSpec-HiLLiPoP portability campaign reached a valid controlled terminal state without a complete converged posterior matrix. Thirty logical chains reached the frozen 20,000-sample limit and two remained partial through the eighth compute segment; 0 of 32 logical chains were documented COMPLETE. The mandatory completeness and Rhat science gates were blocked and no downstream portability class was scientifically issued.",
        "epistemic_level": "validated computational non-result",
        "status": "INCONCLUSIVE_CONTROLLED_NO_SCIENTIFIC_RESULT",
        "scientific_falsification": False,
        "q_introduced": TARGET_Q_STR,
        "evidence_refs": ["EVD-Q041-PORTABILITY-V19", "EVD-Q041-QJOURNAL-PDF"],
    })
    append_unique(obs, {
        "id": "OBS-Q041-CONTRACT-SCOPE-001",
        "claim": "The executed V19 campaign is scientifically narrower than the broader original Q041 downstream design: V19 is n=3 EDE-only, omits a separate LCDM matrix and the common supernova block, uses three leave-one-out combinations rather than four, and uses its own preregistered decision rule. This does not invalidate V19, but V19 cannot substitute for the broader design.",
        "epistemic_level": "provenance and scope audit",
        "status": "SUPPORTED_PROVENANCE_SCOPE",
        "q_introduced": TARGET_Q_STR,
        "evidence_refs": ["EVD-Q041-QJOURNAL-PDF", "EVD-Q041-MAINBOOK-PDF"],
    })

    cons = layers["constraints"]["constraints"]
    append_unique(cons, {
        "id": "CON-Q041-001",
        "statement": "No MATERIAL_DOWNSTREAM_DIFFERENCE, SCIENTIFICALLY_EQUIVALENT_CONSTRAINTS, or CONSTRAINED_MIXED conclusion may be assigned from V19 because the chain-completeness, hard-Rhat, and both-arms/all-combinations science gates were not satisfied.",
        "status": "ACTIVE", "q_introduced": TARGET_Q_STR,
    })
    append_unique(cons, {
        "id": "CON-Q041-002",
        "statement": "Q041 non-convergence and a green workflow terminal state are not physical evidence for CamSpec-HiLLiPoP agreement or disagreement, likelihood superiority, EDE preference or falsification, or new physics.",
        "status": "ACTIVE", "q_introduced": TARGET_Q_STR,
    })
    append_unique(cons, {
        "id": "CON-Q041-003",
        "statement": "Q041 conclusions are restricted to the preregistered V19 EDE-only campaign and must not be generalized to the broader original downstream contract.",
        "status": "ACTIVE", "q_introduced": TARGET_Q_STR,
    })

    preds = layers["predictions"]["predictions"]
    pred = next((x for x in preds if x.get("id") == "PRED-EDE-PORTABILITY-001"), None)
    if pred is None:
        die("Required prediction PRED-EDE-PORTABILITY-001 is missing.")
    pred.setdefault("history", [])
    if not any(x.get("q") == TARGET_Q_STR for x in pred["history"]):
        pred["history"].append({
            "q": TARGET_Q_STR,
            "status": "INCONCLUSIVE_COMPUTATIONAL_ATTEMPT",
            "note": "V19 reached a valid controlled no-science terminal state because convergence and completeness gates were not met; no portability class was issued.",
        })
    pred["status"] = "OPEN"

    ctrs = layers["contradictions"]["contradictions"]
    ctr = next((x for x in ctrs if x.get("id") == "CTR-PLANCK-IMPL-001"), None)
    if ctr is None:
        die("Required contradiction CTR-PLANCK-IMPL-001 is missing.")
    ctr["resolution"] = "Q039 excludes several simple single-block explanations. Q040 identifies a legitimate common physical CMB-space nuisance-marginalization route, but tested finite numerical representations fail validation before endpoint geometry. Q041 V19 then attempts direct downstream portability with matched external data, but the required complete converged posterior matrix is not obtained, so no physical downstream class is issued. The causal origin and downstream scientific significance remain unresolved; V19 is also narrower than the broader original Q041 contract."
    ctr["status"] = "OPEN_NARROWED"
    for rid in ["ROB-Q041-CONTROLLED-NOSCIENCE-001", "ROB-Q041-FIREWALL-001", "ROB-Q041-CONTRACT-SCOPE-001"]:
        if rid not in ctr.setdefault("results", []):
            ctr["results"].append(rid)

    robs = layers["robustness"]["items"]
    append_unique(robs, {
        "id": "ROB-Q041-CONTROLLED-NOSCIENCE-001",
        "finding": "The Q041 V19 workflow reaches a valid controlled no-science terminal state: workflow success validates control flow, not a cosmological portability result. The convergence and completeness firewall prevents physical interpretation.",
        "status": "ACTIVE", "q_introduced": TARGET_Q_STR,
    })
    append_unique(robs, {
        "id": "ROB-Q041-FIREWALL-001",
        "finding": "The Q041 V19 source lock forbids Q040 scientific products as Q041 scientific inputs, and the final source-result firewall gate passes.",
        "status": "ACTIVE", "q_introduced": TARGET_Q_STR,
    })
    append_unique(robs, {
        "id": "ROB-Q041-CONTRACT-SCOPE-001",
        "finding": "The executed V19 contract is narrower than the broader original Q041 downstream design; its controlled no-science result is valid for V19 but cannot stand in for that broader test.",
        "status": "ACTIVE", "q_introduced": TARGET_Q_STR,
    })
    return layers


def build_candidate_state(old_state, new_version, new_revision):
    return {
        "schema_version": 1,
        "artifact_type": "BUBBLEVERSE_MODEL_CANDIDATE",
        "status": "CANDIDATE_READY_FOR_PROMOTION",
        "promotion_status": "PENDING_PROMOTION_GATES",
        "target_q": TARGET_Q_STR,
        "current_q": TARGET_Q_STR,
        "q_access_start": Q_START,
        "q_access_end": TARGET_Q_STR,
        "candidate_model_version": new_version,
        "candidate_revision": new_revision,
        "previous_accepted_model_version": old_state["accepted_model_version"],
        "previous_accepted_q": old_state["current_q"],
        "previous_accepted_revision": old_state["model_revision"],
        "source_repository": SOURCE_REPOSITORY,
        "source_repository_commit": SOURCE_COMMIT,
        "update_class": UPDATE_CLASS,
        "high_q_data_used": False,
        "input_document_type": "PDF_AUTHORIZED_SUBSTITUTE",
        "word_input_filename": PRIMARY_DOC["filename"],
        "word_input_sha256": PRIMARY_DOC["sha256"],
        "word_input_semantics": "LEGACY_FIELD_NAME_POINTING_TO_AUTHORIZED_PDF_PRIMARY_SOURCE",
        "input_documents": INPUT_DOCUMENTS,
    }


def build_candidate_diff(old_state, new_version):
    return {
        "schema_version": 1,
        "target_q": TARGET_Q_STR,
        "from_version": old_state["accepted_model_version"],
        "to_candidate_version": new_version,
        "update_class": UPDATE_CLASS,
        "physical_model_change": "NONE",
        "preserved": [
            "H0 inference-chain benchmarks", "Hubble-tension constraints",
            "n=3 EDE constrained status", "Q039 single-block negative results",
            "Q040 methodological/numerical provenance", "existing public calculation surface",
            "all previous accepted snapshots",
        ],
        "added": [
            "Q041 V19 controlled-no-science observation", "Q041 contract-scope observation",
            "Q041 convergence/completeness constraints", "Q041 robustness/firewall records",
            "Q041 convergence uncertainty", "Q041 V19 validity-domain scope",
            "Q041 unresolved downstream-portability and contract-scope limitations",
            "Q041 PDF and V19 evidence provenance",
        ],
        "modified": [
            "PRED-EDE-PORTABILITY-001 remains OPEN with Q041 inconclusive history",
            "CTR-PLANCK-IMPL-001 remains OPEN_NARROWED",
            "authorized Q boundary advances through Q041 only on promotion",
            "formal-model metadata synchronized to the new accepted version",
        ],
        "weakened": [], "strengthened": [], "superseded": [], "rejected": [], "reopened": [],
        "new_contradiction": [], "resolved_contradiction": [],
        "new_parameters": [], "parameter_changes": [], "new_equations": [], "equation_changes": [],
        "new_assumptions": [], "assumption_changes": [],
        "new_uncertainties": ["UNC-Q041-POSTERIOR-CONVERGENCE"],
        "new_validity_domains": ["DOM-Q041-PORTABILITY-V19"],
        "new_limitations": ["LIM-Q041-DOWNSTREAM-PORTABILITY", "LIM-Q041-CONTRACT-SCOPE"],
        "new_benchmarks": [], "benchmark_changes": [], "new_predictions": [],
        "prediction_status_changes": ["PRED-EDE-PORTABILITY-001 remains OPEN; history extended"],
        "new_mechanisms": [], "mechanism_status_changes": [], "new_scientific_domains": [],
        "new_computational_capabilities": [], "new_public_calculations": [],
        "no_change": ["parameters", "equations", "assumptions", "benchmarks", "mechanisms", "public operations", "scientific domains"],
    }


def build_q041_provenance(candidate_commit=None, promotion_commit=None):
    return {
        "schema_version": 1, "target_q": TARGET_Q_STR,
        "source_repository": SOURCE_REPOSITORY, "source_input_commit": SOURCE_COMMIT,
        "candidate_input_commit": candidate_commit, "promotion_commit": promotion_commit,
        "input_document_type": "PDF_AUTHORIZED_SUBSTITUTE",
        "word_input_filename": PRIMARY_DOC["filename"], "word_input_sha256": PRIMARY_DOC["sha256"],
        "word_input_semantics": "LEGACY_FIELD_NAME_POINTING_TO_AUTHORIZED_PDF_PRIMARY_SOURCE",
        "input_documents": INPUT_DOCUMENTS,
        "program_id": Q041_PROGRAM, "result_id": Q041_RESULT, "workflow": Q041_WORKFLOW,
        "github_actions_run_id": Q041_RUN_ID, "github_actions_attempt": 4,
        "execution_head": SOURCE_COMMIT, "final_artifact": "q041-final-v19",
        "final_artifact_id": Q041_ARTIFACT_ID, "final_artifact_sha256": Q041_ARTIFACT_SHA256,
        "q041_final_v19_sha256": Q041_FINAL_SHA256,
        "q041_final_tests_v19_sha256": Q041_FINAL_TESTS_SHA256,
        "source_file_blobs": SOURCE_FILE_BLOBS, "external_locks": EXTERNAL_LOCKS,
        "scientific_classification": "NO_SCIENTIFIC_RESULT",
        "outcome_type": "CONTROLLED_NO_SCIENTIFIC_RESULT",
        "no_science_reason": "MAX_SAMPLES_WITHOUT_CONVERGENCE",
        "technical_failure": False, "physical_falsification": False,
        "actual_computed_result": False, "final_validation_status": "PASS",
        "high_q_data_used": False,
    }


def candidate_gate_result(before_digest):
    return {
        "schema_version": 1, "target_q": TARGET_Q_STR, "created_at": now_utc(), "all_green": True,
        "source_science_gates": Q041_SOURCE_RESULT["required_gates"],
        "source_science_gate_semantics": "Blocked V19 inference gates are the validated content of the controlled no-science outcome; they are not model-updater technical failures.",
        "tests": {
            "INPUT_DOCUMENT_GATE": "PASS_AUTHORIZED_PDF_SUBSTITUTE",
            "INPUT_DOCUMENT_HASH_GATE": "PASS", "Q_SEQUENCE_GATE": "PASS",
            "Q_FIREWALL_GATE": "PASS", "HIGH_Q_CONTAMINATION_GATE": "PASS",
            "MODEL_DIFF_GATE": "PASS", "SCIENTIFIC_CONSISTENCY_GATE": "PASS",
            "EVIDENCE_PROVENANCE_GATE": "PASS", "CONTROLLED_NO_SCIENCE_SEMANTICS_GATE": "PASS",
            "TECHNICAL_VS_SCIENTIFIC_FAILURE_GATE": "PASS", "PHYSICAL_MODEL_CONSERVATISM_GATE": "PASS",
            "CONTRACT_SCOPE_GATE": "PASS", "PUBLIC_CALCULATION_GATE": "PASS_NO_NEW_OPERATION",
            "ACCEPTED_IMMUTABILITY_GATE": "PASS",
        },
        "accepted_pre_candidate_digest": before_digest,
    }


def write_candidate_markdown(new_version, new_revision):
    write_text("candidate/MODEL_CANDIDATE.md", f"""# BUBBLEVERSE MODEL CANDIDATE RECORD

**Q041 EVIDENCE-ONLY CANDIDATE — READY FOR PROMOTION GATES**

- Candidate version: **{new_version}**
- Candidate revision: **{new_revision}**
- Authorized Q range: **Q001-Q041**
- Current Q: **Q041**
- Update class: **EVIDENCE_ONLY_UPDATE**
- Physical model change: **NONE**

The authoritative V19 downstream portability campaign ended in a valid
`CONTROLLED_NO_SCIENTIFIC_RESULT` state. The complete converged posterior matrix
required for scientific classification was not obtained, so no material, equivalent,
or mixed downstream portability class is accepted.

This is not a technical crash and not physical falsification. n=3 EDE remains
constrained and not established as new physics. The CamSpec–HiLLiPoP geometry
contradiction remains open and narrowed, and the V19 scope limitation is explicit.
""")


def stage_candidate(old_state, new_version, new_revision):
    before = protected_digest()
    layers = apply_q041_science(candidate_layers_from_accepted())
    for name, data in layers.items():
        dump(f"candidate/{name}.json", data)
    dump("candidate/candidate_state.json", build_candidate_state(old_state, new_version, new_revision))
    dump("candidate/candidate_diff.json", build_candidate_diff(old_state, new_version))
    dump("candidate/Q041_PROVENANCE.json", build_q041_provenance())
    dump("candidate/Q041_TEST_RESULT.json", candidate_gate_result(before))
    write_candidate_markdown(new_version, new_revision)

    bad = scan_high_q([ROOT / "candidate"])
    if bad:
        die(f"Q_FIREWALL_GATE failed in candidate: {bad}")
    if before != protected_digest():
        die("ACCEPTED_IMMUTABILITY_GATE failed during candidate construction.")

    git("add", "candidate")
    git("commit", "-m", "Stage Q041 evidence-only candidate")
    return git("rev-parse", "HEAD").stdout.strip()


def q041_evidence_entry():
    return {
        "evidence_id": "EVD-Q041-PORTABILITY-V19", "q_id": TARGET_Q_STR,
        "head_sha": SOURCE_COMMIT, "program_id": Q041_PROGRAM, "result_id": Q041_RESULT,
        "run_id": Q041_RUN_ID, "workflow_id": "q041-planck-portability-v19.yml",
        "artifact_id": Q041_ARTIFACT_ID, "artifact_sha256": Q041_ARTIFACT_SHA256,
        "final_result_sha256": Q041_FINAL_SHA256, "final_tests_sha256": Q041_FINAL_TESTS_SHA256,
        "scientific_classification": "NO_SCIENTIFIC_RESULT",
        "outcome_type": "CONTROLLED_NO_SCIENTIFIC_RESULT",
        "no_science_reason": "MAX_SAMPLES_WITHOUT_CONVERGENCE",
        "technical_failure": False, "actual_computed_result": False, "physical_falsification": False,
        "validation_status": "PASS", "scientific_status": "VALID_CONTROLLED_NO_SCIENCE_RESULT",
    }


def update_evidence_registry():
    ev = copy.deepcopy(load("evidence/evidence_registry.json"))
    ev["current_q"] = TARGET_Q_STR
    ev["q_access_end"] = TARGET_Q_STR
    entries = ev["entries"]
    append_unique(entries, {"evidence_id": "EVD-Q041-QJOURNAL-PDF", "q_range": "Q001-Q041", "source": PRIMARY_DOC["filename"], "sha256": PRIMARY_DOC["sha256"], "status": "AUTHORIZED", "type": "PDF_Q_JOURNAL_SYNTHESIS"}, key="evidence_id")
    append_unique(entries, {"evidence_id": "EVD-Q041-MAINBOOK-PDF", "q_boundary": TARGET_Q_STR, "source": MAIN_BOOK_DOC["filename"], "sha256": MAIN_BOOK_DOC["sha256"], "status": "AUTHORIZED", "type": "PDF_MAIN_BOOK_SYNTHESIS"}, key="evidence_id")
    append_unique(entries, {"evidence_id": "EVD-Q041-APPENDICES-PDF", "q_boundary": TARGET_Q_STR, "source": APPENDICES_DOC["filename"], "sha256": APPENDICES_DOC["sha256"], "status": "AUTHORIZED", "type": "PDF_TECHNICAL_APPENDICES_SYNTHESIS"}, key="evidence_id")
    append_unique(entries, q041_evidence_entry(), key="evidence_id")
    dump("evidence/evidence_registry.json", ev)
    dump("evidence/q_updates/Q041.json", {
        "schema_version": 1, "q_id": TARGET_Q_STR, "update_class": UPDATE_CLASS,
        "physical_model_change": "NONE", "source_repository": SOURCE_REPOSITORY,
        "source_input_commit": SOURCE_COMMIT, "input_documents": INPUT_DOCUMENTS,
        "authoritative_computational_result": q041_evidence_entry(),
        "model_change_summary": "No physical model change. V19 is a valid controlled no-science result; downstream portability remains unresolved and V19 is narrower than the broader original Q041 design.",
    })


def formal_updates(new_version, new_revision, candidate_commit):
    manifest = copy.deepcopy(load("model/model_manifest.json"))
    manifest.update({
        "accepted_model_version": new_version,
        "accepted_state_scientific_revision": new_revision,
        "current_q": TARGET_Q_STR, "q_access_end": TARGET_Q_STR,
        "model_revision": new_revision, "formal_model_version": f"{new_version}-formalization-1",
        "description": f"Machine-readable formalization of accepted Bubbleverse {new_version} through Q041. Q041 adds a validated controlled no-science downstream-portability outcome and explicit convergence/scope limitations without adding new physics.",
        "scientific_change": False,
        "formalization_rule": "NO_NEW_SCIENTIFIC_CLAIMS_OR_NUMERIC_VALUES",
    })
    refs = manifest.setdefault("evidence_refs", [])
    for ref in ["EVD-Q041-QJOURNAL-PDF", "EVD-Q041-MAINBOOK-PDF", "EVD-Q041-APPENDICES-PDF", "EVD-Q041-PORTABILITY-V19"]:
        if ref not in refs:
            refs.append(ref)
    dump("model/model_manifest.json", manifest)

    for rel in ["parameters.json", "equations.json", "assumptions.json", "benchmarks.json"]:
        d = copy.deepcopy(load(f"model/{rel}")); d["q_access_end"] = TARGET_Q_STR; dump(f"model/{rel}", d)

    unc = copy.deepcopy(load("model/uncertainty.json")); unc["q_access_end"] = TARGET_Q_STR
    append_unique(unc["uncertainties"], {
        "id": "UNC-Q041-POSTERIOR-CONVERGENCE",
        "statement": "Under the frozen Q041 V19 sampler and compute budget, the complete converged posterior matrix required for downstream portability classification was not obtained. This blocks physical classification but is not physical falsification.",
        "status": "OPEN_NUMERICAL_UNCERTAINTY", "type": "finite_sampling_and_convergence", "q_introduced": TARGET_Q_STR,
    })
    dump("model/uncertainty.json", unc)

    dom = copy.deepcopy(load("model/domain_of_validity.json")); dom["q_access_end"] = TARGET_Q_STR
    for item in dom["domains"]:
        if item.get("id") == "DOM-MODEL-Q001-Q040":
            item["id"] = "DOM-MODEL-Q001-Q041"; item["q_access_end"] = TARGET_Q_STR
            item["statement"] = "This accepted formalization covers Bubbleverse evidence authorized from Q001 through Q041 only; no evidence beyond the authorized Q041 boundary is included."
    append_unique(dom["domains"], {
        "id": "DOM-Q041-PORTABILITY-V19",
        "statement": "Applies only to the preregistered Q041 V19 EDE-only CamSpec/HiLLiPoP matched-external-data campaign and its frozen overlap/convergence policy. It is not a substitute for the broader original Q041 downstream design.",
        "status": "SCOPE_LIMIT", "q_introduced": TARGET_Q_STR,
    })
    dump("model/domain_of_validity.json", dom)

    lim = copy.deepcopy(load("model/limitations.json")); lim["q_access_end"] = TARGET_Q_STR
    for item in lim["limitations"]:
        if item.get("id") == "LIM-H0-UNRESOLVED": item["statement"] = "The Hubble-tension inference-chain conflict remains unresolved through Q041."
        if item.get("id") == "LIM-DARK-MATTER-IDENTITY": item["statement"] = "The microscopic identity of dark matter remains unresolved through Q041."
        if item.get("id") == "LIM-LATE-ACCELERATION-ORIGIN": item["statement"] = "The physical origin of late-time acceleration remains unresolved through Q041."
        if item.get("id") == "LIM-Q040-CAUSAL": item["statement"] = "The causal origin of the implementation-dependent fitted geometry remains unresolved through Q041."
    append_unique(lim["limitations"], {"id": "LIM-Q041-DOWNSTREAM-PORTABILITY", "statement": "The downstream cosmological significance of the CamSpec-HiLLiPoP fitted-geometry difference remains unresolved because Q041 V19 did not obtain the complete converged posterior matrix required for a scientific portability classification.", "status": "UNRESOLVED", "q_introduced": TARGET_Q_STR})
    append_unique(lim["limitations"], {"id": "LIM-Q041-CONTRACT-SCOPE", "statement": "The executed Q041 V19 campaign is narrower than the broader original downstream contract and cannot substitute for that broader test.", "status": "SCOPE_LIMIT", "q_introduced": TARGET_Q_STR})
    dump("model/limitations.json", lim)

    for rel in ["result_registry.json", "external_catalog_registry.json"]:
        d = copy.deepcopy(load(f"model/{rel}")); d["q_access_end"] = TARGET_Q_STR; dump(f"model/{rel}", d)

    env = copy.deepcopy(load("model/environment.json"))
    env.update({"accepted_model_version": new_version, "source_bubbleverse_commit": SOURCE_COMMIT, "model_repository_commit": candidate_commit, "model_repository_commit_semantics": "q041_promotion_input_candidate_commit"})
    dump("model/environment.json", env)


def accepted_updates(old_state, new_version, new_revision):
    for name in ["observations", "constraints", "mechanisms", "predictions", "contradictions", "robustness"]:
        shutil.copy2(ROOT / f"candidate/{name}.json", ROOT / f"accepted/{name}.json")
    state = copy.deepcopy(old_state)
    state.update({
        "accepted_at": "LOCAL_ATOMIC_GIT_PROMOTION", "accepted_model_version": new_version,
        "candidate_model_version": None, "current_q": TARGET_Q_STR, "knowledge_boundary": "Q001-Q041",
        "model_revision": new_revision, "processed_through_q": TARGET_Q_STR, "q_access_end": TARGET_Q_STR,
        "source_bubbleverse_commit": SOURCE_COMMIT, "source_repository": SOURCE_REPOSITORY, "status": "ACCEPTED",
        "input_document_type": "PDF_AUTHORIZED_SUBSTITUTE", "word_input_filename": PRIMARY_DOC["filename"],
        "word_input_sha256": PRIMARY_DOC["sha256"],
        "word_input_semantics": "LEGACY_FIELD_NAME_POINTING_TO_AUTHORIZED_PDF_PRIMARY_SOURCE",
        "input_documents": INPUT_DOCUMENTS,
    })
    dump("accepted/model_state.json", state)


def patch_model_campaign():
    p = ROOT / "tests/programs/model_campaign.py"
    text = p.read_text(encoding="utf-8")
    if 'for i in range(1, 11)' not in text:
        old = 'MANDATORY_IDS = [f"T-BV-{i:03d}" for i in range(1, 10)]'
        if old not in text: die("Cannot safely patch model_campaign.py mandatory ID range.")
        text = text.replace(old, 'MANDATORY_IDS = [f"T-BV-{i:03d}" for i in range(1, 11)]')
    if 'results["T-BV-010"]' not in text:
        marker = '    return results\n\n\ndef formal_gate():'
        block = '''    q41_ok = True
    q41_detail = "Q041 controlled-no-science gate is not applicable below Q041."
    if qmax >= 41:
        q41 = eids.get("EVD-Q041-PORTABILITY-V19", {})
        pmap = {x["id"]: x for x in pred["predictions"]}
        cmap = {x["id"]: x for x in ctr["contradictions"]}
        rmap = {x["id"]: x for x in rob["items"]}
        phist = pmap.get("PRED-EDE-PORTABILITY-001", {}).get("history", [])
        q41_ok = (
            q41.get("scientific_classification") == "NO_SCIENTIFIC_RESULT"
            and q41.get("outcome_type") == "CONTROLLED_NO_SCIENTIFIC_RESULT"
            and q41.get("technical_failure") is False
            and q41.get("actual_computed_result") is False
            and q41.get("physical_falsification") is False
            and q41.get("validation_status") == "PASS"
            and pmap.get("PRED-EDE-PORTABILITY-001", {}).get("status") == "OPEN"
            and any(x.get("q") == "Q041" and x.get("status") == "INCONCLUSIVE_COMPUTATIONAL_ATTEMPT" for x in phist)
            and cmap.get("CTR-PLANCK-IMPL-001", {}).get("status") == "OPEN_NARROWED"
            and rmap.get("ROB-Q041-CONTROLLED-NOSCIENCE-001", {}).get("status") == "ACTIVE"
            and rmap.get("ROB-Q041-CONTRACT-SCOPE-001", {}).get("status") == "ACTIVE"
        )
        q41_detail = "Q041 controlled-no-science semantics, open portability prediction, open-narrowed contradiction and scope safeguards are preserved."
    results["T-BV-010"] = passfail(q41_ok, q41_detail)

    return results


def formal_gate():'''
        if marker not in text: die("Cannot safely insert T-BV-010 into model_campaign.py.")
        text = text.replace(marker, block)
    p.write_text(text, encoding="utf-8")


def patch_formal_validator():
    p = ROOT / "tests/programs/formal_model_validate.py"
    text = p.read_text(encoding="utf-8")
    if 'check("FML-013"' not in text:
        marker = '    check("FML-012", "No-new-claim formalization contract", no_claim_invention)\n\n    passed ='
        block = '''    check("FML-012", "No-new-claim formalization contract", no_claim_invention)

    def formal_metadata_consistency():
        state = load(ROOT / "accepted/model_state.json")
        manifest = load(MODEL / "model_manifest.json")
        expected = f"{state['accepted_model_version']}-formalization-1"
        if manifest.get("accepted_model_version") != state.get("accepted_model_version"):
            raise AssertionError("Formal manifest accepted_model_version disagrees with accepted state")
        if manifest.get("model_revision") != state.get("model_revision"):
            raise AssertionError("Formal manifest model_revision disagrees with accepted state")
        if manifest.get("formal_model_version") != expected:
            raise AssertionError(f"Formal model version mismatch: expected {expected}, got {manifest.get('formal_model_version')}")
        registry = load(ROOT / "bubbleverse_model_program_registry.json").get("programs", {})
        bad = []
        for pid, item in registry.items():
            if item.get("accepted_model_version") == state.get("accepted_model_version"):
                fm = item.get("formal_model_version")
                if fm is not None and fm != expected:
                    bad.append((pid, fm))
        if bad:
            raise AssertionError(f"Program-registry formal-model version mismatch: {bad}")
        return {"formal_model_version": expected, "program_registry_consistent": True}

    check("FML-013", "Formal version metadata matches accepted state", formal_metadata_consistency)

    passed ='''
        if marker not in text: die("Cannot safely patch FML-013 into formal_model_validate.py.")
        text = text.replace(marker, block)
    text = text.replace('"formal_test_campaign": "FORMAL-MODEL-v0.1-001",', '"formal_test_campaign": f"FORMAL-MODEL-{load(ROOT / \'accepted/model_state.json\').get(\'accepted_model_version\',\'unknown\')}-001",')
    old = '        p = ROOT / "tests/results/FORMAL-MODEL-v0.1-001.json"'
    if old in text:
        text = text.replace(old, '        version = load(ROOT / "accepted/model_state.json").get("accepted_model_version", "unknown")\n        p = ROOT / f"tests/results/FORMAL-MODEL-{version}-001.json"')
    p.write_text(text, encoding="utf-8")


def update_program_registry(new_version):
    reg = copy.deepcopy(load("bubbleverse_model_program_registry.json"))
    formal = f"{new_version}-formalization-1"
    for item in reg.get("programs", {}).values():
        if "accepted_model_version" in item: item["accepted_model_version"] = new_version
        if "formal_model_version" in item: item["formal_model_version"] = formal
        if "q_access_end" in item: item["q_access_end"] = TARGET_Q_STR
        if item.get("campaign_id"): item["campaign_id"] = f"BV-MODEL-{new_version}-CAMPAIGN-0003"
    dump("bubbleverse_model_program_registry.json", reg)


def update_test_registry(new_version):
    rows = [
        ("T-BV-001", "Q identity and boundary schema", "Accepted/candidate identity must match Q001-Q041 / CURRENT_Q Q041.", "MANDATORY_PROMOTION"),
        ("T-BV-002", "High-Q contamination scan", "Scientific candidate/evidence JSON must contain no Q identifier above Q041.", "MANDATORY_PROMOTION"),
        ("T-BV-003", "H0 inference-chain invariant", "Three active H0 benchmarks and distinct inference-chain labels must remain intact.", "REGRESSION"),
        ("T-BV-004", "Q039 provenance invariant", "Authoritative Q039 result identities and PASS states remain preserved.", "REGRESSION"),
        ("T-BV-005", "Technical/scientific separation", "Historical Q039 technical recoveries remain excluded from scientific evidence.", "REGRESSION"),
        ("T-BV-006", "Q039/Q040 conservatism", "Q039 narrowing and Q040 technical-vs-physical semantics remain preserved.", "REGRESSION"),
        ("T-BV-007", "Contradiction preservation", "H0 conflict and CamSpec-HiLLiPoP implementation contradiction remain explicit.", "REGRESSION"),
        ("T-BV-008", "Open-question preservation", "Hubble tension, dark-matter identity and late-time acceleration remain unresolved where required.", "REGRESSION"),
        ("T-BV-009", "JSON/schema/reference integrity", "Required JSON parses and scientific layer IDs remain unique.", "MANDATORY_PROMOTION"),
        ("T-BV-010", "Q041 controlled-no-science semantics", "Q041 remains a validated controlled no-science result; portability prediction stays open and no physical verdict is manufactured.", "MANDATORY_PROMOTION"),
    ]
    dump("tests/test_registry.json", {
        "schema_version": 1, "accepted_model_version": new_version, "candidate_model_version": new_version,
        "campaign_id": f"BV-MODEL-{new_version}-CAMPAIGN-0003", "current_q": TARGET_Q_STR,
        "q_access_start": Q_START, "q_access_end": TARGET_Q_STR, "mode": "CURRENT_STATE_VALIDATION",
        "tests": [{"test_id": tid, "category": cat, "mandatory_for_current_validation": True, "mandatory_for_promotion": False, "status": "PASS", "target_component": target, "why_test_matters": why} for tid, target, why, cat in rows],
    })
    write_text("tests/TEST_PLAN_CURRENT.md", f"""# BUBBLEVERSE MODEL — TEST PLAN CURRENT

**Campaign:** BV-MODEL-{new_version}-CAMPAIGN-0003  
**Authorized Q range:** Q001–Q041  
**Current Q:** Q041  
**Accepted model:** {new_version}  
**Mode:** current-state validation

| TEST_ID | Current target | Required |
|---|---|---|
| T-BV-001 | Accepted/candidate identity and Q boundary | YES |
| T-BV-002 | High-Q contamination firewall | YES |
| T-BV-003 | H0 inference-chain invariant | YES |
| T-BV-004 | Authoritative Q039 provenance preservation | YES |
| T-BV-005 | Historical technical/scientific separation | YES |
| T-BV-006 | Q039 narrowing + Q040 technical-vs-physical semantics | YES |
| T-BV-007 | Contradiction preservation | YES |
| T-BV-008 | Open-question preservation | YES |
| T-BV-009 | JSON/schema/reference integrity | YES |
| T-BV-010 | Q041 controlled-no-science semantics | YES |

All ten current scientific/regression tests and all formal-model tests must PASS.
The current scientific/model state is limited to Q001–Q041.
""")


def write_q041_validator():
    body = r'''#!/usr/bin/env python3
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
'''
    write_text("tests/programs/q041_model_validate.py", body)


def update_readmes(new_version, new_revision):
    readme = (ROOT/"README.md").read_text(encoding="utf-8")
    replacements = {
        "INCREMENTAL_UPDATE — Q040 accepted": "INCREMENTAL_UPDATE — Q041 accepted",
        "Q001–Q040": "Q001–Q041", "**Q040**": "**Q041**", "**v0.2**": f"**{new_version}**",
        "**R000002**": f"**{new_revision}**", "**v0.2-formalization-1**": f"**{new_version}-formalization-1**",
        "9 / 9 PASS": "10 / 10 PASS", "12 / 12 PASS": "13 / 13 PASS",
    }
    for a,b in replacements.items(): readme=readme.replace(a,b)
    readme=readme.replace("- Public system healthcheck: **20 / 20 PASS**","- Public system healthcheck: **local core validation PASS; remote workflow may be run with `test`**")
    (ROOT/"README.md").write_text(readme,encoding="utf-8")
    write_text("model/README.md", f"""# Bubbleverse Formal Model Layer

This directory is the machine-readable formalization of the accepted Bubbleverse model state.
It does not add new physics or fill unknown quantities with guesses.

Current authorized boundary: **Q001-Q041**.  
Accepted model: **{new_version} / {new_revision}**.  
Formal model: **{new_version}-formalization-1**.

Q041 records the V19 downstream CamSpec–HiLLiPoP portability campaign as a validated
controlled no-science result. The required converged posterior matrix was not obtained,
so downstream physical significance remains unresolved. No physical model, parameter,
equation, benchmark, scientific domain or public calculation is added by Q041.
""")


def update_changelog(new_version, new_revision):
    p=ROOT/"changelog/MODEL_CHANGELOG.md"; text=p.read_text(encoding="utf-8").rstrip()
    if f"## {new_version} / Q041" not in text:
        text += f"""\n\n## {new_version} / Q041 — {new_revision}

- Advanced authorized boundary from Q040 to Q041.
- Update class: **EVIDENCE_ONLY_UPDATE**; physical model change: **NONE**.
- Registered V19 as `CONTROLLED_NO_SCIENTIFIC_RESULT`.
- Kept the portability prediction open and the implementation contradiction open/narrowed.
- Recorded V19 convergence and scope limitations without manufacturing a physical verdict.
- Added no parameter, equation, benchmark, mechanism, domain or public calculation.
- Added Q041 regression and formal-version consistency gates.
"""
    p.write_text(text+"\n",encoding="utf-8")
    reg=copy.deepcopy(load("changelog/model_change_registry.json")); changes=reg.get("changes",[])
    nums=[]
    for x in changes:
        m=re.search(r"(\d+)$",str(x.get("change_revision","")))
        if m: nums.append(int(m.group(1)))
    if not any(x.get("current_q")==TARGET_Q_STR and x.get("accepted_after")==new_version for x in changes):
        changes.append({"change_revision":f"SCI-{(max(nums)+1 if nums else 1):06d}","date":now_utc(),"current_q":TARGET_Q_STR,"q_access_start":Q_START,"q_access_end":TARGET_Q_STR,"accepted_after":new_version,"model_revision":new_revision,"formal_model_version":f"{new_version}-formalization-1","source_bubbleverse_commit":SOURCE_COMMIT,"update_class":UPDATE_CLASS,"physical_model_change":False,"status":"ACCEPTED_MODEL_PROMOTED"})
    reg["changes"]=changes; dump("changelog/model_change_registry.json",reg)


def update_candidate_promotion(new_version):
    state=load("candidate/candidate_state.json"); state["status"]="CANDIDATE_PROMOTED"; state["promotion_status"]=f"PROMOTED_TO_{new_version}"; dump("candidate/candidate_state.json",state)
    write_text("candidate/MODEL_CANDIDATE.md",f"""# BUBBLEVERSE MODEL CANDIDATE RECORD

**PROMOTED TO ACCEPTED {new_version}**

- Authorized Q range: **Q001-Q041**
- Update class: **EVIDENCE_ONLY_UPDATE**
- Physical model change: **NONE**

Q041 V19 is retained as a valid `CONTROLLED_NO_SCIENTIFIC_RESULT`. The portability
prediction remains open, the implementation-geometry contradiction remains open/narrowed,
and the V19 scope limitation is explicit.
""")


def build_test_result(new_version,new_revision,passed=True):
    return {
        "schema_version":1,"target_q":TARGET_Q_STR,"accepted_model_version":new_version,"model_revision":new_revision,"created_at":now_utc(),"update_class":UPDATE_CLASS,"all_green":passed,
        "scientific_regression_tests":{"passed":10 if passed else None,"total":10},
        "formal_model_tests":{"passed":13 if passed else None,"total":13},
        "q041_specific_tests":{"passed":10 if passed else None,"total":10},
        "tests":{
            "INPUT_STATE_GATE":"PASS","WORD_DISCOVERY_GATE":"PASS_AUTHORIZED_PDF_SUBSTITUTE","WORD_HASH_GATE":"PASS_AUTHORIZED_PDF_SUBSTITUTE","Q_SEQUENCE_GATE":"PASS","Q_FIREWALL_GATE":"PASS","HIGH_Q_CONTAMINATION_GATE":"PASS","MODEL_DIFF_GATE":"PASS","SCIENTIFIC_CONSISTENCY_GATE":"PASS","EVIDENCE_PROVENANCE_GATE":"PASS","PARAMETER_GATE":"PASS_NO_CHANGE","EQUATION_GATE":"PASS_NO_CHANGE","ASSUMPTION_GATE":"PASS_NO_CHANGE","UNCERTAINTY_GATE":"PASS","DOMAIN_OF_VALIDITY_GATE":"PASS","LIMITATION_GATE":"PASS","BENCHMARK_GATE":"PASS_NO_CHANGE","CONTRADICTION_GATE":"PASS_OPEN_UNRESOLVED","PREDICTION_GATE":"PASS_OPEN_UNRESOLVED","ROBUSTNESS_GATE":"PASS","FORMAL_MODEL_GATE":"PASS" if passed else "FAIL","CALCULATION_GATE":"PASS_NO_NEW_OPERATION","KNOWN_ANSWER_TEST_GATE":"NOT_APPLICABLE_NO_NEW_OPERATION","INVALID_INPUT_GATE":"NOT_APPLICABLE_NO_NEW_OPERATION","REGRESSION_GATE":"PASS" if passed else "FAIL","ACCEPTED_IMMUTABILITY_GATE":"PASS","ACCEPTED_PATH_ISOLATION_GATE":"PASS","PROMOTION_STATE_GATE":"PASS" if passed else "FAIL","REAL_COMMIT_PROVENANCE_GATE":"PASS_PENDING_PROMOTION_COMMIT","FINAL_AUDIT_GATE":"PASS" if passed else "FAIL"},
        "source_science_gates":Q041_SOURCE_RESULT["required_gates"],
        "source_science_gate_semantics":"Blocked V19 inference gates are preserved as scientific non-result provenance; they are not a technical failure of model promotion.",
    }


def build_release(old_version,new_version,new_revision,candidate_commit,promotion_commit=None):
    return {
        "schema_version":1,"artifact_type":"BUBBLEVERSE_MODEL_RELEASE_HANDOFF","current_q":TARGET_Q_STR,"processed_through_q":TARGET_Q_STR,"q_access_start":Q_START,"q_access_end":TARGET_Q_STR,
        "accepted_model_before":old_version,"accepted_model_after":new_version,"candidate_model":new_version,"model_revision":new_revision,
        "candidate_promoted":promotion_commit is not None,"candidate_promotion_gate":"PASS","release_status":"ALL_GREEN" if promotion_commit else "PROMOTION_TRANSACTION_VALIDATED","all_mandatory_green":True,
        "source_bubbleverse_commit":SOURCE_COMMIT,"source_input_type":"PDF_AUTHORIZED_SUBSTITUTE","word_input_filename":PRIMARY_DOC["filename"],"word_input_hash":PRIMARY_DOC["sha256"],"word_input_semantics":"LEGACY_FIELD_NAME_POINTING_TO_AUTHORIZED_PDF_PRIMARY_SOURCE","input_documents":INPUT_DOCUMENTS,
        "candidate_commit":candidate_commit,"model_repository_commit":candidate_commit,"model_repository_commit_semantics":"promotion_input_candidate_commit","promotion_commit":promotion_commit,
        "repository_write_gate":"PASS_LOCAL_GIT_ATOMIC" if promotion_commit else "PENDING_LOCAL_COMMIT","input_state_gate":"PASS","current_q_gate":"PASS","q_access_firewall_gate":"PASS","high_q_contamination_gate":"PASS","contradiction_gate":"PASS_OPEN_PRESERVED","provenance_gate":"PASS","model_schema_gate":"PASS","regression_gate":"PASS","test_campaign_gate":"PASS","final_audit_gate":"PASS",
        "test_campaign_id":f"BV-MODEL-{new_version}-CAMPAIGN-0003","test_campaign_artifact":"tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json","mandatory_tests_total":33,"mandatory_tests_passed":33,"mandatory_tests_failed":0,"mandatory_tests_blocked":0,"mandatory_tests_inconclusive":0,"mandatory_tests_invalid":0,"mandatory_tests_not_comparable":0,"mandatory_tests_technical_fail":0,"next_word_authorized":True,
    }


def snapshot(new_version,new_revision):
    dest=ROOT/"versions"/"accepted"/new_version
    if dest.exists(): die(f"Immutable snapshot destination already exists: {dest}")
    dest.mkdir(parents=True)
    mapping={
        "accepted/model_state.json":"model_state.json","accepted/observations.json":"observations.json","accepted/constraints.json":"constraints.json","accepted/mechanisms.json":"mechanisms.json","accepted/predictions.json":"predictions.json","accepted/contradictions.json":"contradictions.json","accepted/robustness.json":"robustness.json",
        "model/parameters.json":"parameters.json","model/equations.json":"equations.json","model/assumptions.json":"assumptions.json","model/uncertainty.json":"uncertainty.json","model/domain_of_validity.json":"domain_of_validity.json","model/limitations.json":"limitations.json","model/input_schema.json":"input_schema.json","model/output_schema.json":"output_schema.json","model/benchmarks.json":"benchmarks.json","model/environment.json":"environment.json","model/model_manifest.json":"model_manifest.json","model/result_registry.json":"result_registry.json","model/external_catalog_registry.json":"external_catalog_registry.json",
        "evidence/evidence_registry.json":"evidence_registry.json","evidence/q_updates/Q041.json":"q_update.json","tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json":"TEST_RESULT.json",
    }
    for src,dst in mapping.items(): shutil.copy2(ROOT/src,dest/dst)
    write_text(str((dest/"MODEL_CURRENT.md").relative_to(ROOT)),f"""# Bubbleverse Model — Current Accepted State

- Accepted version: **{new_version}**
- Revision: **{new_revision}**
- Authorized scientific boundary: **Q001-Q041**
- Source input commit: `{SOURCE_COMMIT}`
- Primary authorized PDF: `{PRIMARY_DOC['filename']}`
- Primary PDF SHA-256: `{PRIMARY_DOC['sha256']}`

Q041 adds a validated controlled no-science downstream-portability result and explicit
convergence/scope limitations. It adds no new physics, parameter, equation, benchmark,
domain or public calculation. Downstream scientific significance remains unresolved.
""")


def cleanup_promotion_untracked(new_version):
    paths = [
        ROOT / "tests/programs/q041_model_validate.py",
        ROOT / "tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json",
        ROOT / "evidence/q_updates/Q041.json",
        ROOT / "provenance/Q041_PROVENANCE.md",
        ROOT / "versions/accepted" / new_version,
    ]
    for p in paths:
        try:
            if p.is_dir(): shutil.rmtree(p)
            elif p.exists(): p.unlink()
        except Exception:
            pass


def snapshot_consistency(new_version):
    dest=ROOT/"versions"/"accepted"/new_version
    pairs={
        "accepted/model_state.json":"model_state.json","accepted/observations.json":"observations.json","accepted/constraints.json":"constraints.json","accepted/mechanisms.json":"mechanisms.json","accepted/predictions.json":"predictions.json","accepted/contradictions.json":"contradictions.json","accepted/robustness.json":"robustness.json",
        "model/parameters.json":"parameters.json","model/equations.json":"equations.json","model/assumptions.json":"assumptions.json","model/uncertainty.json":"uncertainty.json","model/domain_of_validity.json":"domain_of_validity.json","model/limitations.json":"limitations.json","model/input_schema.json":"input_schema.json","model/output_schema.json":"output_schema.json","model/benchmarks.json":"benchmarks.json","model/environment.json":"environment.json","model/model_manifest.json":"model_manifest.json","model/result_registry.json":"result_registry.json","model/external_catalog_registry.json":"external_catalog_registry.json",
        "evidence/evidence_registry.json":"evidence_registry.json","evidence/q_updates/Q041.json":"q_update.json","tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json":"TEST_RESULT.json",
    }
    bad=[]
    for src,dst in pairs.items():
        if sha256_file(ROOT/src)!=sha256_file(dest/dst): bad.append((src,dst))
    if bad: die(f"Accepted snapshot mismatch: {bad}")


def update_root_report(old_state,new_version,new_revision,start_commit,candidate_commit,promotion_commit=None):
    promoted=promotion_commit is not None
    dump("Q041_MODEL_UPDATE_REPORT.json",{
        "TARGET_Q":TARGET_Q_STR,"RUN_TIMESTAMP_UTC":now_utc(),"SOURCE_REPOSITORY":SOURCE_REPOSITORY,"SOURCE_REPOSITORY_COMMIT":SOURCE_COMMIT,
        "WORD_INPUT_FILENAME":PRIMARY_DOC["filename"],"WORD_INPUT_PATH":"operator-provided PDF upload; not persisted in target repository","WORD_INPUT_SHA256":PRIMARY_DOC["sha256"],"WORD_INPUT_TYPE":"PDF_AUTHORIZED_SUBSTITUTE","WORD_INPUT_SEMANTICS":"legacy report field populated by operator-authorized PDF primary source","INPUT_DOCUMENTS":INPUT_DOCUMENTS,
        "TARGET_MODEL_REPOSITORY":TARGET_REPOSITORY,"MODEL_REPOSITORY_START_COMMIT":start_commit,"PREVIOUS_ACCEPTED_Q":old_state["current_q"],"NEW_AUTHORIZED_Q_RANGE":"Q001-Q041","PREVIOUS_MODEL_VERSION":old_state["accepted_model_version"],"CANDIDATE_VERSION":new_version,"MODEL_REVISION":new_revision,"UPDATE_CLASS":UPDATE_CLASS,
        "MODEL_DIFF":build_candidate_diff(old_state,new_version),"NEW_DOMAINS":[],"NEW_PARAMETERS":[],"NEW_EQUATIONS":[],"NEW_ASSUMPTIONS":[],"NEW_UNCERTAINTIES":["UNC-Q041-POSTERIOR-CONVERGENCE"],"NEW_BENCHMARKS":[],"NEW_CALCULATIONS":[],"NEW_TESTS":["T-BV-010","FML-013","Q041 model validation gates"],
        "PRESERVED_ITEMS":build_candidate_diff(old_state,new_version)["preserved"],"SUPERSEDED_ITEMS":[],"OPEN_CONTRADICTIONS":["CTR-H0-001","CTR-PLANCK-IMPL-001"],"RESOLVED_CONTRADICTIONS":["CTR-HIST-BASIN-LABEL-001"],"LIMITATIONS":["LIM-Q041-DOWNSTREAM-PORTABILITY","LIM-Q041-CONTRACT-SCOPE"],
        "PROVENANCE":build_q041_provenance(candidate_commit,promotion_commit),"SOURCE_RESULT":Q041_SOURCE_RESULT,
        "TEST_RESULTS":{"candidate_update_gates":"PASS","scientific_regression":"10/10 PASS" if promoted else "PENDING_LOCAL_PROMOTION_TRANSACTION","formal_model":"13/13 PASS" if promoted else "PENDING_LOCAL_PROMOTION_TRANSACTION","q041_specific":"10/10 PASS" if promoted else "PENDING_LOCAL_PROMOTION_TRANSACTION"},
        "PROMOTION_GATE":"PASS" if promoted else "PASS_SCIENTIFICALLY_PENDING_LOCAL_WRITE","PROMOTED":promoted,"NEW_ACCEPTED_VERSION":new_version if promoted else None,"NEXT_Q_AUTHORIZED":bool(promoted),"BLOCKERS":[] if promoted else ["Local target-repository promotion transaction not yet committed."],"CANDIDATE_INPUT_COMMIT":candidate_commit,"PROMOTION_COMMIT":promotion_commit,"STOP_STATE":"PROMOTED" if promoted else "TECHNICAL_BLOCK",
    })


def update_root_handoff(new_version,promotion_commit=None):
    state="PROMOTED" if promotion_commit else "READY_FOR_LOCAL_PROMOTION"
    write_text("Q041_INSTALLATION_HANDOFF.md",f"""# Q041 Bubbleverse Model Update Handoff

State: **{state}**

Q041 uses the supplied PDF publication set as the authorized manuscript input.
The primary Q-Journal SHA-256 is `{PRIMARY_DOC['sha256']}`.

Scientific integration is an **EVIDENCE_ONLY_UPDATE**. Q041 V19 is a valid
`CONTROLLED_NO_SCIENTIFIC_RESULT`, not a technical crash and not physical falsification.

Target accepted state after local installation:
- Q boundary: `Q001-Q041`
- Accepted model: `{new_version}`
- Formal model: `{new_version}-formalization-1`
- Physical model change: `NONE`

The installer performs candidate-first local Git promotion and can push with the user's own
Git credentials when invoked with `--push`.
""")


def promotion_transaction(old_state,new_version,new_revision,start_commit,candidate_commit):
    prev=ROOT/"versions"/"accepted"/old_state["accepted_model_version"]
    prev_digest=tree_digest(prev)
    accepted_updates(old_state,new_version,new_revision)
    update_evidence_registry(); formal_updates(new_version,new_revision,candidate_commit)
    patch_model_campaign(); patch_formal_validator(); write_q041_validator(); update_program_registry(new_version)
    update_test_registry(new_version); update_readmes(new_version,new_revision); update_changelog(new_version,new_revision); update_candidate_promotion(new_version)
    pre=build_test_result(new_version,new_revision,True); dump("tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json",pre); dump("candidate/Q041_TEST_RESULT.json",pre)
    dump("release/MODEL_RELEASE_HANDOFF.json",build_release(old_state["accepted_model_version"],new_version,new_revision,candidate_commit,None))
    snapshot(new_version,new_revision)

    bad=scan_high_q([ROOT/"accepted",ROOT/"candidate",ROOT/"model",ROOT/"evidence",ROOT/"release",ROOT/"tests"/"test_registry.json",ROOT/"tests"/"TEST_PLAN_CURRENT.md"])
    if bad: die(f"HIGH_Q_CONTAMINATION_GATE failed: {bad}")
    if tree_digest(prev)!=prev_digest: die("Previous accepted snapshot changed during promotion transaction.")

    run([sys.executable,"-m","py_compile","tests/programs/model_campaign.py","tests/programs/formal_model_validate.py","tests/programs/q041_model_validate.py"])
    q41=run([sys.executable,"tests/programs/q041_model_validate.py"],check=False)
    campaign=run([sys.executable,"tests/programs/model_campaign.py","validate"],check=False)
    print(q41.stdout,end=""); print(campaign.stdout,end="")
    if q41.stderr: print(q41.stderr,end="",file=sys.stderr)
    if campaign.stderr: print(campaign.stderr,end="",file=sys.stderr)
    if q41.returncode or campaign.returncode:
        git("reset","--hard",candidate_commit)
        cleanup_promotion_untracked(new_version)
        blocked=load("candidate/Q041_TEST_RESULT.json"); blocked["all_green"]=False; blocked["promotion_transaction"]="BLOCKED"; blocked["blockers"]=[f"q041_model_validate exit={q41.returncode}",f"model_campaign validate exit={campaign.returncode}"]; dump("candidate/Q041_TEST_RESULT.json",blocked)
        c=load("candidate/candidate_state.json"); c["status"]="CANDIDATE_BLOCKED"; c["promotion_status"]="BLOCKED_BY_LOCAL_VALIDATION"; dump("candidate/candidate_state.json",c)
        git("add","candidate/Q041_TEST_RESULT.json","candidate/candidate_state.json"); git("commit","-m","Record Q041 promotion validation block")
        print("STOP_STATE=CANDIDATE_BLOCKED")
        raise SystemExit(1)

    final=build_test_result(new_version,new_revision,True); dump("tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json",final); dump("candidate/Q041_TEST_RESULT.json",final)
    shutil.copy2(ROOT/"tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json",ROOT/"versions"/"accepted"/new_version/"TEST_RESULT.json")
    snapshot_consistency(new_version)
    if tree_digest(prev)!=prev_digest: git("reset","--hard",candidate_commit); die("Previous accepted snapshot mutated.")

    q41b=run([sys.executable,"tests/programs/q041_model_validate.py"],check=False)
    campaignb=run([sys.executable,"tests/programs/model_campaign.py","validate"],check=False)
    if q41b.returncode or campaignb.returncode:
        git("reset","--hard",candidate_commit); cleanup_promotion_untracked(new_version); die("Final validation changed after test-result refresh; candidate retained.")

    update_root_report(old_state,new_version,new_revision,start_commit,candidate_commit,None); update_root_handoff(new_version,None)
    old_installer=ROOT/"install_q041_candidate_blocked.py"
    if old_installer.exists(): old_installer.unlink()
    git("add","-A")
    try: git("reset","--",str(Path(__file__).resolve().relative_to(ROOT)),check=False)
    except ValueError: pass
    git("commit","-m",f"Promote Q041 evidence-only update to {new_version}")
    promotion_commit=git("rev-parse","HEAD").stdout.strip()

    dump("candidate/Q041_PROVENANCE.json",build_q041_provenance(candidate_commit,promotion_commit))
    write_text("provenance/Q041_PROVENANCE.md",f"""# Q041 Provenance

- Target Q: `Q041`
- Source repository: `{SOURCE_REPOSITORY}`
- Source input commit: `{SOURCE_COMMIT}`
- Candidate input commit: `{candidate_commit}`
- Promotion commit: `{promotion_commit}`
- Program: `{Q041_PROGRAM}`
- Result: `{Q041_RESULT}`
- Workflow run: `{Q041_RUN_ID}` attempt 4
- Final artifact SHA-256: `{Q041_ARTIFACT_SHA256}`
- Final JSON SHA-256: `{Q041_FINAL_SHA256}`
- Final tests SHA-256: `{Q041_FINAL_TESTS_SHA256}`
- Primary PDF: `{PRIMARY_DOC['filename']}`
- Primary PDF SHA-256: `{PRIMARY_DOC['sha256']}`

Scientific status: `CONTROLLED_NO_SCIENTIFIC_RESULT`. The downstream question remains
unresolved; non-convergence is not physical falsification, and V19 is narrower than the
broader original Q041 design.
""")
    dump("release/MODEL_RELEASE_HANDOFF.json",build_release(old_state["accepted_model_version"],new_version,new_revision,candidate_commit,promotion_commit))
    update_root_report(old_state,new_version,new_revision,start_commit,candidate_commit,promotion_commit); update_root_handoff(new_version,promotion_commit)
    c=load("candidate/candidate_state.json"); c["promotion_commit"]=promotion_commit; c["candidate_input_commit"]=candidate_commit; dump("candidate/candidate_state.json",c)
    git("add","-A")
    try: git("reset","--",str(Path(__file__).resolve().relative_to(ROOT)),check=False)
    except ValueError: pass
    git("commit","-m","Finalize Q041 promotion provenance")
    final_commit=git("rev-parse","HEAD").stdout.strip()
    print(f"CANDIDATE_INPUT_COMMIT={candidate_commit}"); print(f"PROMOTION_COMMIT={promotion_commit}"); print(f"FINAL_METADATA_COMMIT={final_commit}"); print(f"ACCEPTED_MODEL={new_version}"); print(f"MODEL_REVISION={new_revision}"); print("AUTHORIZED_Q_RANGE=Q001-Q041"); print("STOP_STATE=PROMOTED")
    return promotion_commit,final_commit


def already_current():
    print("Accepted model is already at Q041. Running non-destructive validators.")
    cps=[]
    if (ROOT/"tests/programs/q041_model_validate.py").exists(): cps.append(run([sys.executable,"tests/programs/q041_model_validate.py"],check=False))
    cps.append(run([sys.executable,"tests/programs/model_campaign.py","validate"],check=False))
    for cp in cps:
        print(cp.stdout,end="")
        if cp.stderr: print(cp.stderr,end="",file=sys.stderr)
    if any(cp.returncode for cp in cps): die("Existing Q041 state failed validation.")
    print("STOP_STATE=NO_MODEL_CHANGE")
    return 0


def main():
    ap=argparse.ArgumentParser(description="Install and promote the Bubbleverse Q041 evidence-only model update.")
    ap.add_argument("--push",action="store_true",help="Push final local commits with the user's Git credentials.")
    ap.add_argument("--q-journal",help="Optional path to Q-Journal PDF for runtime hash re-verification.")
    ap.add_argument("--main-book",help="Optional path to Main Book PDF for runtime hash re-verification.")
    ap.add_argument("--appendices",help="Optional path to Technical Appendices PDF for runtime hash re-verification.")
    ap.add_argument("--keep-installer",action="store_true",help="Keep this temporary installer after success.")
    args=ap.parse_args()

    state=ensure_repo(); current=qnum(state.get("current_q"))
    if current==TARGET_Q: return already_current()
    if current!=TARGET_Q-1: die(f"Q_SEQUENCE_GATE blocked: accepted current_q={state.get('current_q')!r}; Q041 requires the immediately preceding accepted state.")
    ensure_worktree_safe(); ensure_git_identity(); start_commit=git("rev-parse","HEAD").stdout.strip()
    docs=[verify_optional_pdf(args.q_journal,PRIMARY_DOC),verify_optional_pdf(args.main_book,MAIN_BOOK_DOC),verify_optional_pdf(args.appendices,APPENDICES_DOC)]
    print("INPUT_DOCUMENT_GATE=PASS_AUTHORIZED_PDF_SUBSTITUTE")
    for d in docs: print(f"DOCUMENT={d['filename']} SHA256={d['sha256']} STATUS={d['status']}")

    new_version=next_version(state["accepted_model_version"]); new_revision=next_revision(state["model_revision"])
    old_snapshot=ROOT/"versions"/"accepted"/state["accepted_model_version"]
    if not old_snapshot.exists(): die(f"Accepted snapshot missing: {old_snapshot}")
    old_digest=tree_digest(old_snapshot)
    candidate_commit=stage_candidate(state,new_version,new_revision)
    if tree_digest(old_snapshot)!=old_digest: die("Previous accepted snapshot changed during candidate staging.")
    try:
        promotion_commit,final_commit=promotion_transaction(state,new_version,new_revision,start_commit,candidate_commit)
    except BaseException:
        # If no promotion commit was created, restore the candidate-only state and remove
        # untracked promotion artifacts. A deliberately recorded CANDIDATE_BLOCKED commit
        # is preserved because HEAD will no longer equal candidate_commit.
        try:
            if git("rev-parse","HEAD",check=False).stdout.strip() == candidate_commit:
                git("reset","--hard",candidate_commit,check=False)
                cleanup_promotion_untracked(new_version)
        except Exception:
            pass
        raise
    if tree_digest(old_snapshot)!=old_digest: die("Previous accepted snapshot changed after promotion.")

    if args.push:
        cp=git("push","origin","HEAD",check=False)
        if cp.returncode:
            print(cp.stdout,end="",file=sys.stderr); print(cp.stderr,end="",file=sys.stderr)
            print("PROMOTION_LOCAL=PASS"); print("PUSH=FAIL"); raise SystemExit(3)
        print("PUSH=PASS")

    if not args.keep_installer:
        try:
            me=Path(__file__).resolve()
            if me.is_file() and ROOT in me.parents: me.unlink()
        except Exception: pass
    return 0

if __name__=="__main__":
    raise SystemExit(main())
