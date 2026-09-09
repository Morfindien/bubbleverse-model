# Bubbleverse Model

Autonomous, Q-bounded scientific synthesis, formalization, computation and falsification repository.

Bubbleverse Model is the version-controlled scientific model state derived from the Bubbleverse research process.

- `Morfindien/Bubbleverse` = scientific source repository, evidence, manuscripts, numerical results and Q-history.
- `Morfindien/bubbleverse-model` = accepted model, candidate model, formal model, tests, provenance and version history.

The model represents the best current compression of validated Bubbleverse evidence inside the authorized Q range. It is not established truth.

---

## Current State

- Mode: **INCREMENTAL_UPDATE — Q040 accepted**
- Authorized scientific range: **Q001–Q040**
- Current Q: **Q040**
- Accepted model: **v0.2**
- Model revision: **R000002**
- Candidate state: **promoted record retained**
- Formal model: **v0.2-formalization-1**
- Scientific campaign: **9 / 9 PASS**
- Formal-model validation: **12 / 12 PASS**
- Public system healthcheck: **20 / 20 PASS**
- Result context engine: **ACTIVE**
- External astronomy catalog context: **ACTIVE**
- Release status: **ALL_GREEN**
- Next Q: **AUTHORIZED**

---

# Quick Start Guide

Bubbleverse Model is designed so you normally do not need to work directly with repository files.

## Run the model

1. Open the `bubbleverse-model` repository.
2. Press **Actions**.
3. Select **🧪 BUBBLEVERSE MODEL — START**.
4. Press **Run workflow**.
5. Choose the operation you want.
6. Fill in the input field only if the selected operation requires input.
7. Press **Run workflow**.

Permanent public workflow:

```text
.github/workflows/00-bubbleverse-model-start-public.yml
```

---

## Main operations

### test

Runs the model healthcheck.

This operation is non-destructive.

It does not:

- promote a candidate
- modify accepted model state
- change model versions
- alter scientific content

Use this when you simply want to check whether the model is healthy.

---

### validate-model

Validates the current scientific and formal model.

This operation is non-destructive.

Use it when you want a direct validation of the current model state.

---

### model-status

Displays the current model state.

Use it when you want to see which model version and Q-range are currently active.

---

### contradictions

Displays registered unresolved contradictions, tensions and conflicts.

A contradiction is not automatically forced into a resolution.

It may remain open until later evidence resolves it.

---

### provenance

Displays model provenance information.

This is used to trace where scientific results and model state came from.

---

### release-handoff

Displays the canonical current release state.

Use it to inspect promotion status, accepted version and release gates.

---

### gaussian-tension

Calculates the tension between two values with independent Gaussian uncertainties.

Input:

```text
a,sigma_a,b,sigma_b
```

Example:

```text
73.50,0.81,67.24,0.35
```

---

### difference

Calculates the difference between two values.

Input:

```text
a,b
```

---

### percent-shift

Calculates the percentage change from one value to another.

Input:

```text
from,to
```

---

### weighted-mean

Calculates an inverse-variance weighted mean.

Input:

```text
value1,sigma1,value2,sigma2,...
```

---


### known-results

Looks up results already registered inside the current Bubbleverse Q-boundary.

Input may be blank to list everything, or:

```json
{"quantity":"H0"}
```

You may also specify units.

The registry is intentionally Q-bounded and is not a complete catalogue of scientific literature.

---

### contextualize-result

Compares a supplied result with comparable registered Bubbleverse reference results and recommends what should happen next.

Example:

```json
{"quantity":"H0","value":1150.0,"sigma":0.81,"units":"km s^-1 Mpc^-1"}
```

The result includes:

- registry match status
- registered reference span
- nearest registered comparison
- Gaussian distance when uncertainties are available
- follow-up priority
- recommended next steps
- who/what should execute each next step

Executor classes include:

```text
MODEL_CAN_EXECUTE
MODEL_CAN_DESIGN_TEST
HUMAN_INPUT_VERIFICATION_REQUIRED
RESEARCH_AGENT_OR_HUMAN_REQUIRED
HUMAN_OR_EXTERNAL_EXPERIMENT_REQUIRED
MODEL_UPDATE_PIPELINE_REQUIRED
```

Being outside the registered reference span is a reason to investigate. It is **not** automatically evidence for new physics.

---


### astronomy-catalog-context

Queries authoritative external astronomical catalogues for a named object or sky position.

Examples:

```json
{"object":"Vega","radius_arcsec":5}
```

or:

```json
{"ra_deg":279.2347,"dec_deg":38.7837,"radius_arcsec":5}
```

The engine currently cross-checks:

```text
SIMBAD
ESA Gaia DR3 Archive
VizieR / 2MASS All-Sky Point Source Catalogue
```

SIMBAD can resolve an object name to coordinates. Gaia DR3 and VizieR then perform positional cone searches.

External catalogue results are always:

```text
EXTERNAL_REFERENCE_ONLY
```

They do **not** automatically:

- expand the Q firewall
- become Bubbleverse evidence
- modify the accepted model
- promote a candidate
- imply new physics

If an external result is scientifically relevant, it must enter through the normal Bubbleverse evidence and model-update pipeline.

A catalogue service being unavailable is treated as a technical failure, not as evidence that an object does not exist.

---

### campaign

Runs the current scientific/model validation campaign and may write a validation record under `tests/results/`.

In the current implementation it does **not** promote a candidate, expand the Q boundary, or alter accepted scientific state. Scientific promotion belongs to the controlled model-update pipeline.

Use `test` for the complete non-destructive system healthcheck and `validate-model` for direct model validation.

---

# How Model Updates Work

Bubbleverse Model follows a controlled accepted/candidate workflow.

```text
NEW COMPLETED Q
        ↓
AUTHORIZED EVIDENCE
        ↓
MODEL DIFF
        ↓
CANDIDATE MODEL
        ↓
FORMAL MODEL SYNCHRONIZATION
        ↓
SCIENTIFIC TESTS
        ↓
FORMAL TESTS
        ↓
REGRESSION / INTEGRITY TESTS
        ↓
PROMOTION GATE
        ↓
ACCEPTED MODEL
        ↓
IMMUTABLE VERSION SNAPSHOT
```

Accepted model state is not supposed to be edited directly during scientific integration.

New evidence first enters the candidate state.

Only a successful promotion may create a new accepted model state.

---

# Accepted vs Candidate

## accepted/

Contains the current accepted scientific model.

This is the model state that has passed the required promotion gates.

## candidate/

Contains the proposed next model state and candidate history.

Candidate content is not automatically accepted science.

A candidate may:

- pass
- fail
- remain blocked
- be revised
- be rejected
- be superseded

---

# Scientific Q Firewall

Bubbleverse Model is Q-bounded.

The model may only use evidence inside the currently authorized Q range.

For the current baseline:

```text
AUTHORIZED:
Q001–Q040
```

Evidence beyond the authorized boundary must not influence:

- scientific claims
- parameters
- equations
- assumptions
- contradictions
- mechanisms
- predictions
- calculations
- benchmarks
- result registry
- candidate revisions

The Q boundary is expanded only through a controlled model update.

---

# How Results Should Be Interpreted

Bubbleverse Model deliberately distinguishes scientific status.

Examples:

```text
SUPPORTED
```

does not mean:

```text
PROVEN
```

A large tension does not automatically mean:

```text
NEW PHYSICS
```

A technical failure does not automatically mean:

```text
SCIENTIFIC FALSIFICATION
```

A candidate being the best tested option does not mean:

```text
CORRECT THEORY
```

Unknown quantities may remain:

```text
UNKNOWN
```

or:

```text
NOT_ESTABLISHED
```

Scientific incompleteness is preferable to fabricated certainty.

---

# Repository Structure

## accepted/

Current accepted scientific state.

## candidate/

Candidate/staging model and promotion history.

## model/

Machine-readable formal model.

Contains:

- parameters
- equations
- assumptions
- uncertainty
- benchmarks
- domain of validity
- limitations
- input schema
- output schema
- execution environment

## evidence/

Registered Bubbleverse evidence and Q-specific model updates.

## provenance/

Traceability from source material to model state.

## tests/

Scientific campaign, formal validation, integrity tests and regression tests.

## versions/accepted/

Immutable accepted-model snapshots.

## release/

Canonical release handoff.

## changelog/

Human-readable and machine-readable model change history.

---

# Model Capabilities

The current public model engine includes:

```text
test
gaussian-tension
difference
percent-shift
weighted-mean
known-results
contextualize-result
astronomy-catalog-context
validate-model
model-status
contradictions
provenance
release-handoff
campaign
```

New computational capabilities may be added as Bubbleverse expands into additional scientific domains.

A new calculation should not become public until its scientific definition, inputs, units, assumptions, provenance and tests are complete.

---

# Versioning

Accepted versions are frozen under:

```text
versions/accepted/
```

Previous accepted versions must remain immutable.

A successful promotion should preserve:

- model diff
- test results
- promotion status
- release state
- provenance
- accepted snapshot
- Git history

The purpose is to make every accepted model version reconstructable.

---

# Provenance and Reproducibility

A model change should be traceable through a chain like:

```text
Q
↓
SOURCE
↓
EVIDENCE
↓
PROGRAM / RESULT
↓
CANDIDATE CHANGE
↓
TESTS
↓
PROMOTION
↓
ACCEPTED VERSION
↓
GIT COMMIT
```

Where available, provenance may include:

- source file
- source repository commit
- file hash
- workflow ID
- GitHub run ID
- program ID
- result ID
- artifact hash
- model repository commit

---

# Known Limitations

Bubbleverse Model is incomplete by design.

Unknown quantities, unresolved contradictions and unsupported mechanisms remain explicit rather than being filled by assumption.

Detailed scientific limitations are maintained in:

```text
model/limitations.json
```

---

# Do Not

Do not manually modify frozen accepted snapshots.

Do not treat candidate state as accepted science.

Do not weaken tests simply to obtain a green result.

Do not insert evidence beyond the authorized Q boundary.

Do not silently delete unresolved contradictions.

Do not replace unknown values with plausible guesses.

Do not create duplicate root-level copies of canonical model or release files.

Do not overwrite scientific history when a conclusion changes.

Supersede it explicitly.

---

# Core Rule

Bubbleverse Model exists to maintain the best current scientific compression of authorized Bubbleverse evidence.

It does not exist to protect the current theory.

The model is allowed to:

- change
- weaken
- reject
- supersede
- reopen
- falsify
- destroy previous conclusions

when the evidence requires it.
