import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.market_alignment.constants import (
    JANUARY_2018_END_MARKET_1,
    JANUARY_2018_START,
    MARKET_1_INTERVAL,
    january_observation_count,
)
from battery_control.results.reporting import (
    plot_results_png,
    print_run_summary,
    write_results_csv,
)
from battery_control.results.results_table import build_january_results_table
from battery_control.results.trading_revenue import TradingRevenue
from tests.battery_control.battery_optimisation.test_support import (
    aligned_prices,
    revenue_from_markets,
    toy_battery_config,
)


class TestResultsReporting(unittest.TestCase):
    def test_january_table_timestamps_and_revenues(self) -> None:
        expected_rows: int = january_observation_count(
            JANUARY_2018_START,
            JANUARY_2018_END_MARKET_1,
            MARKET_1_INTERVAL,
        )
        hour_count: int = expected_rows // 2
        prices = aligned_prices(
            [10.0] * expected_rows,
            [5.0] * hour_count,
        )
        result = OptimisationResult(
            market_1_charge_mw=np.linspace(0.0, 1.0, expected_rows),
            market_1_discharge_mw=np.linspace(1.0, 0.0, expected_rows),
            market_2_charge_mw=np.full(hour_count, 0.5),
            market_2_discharge_mw=np.full(hour_count, 0.25),
            state_of_charge_mwh=np.linspace(1.0, 2.0, expected_rows + 1),
            total_trading_profit_gbp=123.0,
            solver_status=0,
            solver_message="synthetic",
        )
        revenue = TradingRevenue.from_optimisation(result, prices)
        frame = build_january_results_table(result, prices, revenue)

        self.assertEqual(len(frame), expected_rows)
        self.assertEqual(frame["interval_start"].iloc[0], JANUARY_2018_START)
        self.assertEqual(frame["interval_start"].iloc[-1], JANUARY_2018_END_MARKET_1)
        combined_csv: float = float(
            frame["market_1_revenue_gbp"].sum() + frame["market_2_revenue_gbp"].sum()
        )
        self.assertAlmostEqual(combined_csv, revenue.total_trading_profit_gbp, places=4)
        self.assertAlmostEqual(
            combined_csv,
            revenue_from_markets(result, prices),
            places=4,
        )

    def test_market_2_power_repeated_and_soc_boundaries(self) -> None:
        prices = aligned_prices([0.0, 100.0], [0.0])
        result = BatteryOptimiser().optimise(toy_battery_config(), prices)
        revenue = TradingRevenue.from_optimisation(result, prices)
        frame = build_january_results_table(result, prices, revenue)
        self.assertEqual(
            frame["market_2_charge_mw"].iloc[0],
            frame["market_2_charge_mw"].iloc[1],
        )
        self.assertAlmostEqual(
            frame["soc_end_mwh"].iloc[0],
            frame["soc_start_mwh"].iloc[1],
        )

    def test_csv_and_plot_outputs(self) -> None:
        prices = aligned_prices([0.0, 100.0], [0.0])
        config = toy_battery_config()
        result = BatteryOptimiser().optimise(config, prices)
        revenue = TradingRevenue.from_optimisation(result, prices)
        frame = build_january_results_table(result, prices, revenue)
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "january_2018_results.csv"
            png_path = Path(tmp) / "january_2018_results.png"
            write_results_csv(frame, csv_path)
            plot_results_png(frame, png_path)
            loaded = pd.read_csv(csv_path, parse_dates=["interval_start"])
            self.assertEqual(len(loaded), 2)
            payload = png_path.read_bytes()
            self.assertEqual(payload[:8], b"\x89PNG\r\n\x1a\n")

    def test_summary_print_contains_key_lines(self) -> None:
        prices = aligned_prices([0.0, 100.0], [0.0])
        config = toy_battery_config()
        result = BatteryOptimiser().optimise(config, prices)
        revenue = TradingRevenue.from_optimisation(result, prices)
        buffer = StringIO()
        with patch("sys.stdout", buffer):
            print_run_summary(
                config,
                result,
                revenue,
                Path("output/january_2018_results.csv"),
                Path("output/january_2018_results.png"),
            )
        text = buffer.getvalue()
        self.assertIn("Market 1 trading profit", text)
        self.assertIn("Total trading profit", text)
