# battery-control

Python workspace for battery storage control and optimisation. Data loaders read the committed workbooks under `data/` into typed dataclasses; the January 2018 MILP produces auditable CSV and PNG outputs.

## Assumptions

- Optimisation uses the January 2018 slice from row zero of the committed spreadsheets (see `market_alignment` constants).
- Market 1 and Market 2 are aligned positionally (two half-hours per hour), not by merging timestamps.
- Parallel trading MILP with binary half-hour charge/discharge modes, combined power limits, and 50% initial and final state of charge.
- Interval revenue uses published half-hour and hourly prices with the model’s dispatch (exploratory analysis, not a production trading system).

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) for environments and dependency management

## Installation

From the repository root (directory containing `pyproject.toml`):

```bash
uv sync --frozen
```

## Run the model

From the repository root:

```bash
uv run python -m battery_control
```

Optional arguments:

```bash
uv run python -m battery_control --output-dir output
```

### Outputs

Written under `output/` by default (gitignored):

| File | Description |
|------|-------------|
| `january_2018_results.csv` | Half-hourly dispatch, SOC boundaries, and Market 1 / Market 2 interval revenues |
| `january_2018_results.png` | Top: first 48 h net dispatch; bottom: cumulative daily profit for January |

## Tests

Run the same checks as CI locally:

```bash
uv run ruff check .
uv run ruff format --check .
uv run python -m unittest discover -s smoke_tests -t . -v
uv run python -m unittest discover -s tests -t . -v
```

## Layout

- `src/battery_control/` — installable package (`data_loader`, `market_alignment`, `battery_optimisation`, `results`)
- `data/battery_specification.xlsx` — battery parameters
- `data/market_prices.xlsx` — Market 1 (half-hourly) and Market 2 (hourly) prices
- `smoke_tests/` — fast checks that the environment and package are usable
- `tests/` — unittest suite, mirroring `src/`

## If I had more time

- Add validation on loaded spreadsheets: ensure power and capacity values are positive, and that energy-loss fractions lie in `[0, 1)` before converting them to efficiencies.
- Extend the same idea to market price data (monotonic timestamps, sensible price ranges including negative electricity prices, expected row counts) once alignment and optimisation depend on it.