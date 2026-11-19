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
