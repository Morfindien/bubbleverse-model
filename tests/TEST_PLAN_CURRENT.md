# BUBBLEVERSE MODEL — TEST PLAN CURRENT

**Campaign:** BV-MODEL-v0.2-CAMPAIGN-0002
**Authorized Q range:** Q001–Q040
**Current Q:** Q040
**Accepted model:** v0.2 / R000002
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
Current scientific/model state is limited to Q001–Q040. No current-state validation may ingest scientific evidence above Q040.

## Execution mechanism
`tests/programs/model_campaign.py validate` performs deterministic current-state validation. The permanent public workflow is `.github/workflows/00-bubbleverse-model-start-public.yml`.

## Promotion semantics
This current validator is non-promoting. It does not create a new accepted model, expand the Q boundary, or revise scientific conclusions. Promotion is handled by the controlled model-update pipeline.
