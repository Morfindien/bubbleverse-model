# Current validation plan: Q045/v0.7

Run `python3 tests/programs/formal_model_validate.py`, `python3 tests/programs/q045_model_validate.py`, `python3 tests/programs/model_campaign.py validate`, and `python3 -m unittest discover -s tests/programs -p "test*.py"`.

The permanent public workflow `test` operation performs read-only current validation and system healthchecks. Historical registered gates and source lineage remain required. Regression tests use disposable copies for failure injection. Original numerical trajectories are not rerun.
