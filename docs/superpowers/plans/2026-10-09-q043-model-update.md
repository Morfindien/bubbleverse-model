# Q043 bounded model update implementation plan

**Goal:** Admit the documented Q043 local preparation result into the next controlled model version, with no new cosmological inference.

**Architecture:** Stage the Q043 evidence, candidate layers and formal metadata separately. Validate a disposable projected release before touching accepted state. Preserve every previous snapshot and the source repository.

**Tech stack:** Python standard library, existing model campaign/public workflow, Git, supplied PDF manuscripts and original structured Q043 result.

**Spec:** Operator's autonomous model-updater control prompt; TARGET_Q=Q043.

## Constraints and rulings

- Authorized evidence Q001-Q043 only; no later evidence is included.
- Accepted baseline v0.4/R000004 through Q042 at 14eacce7a93e4ac780d59b1e86dc0cb9060f38ad.
- Source repository read-only at 72cf9e92fc794c122f593a77b6a555e6e97f6a2e.
- No DOCX exists at current source HEAD; use operator-supplied PDF manuscript and original Q043 structured result under the existing PDF-authorized-substitute convention. No Word hash is invented.
- Q043 source records are historical; their no-remote-promotion statement must survive verbatim. Current live Q042 installation is a separate verified event.
- No production restart, new numerical result, equation, parameter, domain or calculation.
- Preserve Q042 candidate records before replacing the active candidate.
- Existing Q042 validator must validate its historical accepted snapshot when the current boundary advances; it must continue rejecting invalid active evidence metadata and physical/production claims.
- Continue autonomously as explicitly instructed; no intermediate approval stop.

## Review focus

- Distinguish historical Q043 local validation from this model admission.
- Reject numerical production/falsification claims and future-Q contamination.
- Preserve all 91 source objects and inherited claim maps exactly.
- Enforce unchanged original predictions, contradictions and physical registries.
- Detect any mutation of old snapshots or read-only test operations.

## Tasks

- [x] Stage source bytes/hashes, structured diff, candidate scientific layers, formal metadata and provenance.
- [x] Add a Q043 read-only validator and public campaign integration with failure-injection tests; verify RED then GREEN.
- [x] Extend Q042 validation to read frozen historical sequence while protecting current evidence boundary; keep all prior scope checks.
- [x] Execute candidate, projected scientific/formal/public healthchecks, invalid-input checks and regression suite; hash protected files before/after.
- [x] Promote atomically only after all mandatory gates pass; create v0.5/R000005 frozen snapshot and release metadata.
- [ ] Publish to target repository, reread exact remote commit and contents, run fresh checks, and record full update report.

## Progress ledger

Discovery complete: original Q043 result digest verified; baseline 13 formal + 11 campaign + 11 Q042 checks and 4 regressions pass. Source/target roles and write scope verified.

Review: two Important gaps (source inventory and qualification coverage) reproduced RED, fixed GREEN; snapshot simultaneous-mutation guard added RED/GREEN. Reviewer confirmed no remaining Critical/Important issue. Projected 22 regression, 20 public, 13 formal, 12 campaign and both 11-gate suites pass; all 117 protected baseline files stayed unchanged until promotion.
