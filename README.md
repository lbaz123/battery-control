# battery-control

Python workspace for battery storage control and optimisation. Data loaders read the committed workbooks under `data/` into typed dataclasses; the January 2018 MILP produces auditable CSV and PNG outputs.

## Assumptions

- **January window:** Optimisation uses January 2018 only. After the price loader drops invalid rows, the aligner takes the first *N* observations per market, where *N* and the start/end timestamps come from `market_alignment.constants`. Those rows must match the expected regular time grid (not a free-form timestamp merge).
- **Battery parameters:** A single static configuration from `data/battery_specification.xlsx` (label/value table). Charging and discharging efficiencies are `1 −` workbook loss fractions. No degradation, ramp limits, or time-varying capacity.
- **Market pairing:** Market 1 (half-hourly) and Market 2 (hourly) are aligned by index: half-hours `2h` and `2h + 1` share Market 2 row `h`. Market 2 charge/discharge variables apply to both half-hours in that hour (power limits, state-of-charge dynamics, and revenue).
- **Optimisation model:** Parallel trading MILP solved with SciPy HiGHS (`scipy.optimize.milp`). One binary per half-hour selects combined charge vs combined discharge across both markets (`p1c + p2c` vs `p1d + p2d`), subject to shared charge/discharge power limits and energy capacity. Initial and final state of charge are fixed at 50% of capacity.
- **Units and economics:** Prices in GBP/MWh; powers in MW; energy in MWh. Interval revenue in outputs uses published prices and the optimised dispatch (`TradingRevenue`); the solver objective uses the same pricing rule. No grid fees, reserves, or other real-market costs.
- **Data quality:** Loaders perform minimal validation (see “If I had more time”). Negative prices and imperfect spreadsheet values are accepted if parsing succeeds.
- **Scope:** Exploratory analysis using committed workbooks under `data/`, not a production trading or control system.

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