# Install the verified repository cleanup correction

Target: Morfindien/bubbleverse-model, branch main.
The repository is already accepted through Q043 at v0.5/R000005. This cleanup does not promote a model.
Remote cleanup publication was denied with HTTP 403; these files are the exact tested fallback.

## Replace or create these three files

Use the following repository paths, preserving the filenames:

```text
tests/programs/test_repository_cleanup.py
repository_cleanup.py
.github/workflows/repository-cleanup-current.yml
```

The first is new. The other two replace existing files. Do not upload the report or this instruction sheet as operational root files.
Commit the test first, then the Python engine, then the workflow. All three must be installed before the final run.
An automatic run during the intermediate engine replacement can stop at the old pinned checksum; the updated workflow contains the correct new checksum.

## Run the existing permanent button

```text
Actions → Repository cleanup → Run workflow
Branch: main
Mode: CLEAN
```

Start a new run after all three files are committed.
The workflow audits the current repository, verifies successful installation provenance and all referenced Git history,
and only then removes completed one-time installation artifacts. It also repairs current README publication information and stale descriptive test metadata.
It runs all current regression tests and the existing non-destructive public healthcheck before and after cleanup.

For the inspected baseline, the verified deletion cohort is:

```text
.github/workflows/q043-install-model.yml
Q043_model_update.bundle
Q043_INSTALL_ACTIONS.md
```

The successful installation receipt remains under provenance/. The original bundle and installer remain recoverable through Git history.
The engine discovers the current accepted state and Q-dependent artifact names; it is not fixed to this Q or model version.
Receipt/hash/history/dependency failures keep the affected cohort as REVIEW_REQUIRED.

## Verified local result

- 219 original files fully inventoried.
- 28 regression tests pass before and after cleanup.
- Public healthcheck: 20/20 before and after cleanup.
- All 194 original protected files remain byte-identical, including 103 immutable snapshot files.
- Scientific values, Q boundary, model version, evidence, provenance and test history remain unchanged.
- Final audit converges with no pending deletions, updates, unknowns or review-required items.

The full report explicitly separates local cleanup from remote publication. No new ZIP, Git bundle or one-time cleanup workflow is required.
Repository rules can still block direct writes to main; a blocked push must not be reported as successful cleanup.
