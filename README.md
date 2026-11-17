# battery-control

Time-boxed technical spike for Aurora Energy: a reproducible Python workspace for battery control and optimisation work. This repository currently contains project setup only—no modelling, data ingestion, or reporting yet.

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
uv run python -c "import battery_control"
uv run python -m unittest discover -s tests -v
```

## Layout

- `src/battery_control/` — installable package (src layout)
- `tests/` — unittest suite, mirroring `src/`