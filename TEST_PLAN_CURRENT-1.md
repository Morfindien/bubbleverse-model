# BUBBLEVERSE MODEL — TEST PLAN CURRENT

**Campaign:** BV-MODEL-v0.1-CAMPAIGN-0001  
**Authorized Q range:** Q001–Q039  
**Current Q:** Q039  
**Candidate:** v0.1-candidate  
**Mode:** BOOTSTRAP validation

This campaign validates the scientific integration of already-authorized and already-validated Bubbleverse evidence. It does **not** pretend to rerun every historical numerical experiment and does not treat workflow success as new observational evidence.

| TEST_ID | Category | Target | Initial status | Promotion |
|---|---|---|---|---|
| T-BV-001 | MANDATORY_PROMOTION | Q identity and boundary schema | READY | MANDATORY |
| T-BV-002 | MANDATORY_PROMOTION | High-Q contamination scan | READY | MANDATORY |
| T-BV-003 | MANDATORY_PROMOTION | H0 inference-chain invariant | READY | MANDATORY |
| T-BV-004 | MANDATORY_PROMOTION | Q039 provenance invariant | READY | MANDATORY |
| T-BV-005 | MANDATORY_PROMOTION | Technical/scientific separation | READY | MANDATORY |
| T-BV-006 | MANDATORY_PROMOTION | Q039 causal conservatism | READY | MANDATORY |
| T-BV-007 | REGRESSION | Contradiction preservation | READY | MANDATORY |
| T-BV-008 | REGRESSION | Open-question preservation | READY | MANDATORY |
| T-BV-009 | MANDATORY_PROMOTION | JSON/schema/reference integrity | READY | MANDATORY |

## Locked success rule
All nine tests must explicitly return PASS. Any non-PASS mandatory state blocks promotion.

## Q firewall
All scientific inputs and candidate state are limited to Q001–Q039. No test may ingest Q040+ scientific evidence.

## Execution mechanism
`tests/programs/model_campaign.py` performs deterministic repository audits. The primary workflow `.github/workflows/00-bubbleverse-model-start.yml` accepts one human input, `command`, normally `test`.

## Promotion
If and only if every mandatory test passes, the program promotes `v0.1-candidate` to accepted `v0.1`, writes the all-green release handoff, and updates the changelog. Otherwise accepted state stays uninitialized and the release stays blocked.
