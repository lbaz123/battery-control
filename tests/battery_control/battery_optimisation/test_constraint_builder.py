import unittest

import scipy.sparse as sp

from battery_control.battery_optimisation.constraint_builder import ConstraintBuilder
from battery_control.battery_optimisation.variable_layout import VariableLayout
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS
from tests.battery_control.battery_optimisation.test_support import (
    constraint_row_coefficients,
)


class TestConstraintBuilder(unittest.TestCase):
    def test_soc_row_coefficients(self) -> None:
        half_hour_count: int = 4
        layout: VariableLayout = VariableLayout.from_counts(half_hour_count, 2)
        config: BatteryConfig = BatteryConfig(
            max_charge_power_mw=3.0,
            max_discharge_power_mw=4.0,
            energy_capacity_mwh=10.0,
            charging_efficiency=0.9,
            discharging_efficiency=0.8,
        )
        duration: float = MARKET_1_INTERVAL_HOURS
        constraint = ConstraintBuilder().build(config, layout, duration)
        matrix: sp.csr_matrix = constraint.A.tocsr()
        half_hour: int = 2
        row: int = 3 * half_hour
        coeffs: dict[int, float] = constraint_row_coefficients(matrix, row)
        hour: int = half_hour // 2
        self.assertAlmostEqual(coeffs[layout.soc_at(half_hour + 1)], 1.0)
        self.assertAlmostEqual(coeffs[layout.soc_at(half_hour)], -1.0)
        self.assertAlmostEqual(
            coeffs[layout.p1c_at(half_hour)],
            -config.charging_efficiency * duration,
        )
        self.assertAlmostEqual(
            coeffs[layout.p2c_at(hour)],
            -config.charging_efficiency * duration,
        )
        self.assertAlmostEqual(
            coeffs[layout.p1d_at(half_hour)],
            duration / config.discharging_efficiency,
        )
        self.assertAlmostEqual(
            coeffs[layout.p2d_at(hour)],
            duration / config.discharging_efficiency,
        )

    def test_soc_equality_rows_have_zero_bounds(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(3, 2)
        constraint = ConstraintBuilder().build(
            BatteryConfig(2.0, 2.0, 5.0, 0.95, 0.95),
            layout,
            MARKET_1_INTERVAL_HOURS,
        )
        for half_hour in range(layout.half_hour_count):
            soc_row: int = 3 * half_hour
            self.assertAlmostEqual(constraint.lb[soc_row], 0.0)
            self.assertAlmostEqual(constraint.ub[soc_row], 0.0)

    def test_charge_mode_uses_combined_power_and_binary(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(2, 1)
        config: BatteryConfig = BatteryConfig(5.0, 5.0, 10.0, 1.0, 1.0)
        constraint = ConstraintBuilder().build(
            config,
            layout,
            MARKET_1_INTERVAL_HOURS,
        )
        matrix: sp.csr_matrix = constraint.A.tocsr()
        charge_row: int = 1
        by_col = constraint_row_coefficients(matrix, charge_row)
        self.assertAlmostEqual(by_col[layout.p1c_at(0)], 1.0)
        self.assertAlmostEqual(by_col[layout.p2c_at(0)], 1.0)
        self.assertAlmostEqual(by_col[layout.z_at(0)], -5.0)
        self.assertAlmostEqual(constraint.ub[charge_row], 0.0)

    def test_discharge_mode_uses_combined_power_and_binary(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(2, 1)
        config: BatteryConfig = BatteryConfig(5.0, 7.0, 10.0, 1.0, 1.0)
        constraint = ConstraintBuilder().build(
            config,
            layout,
            MARKET_1_INTERVAL_HOURS,
        )
        matrix: sp.csr_matrix = constraint.A.tocsr()
        discharge_row: int = 2
        by_col = constraint_row_coefficients(matrix, discharge_row)
        self.assertAlmostEqual(by_col[layout.p1d_at(0)], 1.0)
        self.assertAlmostEqual(by_col[layout.p2d_at(0)], 1.0)
        self.assertAlmostEqual(by_col[layout.z_at(0)], 7.0)
        self.assertAlmostEqual(constraint.ub[discharge_row], 7.0)

    def test_matrix_shape_sparsity_and_nnz(self) -> None:
        half_hour_count: int = 6
        layout: VariableLayout = VariableLayout.from_counts(half_hour_count, 3)
        config: BatteryConfig = BatteryConfig(2.0, 2.0, 5.0, 0.95, 0.95)
        constraint = ConstraintBuilder().build(
            config,
            layout,
            MARKET_1_INTERVAL_HOURS,
        )
        matrix: sp.csr_matrix = constraint.A.tocsr()
        self.assertEqual(matrix.shape, (3 * half_hour_count, layout.variable_count))
        self.assertIsInstance(matrix, sp.csr_matrix)
        self.assertEqual(matrix.nnz, 12 * half_hour_count)
