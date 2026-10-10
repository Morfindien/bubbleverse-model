# Q045 Model Update Implementation Plan

> Execute in this session. The operator explicitly authorizes autonomous repository update and promotion only after all mandatory gates pass.

**Goal:** Admit documented Q045 technical diagnostics and inconclusive closure without physical inference.
**Architecture:** Preserve accepted v0.6 until candidate validation and a projected-release healthcheck pass. Archive Q044 candidate metadata so historical validation continues against immutable v0.6. Add a read-only Q045 validator and failure-injection tests to the existing campaign.
**Tech Stack:** Python standard library, existing public workflow, Git, operator PDFs, hash-verified GitHub artifact.
**Spec:** Operator's Q045 updater instructions in this conversation; no separate filesystem spec supplied.

## Global Constraints
- TARGET_Q Q045; no evidence beyond the authorized TARGET_Q boundary is included.
- Source Morfindien/Bubbleverse; write target Morfindien/bubbleverse-model.
- No new physical parameters, equations, benchmarks, predictions, mechanisms or public calculations.
- Reference truth UNQUALIFIED; final physical result UNRESOLVED; production not authorized.
- Mixed-boundary PDFs archived as raw provenance only; ingest bounded excerpts.
- Preserve all accepted snapshots and inherited scientific definitions.

## Review Focus
- Recovery success must not imply qualified physical reference.
- A damaged derived history or missing source must fail validation.
- Advancing the candidate must not invalidate or bypass historical Q044 checks.
- Unknown physical bias and inference margins must remain unknown.
- Public test must leave accepted, candidate, formal and snapshots unchanged.

### Task 1: Scoped candidate and source provenance
- [x] Create structured diff before constructing the candidate.
- [x] Extract bounded PDF sections; archive raw PDFs and verified artifact.
- [x] Preserve all eight worker reports, four grids, original final report and contract.
- [x] Add traceable constraints, robustness, uncertainties and limitations only.
- [x] Hash accepted inputs and snapshots before changes.

### Task 2: Growing validation
- [x] Write Q045 mutation tests and prove missing validator fails.
- [x] Implement `run_tests(root, candidate=False)`; test source hashes, exact recovery qualification, four tau reversals, references, firewall, physical regression and immutable snapshots.
- [x] Add historical Q044 routing against frozen v0.6 and archived metadata; retain all historical gates.
- [x] Register Q045 in the campaign and run failure-injection tests and existing regressions.

### Task 3: Controlled release
- [x] Run candidate gates and all mandatory audit gates.
- [x] Run projected-release formal and public healthchecks in an isolated copy.
- [x] Obtain an independent review; fix substantive findings and rerun affected tests.
- [x] Promote only a fully passing candidate; freeze v0.7; create report and release handoff.
- [ ] Commit and publish with a checked remote-head lease; verify remote files and head.

## Publication outcome

Local candidate, promotion and validation completed. Git push could not authenticate; the connected GitHub create-blob request returned HTTP 403. Both remote heads were rechecked and are unchanged. The remaining publish/verify task is blocked by integration access. An exact Git bundle and installation handoff preserve the real candidate and local promotion commits.
