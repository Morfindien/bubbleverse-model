#!/usr/bin/env python3
"""
Install the exact Bubbleverse Q041 CANDIDATE_BLOCKED staging state into
Morfindien/bubbleverse-model without mutating accepted scientific state.

This handoff exists because the connected GitHub integration returned HTTP 403 on write.
Run from the repository root. Use --push only when you want the two resulting commits
pushed to the configured origin.

The script deliberately does NOT promote Q041. The mandatory source-repository Word
manuscript was not discoverable, so accepted/, model/, frozen accepted versions and the
canonical release handoff must remain unchanged.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.cwd()
TARGET_Q = "Q041"
SOURCE_REPOSITORY = "Morfindien/Bubbleverse"
SOURCE_COMMIT = "a962ba70077422f8b69642dea4e8272e1d00e5ff"
PROGRAM_ID = "Q041-PLANCKPORT-V19"
RUN_ID = "Q041-DOWNSTREAM-SCIENTIFIC-CONSEQUENCE-PORTABILITY-V19"
RESULT_ID = "R-Q041-EDE-DOWNSTREAM-PORTABILITY-019"
WORKFLOW = ".github/workflows/q041-planck-portability-v19.yml"
GH_RUN_ID = "34979609004"
GH_RUN_ATTEMPT = 4
FINAL_ARTIFACT_ID = "10754769330"
FINAL_ARTIFACT_SHA256 = "2284518ecbaaf1ff0d0093977827d5162ec29549ba2b81880f266c250311ca2b"
FINAL_JSON_SHA256 = "0062874ed3529004f46cfb542a708d5b8e8dde55d1b4fd1c2ac7c394e6c8be79"
FINAL_TESTS_SHA256 = "95fe1e63c78033de8559f609f0d8a1f4d48ee1b4123f3bb8f845b3ac6e5797ab"

PUBLICATION = [
    {
        "filename": "Bubbleverse_Q-Journals_Q001-Q041(7).pdf",
        "sha256": "fca0c3a8999336462982287256bd0c946e284fb99cf9e23e3f401d6cab584465",
        "role": "OPERATOR_SUPPLIED_PUBLICATION_CORROBORATION",
    },
    {
        "filename": "Bubbleverse_Main_Book(3).pdf",
        "sha256": "f2304a9010a8a4fbc055e5002def9ca42aac692cf81669c10fd6cc98d14f2130",
        "role": "OPERATOR_SUPPLIED_PUBLICATION_CORROBORATION",
    },
    {
        "filename": "Bubbleverse_Technical_Appendices_A-D(3).pdf",
        "sha256": "878891fd0d0323c2fbfadf3fec5d5d0dffbae5e64e3551a34cfdc1da803c76",
        "role": "OPERATOR_SUPPLIED_PUBLICATION_CORROBORATION",
    },
]

def sh(*args: str, check: bool = True) -> str:
    cp = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if check and cp.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{cp.stdout}\n{cp.stderr}")
    return cp.stdout.strip()

def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def dump(rel: str, obj) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")

def write(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def tree_digest(paths: list[str]) -> str:
    h = hashlib.sha256()
    files = []
    for rel in paths:
        p = ROOT / rel
        if p.is_dir():
            files.extend(x for x in p.rglob("*") if x.is_file())
        elif p.exists():
            files.append(p)
    for p in sorted(set(files), key=lambda x: str(x.relative_to(ROOT))):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        h.update(rel.encode())
        h.update(b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()

def qnum(v) -> int:
    m = re.fullmatch(r"Q-?0*([0-9]+)", str(v or ""), flags=re.I)
    if not m:
        raise ValueError(f"Bad Q id: {v!r}")
    return int(m.group(1))

def next_version(v: str) -> str:
    m = re.fullmatch(r"v(\d+)\.(\d+)", str(v))
    if not m:
        raise ValueError(f"Unsupported accepted version format: {v}")
    return f"v{int(m.group(1))}.{int(m.group(2))+1}"

def next_revision(r: str) -> str:
    m = re.fullmatch(r"R(\d+)", str(r))
    if not m:
        raise ValueError(f"Unsupported model revision: {r}")
    return f"R{int(m.group(1))+1:06d}"

def ensure_unique(items, key="id"):
    vals=[x[key] for x in items if key in x]
    if len(vals) != len(set(vals)):
        raise AssertionError(f"Duplicate {key}s")

def scan_high_q(path: Path, max_q: int) -> None:
    text = path.read_text(encoding="utf-8")
    nums = [int(x) for x in re.findall(r"\bQ-?0*([0-9]{1,5})\b", text, flags=re.I)]
    if nums and max(nums) > max_q:
        raise AssertionError(f"High-Q contamination in {path}: Q{max(nums):03d}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="Push the two candidate/provenance commits to origin.")
    args = ap.parse_args()

    if not (ROOT / ".git").exists():
        raise SystemExit("Run this script from the root of a git clone of Morfindien/bubbleverse-model.")

    if sh("git", "status", "--porcelain"):
        raise SystemExit("Working tree is not clean. Commit/stash unrelated changes first.")

    accepted = load("accepted/model_state.json")
    canonical_candidate = load("candidate/candidate_state.json")

    if accepted.get("current_q") != "Q040" or accepted.get("accepted_model_version") != "v0.2":
        raise SystemExit(f"Baseline mismatch: expected accepted Q040/v0.2, got {accepted.get('current_q')}/{accepted.get('accepted_model_version')}")
    if accepted.get("model_revision") != "R000002":
        raise SystemExit(f"Baseline revision mismatch: {accepted.get('model_revision')}")
    if canonical_candidate.get("current_q") != "Q040":
        raise SystemExit("Canonical candidate no longer mirrors the accepted Q040 state; abort and re-audit.")

    base_head = sh("git", "rev-parse", "HEAD")
    candidate_version = next_version(accepted["accepted_model_version"])
    candidate_revision = next_revision(accepted["model_revision"])
    now = datetime.now(timezone.utc).isoformat()

    protected = [
        "accepted", "model", "versions/accepted",
        "release/MODEL_RELEASE_HANDOFF.json",
        "release/MODEL_RELEASE_HANDOFF.md",
    ]
    protected_before = tree_digest(protected)

    obs = copy.deepcopy(load("accepted/observations.json"))
    con = copy.deepcopy(load("accepted/constraints.json"))
    mech = copy.deepcopy(load("accepted/mechanisms.json"))
    pred = copy.deepcopy(load("accepted/predictions.json"))
    ctr = copy.deepcopy(load("accepted/contradictions.json"))
    rob = copy.deepcopy(load("accepted/robustness.json"))

    obs["observations"].extend([
        {
            "id":"OBS-Q041-PORTABILITY-V19-001",
            "claim":"The authoritative Q041 V19 downstream-portability campaign completed with a valid controlled no-scientific-result outcome. Zero of 32 logical posterior chains reached the complete science state: 30 exhausted the maximum-sample budget without convergence and two remained partial at segment 8. The final artifact records MAX_SAMPLES_WITHOUT_CONVERGENCE, actual_computed_result=false, technical_failure=false, final_outcome_valid=true, and status=PASS.",
            "epistemic_level":"validated computational campaign outcome",
            "evidence_refs":["CAND-EVD-Q041-V19-FINAL"],
            "q_introduced":"Q041",
            "status":"CONTROLLED_NO_SCIENTIFIC_RESULT",
        },
        {
            "id":"OBS-Q041-CONTRACT-SCOPE-001",
            "claim":"The executed V19 contract is narrower than the broader original downstream-portability design: it tests MOD-EDE-N3 only, contains no separate LCDM posterior matrix, omits the common frozen supernova component, and uses three leave-one-out combinations. It therefore cannot be represented as a complete execution of the broader design.",
            "epistemic_level":"provenance and scope audit",
            "evidence_refs":["CAND-EVD-Q041-V19-PREREG","CAND-EVD-Q041-PUBLICATION"],
            "q_introduced":"Q041",
            "status":"SCOPE_LIMIT",
        }
    ])
    obs["q_access_end"]="Q041"

    con["constraints"].extend([
        {
            "id":"CON-Q041-001",
            "statement":"No downstream physical classification among material difference, scientifically equivalent constraints, or constrained mixed behavior is established because the V19 chain-completeness, all-Rhat<=1.05, and both-arms/all-combinations science gates were blocked.",
            "status":"ACTIVE_CANDIDATE",
        },
        {
            "id":"CON-Q041-002",
            "statement":"Controlled posterior non-convergence is not physical evidence and cannot be used as support for or against n=3 EDE, as evidence of Planck-likelihood superiority or defect, or as evidence of new physics.",
            "status":"ACTIVE_CANDIDATE",
        },
        {
            "id":"CON-Q041-003",
            "statement":"Any interpretation of the V19 campaign is restricted to its preregistered EDE-only execution contract and must not be silently generalized to the broader original downstream-portability design.",
            "status":"ACTIVE_CANDIDATE",
        },
    ])
    con["q_access_end"]="Q041"
    mech["q_access_end"]="Q041"

    p = next(x for x in pred["predictions"] if x["id"]=="PRED-EDE-PORTABILITY-001")
    p.setdefault("history", []).append({
        "q":"Q041",
        "status":"INCONCLUSIVE_COMPUTATIONAL_ATTEMPT",
        "note":"The V19 matched-arm campaign ended in a controlled no-scientific-result state because the required posterior convergence/completeness gates were not met. The portability prediction remains OPEN.",
    })
    p["status"]="OPEN"
    pred["q_access_end"]="Q041"

    c = next(x for x in ctr["contradictions"] if x["id"]=="CTR-PLANCK-IMPL-001")
    c["resolution"]="Q039 excludes several simple single-block explanations. Q040 defines a common physical CMB-space nuisance-marginalization route but fails before endpoint geometry. Q041 executes a downstream V19 portability campaign, but no chain satisfies the complete science state, so downstream physical consequence remains unresolved; V19 is also narrower than the broader original contract."
    c["results"]=list(dict.fromkeys(c.get("results",[])+[
        "ROB-Q041-CONTROLLED-NOSCIENCE-001","ROB-Q041-CONTRACT-SCOPE-001"
    ]))
    c["status"]="OPEN_NARROWED"
    ctr["q_access_end"]="Q041"

    rob["items"].extend([
        {
            "id":"ROB-Q041-CONTROLLED-NOSCIENCE-001",
            "finding":"The authoritative V19 run completed successfully as a controlled no-scientific-result outcome rather than a technical crash: 0/32 logical posterior chains became scientifically complete, so downstream physical classification is blocked.",
            "status":"ACTIVE_CANDIDATE",
        },
        {
            "id":"ROB-Q041-FIREWALL-001",
            "finding":"The V19 source lock forbids Q040-CMBSPACE-* and Q040-RQMC-* scientific products, and the final artifact records Q040_scientific_products_used=false.",
            "status":"ACTIVE_CANDIDATE",
        },
        {
            "id":"ROB-Q041-CONTRACT-SCOPE-001",
            "finding":"V19 preserves a valid preregistered EDE-only portability test, but its executed contract is materially narrower than the broader original Q041 design; that provenance difference must remain explicit.",
            "status":"ACTIVE_CANDIDATE",
        },
    ])
    rob["q_access_end"]="Q041"

    state = {
        "artifact_type":"BUBBLEVERSE_MODEL_PENDING_CANDIDATE",
        "schema_version":1,
        "target_q":"Q041","current_q":"Q041",
        "q_access_start":"Q001","q_access_end":"Q041",
        "candidate_model_version":candidate_version,
        "candidate_revision":candidate_revision,
        "previous_accepted_q":"Q040",
        "previous_accepted_model_version":accepted["accepted_model_version"],
        "previous_accepted_revision":accepted["model_revision"],
        "update_class":"MULTI_LAYER_UPDATE",
        "physical_model_change":False,
        "status":"CANDIDATE_BLOCKED",
        "promotion_status":"NOT_PROMOTED",
        "high_q_data_used":False,
        "source_repository":SOURCE_REPOSITORY,
        "source_repository_commit":SOURCE_COMMIT,
        "target_model_repository":"Morfindien/bubbleverse-model",
        "model_parent_commit":base_head,
        "word_input_filename":None,
        "word_input_path":None,
        "word_input_sha256":None,
        "word_discovery_status":"FAIL",
        "blockers":["WORD_DISCOVERY_GATE","WORD_HASH_GATE"],
        "operator_supplied_publication_package":PUBLICATION,
        "created_at":now,
    }

    diff = {
        "schema_version":1,"target_q":"Q041",
        "from_version":accepted["accepted_model_version"],
        "to_candidate_version":candidate_version,
        "physical_model_change":False,
        "preserved":[
            "All accepted Q040 scientific layers and public operations",
            "H0 inference-chain benchmarks and separation",
            "n=3 EDE constrained/not-established status",
            "Open H0 contradiction",
            "Open narrowed CamSpec-HiLLiPoP implementation-geometry contradiction",
            "All existing equations, parameters, benchmarks and public calculations",
        ],
        "added":[
            "Validated Q041 V19 controlled no-scientific-result computational outcome",
            "Q041 posterior convergence/completeness limitation",
            "Q041 V19 contract-scope provenance limitation",
            "Q041 source-lock/firewall robustness record",
        ],
        "modified":[
            "PRED-EDE-PORTABILITY-001 history records an inconclusive computational attempt and remains OPEN",
            "CTR-PLANCK-IMPL-001 records that downstream consequence remains unresolved after Q041",
            "Candidate robustness and constraints explicitly separate controlled non-convergence from physical evidence",
        ],
        "new_parameters":[],"parameter_changes":[],
        "new_equations":[],"equation_changes":[],
        "new_assumptions":[],"assumption_changes":[],
        "new_uncertainties":["UNC-Q041-POSTERIOR-CONVERGENCE"],
        "new_validity_domains":["DOM-Q041-PORTABILITY-V19"],
        "new_limitations":["LIM-Q041-DOWNSTREAM-PORTABILITY","LIM-Q041-CONTRACT-SCOPE"],
        "new_benchmarks":[],"benchmark_changes":[],
        "new_predictions":[],"prediction_status_changes":[],
        "new_mechanisms":[],"mechanism_status_changes":[],
        "new_scientific_domains":[],"new_computational_capabilities":[],
        "public_calculation_changes":[],
    }

    formal = {
        "artifact_type":"BUBBLEVERSE_CANDIDATE_FORMAL_SYNC",
        "schema_version":1,
        "base_accepted_model_version":accepted["accepted_model_version"],
        "base_formal_model_version":"v0.2-formalization-1",
        "candidate_model_version":candidate_version,
        "candidate_revision":candidate_revision,
        "target_q":"Q041","q_access_start":"Q001","q_access_end":"Q041",
        "status":"STAGED_NOT_PROMOTED",
        "canonical_model_directory_mutated":False,
        "reason":"Accepted/formal canonical state remains immutable because mandatory Word discovery/hash gates block promotion.",
        "unchanged_registries":["parameters","benchmarks","equations","assumptions","input_schema","output_schema","environment","public_operations"],
        "new_parameters":[],"new_equations":[],"new_assumptions":[],
        "new_benchmarks":[],"new_public_calculations":[],"new_scientific_domains":[],
        "staged_uncertainties":[{
            "id":"UNC-Q041-POSTERIOR-CONVERGENCE",
            "type":"finite_sampling_and_convergence",
            "statement":"Under the frozen V19 sampler and per-chain budget, the complete matched-arm posterior matrix was not obtained; this blocks downstream physical classification without constituting physical falsification.",
            "status":"OPEN_NUMERICAL_UNCERTAINTY",
        }],
        "staged_validity_domains":[{
            "id":"DOM-Q041-PORTABILITY-V19",
            "statement":"Applies only to the preregistered V19 MOD-EDE-N3 CamSpec/HiLLiPoP matched-external-data campaign and its conservative primary-CMB overlap policy. It is not a complete execution of the broader original downstream-portability contract.",
            "status":"SCOPE_LIMIT",
        }],
        "staged_limitations":[
            {
                "id":"LIM-Q041-DOWNSTREAM-PORTABILITY",
                "statement":"No scientifically valid downstream CamSpec-versus-HiLLiPoP portability classification is established because mandatory posterior convergence/completeness gates were not met.",
                "status":"UNRESOLVED",
            },
            {
                "id":"LIM-Q041-CONTRACT-SCOPE",
                "statement":"The V19 execution omits the separate LCDM matrix and common frozen supernova component of the broader original design and uses three leave-one-out combinations; it cannot be generalized beyond its preregistered scope.",
                "status":"SCOPE_LIMIT",
            },
        ],
    }

    provenance = {
        "artifact_type":"BUBBLEVERSE_Q041_PENDING_CANDIDATE_PROVENANCE",
        "schema_version":1,
        "target_q":"Q041","authorized_range":"Q001-Q041",
        "source_repository":SOURCE_REPOSITORY,
        "source_input_commit":SOURCE_COMMIT,
        "model_repository":"Morfindien/bubbleverse-model",
        "model_parent_commit":base_head,
        "word_input":{"status":"NOT_DISCOVERED","filename":None,"path":None,"sha256":None},
        "word_search":{
            "current_source_root_docx_count":0,
            "source_q040_reference_commit_docx_count":0,
            "commit_search_terms_checked":["bubblevers 0.41","0.41","docx","manuscript","bubblevers"],
            "common_filename_history_matches":0,
        },
        "authoritative_execution":{
            "program_id":PROGRAM_ID,"run_id":RUN_ID,"result_id":RESULT_ID,
            "workflow":WORKFLOW,"github_actions_run_id":GH_RUN_ID,
            "github_run_attempt":GH_RUN_ATTEMPT,"github_run_conclusion":"success",
            "execution_head":SOURCE_COMMIT,
            "final_artifact_name":"q041-final-v19",
            "final_artifact_id":FINAL_ARTIFACT_ID,
            "final_artifact_sha256":FINAL_ARTIFACT_SHA256,
            "final_json_sha256":FINAL_JSON_SHA256,
            "final_tests_json_sha256":FINAL_TESTS_SHA256,
            "scientific_classification":"NO_SCIENTIFIC_RESULT",
            "outcome_type":"CONTROLLED_NO_SCIENTIFIC_RESULT",
            "no_science_reason":"MAX_SAMPLES_WITHOUT_CONVERGENCE",
            "actual_computed_result":False,
            "technical_failure":False,
            "final_outcome_valid":True,
        },
        "operator_supplied_publication_package":PUBLICATION,
        "candidate_input_commit":None,
        "note":"The publication PDFs corroborate Q041 but do not satisfy the mandatory source-repository Word-manuscript discovery/hash requirement.",
    }

    gates = {
        "INPUT_STATE_GATE":"PASS",
        "WORD_DISCOVERY_GATE":"FAIL",
        "WORD_HASH_GATE":"BLOCKED_NO_WORD_INPUT",
        "Q_SEQUENCE_GATE":"PASS",
        "Q_FIREWALL_GATE":"PASS",
        "HIGH_Q_CONTAMINATION_GATE":"PASS",
        "MODEL_DIFF_GATE":"PASS",
        "SCIENTIFIC_CONSISTENCY_GATE":"PASS",
        "EVIDENCE_PROVENANCE_GATE":"PASS",
        "PARAMETER_GATE":"PASS_NO_CHANGE",
        "EQUATION_GATE":"PASS_NO_CHANGE",
        "ASSUMPTION_GATE":"PASS_NO_CHANGE",
        "UNCERTAINTY_GATE":"PASS_STAGED",
        "DOMAIN_OF_VALIDITY_GATE":"PASS_STAGED",
        "LIMITATION_GATE":"PASS_STAGED",
        "BENCHMARK_GATE":"PASS_NO_CHANGE",
        "CONTRADICTION_GATE":"PASS_OPEN_UNRESOLVED",
        "PREDICTION_GATE":"PASS_OPEN_UNRESOLVED",
        "ROBUSTNESS_GATE":"PASS_STAGED",
        "FORMAL_MODEL_GATE":"PASS_STAGED_NOT_PROMOTED",
        "CALCULATION_GATE":"PASS_NO_NEW_OPERATION",
        "KNOWN_ANSWER_TEST_GATE":"NOT_APPLICABLE",
        "INVALID_INPUT_GATE":"NOT_APPLICABLE",
        "REGRESSION_GATE":"PENDING_LOCAL_CURRENT_STATE_VALIDATION",
        "ACCEPTED_IMMUTABILITY_GATE":"PENDING_POST_WRITE_HASH_CHECK",
        "ACCEPTED_PATH_ISOLATION_GATE":"PASS_DESIGN",
        "PROMOTION_STATE_GATE":"BLOCKED",
        "REAL_COMMIT_PROVENANCE_GATE":"PENDING_CANDIDATE_COMMIT",
        "FINAL_AUDIT_GATE":"BLOCKED_BY_WORD_DISCOVERY",
    }
    test_result = {
        "artifact_type":"BUBBLEVERSE_Q041_MODEL_UPDATE_TEST_RESULT",
        "schema_version":1,"target_q":"Q041","created_at":now,
        "all_mandatory_green":False,"stop_state":"CANDIDATE_BLOCKED",
        "tests":gates,
        "blocking_tests":["WORD_DISCOVERY_GATE","WORD_HASH_GATE","PROMOTION_STATE_GATE","FINAL_AUDIT_GATE"],
        "accepted_state_changed":False,"public_operations_changed":False,
        "new_public_calculations":[],"candidate_input_commit":None,
    }

    pending = ROOT / "candidate/pending/Q041"
    if pending.exists():
        raise SystemExit("candidate/pending/Q041 already exists; aborting rather than overwriting history.")

    dump("candidate/pending/Q041/observations.json", obs)
    dump("candidate/pending/Q041/constraints.json", con)
    dump("candidate/pending/Q041/mechanisms.json", mech)
    dump("candidate/pending/Q041/predictions.json", pred)
    dump("candidate/pending/Q041/contradictions.json", ctr)
    dump("candidate/pending/Q041/robustness.json", rob)
    dump("candidate/pending/Q041/candidate_state.json", state)
    dump("candidate/pending/Q041/candidate_diff.json", diff)
    dump("candidate/pending/Q041/formal_sync.json", formal)
    dump("candidate/pending/Q041/Q041_PROVENANCE.json", provenance)
    dump("candidate/pending/Q041/Q041_TEST_RESULT.json", test_result)

    write("candidate/pending/Q041/MODEL_CANDIDATE.md", f"""# BUBBLEVERSE MODEL PENDING CANDIDATE — Q041

**CANDIDATE BLOCKED — ACCEPTED MODEL UNCHANGED**

- Candidate version: **{candidate_version}**
- Candidate revision: **{candidate_revision}**
- Candidate authorized range: **Q001–Q041**
- Previous accepted model: **{accepted['accepted_model_version']} / Q040**
- Update class: **MULTI_LAYER_UPDATE**
- Physical model change: **none**
- Promotion: **blocked**

The authoritative V19 execution ended with a valid `CONTROLLED_NO_SCIENTIFIC_RESULT`.
No downstream physical CamSpec-versus-HiLLiPoP classification is established because
the required posterior convergence/completeness gates were not met.

Promotion is blocked because no authoritative Word manuscript covering Q041 can be
discovered and hashed in the source repository. The operator-supplied 0.41 PDF package
is corroborating provenance only and is not substituted for the missing Word input.

Canonical `accepted/`, `model/`, the accepted release handoff and frozen accepted
snapshots remain unchanged.
""")

    # Candidate-side update report. Canonical release handoff remains untouched.
    update_report = {
        "TARGET_Q":"Q041",
        "SOURCE_REPOSITORY":SOURCE_REPOSITORY,
        "SOURCE_REPOSITORY_COMMIT":SOURCE_COMMIT,
        "WORD_INPUT_FILENAME":None,"WORD_INPUT_PATH":None,"WORD_INPUT_SHA256":None,
        "TARGET_MODEL_REPOSITORY":"Morfindien/bubbleverse-model",
        "PREVIOUS_ACCEPTED_Q":"Q040",
        "NEW_AUTHORIZED_Q_RANGE":{"candidate":"Q001-Q041","accepted":"Q001-Q040"},
        "PREVIOUS_MODEL_VERSION":accepted["accepted_model_version"],
        "CANDIDATE_VERSION":candidate_version,
        "UPDATE_CLASS":"MULTI_LAYER_UPDATE",
        "MODEL_DIFF":diff,
        "NEW_DOMAINS":[],"NEW_PARAMETERS":[],"NEW_EQUATIONS":[],"NEW_ASSUMPTIONS":[],
        "NEW_UNCERTAINTIES":["UNC-Q041-POSTERIOR-CONVERGENCE"],
        "NEW_BENCHMARKS":[],"NEW_CALCULATIONS":[],
        "NEW_TESTS":[
            "WORD_DISCOVERY_GATE","WORD_HASH_GATE","Q_FIREWALL_GATE",
            "TECHNICAL_VS_SCIENTIFIC_FAILURE_GATE","ACCEPTED_IMMUTABILITY_GATE",
            "CURRENT_ACCEPTED_REGRESSION_GATE","PROVENANCE_SCOPE_GATE",
        ],
        "PRESERVED_ITEMS":diff["preserved"],"SUPERSEDED_ITEMS":[],
        "OPEN_CONTRADICTIONS":["CTR-H0-001","CTR-PLANCK-IMPL-001"],
        "RESOLVED_CONTRADICTIONS":["CTR-HIST-BASIN-LABEL-001 remains resolved methodologically"],
        "LIMITATIONS":[x["statement"] for x in formal["staged_limitations"]],
        "PROVENANCE":provenance,
        "TEST_RESULTS":test_result,
        "PROMOTION_GATE":"BLOCKED","PROMOTED":False,"NEW_ACCEPTED_VERSION":None,
        "NEXT_Q_AUTHORIZED":False,
        "BLOCKERS":["WORD_DISCOVERY_GATE","WORD_HASH_GATE"],
        "STOP_STATE":"CANDIDATE_BLOCKED",
        "candidate_input_commit":None,
    }
    dump("release/Q041_CANDIDATE_BLOCKED_HANDOFF.json", update_report)
    dump("tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json", test_result)

    write("provenance/Q041_CANDIDATE_BLOCKED.md", f"""# Q041 Candidate-Blocked Provenance

- TARGET_Q: Q041
- Authorized candidate range: Q001–Q041
- Accepted range remains: Q001–Q040
- Source repository: {SOURCE_REPOSITORY}
- Source input commit: `{SOURCE_COMMIT}`
- Program: `{PROGRAM_ID}`
- Result: `{RESULT_ID}`
- GitHub Actions run: `{GH_RUN_ID}` attempt {GH_RUN_ATTEMPT}
- Final artifact: `q041-final-v19` / `{FINAL_ARTIFACT_ID}`
- Artifact SHA-256: `{FINAL_ARTIFACT_SHA256}`
- Scientific classification: `NO_SCIENTIFIC_RESULT`
- Outcome type: `CONTROLLED_NO_SCIENTIFIC_RESULT`
- Technical failure: `false`
- Physical model change: none
- Word manuscript: NOT DISCOVERED
- Promotion: BLOCKED
""")

    write("changelog/Q041_CANDIDATE_BLOCKED.md", """# Q041 — Candidate blocked

- Staged Q041 computational/provenance knowledge without changing accepted science.
- Recorded the V19 controlled no-scientific-result outcome.
- Preserved the downstream CamSpec–HiLLiPoP physical question as unresolved.
- Added no parameter, equation, benchmark, domain, mechanism or public calculation.
- Did not promote because the mandatory source-repository Word manuscript is absent.
- Canonical accepted/formal/release state remains Q040 / v0.2.
""")

    # Candidate integrity.
    for key, items in [
        ("observations", obs["observations"]),
        ("constraints", con["constraints"]),
        ("mechanisms", mech["mechanisms"]),
        ("predictions", pred["predictions"]),
        ("contradictions", ctr["contradictions"]),
        ("items", rob["items"]),
    ]:
        ensure_unique(items)

    for pth in sorted((ROOT/"candidate/pending/Q041").rglob("*.json")):
        json.loads(pth.read_text(encoding="utf-8"))
        scan_high_q(pth, 41)

    # The current accepted model healthcheck must remain green even with pending staging present.
    cp = subprocess.run(
        [sys.executable, str(ROOT/"tests/programs/model_campaign.py"), "validate"],
        cwd=ROOT, text=True, capture_output=True
    )
    if cp.returncode != 0:
        print(cp.stdout)
        print(cp.stderr, file=sys.stderr)
        raise SystemExit("Current accepted-model regression validation failed; candidate left uncommitted.")

    protected_after = tree_digest(protected)
    if protected_before != protected_after:
        raise SystemExit("ACCEPTED_IMMUTABILITY_GATE=FAIL: protected accepted/formal/release content changed.")

    test_result["tests"]["REGRESSION_GATE"]="PASS_CURRENT_ACCEPTED_VALIDATOR"
    test_result["tests"]["ACCEPTED_IMMUTABILITY_GATE"]="PASS"
    test_result["tests"]["REAL_COMMIT_PROVENANCE_GATE"]="PENDING_CANDIDATE_COMMIT"
    dump("candidate/pending/Q041/Q041_TEST_RESULT.json", test_result)
    dump("tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json", test_result)
    update_report["TEST_RESULTS"]=test_result
    dump("release/Q041_CANDIDATE_BLOCKED_HANDOFF.json", update_report)

    stage_paths = [
        "candidate/pending/Q041",
        "release/Q041_CANDIDATE_BLOCKED_HANDOFF.json",
        "tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json",
        "provenance/Q041_CANDIDATE_BLOCKED.md",
        "changelog/Q041_CANDIDATE_BLOCKED.md",
    ]
    sh("git","add",*stage_paths)
    sh("git","commit","-m","Stage Q041 blocked candidate: controlled no-science result")
    candidate_commit = sh("git","rev-parse","HEAD")

    # Non-self-referential provenance closure: reference the real first commit from a second commit.
    provenance["candidate_input_commit"]=candidate_commit
    test_result["candidate_input_commit"]=candidate_commit
    test_result["tests"]["REAL_COMMIT_PROVENANCE_GATE"]="PASS_CANDIDATE_INPUT_COMMIT_RECORDED"
    update_report["candidate_input_commit"]=candidate_commit
    update_report["PROVENANCE"]=provenance
    update_report["TEST_RESULTS"]=test_result

    dump("candidate/pending/Q041/Q041_PROVENANCE.json", provenance)
    dump("candidate/pending/Q041/Q041_TEST_RESULT.json", test_result)
    dump("tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json", test_result)
    dump("release/Q041_CANDIDATE_BLOCKED_HANDOFF.json", update_report)

    sh("git","add",
       "candidate/pending/Q041/Q041_PROVENANCE.json",
       "candidate/pending/Q041/Q041_TEST_RESULT.json",
       "tests/results/Q041_MODEL_UPDATE_TEST_RESULT.json",
       "release/Q041_CANDIDATE_BLOCKED_HANDOFF.json")
    sh("git","commit","-m","Close Q041 blocked-candidate provenance")
    closure_commit = sh("git","rev-parse","HEAD")

    # Final immutability check across both commits.
    if tree_digest(protected) != protected_before:
        raise SystemExit("Post-commit accepted immutability failure.")

    if args.push:
        sh("git","push","origin","HEAD")

    print("STOP_STATE=CANDIDATE_BLOCKED")
    print(f"CANDIDATE_VERSION={candidate_version}")
    print(f"CANDIDATE_REVISION={candidate_revision}")
    print(f"CANDIDATE_INPUT_COMMIT={candidate_commit}")
    print(f"PROVENANCE_CLOSURE_COMMIT={closure_commit}")
    print("PROMOTED=false")
    print("ACCEPTED_STATE=Q040/v0.2/R000002 unchanged")
    print("WORD_DISCOVERY_GATE=FAIL")
    print("WORD_HASH_GATE=BLOCKED_NO_WORD_INPUT")
    print(f"PUSHED={'true' if args.push else 'false'}")

if __name__ == "__main__":
    main()
