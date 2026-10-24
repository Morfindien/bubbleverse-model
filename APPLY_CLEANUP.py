#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AUDITED_BASE = '458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee'
RUN_ID = 'BV-CLEANUP-BM-20261024-458d6c33-v330'
TARGET_REPO = "Morfindien/bubbleverse-model"
BOOTSTRAP_ALLOWED = set(['APPLY_CLEANUP.py', '.github/workflows/apply-bubbleverse-model-cleanup-v330.yml'])
MOVES = [{'authorization_scope': 'Bubbleverse Repository Cleanup Prompt v3.3.0 section 7.1 + operator CLEAN invocation', 'bundle_id': 'Q045-install-v0.7', 'compatibility_strategy': 'remove from active workflow discovery; preserve original path below payload/ and source retrieval through Git history', 'dependency_closure': 'installer workflow + installer payload only; completion evidence and accepted snapshots remain in place', 'expected_destination_git_blob_sha': '9449ee232a5d41d70c4cc754ee8255981f890fe8', 'git_blob_sha': '9449ee232a5d41d70c4cc754ee8255981f890fe8', 'known_hash_note': 'Git blob identity is verified at BASE_SHA; SHA-256 is computed by APPLY_CLEANUP.py before mutation.', 'new_path': 'archive/programs/Q045/install-q045-model-v07/v0.7/payload/.github/workflows/install-q045-model-v07.yml', 'old_path': '.github/workflows/install-q045-model-v07.yml', 'operation': 'ARCHIVE', 'operation_id': 'ARCH-Q045-WF', 'placement_decision': 'ARCHIVE_RETIRED', 'protection_classification': 'RETIRED_PROGRAM_FROZEN_PAYLOAD', 'recovery_method': 'git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:.github/workflows/install-q045-model-v07.yml or scoped revert of cleanup commit', 'sha256': None, 'verification_state': 'PREPARED; installer verifies before/after Git blob and SHA-256'}, {'authorization_scope': 'Bubbleverse Repository Cleanup Prompt v3.3.0 section 7.1 + operator CLEAN invocation', 'bundle_id': 'Q045-install-v0.7', 'compatibility_strategy': 'remove from active workflow discovery; preserve original path below payload/ and source retrieval through Git history', 'dependency_closure': 'installer workflow + installer payload only; completion evidence and accepted snapshots remain in place', 'expected_destination_git_blob_sha': '427fdb0de3164782fa4d681a0e9295e15714f611', 'git_blob_sha': '427fdb0de3164782fa4d681a0e9295e15714f611', 'new_path': 'archive/programs/Q045/install-q045-model-v07/v0.7/payload/Bubbleverse_Q045_v0.7.bundle', 'old_path': 'Bubbleverse_Q045_v0.7.bundle', 'operation': 'ARCHIVE', 'operation_id': 'ARCH-Q045-BUNDLE', 'placement_decision': 'ARCHIVE_RETIRED', 'protection_classification': 'RETIRED_PROGRAM_FROZEN_PAYLOAD', 'recovery_method': 'git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:Bubbleverse_Q045_v0.7.bundle or scoped revert of cleanup commit', 'sha256': 'fd1bb405dbde3b357543ac1ed301253fedd4df8a0faed69d2c8d712ce24aaf36', 'verification_state': 'PREPARED; installer verifies before/after Git blob and SHA-256'}, {'authorization_scope': 'Bubbleverse Repository Cleanup Prompt v3.3.0 section 7.1 + operator CLEAN invocation', 'bundle_id': 'Q046-install-v0.8', 'compatibility_strategy': 'remove from active workflow discovery; preserve original path below payload/ and source retrieval through Git history', 'dependency_closure': 'installer workflow + installer payload only; completion evidence and accepted snapshots remain in place', 'expected_destination_git_blob_sha': '91e10c4325d80f094b6a1e45ad1851b3c807a296', 'git_blob_sha': '91e10c4325d80f094b6a1e45ad1851b3c807a296', 'known_hash_note': 'Git blob identity is verified at BASE_SHA; SHA-256 is computed by APPLY_CLEANUP.py before mutation.', 'new_path': 'archive/programs/Q046/install-q046-model-v08/v0.8/payload/.github/workflows/install-q046-model-v08.yml', 'old_path': '.github/workflows/install-q046-model-v08.yml', 'operation': 'ARCHIVE', 'operation_id': 'ARCH-Q046-WF', 'placement_decision': 'ARCHIVE_RETIRED', 'protection_classification': 'RETIRED_PROGRAM_FROZEN_PAYLOAD', 'recovery_method': 'git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:.github/workflows/install-q046-model-v08.yml or scoped revert of cleanup commit', 'sha256': None, 'verification_state': 'PREPARED; installer verifies before/after Git blob and SHA-256'}, {'authorization_scope': 'Bubbleverse Repository Cleanup Prompt v3.3.0 section 7.1 + operator CLEAN invocation', 'bundle_id': 'Q046-install-v0.8', 'compatibility_strategy': 'remove from active workflow discovery; preserve original path below payload/ and source retrieval through Git history', 'dependency_closure': 'installer workflow + installer payload only; completion evidence and accepted snapshots remain in place', 'expected_destination_git_blob_sha': '5b23d0b52d8d7584d4672e2794ebc0caaa75009d', 'git_blob_sha': '5b23d0b52d8d7584d4672e2794ebc0caaa75009d', 'new_path': 'archive/programs/Q046/install-q046-model-v08/v0.8/payload/q046_model_update.py', 'old_path': 'q046_model_update.py', 'operation': 'ARCHIVE', 'operation_id': 'ARCH-Q046-PY', 'placement_decision': 'ARCHIVE_RETIRED', 'protection_classification': 'RETIRED_PROGRAM_FROZEN_PAYLOAD', 'recovery_method': 'git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:q046_model_update.py or scoped revert of cleanup commit', 'sha256': '7bc8da5bbb1fa224d22da80384cb40b0b5b5441d6d4018326e948b466ca41522', 'verification_state': 'PREPARED; installer verifies before/after Git blob and SHA-256'}, {'authorization_scope': 'Bubbleverse Repository Cleanup Prompt v3.3.0 section 7.1 + operator CLEAN invocation', 'bundle_id': 'Q047-install-v0.9', 'compatibility_strategy': 'remove from active workflow discovery; preserve original path below payload/ and source retrieval through Git history', 'dependency_closure': 'installer workflow + installer payload only; completion evidence and accepted snapshots remain in place', 'expected_destination_git_blob_sha': '9b101b1ee08079f60cc8d97b82e5c7aa538a20d3', 'git_blob_sha': '9b101b1ee08079f60cc8d97b82e5c7aa538a20d3', 'known_hash_note': 'Git blob identity is verified at BASE_SHA; SHA-256 is computed by APPLY_CLEANUP.py before mutation.', 'new_path': 'archive/programs/Q047/install-q047-model-v09/v0.9/payload/.github/workflows/install-q047-model-v09.yml', 'old_path': '.github/workflows/install-q047-model-v09.yml', 'operation': 'ARCHIVE', 'operation_id': 'ARCH-Q047-WF', 'placement_decision': 'ARCHIVE_RETIRED', 'protection_classification': 'RETIRED_PROGRAM_FROZEN_PAYLOAD', 'recovery_method': 'git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:.github/workflows/install-q047-model-v09.yml or scoped revert of cleanup commit', 'sha256': None, 'verification_state': 'PREPARED; installer verifies before/after Git blob and SHA-256'}, {'authorization_scope': 'Bubbleverse Repository Cleanup Prompt v3.3.0 section 7.1 + operator CLEAN invocation', 'bundle_id': 'Q047-install-v0.9', 'compatibility_strategy': 'remove from active workflow discovery; preserve original path below payload/ and source retrieval through Git history', 'dependency_closure': 'installer workflow + installer payload only; completion evidence and accepted snapshots remain in place', 'expected_destination_git_blob_sha': '9e90cc1d5858e463e87328920f82a3333491e288', 'git_blob_sha': '9e90cc1d5858e463e87328920f82a3333491e288', 'new_path': 'archive/programs/Q047/install-q047-model-v09/v0.9/payload/q047_model_update.py', 'old_path': 'q047_model_update.py', 'operation': 'ARCHIVE', 'operation_id': 'ARCH-Q047-PY', 'placement_decision': 'ARCHIVE_RETIRED', 'protection_classification': 'RETIRED_PROGRAM_FROZEN_PAYLOAD', 'recovery_method': 'git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:q047_model_update.py or scoped revert of cleanup commit', 'sha256': 'df246ad14dc83b9bcb3226af5787583b6dfdff0843116d7cd54f764435cc5c98', 'verification_state': 'PREPARED; installer verifies before/after Git blob and SHA-256'}, {'authorization_scope': 'Bubbleverse Repository Cleanup Prompt v3.3.0 section 7.1 + operator CLEAN invocation', 'bundle_id': 'Q048-install-v0.10', 'compatibility_strategy': 'remove from active workflow discovery; preserve original path below payload/ and source retrieval through Git history', 'dependency_closure': 'installer workflow + installer payload only; completion evidence and accepted snapshots remain in place', 'expected_destination_git_blob_sha': 'f9d6e3add055f83b7661056d3d563ddf33cefe81', 'git_blob_sha': 'f9d6e3add055f83b7661056d3d563ddf33cefe81', 'known_hash_note': 'Git blob identity is verified at BASE_SHA; SHA-256 is computed by APPLY_CLEANUP.py before mutation.', 'new_path': 'archive/programs/Q048/install-q048-model-v010/v0.10/payload/.github/workflows/install-q048-model-v010.yml', 'old_path': '.github/workflows/install-q048-model-v010.yml', 'operation': 'ARCHIVE', 'operation_id': 'ARCH-Q048-WF', 'placement_decision': 'ARCHIVE_RETIRED', 'protection_classification': 'RETIRED_PROGRAM_FROZEN_PAYLOAD', 'recovery_method': 'git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:.github/workflows/install-q048-model-v010.yml or scoped revert of cleanup commit', 'sha256': None, 'verification_state': 'PREPARED; installer verifies before/after Git blob and SHA-256'}, {'authorization_scope': 'Bubbleverse Repository Cleanup Prompt v3.3.0 section 7.1 + operator CLEAN invocation', 'bundle_id': 'Q048-install-v0.10', 'compatibility_strategy': 'remove from active workflow discovery; preserve original path below payload/ and source retrieval through Git history', 'dependency_closure': 'installer workflow + installer payload only; completion evidence and accepted snapshots remain in place', 'expected_destination_git_blob_sha': '03b47bd6275fa8725faffdbc2fb845ac239d187d', 'git_blob_sha': '03b47bd6275fa8725faffdbc2fb845ac239d187d', 'new_path': 'archive/programs/Q048/install-q048-model-v010/v0.10/payload/q048_model_update.py', 'old_path': 'q048_model_update.py', 'operation': 'ARCHIVE', 'operation_id': 'ARCH-Q048-PY', 'placement_decision': 'ARCHIVE_RETIRED', 'protection_classification': 'RETIRED_PROGRAM_FROZEN_PAYLOAD', 'recovery_method': 'git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:q048_model_update.py or scoped revert of cleanup commit', 'sha256': '3342ce4ffc33b918765310b81b216d83387a7e38ef8e4cdde8751020994a9c61', 'verification_state': 'PREPARED; installer verifies before/after Git blob and SHA-256'}]
DEFERRED = [{'path': '.github/workflows/apply-reviewed-repository-cleanup.yml', 'placement_decision': 'DEFER_BLOCKED', 'reason': 'One-time semantics are likely, but the workflow was deleted and later reintroduced; explicit current retirement is not established.'}, {'path': '.github/workflows/q046-model-admission.yml', 'placement_decision': 'DEFER_BLOCKED', 'reason': 'Historical Q046 admission semantics are apparent, but retirement is not explicitly recorded by the current lifecycle registry.'}, {'path': '.github/workflows/repair-q048-final-selftests.yml', 'placement_decision': 'DEFER_BLOCKED', 'reason': 'The current HEAD records the repair result, but future repair/re-entry intent is not explicitly retired.'}]
EMBEDDED_TEXT_FILES = {'README.md': '# Bubbleverse Model\n\nAutonomous, Q-bounded scientific synthesis, formalization, computation and falsification repository.\n\n`Morfindien/bubbleverse-model` stores the accepted model, candidate state, formal model, validation programs, provenance and immutable accepted-version history. `Morfindien/Bubbleverse` remains the scientific source repository.\n\nThe model is the best current compression of validated Bubbleverse evidence inside the authorized Q range. It is not established truth.\n\n## Current state\n\n- Accepted state: **v0.10 / R000010 through Q048**.\n- Q048 is integrated as terminal **UNSOLVED / UNRESOLVED** with partial/conditional evidence only.\n- No physical model change, cosmological verdict or production restart follows from the Q048 admission.\n- Frozen predecessor snapshot: `versions/accepted/v0.9/`.\n- Current accepted snapshot: `versions/accepted/v0.10/`.\n- One-time Q045–Q048 installer programs are retired and archived under `archive/programs/`; their historical bytes and command lineage remain traceable.\n- Current routine operation uses `.github/workflows/00-bubbleverse-model-start-public.yml`.\n\n## Start here\n\nComplete launch registry: [`START_CODES.md`](START_CODES.md).\n\nRepository map: [`docs/REPOSITORY_STRUCTURE.md`](docs/REPOSITORY_STRUCTURE.md).\n\n### GitHub Actions quick start\n\n1. Open the repository in GitHub.\n2. Open **Actions**.\n3. Select **🧪 BUBBLEVERSE MODEL — START**.\n4. Choose an operation.\n5. Supply input only when the selected operation requires it.\n\nPermanent public workflow:\n\n```text\n.github/workflows/00-bubbleverse-model-start-public.yml\n```\n\nCommon non-destructive operations:\n\n```text\ntest\nvalidate-model\nmodel-status\ncontradictions\nprovenance\nrelease-handoff\nknown-results\ncontextualize-result\nastronomy-catalog-context\ngaussian-tension\ndifference\npercent-shift\nweighted-mean\n```\n\n`campaign` and `install-context-engine` have repository-write paths in the workflow and should be invoked deliberately.\n\n## Local validation\n\nPython 3.11 is the validated runtime family. The current model tooling uses the Python standard library.\n\n```bash\npython3 tests/programs/formal_model_validate.py\npython3 tests/programs/q048_model_validate.py\npython3 tests/programs/model_campaign.py validate\npython3 -m unittest discover -s tests/programs -p "test*.py"\n```\n\nThe canonical current plan is [`tests/TEST_PLAN_CURRENT.md`](tests/TEST_PLAN_CURRENT.md).\n\n## Model update flow\n\n```text\nNEW COMPLETED Q\n        ↓\nAUTHORIZED EVIDENCE\n        ↓\nMODEL DIFF\n        ↓\nCANDIDATE MODEL\n        ↓\nFORMAL MODEL SYNCHRONIZATION\n        ↓\nSCIENTIFIC / FORMAL / REGRESSION TESTS\n        ↓\nPROMOTION GATE\n        ↓\nACCEPTED MODEL\n        ↓\nIMMUTABLE VERSION SNAPSHOT\n```\n\nAccepted model state is not edited directly merely for repository organization. Candidate evidence does not become accepted science without the controlled model-update process.\n\n## Scientific Q firewall\n\nAt this baseline the authorized range is:\n\n```text\nQ001–Q048\n```\n\nEvidence beyond that boundary must not influence the current accepted scientific state. Expanding the boundary is a scientific model-update action, not a cleanup action.\n\n## Repository structure\n\n- `accepted/` — current accepted scientific state.\n- `candidate/` — candidate/staging state and bounded candidate evidence.\n- `model/` — machine-readable formal model.\n- `evidence/` — registered evidence and Q-specific updates.\n- `provenance/` — traceability and durable cleanup memory.\n- `release/` — canonical release handoff.\n- `versions/accepted/` — immutable accepted-model snapshots.\n- `tests/` — current validators, regression guards and protected results.\n- `changelog/` — model change history.\n- `archive/programs/` — verified retired program bundles, not routine execution targets.\n- `docs/` — repository and historical planning documentation.\n\nSee [`docs/REPOSITORY_STRUCTURE.md`](docs/REPOSITORY_STRUCTURE.md) for the detailed map and root exceptions.\n\n## Accepted vs candidate\n\n`accepted/` contains the current accepted scientific model. `candidate/` contains proposed or staged state and may pass, fail, remain blocked, be revised, be rejected or be superseded.\n\nScientific incompleteness is preferable to fabricated certainty. `SUPPORTED` does not mean `PROVEN`; a technical failure does not automatically mean physical falsification; unknown quantities may remain `UNKNOWN` or `NOT_ESTABLISHED`.\n\n## Provenance and reproducibility\n\nA model change should remain traceable through:\n\n```text\nQ → SOURCE → EVIDENCE → PROGRAM / RESULT → CANDIDATE CHANGE\n  → TESTS → PROMOTION → ACCEPTED VERSION → GIT COMMIT\n```\n\nPreserve source commits, hashes, workflow/run IDs, program/result IDs and artifact identity where available.\n\n## Repository maintenance\n\nCurrent cleanup engine:\n\n```bash\npython3 repository_cleanup.py --repo . --mode AUDIT\n```\n\nThe scheduled/current workflow is:\n\n```text\n.github/workflows/repository-cleanup-current.yml\n```\n\nCleanup must not rewrite scientific history, change a scientific verdict, rerun expensive completed campaigns for organizational convenience, or treat an archive as scientific acceptance.\n\n## Do not\n\n- Do not manually rewrite frozen accepted snapshots.\n- Do not treat candidate state as accepted science.\n- Do not weaken tests merely to obtain a green result.\n- Do not insert future-Q evidence across the Q firewall.\n- Do not silently delete unresolved contradictions.\n- Do not replace unknown values with plausible guesses.\n- Do not execute archived installers as routine validation.\n- Do not overwrite scientific history when a conclusion changes; supersede it explicitly.\n\n## Core rule\n\nBubbleverse Model exists to maintain the best current scientific compression of authorized Bubbleverse evidence. It does not exist to protect the current theory. The model may change, weaken, reject, supersede, reopen or falsify earlier conclusions when authorized evidence requires it.\n\n### Q048 terminal UNSOLVED admission\n\nQ048 is integrated as **UNSOLVED / UNRESOLVED** with partial/conditional evidence only. No physical model change or production restart follows.\n', 'START_CODES.md': '# Bubbleverse Model — START_CODES\n\nCanonical launch registry for `Morfindien/bubbleverse-model`.\n\nBaseline used for this registry: `458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee`.\nCurrent accepted model at that baseline: **v0.10 / R000010 through Q048**.\n\nLifecycle and verification state are separate. `ACTIVE` means supported now; `ARCHIVED` means reference-only; `HISTORICAL` means retained but not recommended for current operation.\n\n## Prerequisites\n\n- GitHub Actions route: authenticated GitHub CLI (`gh`) with access to `Morfindien/bubbleverse-model`.\n- Local validation route: Python 3.11 and a clean checkout.\n- Run commands from the repository root unless another working directory is stated.\n- Never place secrets directly in commands.\n\n## Active public workflow\n\nWorkflow: `.github/workflows/00-bubbleverse-model-start-public.yml`\n\nRead-only operations:\n\n```bash\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=test -f input=\'\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=validate-model -f input=\'\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=model-status -f input=\'\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=contradictions -f input=\'\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=provenance -f input=\'\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=release-handoff -f input=\'\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=known-results -f input=\'{"quantity":"H0"}\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=contextualize-result -f input=\'{"quantity":"H0","value":1150.0,"sigma":0.81,"units":"km s^-1 Mpc^-1"}\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=astronomy-catalog-context -f input=\'{"object":"Vega","radius_arcsec":5}\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=gaussian-tension -f input=\'73.50,0.81,67.24,0.35\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=difference -f input=\'5,3\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=percent-shift -f input=\'67.24,73.50\'\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=weighted-mean -f input=\'73.50,0.81,67.24,0.35\'\n```\n\nThe `campaign` route is active but can write a current validation record and the workflow contains a commit step:\n\n```bash\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=campaign -f input=\'\'\n```\n\nThe `install-context-engine` route is an active maintenance operation and may commit model/README/changelog/registry changes when it produces a diff:\n\n```bash\ngh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=install-context-engine -f input=\'\'\n```\n\n## Active local validation\n\n```bash\npython3 tests/programs/formal_model_validate.py\npython3 tests/programs/q048_model_validate.py\npython3 tests/programs/model_campaign.py validate\npython3 -m unittest discover -s tests/programs -p "test*.py"\n```\n\nCurrent validation source paths:\n\n- `tests/programs/formal_model_validate.py`\n- `tests/programs/q048_model_validate.py`\n- `tests/programs/model_campaign.py`\n\n## Active repository maintenance\n\nRead-only audit:\n\n```bash\npython3 repository_cleanup.py --repo . --mode AUDIT\n```\n\nLocal CLEAN preparation:\n\n```bash\npython3 repository_cleanup.py --repo . --mode CLEAN --report /tmp/bubbleverse-cleanup-report.json\n```\n\nGitHub audit:\n\n```bash\ngh workflow run repository-cleanup-current.yml --ref main -f mode=AUDIT\n```\n\nGitHub CLEAN is remote-mutating and should only be run deliberately:\n\n```bash\ngh workflow run repository-cleanup-current.yml --ref main -f mode=CLEAN\n```\n\n## Historical / deferred workflows still in active discovery\n\nThese are not classified as retired by this cleanup because lifecycle evidence is insufficient. They remain at their original workflow paths.\n\n```bash\ngh workflow run apply-reviewed-repository-cleanup.yml --ref main\ngh workflow run q046-model-admission.yml --ref main\ngh workflow run repair-q048-final-selftests.yml --ref main\n```\n\nLifecycle: `HISTORICAL / RETIREMENT_UNCONFIRMED`.\nVerification for this cleanup: `NOT_RUN`.\n\n## Archived one-time installers — reference only\n\nAfter cleanup installation, these commands are historical records only and are **not runnable from GitHub Actions discovery**.\n\nOriginal Q045 command:\n\n```bash\ngh workflow run install-q045-model-v07.yml --ref main\n```\n\nOriginal Q046 commands:\n\n```bash\ngh workflow run install-q046-model-v08.yml --ref main\npython3 q046_model_update.py --apply\n```\n\nOriginal Q047 commands:\n\n```bash\ngh workflow run install-q047-model-v09.yml --ref main\npython3 q047_model_update.py --apply\n```\n\nOriginal Q048 commands:\n\n```bash\ngh workflow run install-q048-model-v010.yml --ref main\npython3 q048_model_update.py --apply\n```\n\nLifecycle: `ARCHIVED — NOT FOR ROUTINE EXECUTION`.\nHistorical completion evidence is linked from `archive/programs/INDEX.md`.\n\n## Safety\n\nArchived programs are retained byte-for-byte for traceability. Do not execute archived installer payloads merely to verify the archive. Restore/reactivate only through a separate explicit decision.\n', 'docs/REPOSITORY_STRUCTURE.md': '# Repository Structure\n\nThis document describes the intended installed structure for `Morfindien/bubbleverse-model` after cleanup package `BV-CLEANUP-BM-20261024-458d6c33-v330` is applied.\n\nThe cleanup changes repository organization only. It does not change the accepted scientific verdict, Q boundary, numerical results, or immutable accepted snapshots.\n\n```text\n/\n├── README.md\n├── START_CODES.md\n├── .gitattributes\n├── .gitignore\n├── bubbleverse_model_program_registry.json\n├── repository_cleanup.py\n├── .github/\n│   └── workflows/\n│       ├── 00-bubbleverse-model-start-public.yml\n│       ├── repository-cleanup-current.yml\n│       ├── apply-reviewed-repository-cleanup.yml        # retirement unconfirmed\n│       ├── q046-model-admission.yml                     # retirement unconfirmed\n│       └── repair-q048-final-selftests.yml              # retirement unconfirmed\n├── accepted/                  # current accepted scientific state\n├── candidate/                 # candidate/staging state and bounded evidence\n├── model/                     # current formal model layer\n├── evidence/                  # registered evidence and Q updates\n├── provenance/                # provenance and cleanup memory\n│   └── cleanup/\n├── release/                   # current release handoff\n├── changelog/                 # model change history\n├── versions/\n│   └── accepted/              # immutable accepted snapshots\n├── tests/\n│   ├── programs/              # current and historical validation programs\n│   ├── results/               # protected validation records\n│   └── TEST_PLAN_CURRENT.md   # current Q048/v0.10 validation plan\n├── docs/\n│   ├── REPOSITORY_STRUCTURE.md\n│   └── superpowers/           # existing historical plans\n└── archive/\n    └── programs/\n        ├── INDEX.md\n        ├── Q045/install-q045-model-v07/v0.7/\n        ├── Q046/install-q046-model-v08/v0.8/\n        ├── Q047/install-q047-model-v09/v0.9/\n        └── Q048/install-q048-model-v010/v0.10/\n```\n\n## Root exceptions\n\n`README.md` and `START_CODES.md` are deliberate public entry points.\n\n`.gitattributes` and `.gitignore` remain at the root because Git consumes them there.\n\n`bubbleverse_model_program_registry.json` remains at the root because the current cleanup engine and model tooling use that canonical path.\n\n`repository_cleanup.py` remains at the root because `.github/workflows/repository-cleanup-current.yml` executes and hash-checks it from that location.\n\n## Protected scientific areas\n\nThe cleanup does not rewrite:\n\n- `accepted/`\n- `candidate/`\n- `model/`\n- `evidence/`\n- `provenance/` historical records\n- `release/`\n- `versions/accepted/`\n- `tests/results/`\n- `changelog/`\n\nHistorical executable material stored inside protected evidence/provenance trees stays in place. Its location is part of the historical record.\n\n## Program archive\n\n`archive/programs/` contains verified retired, one-time installer programs. Each archived bundle preserves the original repository-relative path below its `payload/` directory. `ARCHIVE_INFO.md` records the source path, source commit, Git blob identity, completion evidence, accepted snapshot, and recovery route.\n\nArchived workflow YAML is moved out of `.github/workflows/`, so GitHub no longer discovers it as an active workflow.\n\n## Active entry points\n\nHuman launch registry: [`../START_CODES.md`](../START_CODES.md).\n\nPermanent public workflow: `../.github/workflows/00-bubbleverse-model-start-public.yml`.\n\nCurrent local validation:\n\n```bash\npython3 tests/programs/formal_model_validate.py\npython3 tests/programs/q048_model_validate.py\npython3 tests/programs/model_campaign.py validate\npython3 -m unittest discover -s tests/programs -p "test*.py"\n```\n\n## Cleanup memory\n\nNew cleanup evidence is written beneath `provenance/cleanup/`. Historical cleanup records are retained. Derived cleanup indexes are navigation aids, not scientific sources of truth.\n', 'tests/TEST_PLAN_CURRENT.md': '# Current validation plan: Q048/v0.10\n\nRun:\n\n```bash\npython3 tests/programs/formal_model_validate.py\npython3 tests/programs/q048_model_validate.py\npython3 tests/programs/model_campaign.py validate\npython3 -m unittest discover -s tests/programs -p "test*.py"\n```\n\nThe permanent public workflow `test` operation performs read-only current validation and system healthchecks. Historical registered gates and source lineage remain required. Regression tests use disposable copies for failure injection. Original numerical trajectories are not rerun.\n\nThe Q048 validator verifies the terminal UNSOLVED / UNRESOLVED admission and does not convert technical cleanup status into a scientific verdict.\n', 'archive/programs/INDEX.md': '# Archived Programs\n\nThis index records retired executable material removed from routine discovery by cleanup run `BV-CLEANUP-BM-20261024-458d6c33-v330`.\n\nSource repository: `Morfindien/bubbleverse-model`  \nSource commit: `458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee`\n\n| Q | Program | Archived lifecycle | Completion evidence | Accepted snapshot |\n|---|---|---|---|---|\n| Q045 | `install-q045-model-v07` | ARCHIVED — NOT FOR ROUTINE EXECUTION | `provenance/Q045_GITHUB_INSTALLATION_RECEIPT.json` | `versions/accepted/v0.7/` |\n| Q046 | `install-q046-model-v08` | ARCHIVED — NOT FOR ROUTINE EXECUTION | `provenance/Q046_INSTALLATION_RECEIPT.json` | `versions/accepted/v0.8/` |\n| Q047 | `install-q047-model-v09` | ARCHIVED — NOT FOR ROUTINE EXECUTION | `provenance/Q047_INSTALLATION_RECEIPT.json` | `versions/accepted/v0.9/` |\n| Q048 | `install-q048-model-v010` | ARCHIVED — NOT FOR ROUTINE EXECUTION | `provenance/Q048_INSTALLATION_RECEIPT.json` | `versions/accepted/v0.10/` |\n\nArchived programs are historical execution records. Do not treat this index as a launch menu. Restoration/reactivation is a separate explicit decision.\n\nThe following workflow candidates were deliberately **not** archived because retirement was not sufficiently established at the cleanup baseline:\n\n- `.github/workflows/apply-reviewed-repository-cleanup.yml`\n- `.github/workflows/q046-model-admission.yml`\n- `.github/workflows/repair-q048-final-selftests.yml`\n', 'archive/programs/Q045/install-q045-model-v07/v0.7/ARCHIVE_INFO.md': '# Q045 one-time model installer v0.7\n\n**ARCHIVED — NOT FOR ROUTINE EXECUTION**\n\nSource repository: `Morfindien/bubbleverse-model`  \nSource commit: `458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee`  \nCompletion evidence: `provenance/Q045_GITHUB_INSTALLATION_RECEIPT.json`  \nAccepted snapshot: `versions/accepted/v0.7/`\n\nInstallation complete; all validation green in persisted receipt. Production authorization remains false.\n\n## Archived payload\n\nThe `payload/` subtree preserves each original repository-relative path without rewriting the retired program.\n\n- `.github/workflows/install-q045-model-v07.yml` → `archive/programs/Q045/install-q045-model-v07/v0.7/payload/.github/workflows/install-q045-model-v07.yml`\n  - source Git blob: `9449ee232a5d41d70c4cc754ee8255981f890fe8`\n  - expected archive Git blob: `9449ee232a5d41d70c4cc754ee8255981f890fe8`\n- `Bubbleverse_Q045_v0.7.bundle` → `archive/programs/Q045/install-q045-model-v07/v0.7/payload/Bubbleverse_Q045_v0.7.bundle`\n  - source Git blob: `427fdb0de3164782fa4d681a0e9295e15714f611`\n  - expected archive Git blob: `427fdb0de3164782fa4d681a0e9295e15714f611`\n  - verified source SHA-256: `fd1bb405dbde3b357543ac1ed301253fedd4df8a0faed69d2c8d712ce24aaf36`\n\n## Retirement evidence\n\nThe repository README at the cleanup baseline states that one-time installations are complete and that the historical installation files were awaiting workflow-aware cleanup. The current program registry does not register this installer as an active program. Current active validation is provided by the permanent public workflow and current validators.\n\n## Recovery\n\nOriginal source bytes remain retrievable from Git history, for example: `git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:<original-path>`.\n\nReactivation is not part of cleanup. If reactivation is ever required, make a separate explicit decision and restore from the recorded source commit rather than editing the archived payload in place.\n', 'archive/programs/Q046/install-q046-model-v08/v0.8/ARCHIVE_INFO.md': '# Q046 one-time model installer v0.8\n\n**ARCHIVED — NOT FOR ROUTINE EXECUTION**\n\nSource repository: `Morfindien/bubbleverse-model`  \nSource commit: `458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee`  \nCompletion evidence: `provenance/Q046_INSTALLATION_RECEIPT.json`  \nAccepted snapshot: `versions/accepted/v0.8/`\n\nInstallation admitted v0.8; scientific assessment remained INSUFFICIENT QUALIFICATION.\n\n## Archived payload\n\nThe `payload/` subtree preserves each original repository-relative path without rewriting the retired program.\n\n- `.github/workflows/install-q046-model-v08.yml` → `archive/programs/Q046/install-q046-model-v08/v0.8/payload/.github/workflows/install-q046-model-v08.yml`\n  - source Git blob: `91e10c4325d80f094b6a1e45ad1851b3c807a296`\n  - expected archive Git blob: `91e10c4325d80f094b6a1e45ad1851b3c807a296`\n- `q046_model_update.py` → `archive/programs/Q046/install-q046-model-v08/v0.8/payload/q046_model_update.py`\n  - source Git blob: `5b23d0b52d8d7584d4672e2794ebc0caaa75009d`\n  - expected archive Git blob: `5b23d0b52d8d7584d4672e2794ebc0caaa75009d`\n  - verified source SHA-256: `7bc8da5bbb1fa224d22da80384cb40b0b5b5441d6d4018326e948b466ca41522`\n\n## Retirement evidence\n\nThe repository README at the cleanup baseline states that one-time installations are complete and that the historical installation files were awaiting workflow-aware cleanup. The current program registry does not register this installer as an active program. Current active validation is provided by the permanent public workflow and current validators.\n\n## Recovery\n\nOriginal source bytes remain retrievable from Git history, for example: `git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:<original-path>`.\n\nReactivation is not part of cleanup. If reactivation is ever required, make a separate explicit decision and restore from the recorded source commit rather than editing the archived payload in place.\n', 'archive/programs/Q047/install-q047-model-v09/v0.9/ARCHIVE_INFO.md': '# Q047 one-time model installer v0.9\n\n**ARCHIVED — NOT FOR ROUTINE EXECUTION**\n\nSource repository: `Morfindien/bubbleverse-model`  \nSource commit: `458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee`  \nCompletion evidence: `provenance/Q047_INSTALLATION_RECEIPT.json`  \nAccepted snapshot: `versions/accepted/v0.9/`\n\nInstallation admitted v0.9; assessment remained INCONCLUSIVE / INSUFFICIENT_EVIDENCE.\n\n## Archived payload\n\nThe `payload/` subtree preserves each original repository-relative path without rewriting the retired program.\n\n- `.github/workflows/install-q047-model-v09.yml` → `archive/programs/Q047/install-q047-model-v09/v0.9/payload/.github/workflows/install-q047-model-v09.yml`\n  - source Git blob: `9b101b1ee08079f60cc8d97b82e5c7aa538a20d3`\n  - expected archive Git blob: `9b101b1ee08079f60cc8d97b82e5c7aa538a20d3`\n- `q047_model_update.py` → `archive/programs/Q047/install-q047-model-v09/v0.9/payload/q047_model_update.py`\n  - source Git blob: `9e90cc1d5858e463e87328920f82a3333491e288`\n  - expected archive Git blob: `9e90cc1d5858e463e87328920f82a3333491e288`\n  - verified source SHA-256: `df246ad14dc83b9bcb3226af5787583b6dfdff0843116d7cd54f764435cc5c98`\n\n## Retirement evidence\n\nThe repository README at the cleanup baseline states that one-time installations are complete and that the historical installation files were awaiting workflow-aware cleanup. The current program registry does not register this installer as an active program. Current active validation is provided by the permanent public workflow and current validators.\n\n## Recovery\n\nOriginal source bytes remain retrievable from Git history, for example: `git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:<original-path>`.\n\nReactivation is not part of cleanup. If reactivation is ever required, make a separate explicit decision and restore from the recorded source commit rather than editing the archived payload in place.\n', 'archive/programs/Q048/install-q048-model-v010/v0.10/ARCHIVE_INFO.md': '# Q048 one-time model installer v0.10\n\n**ARCHIVED — NOT FOR ROUTINE EXECUTION**\n\nSource repository: `Morfindien/bubbleverse-model`  \nSource commit: `458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee`  \nCompletion evidence: `provenance/Q048_INSTALLATION_RECEIPT.json`  \nAccepted snapshot: `versions/accepted/v0.10/`\n\nInstallation admitted terminal UNSOLVED / UNRESOLVED v0.10; no physical model change or production restart.\n\n## Archived payload\n\nThe `payload/` subtree preserves each original repository-relative path without rewriting the retired program.\n\n- `.github/workflows/install-q048-model-v010.yml` → `archive/programs/Q048/install-q048-model-v010/v0.10/payload/.github/workflows/install-q048-model-v010.yml`\n  - source Git blob: `f9d6e3add055f83b7661056d3d563ddf33cefe81`\n  - expected archive Git blob: `f9d6e3add055f83b7661056d3d563ddf33cefe81`\n- `q048_model_update.py` → `archive/programs/Q048/install-q048-model-v010/v0.10/payload/q048_model_update.py`\n  - source Git blob: `03b47bd6275fa8725faffdbc2fb845ac239d187d`\n  - expected archive Git blob: `03b47bd6275fa8725faffdbc2fb845ac239d187d`\n  - verified source SHA-256: `3342ce4ffc33b918765310b81b216d83387a7e38ef8e4cdde8751020994a9c61`\n\n## Retirement evidence\n\nThe repository README at the cleanup baseline states that one-time installations are complete and that the historical installation files were awaiting workflow-aware cleanup. The current program registry does not register this installer as an active program. Current active validation is provided by the permanent public workflow and current validators.\n\n## Recovery\n\nOriginal source bytes remain retrievable from Git history, for example: `git show 458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee:<original-path>`.\n\nReactivation is not part of cleanup. If reactivation is ever required, make a separate explicit decision and restore from the recorded source commit rather than editing the archived payload in place.\n', 'provenance/cleanup/UPGRADE_COVERAGE.md': '# Bubbleverse 2.0 Cleanup Upgrade Coverage\n\nCoverage for cleanup run `BV-CLEANUP-BM-20261024-458d6c33-v330`.\n\n| Upgrade items | Status | Evidence / reason |\n|---|---|---|\n| 1–23 | PRESERVED_EXISTING / PARTIALLY_IMPLEMENTED | Q firewall, immutable state, provenance, handoff, capability honesty and current registries observed. START_CODES and run records prepared. |\n| 37–46 | IMPLEMENTED | Bounded context/reuse approach; no unnecessary scientific rerun; archive batch is limited to four verified installers. |\n| 51–70 | PARTIALLY_IMPLEMENTED | Directory map, archive policy, recovery, validation plan and machine records prepared. Real post-change execution remains blocked until checkout. |\n| 92–101 | IMPLEMENTED / VERIFIED | Dry-run installer, collision checks, rollback-safe scope, no provenance-gated deletion, human gate respected. |\n| 106–140 | PRESERVED_EXISTING / IMPLEMENTED | Dependency impact checked for active consumers; historical scientific bytes remain protected; technical-vs-scientific status kept separate. |\n| 146–150 | IMPLEMENTED | Explicit exit state, evidence-based report, blockers and cheapest next action recorded. |\n| 24–36, 47–50, 103–105, 142–145 | DEFERRED_SEPARATE_SCOPE | Scientific/model/research features are outside cleanup authority. |\n| 71–91 | NOT_APPLICABLE | Community/content/site/analytics work not part of repository cleanup. |\n\nNo item is marked implemented merely because it appears in the prompt.\n'}
ENTRYPOINT_REGISTRY = {'base_sha': '458d6c33ec95b641baa8c9a3c10ba0185d1ed9ee', 'entries': [{'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=test -f input=''", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-01', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'test', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=validate-model -f input=''", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-02', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'validate-model', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=model-status -f input=''", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-03', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'model-status', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=contradictions -f input=''", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-04', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'contradictions', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=provenance -f input=''", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-05', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'provenance', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=release-handoff -f input=''", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-06', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'release-handoff', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': 'gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=known-results -f input=\'{"quantity":"H0"}\'', 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-07', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'known-results', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': 'gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=contextualize-result -f input=\'{"quantity":"H0","value":1150.0,"sigma":0.81,"units":"km s^-1 Mpc^-1"}\'', 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-08', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'contextualize-result', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': 'gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=astronomy-catalog-context -f input=\'{"object":"Vega","radius_arcsec":5}\'', 'effect_class': 'EXTERNAL_READ', 'entry_id': 'BV-PUBLIC-09', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'astronomy-catalog-context', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=gaussian-tension -f input='73.50,0.81,67.24,0.35'", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-10', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'gaussian-tension', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=difference -f input='5,3'", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-11', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'difference', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=percent-shift -f input='67.24,73.50'", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-12', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'percent-shift', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=weighted-mean -f input='73.50,0.81,67.24,0.35'", 'effect_class': 'READ_ONLY', 'entry_id': 'BV-PUBLIC-13', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'weighted-mean', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=campaign -f input=''", 'effect_class': 'MAY_WRITE_VALIDATION_RECORD', 'entry_id': 'BV-PUBLIC-14', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'campaign', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': '.github/workflows/00-bubbleverse-model-start-public.yml', 'command': "gh workflow run 00-bubbleverse-model-start-public.yml --ref main -f operation=install-context-engine -f input=''", 'effect_class': 'MAY_WRITE_TECHNICAL_STATE', 'entry_id': 'BV-PUBLIC-15', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT/Q001-Q048', 'purpose': 'install-context-engine', 'q_access_end': 'Q048', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root / GitHub Actions checkout'}, {'canonical_source_path': 'tests/programs/formal_model_validate.py', 'command': 'python3 tests/programs/formal_model_validate.py', 'entry_id': 'BV-LOCAL-16', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT', 'purpose': 'local validation/maintenance', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root'}, {'canonical_source_path': 'tests/programs/q048_model_validate.py', 'command': 'python3 tests/programs/q048_model_validate.py', 'entry_id': 'BV-LOCAL-17', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT', 'purpose': 'local validation/maintenance', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root'}, {'canonical_source_path': 'tests/programs/model_campaign.py', 'command': 'python3 tests/programs/model_campaign.py validate', 'entry_id': 'BV-LOCAL-18', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT', 'purpose': 'local validation/maintenance', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root'}, {'canonical_source_path': 'tests/programs/', 'command': 'python3 -m unittest discover -s tests/programs -p "test*.py"', 'entry_id': 'BV-LOCAL-19', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT', 'purpose': 'local validation/maintenance', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root'}, {'canonical_source_path': 'repository_cleanup.py', 'command': 'python3 repository_cleanup.py --repo . --mode AUDIT', 'entry_id': 'BV-LOCAL-20', 'lifecycle': 'ACTIVE', 'program_q': 'CURRENT', 'purpose': 'local validation/maintenance', 'verification_state': 'DISCOVERED_AT_BASE_SHA', 'working_directory': 'repository root'}, {'canonical_source_path': '.github/workflows/apply-reviewed-repository-cleanup.yml', 'command': 'gh workflow run apply-reviewed-repository-cleanup.yml --ref main', 'entry_id': 'BV-HIST-21', 'lifecycle': 'HISTORICAL', 'program_q': 'HISTORICAL', 'purpose': 'retained workflow; retirement unconfirmed', 'verification_state': 'NOT_RUN', 'working_directory': 'GitHub Actions'}, {'canonical_source_path': '.github/workflows/q046-model-admission.yml', 'command': 'gh workflow run q046-model-admission.yml --ref main', 'entry_id': 'BV-HIST-22', 'lifecycle': 'HISTORICAL', 'program_q': 'HISTORICAL', 'purpose': 'retained workflow; retirement unconfirmed', 'verification_state': 'NOT_RUN', 'working_directory': 'GitHub Actions'}, {'canonical_source_path': '.github/workflows/repair-q048-final-selftests.yml', 'command': 'gh workflow run repair-q048-final-selftests.yml --ref main', 'entry_id': 'BV-HIST-23', 'lifecycle': 'HISTORICAL', 'program_q': 'HISTORICAL', 'purpose': 'retained workflow; retirement unconfirmed', 'verification_state': 'NOT_RUN', 'working_directory': 'GitHub Actions'}, {'canonical_source_path': 'archive/programs/Q045/install-q045-model-v07/v0.7/payload/.github/workflows/install-q045-model-v07.yml', 'command': 'gh workflow run install-q045-model-v07.yml --ref main', 'entry_id': 'BV-ARCH-24', 'lifecycle': 'ARCHIVED', 'program_q': 'Q045', 'purpose': 'historical one-time installer command', 'verification_state': 'HISTORICAL_ONLY', 'working_directory': 'historical repository root'}, {'canonical_source_path': 'archive/programs/Q046/install-q046-model-v08/v0.8/payload/.github/workflows/install-q046-model-v08.yml', 'command': 'gh workflow run install-q046-model-v08.yml --ref main', 'entry_id': 'BV-ARCH-25', 'lifecycle': 'ARCHIVED', 'program_q': 'Q046', 'purpose': 'historical one-time installer command', 'verification_state': 'HISTORICAL_ONLY', 'working_directory': 'historical repository root'}, {'canonical_source_path': 'archive/programs/Q046/install-q046-model-v08/v0.8/payload/q046_model_update.py', 'command': 'python3 q046_model_update.py --apply', 'entry_id': 'BV-ARCH-26', 'lifecycle': 'ARCHIVED', 'program_q': 'Q046', 'purpose': 'historical one-time installer source command', 'verification_state': 'HISTORICAL_ONLY', 'working_directory': 'historical repository root'}, {'canonical_source_path': 'archive/programs/Q047/install-q047-model-v09/v0.9/payload/.github/workflows/install-q047-model-v09.yml', 'command': 'gh workflow run install-q047-model-v09.yml --ref main', 'entry_id': 'BV-ARCH-27', 'lifecycle': 'ARCHIVED', 'program_q': 'Q047', 'purpose': 'historical one-time installer command', 'verification_state': 'HISTORICAL_ONLY', 'working_directory': 'historical repository root'}, {'canonical_source_path': 'archive/programs/Q047/install-q047-model-v09/v0.9/payload/q047_model_update.py', 'command': 'python3 q047_model_update.py --apply', 'entry_id': 'BV-ARCH-28', 'lifecycle': 'ARCHIVED', 'program_q': 'Q047', 'purpose': 'historical one-time installer source command', 'verification_state': 'HISTORICAL_ONLY', 'working_directory': 'historical repository root'}, {'canonical_source_path': 'archive/programs/Q048/install-q048-model-v010/v0.10/payload/.github/workflows/install-q048-model-v010.yml', 'command': 'gh workflow run install-q048-model-v010.yml --ref main', 'entry_id': 'BV-ARCH-29', 'lifecycle': 'ARCHIVED', 'program_q': 'Q048', 'purpose': 'historical one-time installer command', 'verification_state': 'HISTORICAL_ONLY', 'working_directory': 'historical repository root'}, {'canonical_source_path': 'archive/programs/Q048/install-q048-model-v010/v0.10/payload/q048_model_update.py', 'command': 'python3 q048_model_update.py --apply', 'entry_id': 'BV-ARCH-30', 'lifecycle': 'ARCHIVED', 'program_q': 'Q048', 'purpose': 'historical one-time installer source command', 'verification_state': 'HISTORICAL_ONLY', 'working_directory': 'historical repository root'}], 'repository': 'Morfindien/bubbleverse-model', 'run_id': 'BV-CLEANUP-BM-20261024-458d6c33-v330', 'schema_version': '1.0'}


def cp(repo: Path, *args, check=True):
    p = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed\n{p.stdout}{p.stderr}")
    return p


def git(repo: Path, *args):
    return cp(repo, *args).stdout.strip()


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_rel(value: str):
    p = Path(value)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise RuntimeError(f"Unsafe repository path: {value}")
    return p


def origin_ok(url: str):
    u = url.strip().lower().rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    return u in {
        "https://github.com/morfindien/bubbleverse-model",
        "git@github.com:morfindien/bubbleverse-model",
        "ssh://git@github.com/morfindien/bubbleverse-model",
    }


def tracked(repo: Path):
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=repo)
    return [x.decode() for x in raw.split(b"\0") if x]


def file_record(repo: Path, rel: str):
    p = repo / rel
    if not p.exists() and not p.is_symlink():
        raise RuntimeError(f"Tracked path missing: {rel}")
    if p.is_symlink():
        raw = os.readlink(p).encode()
        digest = hashlib.sha256(raw).hexdigest()
        size = len(raw)
        target = os.readlink(p)
    else:
        digest = sha256_file(p)
        size = p.stat().st_size
        target = None
    return {
        "path": rel,
        "git_blob_sha": git(repo, "hash-object", "--", rel),
        "sha256": digest,
        "size": size,
        "mode": oct(stat.S_IMODE(p.lstat().st_mode)),
        "symlink_target": target,
    }


def inventory(repo: Path, paths):
    return [file_record(repo, p) for p in paths]


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_audited_lineage(repo: Path):
    # The scientific/technical repository state audited at AUDITED_BASE must still
    # be an ancestor. Only bootstrap cleanup files may have changed since then.
    anc = cp(repo, "merge-base", "--is-ancestor", AUDITED_BASE, "HEAD", check=False)
    if anc.returncode != 0:
        raise RuntimeError(f"Audited base {AUDITED_BASE} is not an ancestor of current HEAD")

    changed = set(git(repo, "diff", "--name-only", f"{AUDITED_BASE}..HEAD").splitlines())
    unexpected = sorted(changed - BOOTSTRAP_ALLOWED)
    if unexpected:
        raise RuntimeError(
            "Repository changed outside the audited cleanup bootstrap surface since "
            f"{AUDITED_BASE}: " + ", ".join(unexpected)
        )
    return sorted(changed)


def accepted_identity(repo: Path):
    state = json.loads((repo / "accepted/model_state.json").read_text(encoding="utf-8"))
    if state.get("current_q") != "Q048" or state.get("accepted_model_version") != "v0.10":
        raise RuntimeError("Accepted scientific identity is no longer Q048/v0.10")
    if state.get("candidate_revision") != "R000010":
        raise RuntimeError("Accepted scientific revision is no longer R000010")
    return state


def receipt_gate(repo: Path):
    checks = [
        ("provenance/Q045_GITHUB_INSTALLATION_RECEIPT.json", "Q045", "v0.7"),
        ("provenance/Q046_INSTALLATION_RECEIPT.json", "Q046", "v0.8"),
        ("provenance/Q047_INSTALLATION_RECEIPT.json", "Q047", "v0.9"),
        ("provenance/Q048_INSTALLATION_RECEIPT.json", "Q048", "v0.10"),
    ]
    for path, q, version in checks:
        data = json.loads((repo / path).read_text(encoding="utf-8"))
        if data.get("target_q") != q:
            raise RuntimeError(f"{path}: target Q changed")
        observed = data.get("accepted_version") or data.get("accepted_after")
        if observed != version:
            raise RuntimeError(f"{path}: accepted version changed")
        if not (repo / "versions/accepted" / version).is_dir():
            raise RuntimeError(f"{path}: accepted snapshot missing")


def guard(repo: Path):
    repo = repo.resolve()
    if not (repo / ".git").exists():
        raise RuntimeError("Not a normal Git checkout")
    if not origin_ok(git(repo, "config", "--get", "remote.origin.url")):
        raise RuntimeError("Wrong repository origin")
    if git(repo, "branch", "--show-current") != "main":
        raise RuntimeError("Cleanup requires branch main")
    if git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("Working tree must be completely clean")

    bootstrap_changes = ensure_audited_lineage(repo)
    accepted_identity(repo)
    receipt_gate(repo)

    for m in MOVES:
        old = safe_rel(m["old_path"])
        new = safe_rel(m["new_path"])
        src, dst = repo / old, repo / new
        if not src.is_file():
            raise RuntimeError(f"Archive source missing: {old}")
        if dst.exists() or dst.is_symlink():
            raise RuntimeError(f"Archive destination already exists: {new}")
        blob = git(repo, "hash-object", "--", old.as_posix())
        if blob != m["git_blob_sha"]:
            raise RuntimeError(f"Archive source Git blob changed: {old}")
        expected_sha = m.get("sha256")
        if expected_sha and sha256_file(src) != expected_sha:
            raise RuntimeError(f"Archive source SHA-256 changed: {old}")

    # New destinations must still be absent.
    for rel in EMBEDDED_TEXT_FILES:
        if rel in {"README.md", "tests/TEST_PLAN_CURRENT.md", "provenance/cleanup/UPGRADE_COVERAGE.md"}:
            continue
        p = repo / rel
        if p.exists() or p.is_symlink():
            raise RuntimeError(f"New cleanup destination already exists: {rel}")
    if (repo / "provenance/cleanup" / RUN_ID).exists():
        raise RuntimeError("Cleanup run directory already exists")

    return repo, bootstrap_changes


def validators(repo: Path):
    commands = [
        [sys.executable, "tests/programs/formal_model_validate.py"],
        [sys.executable, "tests/programs/q048_model_validate.py"],
        [sys.executable, "tests/programs/model_campaign.py", "validate"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests/programs", "-p", "test*.py"],
    ]
    results = []
    for command in commands:
        p = subprocess.run(command, cwd=repo, text=True, capture_output=True)
        row = {
            "command": " ".join(command),
            "returncode": p.returncode,
            "stdout_tail": p.stdout[-6000:],
            "stderr_tail": p.stderr[-6000:],
            "status": "PASS" if p.returncode == 0 else "FAIL",
        }
        results.append(row)
        if p.returncode:
            raise RuntimeError(
                f"Validation failed: {' '.join(command)}\n{p.stdout}\n{p.stderr}"
            )
    return results


def write_embedded(repo: Path):
    for rel, content in EMBEDDED_TEXT_FILES.items():
        if rel == "provenance/cleanup/UPGRADE_COVERAGE.md":
            continue
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def classify(rel: str):
    by_old = {m["old_path"]: m for m in MOVES}
    if rel in by_old:
        return "ARCHIVE_RETIRED", "ARCHIVE"
    if rel in BOOTSTRAP_ALLOWED:
        return "KEEP_REQUIRED_BOOTSTRAP", "KEEP"
    if rel == "README.md":
        return "KEEP_REQUIRED_ROOT", "UPDATE"
    if rel == "tests/TEST_PLAN_CURRENT.md":
        return "KEEP_CORRECT_LOCATION", "UPDATE"
    if rel in {".gitattributes", ".gitignore", "bubbleverse_model_program_registry.json", "repository_cleanup.py"}:
        return "KEEP_REQUIRED_ROOT", "KEEP"
    if rel in {d["path"] for d in DEFERRED}:
        return "DEFER_BLOCKED", "KEEP"
    if rel.startswith(("accepted/", "candidate/", "model/", "evidence/", "provenance/", "release/", "versions/accepted/", "tests/results/", "changelog/")):
        return "KEEP_PROTECTED", "KEEP"
    return "KEEP_CORRECT_LOCATION", "KEEP"


def runtime_records(repo: Path, head_before: str, bootstrap_changes, before_rows, protected_before, pre_checks):
    run_dir = repo / "provenance/cleanup" / RUN_ID
    run_dir.mkdir(parents=True, exist_ok=False)

    move_map = {m["old_path"]: m for m in MOVES}
    relocation = []
    for row in before_rows:
        placement, operation = classify(row["path"])
        item = dict(row)
        item.update({"placement_decision": placement, "operation": operation})
        if row["path"] in move_map:
            m = move_map[row["path"]]
            item.update({
                "new_path": m["new_path"],
                "expected_destination_git_blob_sha": m["git_blob_sha"],
                "batch_id": m["bundle_id"],
            })
        relocation.append(item)

    for rel in [
        "START_CODES.md",
        "docs/REPOSITORY_STRUCTURE.md",
        "archive/programs/INDEX.md",
        "archive/programs/Q045/install-q045-model-v07/v0.7/ARCHIVE_INFO.md",
        "archive/programs/Q046/install-q046-model-v08/v0.8/ARCHIVE_INFO.md",
        "archive/programs/Q047/install-q047-model-v09/v0.9/ARCHIVE_INFO.md",
        "archive/programs/Q048/install-q048-model-v010/v0.10/ARCHIVE_INFO.md",
    ]:
        relocation.append({
            "path": rel,
            "placement_decision": "KEEP_CORRECT_LOCATION",
            "operation": "ADD",
        })

    write_json(run_dir / "RELOCATION_MANIFEST.json", {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "audited_base_sha": AUDITED_BASE,
        "bootstrap_head_before": head_before,
        "entries": relocation,
    })
    write_json(run_dir / "PROTECTED_INVENTORY.json", {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "records": protected_before,
    })
    write_json(run_dir / "VALIDATION_RESULTS.json", {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "baseline": pre_checks,
        "post_change": [],
    })
    write_json(run_dir / "ENTRYPOINT_REGISTRY.json", ENTRYPOINT_REGISTRY)
    (run_dir / "UPGRADE_COVERAGE.md").write_text(
        EMBEDDED_TEXT_FILES["provenance/cleanup/UPGRADE_COVERAGE.md"],
        encoding="utf-8",
    )
    write_json(run_dir / "RUN_MANIFEST.json", {
        "schema_version": "1.0",
        "run_id": RUN_ID,
        "prompt_id": "BV-REPOSITORY-CLEANUP",
        "prompt_version": "3.3.0",
        "repository": TARGET_REPO,
        "audited_base_sha": AUDITED_BASE,
        "bootstrap_head_before": head_before,
        "bootstrap_changes_since_audit": bootstrap_changes,
        "mode": "CLEAN",
        "target_q": "UNSET",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_change": False,
        "archive_moves": len(MOVES),
        "deletions": 0,
        "delivery_state": "LOCAL_STAGED_NOT_COMMITTED",
    })
    return run_dir


def protected_check(repo: Path, records):
    for row in records:
        now = file_record(repo, row["path"])
        if now["sha256"] != row["sha256"] or now["git_blob_sha"] != row["git_blob_sha"]:
            raise RuntimeError(f"Protected file changed: {row['path']}")


def apply(repo: Path):
    repo, bootstrap_changes = guard(repo)
    head_before = git(repo, "rev-parse", "HEAD")

    baseline_paths = tracked(repo)
    before_rows = inventory(repo, baseline_paths)

    mutable = {m["old_path"] for m in MOVES} | {"README.md", "tests/TEST_PLAN_CURRENT.md"}
    protected_paths = [p for p in baseline_paths if p not in mutable]
    protected_before = inventory(repo, protected_paths)

    pre_checks = validators(repo)

    try:
        for m in MOVES:
            (repo / m["new_path"]).parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "mv", "--", m["old_path"], m["new_path"]],
                cwd=repo,
                check=True,
            )
            if git(repo, "hash-object", "--", m["new_path"]) != m["git_blob_sha"]:
                raise RuntimeError(f"Archive byte identity changed: {m['new_path']}")
            if m.get("sha256") and sha256_file(repo / m["new_path"]) != m["sha256"]:
                raise RuntimeError(f"Archive SHA-256 changed: {m['new_path']}")

        write_embedded(repo)

        cleanup_index = repo / "provenance/cleanup/INDEX.md"
        if cleanup_index.exists():
            old = cleanup_index.read_text(encoding="utf-8")
            if RUN_ID not in old:
                cleanup_index.write_text(
                    old.rstrip()
                    + f"\n\n- `{RUN_ID}` — Q045–Q048 retired-installer archive cleanup; "
                      f"see `{RUN_ID}/RUN_MANIFEST.json`.\n",
                    encoding="utf-8",
                )
        else:
            cleanup_index.parent.mkdir(parents=True, exist_ok=True)
            cleanup_index.write_text(
                f"# Cleanup Memory Index\n\n- `{RUN_ID}` — Q045–Q048 retired-installer "
                f"archive cleanup; see `{RUN_ID}/RUN_MANIFEST.json`.\n",
                encoding="utf-8",
            )

        run_dir = runtime_records(
            repo, head_before, bootstrap_changes, before_rows, protected_before, pre_checks
        )

        protected_check(repo, protected_before)
        post_checks = validators(repo)
        protected_check(repo, protected_before)

        results_path = run_dir / "VALIDATION_RESULTS.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        results["post_change"] = post_checks
        write_json(results_path, results)

        report = f"""# Bubbleverse Model Repository Cleanup — Applied Result

**CLEANUP_VERIFIED**  
**Delivery state: LOCAL_ONLY / STAGED_FOR_REVIEW**

Repository: `{TARGET_REPO}`  
Audited scientific/technical base: `{AUDITED_BASE}`  
Bootstrap HEAD before cleanup: `{head_before}`  
Run ID: `{RUN_ID}`

Four verified retired one-time installer bundles (Q045–Q048) were archived byte-for-byte. Eight source files were relocated; zero scientific/history files were deleted.

The accepted scientific state remains v0.10 / R000010 through Q048, with Q048 terminal UNSOLVED / UNRESOLVED.

Baseline and post-change validation passed:

- `python3 tests/programs/formal_model_validate.py`
- `python3 tests/programs/q048_model_validate.py`
- `python3 tests/programs/model_campaign.py validate`
- `python3 -m unittest discover -s tests/programs -p "test*.py"`

`tests/TEST_PLAN_CURRENT.md` was corrected to Q048/v0.10. `START_CODES.md`, `docs/REPOSITORY_STRUCTURE.md`, archive metadata and cleanup memory were installed.

No commit or push was performed. The cleanup is staged locally for review.
"""
        (run_dir / "REPORT.md").write_text(report, encoding="utf-8")

        subprocess.run(
            [
                "git", "add", "-A", "--",
                "README.md",
                "START_CODES.md",
                "docs/REPOSITORY_STRUCTURE.md",
                "tests/TEST_PLAN_CURRENT.md",
                "archive/programs",
                "provenance/cleanup",
            ],
            cwd=repo,
            check=True,
        )
        diff_check = cp(repo, "diff", "--cached", "--check", check=False)
        if diff_check.returncode:
            raise RuntimeError(
                "git diff --cached --check failed\n"
                + diff_check.stdout
                + diff_check.stderr
            )

        patch_path = run_dir / "APPLIED.patch"
        with patch_path.open("wb") as f:
            subprocess.run(
                ["git", "diff", "--cached", "--binary"],
                cwd=repo,
                stdout=f,
                check=True,
            )
        subprocess.run(
            ["git", "add", "--", patch_path.relative_to(repo).as_posix()],
            cwd=repo,
            check=True,
        )

        print("CLEANUP_APPLIED_AND_STAGED")
        print(f"audited_base={AUDITED_BASE}")
        print(f"bootstrap_head={head_before}")
        print(f"run_record={run_dir.relative_to(repo)}")
        print("No commit or push was performed.")

    except Exception:
        print("APPLY_FAILED: attempting scoped rollback", file=sys.stderr)
        rollback(repo, strict=False)
        raise


def preview(repo: Path):
    repo, bootstrap_changes = guard(repo)
    print("PREVIEW_OK")
    print(f"repository={TARGET_REPO}")
    print(f"audited_base={AUDITED_BASE}")
    print(f"current_head={git(repo, 'rev-parse', 'HEAD')}")
    print("allowed_changes_since_audit=" + ",".join(bootstrap_changes))
    print(f"archive_moves={len(MOVES)}")
    for m in MOVES:
        print(f"ARCHIVE {m['old_path']} -> {m['new_path']}")
    for d in DEFERRED:
        print(f"DEFER {d['path']}: {d['reason']}")
    print("No files changed.")


def rollback(repo: Path, strict=True):
    repo = repo.resolve()
    if not (repo / ".git").exists() or not origin_ok(git(repo, "config", "--get", "remote.origin.url")):
        raise RuntimeError("Wrong repository for rollback")

    known = [
        "README.md",
        "START_CODES.md",
        "docs/REPOSITORY_STRUCTURE.md",
        "tests/TEST_PLAN_CURRENT.md",
        "archive/programs",
        "provenance/cleanup",
    ]
    for m in MOVES:
        known.extend([m["old_path"], m["new_path"]])

    cp(repo, "reset", "HEAD", "--", *known, check=False)

    for m in reversed(MOVES):
        old, new = repo / m["old_path"], repo / m["new_path"]
        if new.exists() and not old.exists():
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(new), str(old))

    for rel in ["README.md", "tests/TEST_PLAN_CURRENT.md"]:
        data = subprocess.check_output(["git", "show", f"HEAD:{rel}"], cwd=repo)
        (repo / rel).write_bytes(data)

    for rel in ["START_CODES.md", "docs/REPOSITORY_STRUCTURE.md", "archive/programs"]:
        p = repo / rel
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    run_dir = repo / "provenance/cleanup" / RUN_ID
    if run_dir.exists():
        shutil.rmtree(run_dir)

    idx = repo / "provenance/cleanup/INDEX.md"
    if idx.exists():
        lines = [ln for ln in idx.read_text(encoding="utf-8").splitlines() if RUN_ID not in ln]
        content = "\n".join(lines).rstrip()
        if content == "# Cleanup Memory Index":
            idx.unlink()
        else:
            idx.write_text(content + "\n", encoding="utf-8")

    if strict and git(repo, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("Scoped rollback left repository changes; inspect manually")

    print("SCOPED_ROLLBACK_COMPLETE")


def self_test():
    olds, news = set(), set()
    for m in MOVES:
        safe_rel(m["old_path"])
        safe_rel(m["new_path"])
        assert m["old_path"] not in olds
        assert m["new_path"] not in news
        assert m["new_path"].startswith("archive/programs/")
        assert "/payload/" in m["new_path"]
        assert len(m["git_blob_sha"]) == 40
        olds.add(m["old_path"])
        news.add(m["new_path"])

    assert len(MOVES) == 8
    assert BOOTSTRAP_ALLOWED == {
        "APPLY_CLEANUP.py",
        ".github/workflows/apply-bubbleverse-model-cleanup-v330.yml",
    }
    assert "README.md" in EMBEDDED_TEXT_FILES
    assert "START_CODES.md" in EMBEDDED_TEXT_FILES
    print("PACKAGE_SELF_TEST=PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--preview", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--rollback", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    repo = Path(args.repo)
    if args.preview:
        return preview(repo)
    if args.apply:
        return apply(repo)
    if args.rollback:
        return rollback(repo)


if __name__ == "__main__":
    main()
