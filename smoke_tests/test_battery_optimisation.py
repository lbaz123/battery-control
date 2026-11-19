import unittest

import numpy as np

from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.battery_optimisation.trading_milp_builder import TradingMilpBuilder
from battery_control.data_loader.battery_config.battery_config_loader import (
    BatteryConfigLoader,
)
from battery_control.data_loader.market_prices.market_prices_loader import (
    MarketPricesLoader,
)
from battery_control.market_alignment.market_prices_aligner import MarketPricesAligner
from smoke_tests.paths import BATTERY_SPEC_PATH, MARKET_PRICES_PATH


class TestBatteryOptimisationSmoke(unittest.TestCase):
    def test_optimises_january_2018_from_committed_data(self) -> None:
        config = BatteryConfigLoader().load(BATTERY_SPEC_PATH)
        prices = MarketPricesLoader().load(MARKET_PRICES_PATH)
        aligned = MarketPricesAligner().align(prices)
        result = BatteryOptimiser().optimise(config, aligned)
        self.assertTrue(np.isfinite(result.total_trading_profit_gbp))
        self.assertEqual(
            result.market_1_charge_mw.shape,
            aligned.market_1_prices_gbp_per_mwh.shape,
        )
        self.assertEqual(
            result.market_2_charge_mw.shape,
            aligned.market_2_prices_gbp_per_mwh.shape,
        )
        initial_soc: float = (
            TradingMilpBuilder.INITIAL_SOC_FRACTION * config.energy_capacity_mwh
        )
        self.assertAlmostEqual(result.state_of_charge_mwh[0], initial_soc, places=3)
        self.assertAlmostEqual(result.state_of_charge_mwh[-1], initial_soc, places=3)
        self.assertTrue(np.all(result.state_of_charge_mwh >= -1e-6))
        self.assertTrue(
            np.all(result.state_of_charge_mwh <= config.energy_capacity_mwh + 1e-6),
        )
