# battery-control

Python workspace for battery storage control and optimisation. Data loaders read the committed workbooks under `data/` into typed dataclasses.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/) for environments and dependency management

## Development setup

```bash
uv sync
```

Run the same checks as CI locally:

```bash
uv run ruff check .
uv run ruff format --check .
uv run python -m unittest discover -s smoke_tests -t . -v
uv run python -m unittest discover -s tests -t . -v
```

## Layout

- `src/battery_control/` — installable package; `data_loader` subpackage holds ingestion code
- `data/battery_specification.xlsx` — battery parameters (dispatch fields used by loaders)
- `data/market_prices.xlsx` — Market 1 (half-hourly) and Market 2 (hourly) prices
- `smoke_tests/` — fast checks that the environment and package are usable
- `tests/` — unittest suite, mirroring `src/`

## If I had more time

- Add validation on loaded spreadsheets: ensure power and capacity values are positive, and that energy-loss fractions lie in `[0, 1)` before converting them to efficiencies.
- Extend the same idea to market price data (monotonic timestamps, sensible price ranges including negative electricity prices, expected row counts) once alignment and optimisation depend on it.