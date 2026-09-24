# Q041 Bubbleverse model-update handoff

The connected GitHub integration could read both repositories but could not write to
`Morfindien/bubbleverse-model`; the first Git-object write returned HTTP 403
`Resource not accessible by integration`. No repository write succeeded.

The scientific/update decision is therefore **CANDIDATE_BLOCKED**, not promoted:

- Q041 V19 is a valid `CONTROLLED_NO_SCIENTIFIC_RESULT`.
- No downstream physical portability classification is established.
- The accepted model remains Q040 / v0.2 / R000002.
- The mandatory source-repository Word manuscript could not be discovered, so
  `WORD_DISCOVERY_GATE=FAIL` and `WORD_HASH_GATE=BLOCKED_NO_WORD_INPUT`.
- The three supplied Bubbleverse 0.41 PDFs are preserved as corroborating publication
  provenance, not substituted for the missing Word input.

## Installation

From a clean clone of `Morfindien/bubbleverse-model`, run:

```bash
python install_q041_candidate_blocked.py
```

This stages the blocked Q041 candidate, runs the current accepted-model regression
validator, verifies accepted/formal/frozen-release immutability, and creates two local
Git commits: an atomic candidate-staging commit and a non-self-referential provenance
closure commit.

If you want automatic push, use this on the **first** run:

```bash
python install_q041_candidate_blocked.py --push
```

If you already ran it without `--push`, push the two validated local commits with:

```bash
git push origin HEAD
```

The script does **not** modify `accepted/`, canonical `model/`, the current accepted release
handoff, or `versions/accepted/`, and it does **not** authorize the next Q boundary.
