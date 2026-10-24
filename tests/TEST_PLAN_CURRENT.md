# Current validation plan: Q049/v0.11

Run `python3 tests/programs/formal_model_validate.py`, `python3 tests/programs/q049_model_validate.py`, `python3 tests/programs/model_campaign.py validate`, and `python3 -m unittest discover -s tests/programs -p "test*.py"`.

The current campaign also verifies historical Q048 through its immutable v0.10 snapshot. Failure-injection tests reject altered certificate bytes, understated caps and unsupported scope upgrades. Stored scientific checks are reused without rerunning the original producer or native trajectories. The healthcheck may write separate test logs but leaves scientific state unchanged.
