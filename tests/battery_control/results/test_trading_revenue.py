import unittest

import numpy as np

from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.results.trading_revenue import TradingRevenue
from tests.battery_control.battery_optimisation.test_support import (
    aligned_prices,
    revenue_from_markets,
    toy_battery_config,
)


class TestTradingRevenue(unittest.TestCase):
    def test_market_profits_sum_to_total_and_match_optimiser(self) -> None:
        prices = aligned_prices([0.0, 100.0], [0.0])
        config = toy_battery_config(energy_capacity_mwh=20.0)
        result: OptimisationResult = BatteryOptimiser().optimise(config, prices)
        revenue: TradingRevenue = TradingRevenue.from_optimisation(result, prices)

        self.assertAlmostEqual(
            revenue.market_1_trading_profit_gbp + revenue.market_2_trading_profit_gbp,
            revenue.total_trading_profit_gbp,
            places=9,
        )
        self.assertAlmostEqual(
            revenue.total_trading_profit_gbp,
            result.total_trading_profit_gbp,
            places=4,
        )
        independent_total: float = revenue_from_markets(result, prices)
        self.assertAlmostEqual(
            revenue.total_trading_profit_gbp,
            independent_total,
            places=4,
        )

    def test_half_hour_arrays_match_row_sums(self) -> None:
        prices = aligned_prices([10.0, 20.0], [5.0])
        config = toy_battery_config(energy_capacity_mwh=20.0)
        result = BatteryOptimiser().optimise(config, prices)
        revenue = TradingRevenue.from_optimisation(result, prices)

        self.assertAlmostEqual(
            float(np.sum(revenue.market_1_half_hour_revenue_gbp)),
            revenue.market_1_trading_profit_gbp,
            places=9,
        )
        self.assertAlmostEqual(
            float(np.sum(revenue.market_2_half_hour_revenue_gbp)),
            revenue.market_2_trading_profit_gbp,
            places=9,
        )
