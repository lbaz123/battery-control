import unittest

import numpy as np

from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.market_alignment.constants import (
    JANUARY_2018_END_MARKET_1,
    JANUARY_2018_START,
    MARKET_1_INTERVAL,
    january_observation_count,
)
from battery_control.results.results_table_builder import ResultsTableBuilder
from battery_control.results.trading_revenue import TradingRevenue
from tests.battery_control.battery_optimisation.test_support import (
    aligned_prices,
    revenue_from_markets,
    toy_battery_config,
)


class TestResultsTableBuilder(unittest.TestCase):
    builder: ResultsTableBuilder

    def setUp(self) -> None:
        self.builder = ResultsTableBuilder()

    def test_january_timestamps_and_revenues(self) -> None:
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
        frame = self.builder.build(result, prices, revenue)

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
        frame = self.builder.build(result, prices, revenue)
        self.assertEqual(
            frame["market_2_charge_mw"].iloc[0],
            frame["market_2_charge_mw"].iloc[1],
        )
        self.assertAlmostEqual(
            frame["soc_end_mwh"].iloc[0],
            frame["soc_start_mwh"].iloc[1],
        )
