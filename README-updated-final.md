# Bubbleverse Model

Autonomous, Q-bounded scientific synthesis, formalization, computation, contextualization and falsification repository.

Bubbleverse Model is the version-controlled scientific model state derived from the Bubbleverse research process.

- `Morfindien/Bubbleverse` = scientific source repository, evidence, manuscripts, numerical results and Q-history.
- `Morfindien/bubbleverse-model` = accepted model, candidate model, formal model, tests, provenance, contextualization and version history.

The model represents the best current compression of validated Bubbleverse evidence inside the authorized Q range.

It is not established truth.

Unknowns remain explicit.

Unexpected results are investigated rather than automatically promoted into new physics.

---

## Current State

- Mode: **BOOTSTRAP_MODE — accepted baseline established**
- Authorized scientific range: **Q001–Q039**
- Current Q: **Q039**
- Accepted model: **v0.1**
- Candidate history: **v0.1-candidate → promoted to v0.1**
- Formal model: **v0.1-formalization-3**
- Scientific campaign: **9 / 9 PASS**
- Formal-model validation: **12 / 12 PASS**
- Public system healthcheck: **SELF-001 → SELF-020**
- Result context engine: **ACTIVE**
- External astronomy catalog context: **ACTIVE**
- Release status: **ALL_GREEN**
- Next Q: **AUTHORIZED**

The Q039 baseline is complete and ready for automatic future model updates.

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
8. Open the generated artifact to inspect the complete result.

Permanent public workflow:

```text
.github/workflows/00-bubbleverse-model-start-public.yml
```

---

# Main Operations

## test

Runs the complete model healthcheck.

This operation is non-destructive.

It checks the current repository/model system, including:

- repository structure
- Q firewall
- JSON/schema integrity
- mathematical operations
- model readers
- scientific/model validation
- accepted-model immutability
- accepted-path isolation
- promotion consistency
- Git provenance
- known-result contextualization
- external astronomy catalog configuration

It does not:

- promote a candidate
- modify accepted model state
- change model versions
- alter scientific conclusions

Use this when you simply want to know:

```text
Is the model healthy?
```

---

## validate-model

Validates the current scientific and formal model.

This operation is non-destructive.

Use it when you want direct validation without running a promotion campaign.

---

## model-status

Displays the current accepted and candidate model state.

Use it to inspect:

- current Q
- authorized Q boundary
- accepted model version
- candidate state

---

## contradictions

Displays registered unresolved contradictions, tensions and conflicts.

A contradiction is not automatically forced into a resolution.

It may remain open until later evidence resolves it.

---

## provenance

Displays registered model provenance.

Use this when you want to trace where Bubbleverse model information came from.

---

## release-handoff

Displays the canonical current release state.

Use it to inspect:

- promotion state
- accepted version
- release gates
- model repository provenance

---

# Mathematical Operations

## gaussian-tension

Calculates the tension between two values with independent Gaussian uncertainties.

Input:

```text
a,sigma_a,b,sigma_b
```

Example:

```text
73.50,0.81,67.24,0.35
```

The operation returns:

- difference
- absolute difference
- combined Gaussian uncertainty
- tension in sigma

A large Gaussian tension is not by itself evidence of new physics.

---

## difference

Calculates the difference between two values.

Input:

```text
a,b
```

---

## percent-shift

Calculates the percentage change from one value to another.

Input:

```text
from,to
```

---

## weighted-mean

Calculates an inverse-variance weighted mean.

Input:

```text
value1,sigma1,value2,sigma2,...
```

The operation assumes the supplied measurements are suitable for that combination.

---

# Result Context Engine

Bubbleverse Model can compare a supplied result against known results already registered inside the authorized Bubbleverse model state.

This contextualization layer does not alter the underlying calculation.

A calculation can be mathematically valid while its scientific context is unusual.

---

## known-results

Lists results already registered inside the current Bubbleverse Q-boundary.

Example:

```json
{"quantity":"H0"}
```

Optional unit filtering:

```json
{"quantity":"H0","units":"km s^-1 Mpc^-1"}
```

The current registry derives its reference values from canonical model sources instead of manually duplicating them.

The registry is intentionally Q-bounded.

It is not a complete catalogue of all scientific literature.

---

## contextualize-result

Compares a supplied result with comparable registered Bubbleverse results.

Example:

```json
{
  "quantity":"H0",
  "value":1150.0,
  "sigma":0.81,
  "units":"km s^-1 Mpc^-1"
}
```

The result may include:

```text
registry_match_status
span_status
comparison_status
nearest_registered_result
registered_reference_span
follow_up_recommended
follow_up_priority
next_steps
new_physics_claim
```

Typical classifications include:

```text
WITHIN_REGISTERED_REFERENCE_SPAN
OUTSIDE_REGISTERED_REFERENCE_SPAN
UNREGISTERED_QUANTITY
NO_COMPARABLE_REGISTERED_RESULT
```

Important:

```text
OUTSIDE_REGISTERED_REFERENCE_SPAN
```

does **not** mean:

```text
NEW PHYSICS
```

The registered span is a reference span, not a physical allowed range.

An unusual result is a reason to investigate further.

---

# Next-Step Router

When a result needs follow-up, Bubbleverse Model can classify what should happen next.

Possible executor classes include:

```text
MODEL_CAN_EXECUTE
MODEL_CAN_DESIGN_TEST
HUMAN_INPUT_VERIFICATION_REQUIRED
RESEARCH_AGENT_OR_HUMAN_REQUIRED
HUMAN_OR_EXTERNAL_EXPERIMENT_REQUIRED
MODEL_UPDATE_PIPELINE_REQUIRED
```

Examples:

## MODEL_CAN_EXECUTE

The model can perform the next calculation or registry comparison itself.

## MODEL_CAN_DESIGN_TEST

The model can construct a reproduction, falsification or systematic-error test.

## HUMAN_INPUT_VERIFICATION_REQUIRED

A human should verify input meaning, units, uncertainty, target identity or provenance.

## RESEARCH_AGENT_OR_HUMAN_REQUIRED

External literature, databases or scientific sources should be checked.

## HUMAN_OR_EXTERNAL_EXPERIMENT_REQUIRED

The next step requires new empirical evidence, observation, measurement, laboratory work or instrument data.

## MODEL_UPDATE_PIPELINE_REQUIRED

External information may be relevant, but it must enter through the normal Bubbleverse evidence and model-update process before it becomes model knowledge.

---

# Astronomy Catalog Context

Bubbleverse Model can perform live read-only cross-checks against authoritative astronomical catalog services.

Operation:

```text
astronomy-catalog-context
```

---

## Search by object name

Example:

```json
{
  "object":"Vega",
  "radius_arcsec":5
}
```

SIMBAD can resolve the object name to sky coordinates.

The resolved position can then be cross-checked against additional catalogues.

---

## Search by coordinates

Example:

```json
{
  "ra_deg":279.2347,
  "dec_deg":38.7837,
  "radius_arcsec":5
}
```

Coordinates are interpreted in the ICRS frame.

---

## External catalogues

The current astronomy context engine uses:

### SIMBAD

Used for:

- object identity
- object names
- coordinates
- object type
- selected measurements
- bibliography context

### ESA Gaia DR3 Archive

Used for available Gaia DR3 information such as:

- position
- parallax
- proper motion
- photometry
- radial velocity where available

### VizieR / 2MASS

Used as an additional independent positional and near-infrared catalogue cross-check through the 2MASS All-Sky Point Source Catalogue.

---

# External Data Safety Rule

External catalogue results are always classified as:

```text
EXTERNAL_REFERENCE_ONLY
```

They do not automatically:

- become accepted Bubbleverse evidence
- modify the accepted model
- modify candidate scientific state
- expand the authorized Q boundary
- promote a candidate
- create a new model version
- establish new physics

If external data become scientifically relevant, the normal path is:

```text
EXTERNAL RESULT
        ↓
SOURCE / PROVENANCE CHECK
        ↓
BUBBLEVERSE EVIDENCE
        ↓
AUTHORIZED Q
        ↓
CANDIDATE MODEL UPDATE
        ↓
TESTS
        ↓
PROMOTION GATE
        ↓
ACCEPTED MODEL
```

---

# External Service Failure Rule

A catalogue service being unavailable is a technical condition.

For example:

```text
UNAVAILABLE
```

does not mean:

```text
NO_CATALOG_MATCH
```

and certainly does not mean:

```text
OBJECT DOES NOT EXIST
```

Bubbleverse keeps technical failure separate from scientific interpretation.

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
        ↓
REPOSITORY CLEANUP
```

Accepted model state is not supposed to be edited directly during scientific integration.

New scientific evidence first enters the candidate state.

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

The model may only use scientific evidence inside the currently authorized Q range.

Current baseline:

```text
AUTHORIZED:
Q001–Q039
```

Evidence beyond the authorized boundary must not silently influence:

- scientific claims
- parameters
- equations
- assumptions
- contradictions
- mechanisms
- predictions
- accepted benchmarks
- candidate revisions
- model promotion

The Q boundary is expanded only through a controlled model update.

Live external catalogue context does not expand the firewall.

---

# How Results Should Be Interpreted

Bubbleverse Model deliberately distinguishes scientific status.

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

A catalogue no-match does not automatically mean:

```text
NEW OBJECT
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
- result registry
- external astronomy catalog registry
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

# Public Model Capabilities

The current public engine includes:

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

Installation or maintenance operations may also temporarily exist in the workflow when required.

New computational capabilities may be added as Bubbleverse expands into additional scientific domains.

A new capability should not become part of the normal public model surface until its:

- definition
- inputs
- units
- assumptions
- provenance rules
- failure semantics
- regression tests

are complete.

---

# Campaign

## campaign

Runs the explicit model campaign.

This operation may modify model state and may promote a candidate when all mandatory gates pass.

Do not use `campaign` if you only want to inspect the model.

Use:

```text
test
```

or:

```text
validate-model
```

instead.

---

# Versioning

Accepted versions are frozen under:

```text
versions/accepted/
```

Previous accepted versions must remain immutable.

A successful promotion should preserve:

- model diff
- evidence references
- test results
- promotion status
- release state
- provenance
- accepted snapshot
- Git history

The goal is to make every accepted model version reconstructable.

---

# Provenance and Reproducibility

A scientific model change should be traceable through a chain like:

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

Live catalogue lookups remain external context until explicitly admitted through this chain.

---

# Known Limitations

Bubbleverse Model is incomplete by design.

Unknown quantities, unresolved contradictions and unsupported mechanisms remain explicit rather than being filled by assumption.

The internal known-result registry is Q-bounded and therefore incomplete by design.

External astronomy catalogues are not guaranteed to contain every object, every measurement or every relevant scientific result.

Catalogue coverage, epochs, selection functions, identifiers and measurement definitions may differ.

Detailed model limitations are maintained in:

```text
model/limitations.json
```

---

# Do Not

Do not manually modify frozen accepted snapshots.

Do not treat candidate state as accepted science.

Do not weaken tests simply to obtain a green result.

Do not insert scientific evidence beyond the authorized Q boundary.

Do not silently delete unresolved contradictions.

Do not replace unknown values with plausible guesses.

Do not treat an external catalogue result as automatically accepted evidence.

Do not treat an unavailable external service as a scientific no-match.

Do not treat a catalogue no-match as evidence of new physics.

Do not create duplicate root-level copies of canonical model or release files.

Do not overwrite scientific history when a conclusion changes.

Supersede it explicitly.

---

# Core Rule

Bubbleverse Model exists to maintain the best current scientific compression of authorized Bubbleverse evidence.

It does not exist to protect the current theory.

It does not exist to manufacture certainty.

The model is allowed to:

- change
- weaken
- reject
- supersede
- reopen
- falsify
- destroy previous conclusions

when the evidence requires it.

When a result lies outside what the model currently knows, the correct response is:

```text
INVESTIGATE
```

not automatically:

```text
NEW PHYSICS
```
