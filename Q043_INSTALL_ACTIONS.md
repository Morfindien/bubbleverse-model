# Install Q043 through GitHub Actions

These two files install the reviewed model package without a local Git client.

## 1. Upload the package

In **Morfindien/bubbleverse-model**, on **main**, choose **Add file → Upload files**.
Upload `Q043_model_update.bundle` to the repository root and commit it.
Keep its exact filename. It is a Git-history file, not a ZIP.

## 2. Add the workflow

Choose **Add file → Create new file**. Enter this complete filename:

```text
.github/workflows/q043-install-model.yml
```

Paste the entire contents of `q043-install-model.yml` and commit to main.
Do not edit model files or other repository files between these uploads and installation.

## 3. Start

Open **Actions → BUBBLEVERSE — INSTALL Q043 MODEL → Run workflow**.
Select branch **main**, mode **install**, then **Run workflow**.
Mode **validate** performs the checks without publishing.

The workflow verifies the bundle hash and baseline, imports the original reviewed Git history,
runs 22 regression tests and the 20-test public healthcheck, then writes the model through a normal push.
It never uses force push. Concurrent changes, failed tests, branch protection or denied token writes block installation.
It requests the repository's built-in GITHUB_TOKEN with contents:write; no personal access token is required by this workflow.
Repository or organization policy can still deny a direct write to main.

## Result

Only a verified successful installation advances remote accepted state to **v0.5 / R000005 / Q001–Q043**.
The Actions summary and downloaded result artifact show the actual outcome.
`provenance/Q043_REMOTE_INSTALLATION_RECEIPT.json` is created after the model push is verified.
Older report files deliberately preserve their historical publication-blocked status.

Q043 adds internal technical evidence and provenance. No new physical result is claimed.
Numerical production remains unauthorized. Morfindien/Bubbleverse is untouched.

If the baseline has changed beyond these two uploads, the workflow stops for a fresh compatibility review.
Rerunning the exact installed model validates it and reports ALREADY_CURRENT.

Bundle SHA256:
```text
d18c0ad4e3438d86cbec4a137800abf652fe6ade70b88cc61f16bfb6d3f3c459
```

## Installer verification

Seven local installation integration tests passed against disposable bare Git remotes, including denied writes, changed baseline, tampered package, validate-only mode, successful installation and an idempotent rerun. A separate read-only code review found no Critical or Important defects. The new installer has not yet run on GitHub Actions.

Technical reference: https://docs.github.com/en/actions/tutorials/authenticate-with-github_token
