#!/usr/bin/env python3
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
