import unittest

from battery_control.battery_optimisation.trading_milp_builder import (
    TradingMilpBuilder,
    build_objective_coefficients,
    build_variable_bounds,
)
from battery_control.battery_optimisation.trading_milp_problem import TradingMilpProblem
from battery_control.battery_optimisation.variable_layout import VariableLayout
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS
from tests.battery_control.battery_optimisation.test_support import (
    aligned_prices,
    expected_terminal_state_of_charge,
)


class TestTradingMilpBuilder(unittest.TestCase):
    def test_objective_doubles_market_2_coefficients_per_hour(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(2, 1)
        prices = aligned_prices([1.0, 3.0], [5.0])
        duration: float = MARKET_1_INTERVAL_HOURS
        objective = build_objective_coefficients(prices, layout, duration)
        self.assertAlmostEqual(objective[layout.p1c_at(0)], 1.0 * duration)
        self.assertAlmostEqual(objective[layout.p2c_at(0)], 2.0 * 5.0 * duration)
        self.assertAlmostEqual(objective[layout.p1d_at(1)], -3.0 * duration)

    def test_terminal_state_of_charge_bounds_are_fixed(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(2, 1)
        config: BatteryConfig = BatteryConfig(
            max_charge_power_mw=2.0,
            max_discharge_power_mw=2.0,
            energy_capacity_mwh=8.0,
            charging_efficiency=0.95,
            discharging_efficiency=0.95,
        )
        terminal_soc: float = expected_terminal_state_of_charge(
            config.energy_capacity_mwh,
        )
        bounds = build_variable_bounds(config, layout, terminal_soc)
        self.assertAlmostEqual(bounds.lb[layout.soc_at(0)], terminal_soc)
        self.assertAlmostEqual(bounds.ub[layout.soc_at(0)], terminal_soc)
        self.assertAlmostEqual(bounds.lb[layout.soc_at(2)], terminal_soc)
        self.assertAlmostEqual(bounds.ub[layout.soc_at(2)], terminal_soc)

    def test_build_returns_problem_matching_layout_size(self) -> None:
        prices = aligned_prices([1.0, 2.0], [3.0])
        problem: TradingMilpProblem = TradingMilpBuilder().build(
            BatteryConfig(2.0, 2.0, 4.0, 0.95, 0.95),
            prices,
        )
        self.assertEqual(len(problem.objective), problem.layout.variable_count)
        self.assertEqual(len(problem.integrality), problem.layout.variable_count)