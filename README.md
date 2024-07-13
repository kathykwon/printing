# printing
printing g's

# Repo setup
1. `python3 -m venv.venv`
2. `source ./.venv/bin/activate`
3. `poetry env use 3.12`
4. `pre-commit install`
5. `cp env.default .env`

# Run cli command
1. `poetry install`
2. Run `printing -h` for help.

# Quick start
`printing price -s aapl`
will display the price information for AAPL.

`printing options -s tsla --type call --date 2024-07-19 --c 10`
will display 10 options information for tesla calls on that date
