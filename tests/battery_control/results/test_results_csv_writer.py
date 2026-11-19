import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.results.results_csv_writer import ResultsCsvWriter
from battery_control.results.results_table_builder import ResultsTableBuilder
from battery_control.results.trading_revenue import TradingRevenue
from tests.battery_control.battery_optimisation.test_support import (
    aligned_prices,
    toy_battery_config,
)


class TestResultsCsvWriter(unittest.TestCase):
    def test_writes_expected_row_count(self) -> None:
        prices = aligned_prices([0.0, 100.0], [0.0])
        result = BatteryOptimiser().optimise(toy_battery_config(), prices)
        revenue = TradingRevenue.from_optimisation(result, prices)
        frame = ResultsTableBuilder().build(result, prices, revenue)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "january_2018_results.csv"
            ResultsCsvWriter().write(frame, path)
            loaded = pd.read_csv(path, parse_dates=["interval_start"])
            self.assertEqual(len(loaded), 2)

    def test_csv_never_writes_negative_zero(self) -> None:
        frame = pd.DataFrame(
            {
                "interval_start": pd.to_datetime(["2018-01-01 00:00:00"]),
                "market_1_charge_mw": [-0.0],
                "market_1_discharge_mw": [0.0],
                "market_2_charge_mw": [-0.0],
                "market_2_discharge_mw": [0.0],
                "net_battery_power_mw": [-0.0],
                "soc_start_mwh": [-0.0],
                "soc_end_mwh": [0.0],
                "market_1_revenue_gbp": [-0.0],
                "market_2_revenue_gbp": [0.0],
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "january_2018_results.csv"
            ResultsCsvWriter().write(frame, path)
            text: str = path.read_text()
            self.assertNotIn("-0.0", text)
            loaded = pd.read_csv(path)
            for column in loaded.select_dtypes(include="number").columns:
                for value in loaded[column]:
                    if float(value) == 0.0:
                        self.assertGreaterEqual(
                            math.copysign(1.0, float(value)),
                            0.0,
                        )
