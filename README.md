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
uv run python -m unittest discover -s smoke_tests -v
uv run python -m unittest discover -s tests -t . -v
```

## Layout

- `src/battery_control/` — installable package (src layout)
- `data/battery_specification.xlsx` — battery parameters (dispatch fields used by loaders)
- `data/market_prices.xlsx` — Market 1 (half-hourly) and Market 2 (hourly) prices
- `smoke_tests/` — fast checks that the environment and package are usable
- `tests/` — unittest suite, mirroring `src/`

## Data loading

```python
from pathlib import Path

from battery_control.battery_config import load_battery_config
from battery_control.market_prices import load_market_prices

battery = load_battery_config(Path("data/battery_specification.xlsx"))
prices = load_market_prices(Path("data/market_prices.xlsx"))
```

Battery charging and discharging values in the specification workbook are **fractional energy losses** (for example `0.05` means 5% loss). Loaders convert them to round-trip efficiency as `1 - loss` (so `0.95` in each direction).