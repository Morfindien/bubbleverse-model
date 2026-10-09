# Current validation plan: Q043/v0.5

Run `python3 tests/programs/model_campaign.py validate`, `python3 tests/programs/q043_model_validate.py`, and `python3 -m unittest discover -s tests/programs -p "test*.py"`.

The permanent public workflow `test` operation invokes current validation and 20 system healthchecks; it is non-destructive. Q043 has 11 source/qualification/preservation gates. Q042 historical checks remain mandatory. All 22 regressions exercise real state and restore injected changes. Original numerical trajectories are not rerun and no cosmological inference follows from technical passes.
