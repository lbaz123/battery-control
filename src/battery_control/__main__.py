import argparse
import sys
from pathlib import Path

from battery_control.battery_optimisation.battery_optimisation_error import (
    BatteryOptimisationError,
)
from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.data_loader.battery_config.battery_config_loader import (
    BatteryConfigLoader,
)
from battery_control.data_loader.market_prices.market_prices_loader import (
    MarketPricesLoader,
)
from battery_control.market_alignment.market_prices_aligner import MarketPricesAligner
from battery_control.results.constants import RESULTS_CSV_NAME, RESULTS_PLOT_NAME
from battery_control.results.results_csv_writer import ResultsCsvWriter
from battery_control.results.results_plotter import ResultsPlotter
from battery_control.results.results_table_builder import ResultsTableBuilder
from battery_control.results.run_summary_printer import RunSummaryPrinter
from battery_control.results.trading_revenue import TradingRevenue


def _repository_root() -> Path:
    """Locate the repository root (directory containing ``pyproject.toml``).

    Returns:
        Path: Repository root path.

    Raises:
        FileNotFoundError: If no parent contains ``pyproject.toml``.
    """
    candidate: Path = Path(__file__).resolve()
    for path in (candidate, *candidate.parents):
        if (path / "pyproject.toml").is_file():
            return path
    msg: str = "Could not locate repository root (no pyproject.toml in parents)"
    raise FileNotFoundError(msg)


def main(argv: list[str] | None = None) -> int:
    """Run January optimisation and write CSV and PNG results.

    Args:
        argv (list[str] | None): Command-line arguments; ``None`` uses ``sys.argv``.

    Returns:
        int: ``0`` on success, ``1`` if optimisation fails.
    """
    parser = argparse.ArgumentParser(
        description="Run January 2018 battery trading optimisation and export results.",
    )
    root: Path = _repository_root()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(root / "output"),
        help="Directory for CSV and PNG outputs (default: output).",
    )
    args = parser.parse_args(argv)
    battery_spec: Path = root / "data" / "battery_specification.xlsx"
    market_prices: Path = root / "data" / "market_prices.xlsx"
    try:
        config = BatteryConfigLoader().load(battery_spec)
        prices = MarketPricesLoader().load(market_prices)
        aligned = MarketPricesAligner().align(prices)
        result = BatteryOptimiser().optimise(config, aligned)
        revenue = TradingRevenue.from_optimisation(result, aligned)
        frame = ResultsTableBuilder().build(result, aligned, revenue)
        csv_path: Path = args.output_dir / RESULTS_CSV_NAME
        plot_path: Path = args.output_dir / RESULTS_PLOT_NAME
        RunSummaryPrinter().print_summary(
            config,
            result,
            revenue,
            csv_path,
            plot_path,
        )
        ResultsCsvWriter().write(frame, csv_path)
        ResultsPlotter().save(frame, plot_path)
    except BatteryOptimisationError as exc:
        print(f"Optimisation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
