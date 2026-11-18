# battery-control

Python workspace for battery storage control and optimisation. This repository currently holds project scaffolding; modelling, data ingestion, and reporting will be added incrementally.

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
uv run python -m unittest discover -s tests -v
```

## Layout

- `src/battery_control/` — installable package (src layout)
- `smoke_tests/` — fast checks that the environment and package are usable
- `tests/` — unittest suite, mirroring `src/`