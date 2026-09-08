# Bubbleverse Model

Autonomous, Q-bounded scientific synthesis, formalization, computation and falsification repository.

## Current state
- Mode: **BOOTSTRAP_MODE — accepted baseline established**
- Authorized scientific range: **Q001–Q039**
- Current Q: **Q039**
- Accepted model: **v0.1**
- Candidate history: **v0.1-candidate → promoted to v0.1**
- Formal model: **v0.1-formalization-1**
- Scientific campaign: **9 / 9 PASS**
- Formal-model validation: **12 / 12 PASS**
- Release status: **ALL_GREEN**
- Next Q: **AUTHORIZED**

## Repository roles
- `accepted/` — current accepted scientific state.
- `candidate/` — candidate/staging state and promotion history.
- `model/` — machine-readable formal model: parameters, equations, assumptions, uncertainty, validity domains, limitations, benchmarks and I/O schemas.
- `evidence/` and `provenance/` — source and result traceability.
- `tests/` — scientific campaign, formal-model validation, regression and integrity tests.
- `versions/accepted/` — immutable accepted-model snapshots.
- `release/` — canonical release handoff.

## Start button
Open GitHub Actions → **🧪 BUBBLEVERSE MODEL — START** → **Run workflow**.

Permanent public workflow:
`.github/workflows/00-bubbleverse-model-start-public.yml`

The public `test` operation is non-destructive. `validate-model` validates the current model without promotion. `campaign` runs the explicit mutating campaign/promotion path.

The model represents the best current compression of validated Bubbleverse state inside the authorized Q range; it is not established truth and unresolved quantities remain explicit.
