import tempfile
import unittest
from pathlib import Path

from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.results.results_plotter import ResultsPlotter
from battery_control.results.results_table_builder import ResultsTableBuilder
from battery_control.results.trading_revenue import TradingRevenue
from tests.battery_control.battery_optimisation.test_support import (
    aligned_prices,
    toy_battery_config,
)


class TestResultsPlotter(unittest.TestCase):
    def test_generates_png(self) -> None:
        prices = aligned_prices([0.0, 100.0], [0.0])
        result = BatteryOptimiser().optimise(toy_battery_config(), prices)
        revenue = TradingRevenue.from_optimisation(result, prices)
        frame = ResultsTableBuilder().build(result, prices, revenue)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "january_2018_results.png"
            ResultsPlotter().save(frame, path)
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
