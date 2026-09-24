# Q041 Bubbleverse Model Update — Installation Handoff

This package replaces the earlier blocked-only Q041 installer.

## Scientific decision

- Target: `Q041`
- Previous accepted state: `Q040 / v0.2 / R000002`
- Candidate: `v0.3 / R000003`
- Update class: `EVIDENCE_ONLY_UPDATE`
- Physical model change: `NONE`
- Q041 result: `CONTROLLED_NO_SCIENTIFIC_RESULT`
- Q041 technical failure: `false`
- Downstream portability question: unresolved

The supplied PDFs are the authorized manuscript source for this run. The primary Q-Journal
SHA-256 is:

`fca0c3a8999336462982287256bd0c946e284fb99cf9e23e3f401d6cab584465`

## Install

Place `install_q041_model_update.py` in the root of a clean local clone of
`Morfindien/bubbleverse-model`, then run:

```bash
python install_q041_model_update.py
```

To push the finished commits with your own GitHub credentials:

```bash
python install_q041_model_update.py --push
```

The installer performs candidate-first integration, atomic promotion, regression/formal/Q041
validation, immutable v0.3 snapshot creation, real Git provenance, and rollback to the
candidate state if promotion validation fails.

Installer SHA-256:

`4f1c12d8c046668445388671055ffbe02de1f32352656c22d466982000867f2b`

The PDFs do not need to be committed to the model repository. Optional runtime hash
re-verification is available with `--q-journal`, `--main-book`, and `--appendices`.
