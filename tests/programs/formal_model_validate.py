#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "model"
REQUIRED_FILES = [
    "model_manifest.json",
    "parameters.json",
    "equations.json",
    "assumptions.json",
    "uncertainty.json",
    "domain_of_validity.json",
    "limitations.json",
    "input_schema.json",
    "output_schema.json",
    "benchmarks.json",
    "environment.json",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def qnum(value):
    m = re.fullmatch(r"Q-?0*([0-9]{1,5})", str(value), flags=re.I)
    return int(m.group(1)) if m else None


def ids(items):
    return [x["id"] for x in items]


def run_tests():
    tests = []

    def check(tid, name, fn):
        try:
            detail = fn()
            tests.append({"test_id": tid, "name": name, "status": "PASS", "detail": detail})
        except Exception as exc:
            tests.append({"test_id": tid, "name": name, "status": "FAIL", "detail": f"{type(exc).__name__}: {exc}"})

    def files_and_json():
        missing = [x for x in REQUIRED_FILES if not (MODEL / x).exists()]
        if missing:
            raise AssertionError(f"Missing formal model files: {missing}")
        for name in REQUIRED_FILES:
            load(MODEL / name)
        return {"files_parsed": len(REQUIRED_FILES)}
    check("FML-001", "Formal model files exist and parse", files_and_json)

    def boundary():
        state = load(ROOT / "accepted/model_state.json")
        manifest = load(MODEL / "model_manifest.json")
        for key in ("q_access_start", "q_access_end", "current_q"):
            if manifest.get(key) != state.get(key):
                raise AssertionError(f"{key} mismatch: model={manifest.get(key)} accepted={state.get(key)}")
        start, end, cur = map(qnum, [manifest["q_access_start"], manifest["q_access_end"], manifest["current_q"]])
        if None in (start, end, cur) or not start <= cur <= end:
            raise AssertionError("Invalid formal-model Q boundary")
        text = " ".join((MODEL / x).read_text(encoding="utf-8") for x in REQUIRED_FILES)
        high = [int(x) for x in re.findall(r"\bQ-?0*([0-9]{1,5})\b", text, flags=re.I) if int(x) > end]
        if high:
            raise AssertionError(f"High-Q contamination in formal model: {sorted(set(high))[:10]}")
        return {"q_access_start": start, "current_q": cur, "q_access_end": end}
    check("FML-002", "Q boundary and contamination firewall", boundary)

    def benchmarks():
        obs = load(ROOT / "accepted/observations.json")["observations"]
        by_obs = {x["id"]: x for x in obs}
        b = load(MODEL / "benchmarks.json")["benchmarks"]
        for item in b:
            src = by_obs[item["source_observation_id"]]
            for key in ("value", "sigma", "units", "inference_chain"):
                if item.get(key) != src.get(key):
                    raise AssertionError(f"Benchmark {item['id']} disagrees with {item['source_observation_id']} on {key}")
        if len(b) != 3:
            raise AssertionError(f"Expected three active H0 benchmarks, got {len(b)}")
        return {"benchmarks_verified": len(b)}
    check("FML-003", "Benchmarks exactly match accepted observations", benchmarks)

    def parameters():
        p = load(MODEL / "parameters.json")["parameters"]
        pids = ids(p)
        if len(pids) != len(set(pids)):
            raise AssertionError("Duplicate parameter IDs")
        b_ids = set(ids(load(MODEL / "benchmarks.json")["benchmarks"]))
        for item in p:
            for ref in item.get("benchmark_refs", []):
                if ref not in b_ids:
                    raise AssertionError(f"Unknown benchmark ref {ref}")
            if item.get("value_status") == "NOT_ESTABLISHED_THROUGH_Q039" and item.get("value") is not None:
                raise AssertionError(f"Unknown parameter {item['id']} must have null value")
        n3 = next((x for x in p if x["id"] == "PAR-EDE-N-SCF"), None)
        if not n3 or n3.get("value") != 3:
            raise AssertionError("n_scf=3 formalization missing")
        return {"parameters_verified": len(p)}
    check("FML-004", "Parameter registry integrity", parameters)

    def equations():
        equations = load(MODEL / "equations.json")["equations"]
        assumptions = set(ids(load(MODEL / "assumptions.json")["assumptions"]))
        ops = set(load(MODEL / "input_schema.json")["operations"])
        eids = ids(equations)
        if len(eids) != len(set(eids)):
            raise AssertionError("Duplicate equation IDs")
        for eq in equations:
            for ref in eq.get("assumption_refs", []):
                if ref not in assumptions:
                    raise AssertionError(f"Equation {eq['id']} has unknown assumption ref {ref}")
            op = eq.get("implementation_operation")
            if op and op not in ops:
                raise AssertionError(f"Equation {eq['id']} operation {op} absent from input schema")
        required = {"difference", "gaussian-tension", "percent-shift", "weighted-mean"}
        implemented = {x.get("implementation_operation") for x in equations}
        if not required <= implemented:
            raise AssertionError(f"Missing implemented equations for {sorted(required-implemented)}")
        return {"equations_verified": len(equations)}
    check("FML-005", "Equation-to-assumption and operation references", equations)

    def uncertainty():
        b = {x["id"]: x for x in load(MODEL / "benchmarks.json")["benchmarks"]}
        u = load(MODEL / "uncertainty.json")["uncertainties"]
        for item in u:
            ref = item.get("benchmark_ref")
            if ref:
                if ref not in b:
                    raise AssertionError(f"Unknown uncertainty benchmark ref {ref}")
                if item.get("sigma") != b[ref].get("sigma") or item.get("units") != b[ref].get("units"):
                    raise AssertionError(f"Uncertainty {item['id']} disagrees with benchmark {ref}")
        kinds = {x.get("type") for x in u}
        for required in ("inference_uncertainty", "optimization_globality", "likelihood_implementation_dependence"):
            if required not in kinds:
                raise AssertionError(f"Missing uncertainty type {required}")
        return {"uncertainties_verified": len(u)}
    check("FML-006", "Uncertainty registry and benchmark consistency", uncertainty)

    def assumptions_domains():
        assumptions = load(MODEL / "assumptions.json")["assumptions"]
        domains = load(MODEL / "domain_of_validity.json")["domains"]
        if not any(x["id"] == "ASSUMP-INDEPENDENT-GAUSSIAN" for x in assumptions):
            raise AssertionError("Independent-Gaussian assumption missing")
        if not any(x["id"] == "DOM-Q039-INTERVENTIONS" for x in domains):
            raise AssertionError("Q039 domain-of-validity boundary missing")
        if not any("not" in x.get("statement", "").lower() for x in domains):
            raise AssertionError("Domain registry lacks explicit exclusion language")
        return {"assumptions": len(assumptions), "domains": len(domains)}
    check("FML-007", "Assumptions and domain-of-validity are explicit", assumptions_domains)

    def limitations():
        lim = load(MODEL / "limitations.json")["limitations"]
        text = json.dumps(lim).lower()
        required = ["hubble", "dark matter", "late-time acceleration", "q039"]
        if not all(x in text for x in required):
            raise AssertionError("Required unresolved limitations are not explicit")
        if not all(x.get("status") in {"OPEN", "UNRESOLVED", "SCOPE_LIMIT"} for x in lim):
            raise AssertionError("Limitation statuses must remain open/unresolved/scope-limited")
        return {"limitations_verified": len(lim)}
    check("FML-008", "Unknowns and limitations remain explicit", limitations)

    def schemas():
        inp = load(MODEL / "input_schema.json")
        out = load(MODEL / "output_schema.json")
        required = {"test", "gaussian-tension", "difference", "percent-shift", "weighted-mean", "validate-model", "model-status", "contradictions", "provenance", "release-handoff", "campaign"}
        if not required <= set(inp["operations"]):
            raise AssertionError(f"Input schema missing operations: {sorted(required-set(inp['operations']))}")
        if set(out["calculation_result_types"]) != {"difference", "gaussian-tension", "percent-shift", "weighted-mean"}:
            raise AssertionError("Output calculation result types do not match calculator surface")
        workflow = ROOT / ".github/workflows/00-bubbleverse-model-start-public.yml"
        if not workflow.exists():
            raise AssertionError("Public Bubbleverse start workflow is missing")
        workflow_text = workflow.read_text(encoding="utf-8")
        absent = [op for op in required if f"- {op}" not in workflow_text]
        if absent:
            raise AssertionError(f"Input schema advertises operations absent from public workflow: {sorted(absent)}")
        return {"operations": len(inp["operations"]), "calculation_result_types": len(out["calculation_result_types"]), "workflow_surface_verified": True}
    check("FML-009", "Input/output schemas cover the public engine", schemas)

    def provenance():
        manifest = load(MODEL / "model_manifest.json")
        ev = load(ROOT / "evidence/evidence_registry.json")["entries"]
        eids = {x["evidence_id"] for x in ev}
        missing = [x for x in manifest.get("evidence_refs", []) if x not in eids]
        if missing:
            raise AssertionError(f"Missing evidence refs: {missing}")
        return {"evidence_refs_verified": len(manifest.get("evidence_refs", []))}
    check("FML-010", "Formal model provenance references exist", provenance)

    def environment():
        env = load(MODEL / "environment.json")
        sha = str(env.get("model_repository_commit", ""))
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise AssertionError(f"Invalid model repository SHA {sha!r}")
        subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if env.get("calculator_dependency_profile") != "PYTHON_STANDARD_LIBRARY_ONLY":
            raise AssertionError("Unexpected calculator dependency profile")
        return {"reachable_commit": sha, "runtime": env.get("validated_runtime")}
    check("FML-011", "Execution environment and Git provenance", environment)

    def no_claim_invention():
        manifest = load(MODEL / "model_manifest.json")
        if manifest.get("scientific_change") is not False:
            raise AssertionError("Formalization must declare scientific_change=false")
        if manifest.get("formalization_rule") != "NO_NEW_SCIENTIFIC_CLAIMS_OR_NUMERIC_VALUES":
            raise AssertionError("Formalization anti-invention rule missing")
        return {"scientific_change": False, "rule": manifest["formalization_rule"]}
    check("FML-012", "No-new-claim formalization contract", no_claim_invention)

    passed = sum(x["status"] == "PASS" for x in tests)
    return {
        "artifact_type": "BUBBLEVERSE_FORMAL_MODEL_TEST_RESULT",
        "formal_test_campaign": "FORMAL-MODEL-v0.1-001",
        "tests_total": len(tests),
        "tests_passed": passed,
        "tests_failed": len(tests) - passed,
        "all_green": passed == len(tests),
        "tests": tests,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-result", action="store_true")
    args = ap.parse_args()
    result = run_tests()
    for t in result["tests"]:
        print(f"{t['test_id']}={t['status']} {t['name']} — {t['detail']}")
    print(f"FORMAL_MODEL_TESTS={result['tests_passed']}/{result['tests_total']}")
    if args.write_result:
        p = ROOT / "tests/results/FORMAL-MODEL-v0.1-001.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raise SystemExit(0 if result["all_green"] else 1)


if __name__ == "__main__":
    main()
