import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.results.run_summary_printer import RunSummaryPrinter
from battery_control.results.trading_revenue import TradingRevenue
from tests.battery_control.battery_optimisation.test_support import (
    aligned_prices,
    toy_battery_config,
)


class TestRunSummaryPrinter(unittest.TestCase):
    def test_summary_contains_key_lines(self) -> None:
        prices = aligned_prices([0.0, 100.0], [0.0])
        config = toy_battery_config()
        result = BatteryOptimiser().optimise(config, prices)
        revenue = TradingRevenue.from_optimisation(result, prices)
        buffer = StringIO()
        with patch("sys.stdout", buffer):
            RunSummaryPrinter().print_summary(
                config,
                result,
                revenue,
                Path("output/january_2018_results.csv"),
                Path("output/january_2018_results.png"),
            )
        text = buffer.getvalue()
        self.assertIn("Market 1 trading profit", text)
        self.assertIn("Total trading profit", text)
