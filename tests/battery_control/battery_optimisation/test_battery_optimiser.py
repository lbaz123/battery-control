import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np

from battery_control.battery_optimisation.battery_optimisation_error import (
    BatteryOptimisationError,
)
from battery_control.battery_optimisation.battery_optimiser import BatteryOptimiser
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS


def _aligned(
    market_1_prices: list[float],
    market_2_prices: list[float],
) -> AlignedMarketPrices:
    return AlignedMarketPrices(
        market_1_prices_gbp_per_mwh=np.asarray(market_1_prices, dtype=np.float64),
        market_2_prices_gbp_per_mwh=np.asarray(market_2_prices, dtype=np.float64),
    )


def _config(
    *,
    max_charge_power_mw: float = 10.0,
    max_discharge_power_mw: float = 10.0,
    energy_capacity_mwh: float = 10.0,
    charging_efficiency: float = 1.0,
    discharging_efficiency: float = 1.0,
) -> BatteryConfig:
    return BatteryConfig(
        max_charge_power_mw=max_charge_power_mw,
        max_discharge_power_mw=max_discharge_power_mw,
        energy_capacity_mwh=energy_capacity_mwh,
        charging_efficiency=charging_efficiency,
        discharging_efficiency=discharging_efficiency,
    )


class TestBatteryOptimiser(unittest.TestCase):
    optimiser: BatteryOptimiser

    def setUp(self) -> None:
        self.optimiser = BatteryOptimiser()

    def test_exact_profit_two_step_arbitrage(self) -> None:
        config: BatteryConfig = _config()
        prices: AlignedMarketPrices = _aligned([0.0, 100.0], [0.0])
        result = self.optimiser.optimise(config, prices)
        self.assertAlmostEqual(result.total_trading_profit_gbp, 500.0)
        self.assertAlmostEqual(result.state_of_charge_mwh[0], 5.0)
        self.assertAlmostEqual(result.state_of_charge_mwh[-1], 5.0)
        self.assertAlmostEqual(result.market_1_charge_mw[0], 10.0)
        self.assertAlmostEqual(result.market_1_discharge_mw[1], 10.0)

    def test_profitable_arbitrage_is_positive(self) -> None:
        prices: AlignedMarketPrices = _aligned([10.0, 50.0, 200.0, 80.0], [5.0, 40.0])
        result = self.optimiser.optimise(_config(), prices)
        self.assertGreater(result.total_trading_profit_gbp, 0.0)

    def test_zero_prices_yield_zero_profit(self) -> None:
        prices: AlignedMarketPrices = _aligned([0.0, 0.0], [0.0])
        result = self.optimiser.optimise(_config(), prices)
        self.assertAlmostEqual(result.total_trading_profit_gbp, 0.0)
        self.assertAlmostEqual(result.state_of_charge_mwh[-1], 5.0)

    def test_efficiency_reduces_arbitrage_profit(self) -> None:
        prices: AlignedMarketPrices = _aligned([0.0, 100.0], [0.0])
        ideal = self.optimiser.optimise(
            _config(charging_efficiency=1.0, discharging_efficiency=1.0),
            prices,
        )
        lossy = self.optimiser.optimise(
            _config(charging_efficiency=0.9, discharging_efficiency=0.9),
            prices,
        )
        self.assertGreater(
            ideal.total_trading_profit_gbp,
            lossy.total_trading_profit_gbp,
        )

    def test_capacity_limit(self) -> None:
        config: BatteryConfig = _config(energy_capacity_mwh=6.0)
        prices: AlignedMarketPrices = _aligned([0.0, 100.0], [0.0])
        result = self.optimiser.optimise(config, prices)
        self.assertLessEqual(np.max(result.state_of_charge_mwh), 6.0 + 1e-6)
        self.assertAlmostEqual(result.state_of_charge_mwh[0], 3.0)
        self.assertAlmostEqual(result.state_of_charge_mwh[-1], 3.0)

    def test_power_limit(self) -> None:
        config: BatteryConfig = _config(
            max_charge_power_mw=2.0,
            max_discharge_power_mw=2.0,
        )
        prices: AlignedMarketPrices = _aligned([0.0, 100.0], [0.0])
        result = self.optimiser.optimise(config, prices)
        interval_energy: float = 2.0 * MARKET_1_INTERVAL_HOURS
        self.assertAlmostEqual(
            result.total_trading_profit_gbp,
            100.0 * interval_energy,
        )

    def test_no_simultaneous_charging_and_discharging(self) -> None:
        prices: AlignedMarketPrices = _aligned([0.0, 100.0, 40.0, 60.0], [0.0, 50.0])
        result = self.optimiser.optimise(_config(), prices)
        for half_hour in range(len(prices.market_1_prices_gbp_per_mwh)):
            hour: int = half_hour // 2
            total_charge: float = (
                result.market_1_charge_mw[half_hour] + result.market_2_charge_mw[hour]
            )
            total_discharge: float = (
                result.market_1_discharge_mw[half_hour]
                + result.market_2_discharge_mw[hour]
            )
            self.assertLessEqual(
                total_charge * total_discharge,
                1e-6,
                msg=f"interval {half_hour}",
            )

    def test_terminal_state_of_charge_matches_initial(self) -> None:
        config: BatteryConfig = _config(energy_capacity_mwh=8.0)
        prices: AlignedMarketPrices = _aligned([5.0, 25.0, 80.0, 15.0], [10.0, 30.0])
        result = self.optimiser.optimise(config, prices)
        self.assertAlmostEqual(
            result.state_of_charge_mwh[-1],
            0.5 * config.energy_capacity_mwh,
        )
        self.assertAlmostEqual(
            result.state_of_charge_mwh[0],
            0.5 * config.energy_capacity_mwh,
        )

    def test_mismatched_length_raises_before_solve(self) -> None:
        prices: AlignedMarketPrices = _aligned([0.0, 10.0, 20.0], [0.0])
        with self.assertRaises(ValueError):
            self.optimiser.optimise(_config(), prices)

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
        prices: AlignedMarketPrices = _aligned([0.0, 10.0], [5.0])
        with self.assertRaises(BatteryOptimisationError):
            self.optimiser.optimise(_config(), prices)
