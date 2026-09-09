# BUBBLEVERSE MODEL CHANGELOG

## R000001 — 2026-09-08 10:25 CEST
- Authorized range: Q001–Q039.
- Entered BOOTSTRAP_MODE because no accepted model existed.
- Constructed v0.1-candidate from the Q-bounded Word manuscript and authorized Q039 source-repository provenance.
- Q039 narrows the CamSpec–HiLLiPoP explanation space: tested calibration, off-diagonal precision, combined calibration+precision, and native foreground-profile freedom are insufficient single explanations.
- Q039 does not establish a physical defect, EDE verdict, or new physics.
- Preregistered 9 mandatory bootstrap integration/regression tests.
- Candidate NOT promoted pending `test`.
- NEXT_WORD_AUTHORIZED = false.

## R000002 — automatic campaign promotion
- 9/9 mandatory tests PASS.
- v0.1-candidate promoted to accepted v0.1.
- NEXT_WORD_AUTHORIZED = true.

## R000003 — model integrity repair
- Corrected accepted layer paths from mutable candidate/ paths to accepted/ paths.
- Added explicit candidate promotion state for v0.1.
- Replaced placeholder model-repository provenance with a real reachable Git commit.
- Patched campaign promotion logic so these integrity defects are not regenerated.
- Scientific claims, Q boundary, evidence registry, constraints, mechanisms and predictions unchanged.

## R000004 — formal scientific model layer
- Added machine-readable parameter, benchmark, equation, assumption, uncertainty, validity-domain, limitation, I/O-schema and execution-environment registries.
- Added FORMAL-MODEL-v0.1-001 validator and connected it to the normal model validation gate.
- Historical nine-test scientific campaign remains unchanged; the formal model gate is an additional integrity/schema gate.
- Scientific claims and Q001-Q039 evidence state unchanged.

## R000005 — result context and next-step router
- Added a Q-bounded known-result registry that references canonical model benchmarks instead of duplicating their values.
- Added `known-results` and `contextualize-result` public operations.
- Added explicit distinction between registered reference span and a physical allowed range.
- Results outside the registered span trigger follow-up, not a new-physics claim.
- Added next-step executor routing for model-executable checks, model-designed tests, human input verification, literature research, model-update ingestion and external empirical work.
- Accepted scientific model, Q boundary, evidence, mechanisms, predictions and immutable accepted snapshots unchanged.
- Scientific change: false.

## R000006 — external astronomy catalogue context
- Added read-only live context from SIMBAD, the ESA Gaia DR3 Archive and VizieR/2MASS.
- Added `astronomy-catalog-context` for object-name or coordinate cone searches.
- External catalogue responses are classified as `EXTERNAL_REFERENCE_ONLY`.
- Catalogue lookup never expands the Q firewall and never promotes data directly into accepted model state.
- Service outage is treated as a technical unavailable state, not as a scientific no-match.
- Added explicit next-step routing for catalogue cross-checks and unresolved targets.
- Accepted scientific model, Q boundary, evidence, mechanisms, predictions and immutable accepted snapshots unchanged.
- Scientific change: false.


## v0.2 / Q040

- Advanced authorized boundary from Q039 to Q040.
- Preserved H0 benchmarks and public calculations.
- Added the native-nuisance marginalized common-CMB equation.
- Recorded numerical representation failures as TECHNICAL_FAIL, not physical falsification.
- Kept the CamSpec-HiLLiPoP causal discrepancy open and narrowed.
- Added no parameter, benchmark, mechanism, scientific domain or public calculation.
- Promotion commit: `26bfb093bee892ac32b9e1db78c36df3dd43ac3e`.


## Q040 post-promotion consistency repair

- Repair type: structural/provenance consistency only; no new scientific claim.
- Accepted scientific state remains Q040 / v0.2 / R000002.
- Added missing `current_q` and promotion metadata to the retained candidate record.
- Aligned formal/context registries with the Q040 firewall.
- Corrected the formalization-layer `scientific_change` flag to false; the Q040 scientific change is already represented in accepted state.
- Replaced the legacy Q039-hardcoded campaign validator with a current-state validator.
- Completed the frozen v0.2 snapshot with `MODEL_CURRENT.md` and current context registries.
- Preserved Q040 `TECHNICAL_FAIL` as non-physical falsification.


## Repository cleanup — Q040 post-promotion hygiene

- Removed completed one-time Q040 updater and repair infrastructure from the active tree.
- Removed stale secondary README copy.
- Synchronized current README, release mirror and current test metadata to canonical accepted state.
- Preserved accepted snapshots, evidence, provenance and historical test results.
- Added runtime-clutter ignore rules.
- Scientific change: false.
- Accepted state changed: false.
- Q boundary changed: false.
- Model version changed: false.
