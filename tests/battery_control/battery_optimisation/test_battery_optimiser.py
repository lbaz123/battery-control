import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from battery_control.battery_optimisation.battery_optimisation_error import (
    BatteryOptimisationError,
)
from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS
from tests.battery_control.battery_optimisation.test_support import (
    aligned_prices,
    assert_solution_consistent,
    expected_terminal_state_of_charge,
    toy_battery_config,
)


class TestBatteryOptimiser(unittest.TestCase):
    optimiser: BatteryOptimiser

    def setUp(self) -> None:
        self.optimiser = BatteryOptimiser()

    def test_exact_profit_two_step_arbitrage(self) -> None:
        config = toy_battery_config()
        prices: AlignedMarketPrices = aligned_prices([0.0, 100.0], [0.0])
        result = self.optimiser.optimise(config, prices)
        assert_solution_consistent(self, result, config, prices)
        terminal_soc: float = expected_terminal_state_of_charge(
            config.energy_capacity_mwh,
        )
        self.assertAlmostEqual(result.total_trading_profit_gbp, 500.0)
        self.assertAlmostEqual(result.state_of_charge_mwh[0], terminal_soc)
        self.assertAlmostEqual(result.state_of_charge_mwh[-1], terminal_soc)
        self.assertAlmostEqual(result.market_1_charge_mw[0], 10.0)
        self.assertAlmostEqual(result.market_1_discharge_mw[1], 10.0)

    def test_profitable_arbitrage_is_positive(self) -> None:
        config = toy_battery_config()
        prices: AlignedMarketPrices = aligned_prices(
            [10.0, 50.0, 200.0, 80.0],
            [5.0, 40.0],
        )
        result = self.optimiser.optimise(config, prices)
        assert_solution_consistent(self, result, config, prices)
        self.assertGreater(result.total_trading_profit_gbp, 0.0)

    def test_negative_prices_allow_profitable_charging(self) -> None:
        config = toy_battery_config()
        prices: AlignedMarketPrices = aligned_prices([-50.0, 100.0], [-10.0])
        result = self.optimiser.optimise(config, prices)
        assert_solution_consistent(self, result, config, prices)
        self.assertGreater(result.total_trading_profit_gbp, 0.0)
        self.assertGreater(result.market_1_charge_mw[0], 1.0)
        self.assertGreater(result.market_1_discharge_mw[1], 1.0)

    def test_zero_prices_yield_zero_profit(self) -> None:
        config = toy_battery_config()
        prices: AlignedMarketPrices = aligned_prices([0.0, 0.0], [0.0])
        result = self.optimiser.optimise(config, prices)
        assert_solution_consistent(self, result, config, prices)
        self.assertAlmostEqual(result.total_trading_profit_gbp, 0.0)
        self.assertAlmostEqual(
            result.state_of_charge_mwh[-1],
            expected_terminal_state_of_charge(config.energy_capacity_mwh),
        )

    def test_efficiency_reduces_arbitrage_profit(self) -> None:
        prices: AlignedMarketPrices = aligned_prices([0.0, 100.0], [0.0])
        ideal_config = toy_battery_config(
            charging_efficiency=1.0,
            discharging_efficiency=1.0,
        )
        lossy_config = toy_battery_config(
            charging_efficiency=0.9,
            discharging_efficiency=0.9,
        )
        ideal = self.optimiser.optimise(ideal_config, prices)
        lossy = self.optimiser.optimise(lossy_config, prices)
        assert_solution_consistent(self, ideal, ideal_config, prices)
        assert_solution_consistent(self, lossy, lossy_config, prices)
        self.assertGreater(
            ideal.total_trading_profit_gbp,
            lossy.total_trading_profit_gbp,
        )

    def test_capacity_limit(self) -> None:
        config = toy_battery_config(energy_capacity_mwh=6.0)
        prices: AlignedMarketPrices = aligned_prices([0.0, 100.0], [0.0])
        result = self.optimiser.optimise(config, prices)
        assert_solution_consistent(self, result, config, prices)
        self.assertLessEqual(np.max(result.state_of_charge_mwh), 6.0 + 1e-6)
        terminal_soc: float = expected_terminal_state_of_charge(
            config.energy_capacity_mwh,
        )
        self.assertAlmostEqual(result.state_of_charge_mwh[0], terminal_soc)
        self.assertAlmostEqual(result.state_of_charge_mwh[-1], terminal_soc)

    def test_power_limit(self) -> None:
        config = toy_battery_config(
            max_charge_power_mw=2.0,
            max_discharge_power_mw=2.0,
        )
        prices: AlignedMarketPrices = aligned_prices([0.0, 100.0], [0.0])
        result = self.optimiser.optimise(config, prices)
        assert_solution_consistent(self, result, config, prices)
        interval_energy: float = 2.0 * MARKET_1_INTERVAL_HOURS
        self.assertAlmostEqual(
            result.total_trading_profit_gbp,
            100.0 * interval_energy,
        )

    def test_no_simultaneous_charging_and_discharging(self) -> None:
        config = toy_battery_config()
        prices: AlignedMarketPrices = aligned_prices(
            [0.0, 100.0, 40.0, 60.0],
            [0.0, 50.0],
        )
        result = self.optimiser.optimise(config, prices)
        assert_solution_consistent(self, result, config, prices)

    def test_terminal_state_of_charge_matches_initial(self) -> None:
        config = toy_battery_config(energy_capacity_mwh=8.0)
        prices: AlignedMarketPrices = aligned_prices(
            [5.0, 25.0, 80.0, 15.0],
            [10.0, 30.0],
        )
        result = self.optimiser.optimise(config, prices)
        assert_solution_consistent(self, result, config, prices)
        terminal_soc: float = expected_terminal_state_of_charge(
            config.energy_capacity_mwh,
        )
        self.assertAlmostEqual(result.state_of_charge_mwh[-1], terminal_soc)
        self.assertAlmostEqual(result.state_of_charge_mwh[0], terminal_soc)

    def test_mismatched_length_raises_before_solve(self) -> None:
        prices: AlignedMarketPrices = aligned_prices([0.0, 10.0, 20.0], [0.0])
        with self.assertRaises(ValueError):
            self.optimiser.optimise(toy_battery_config(), prices)

    @patch("battery_control.battery_optimisation.battery_optimiser.milp")
    def test_raises_battery_optimisation_error_on_solver_failure(
        self,
        mock_milp: MagicMock,
    ) -> None:
        mock_milp.return_value = SimpleNamespace(
            success=False,
            message="infeasible",
            x=np.array([]),
            status=2,
        )
        prices: AlignedMarketPrices = aligned_prices([0.0, 10.0], [5.0])
        with self.assertRaises(BatteryOptimisationError):
            self.optimiser.optimise(toy_battery_config(), prices)
