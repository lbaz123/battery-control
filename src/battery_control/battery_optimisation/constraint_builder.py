import numpy as np
from scipy.optimize import LinearConstraint

from battery_control.battery_optimisation.sparse_constraint_accumulator import (
    SparseConstraintAccumulator,
)
from battery_control.battery_optimisation.variable_layout import VariableLayout
from battery_control.data_loader.battery_config.battery_config import BatteryConfig


class ConstraintBuilder:
    """Sparse linear constraints for SOC, power limits and charge/discharge modes."""

    def build(
        self,
        config: BatteryConfig,
        layout: VariableLayout,
        duration_hours: float,
    ) -> LinearConstraint:
        accumulator: SparseConstraintAccumulator = SparseConstraintAccumulator(
            layout.variable_count,
        )
        for half_hour in range(layout.half_hour_count):
            hour: int = half_hour // 2
            accumulator.add_row(
                [
                    layout.soc_at(half_hour + 1),
                    layout.soc_at(half_hour),
                    layout.p1c_at(half_hour),
                    layout.p2c_at(hour),
                    layout.p1d_at(half_hour),
                    layout.p2d_at(hour),
                ],
                [
                    1.0,
                    -1.0,
                    -config.charging_efficiency * duration_hours,
                    -config.charging_efficiency * duration_hours,
                    duration_hours / config.discharging_efficiency,
                    duration_hours / config.discharging_efficiency,
                ],
                lower=0.0,
                upper=0.0,
            )
            accumulator.add_row(
                [
                    layout.p1c_at(half_hour),
                    layout.p2c_at(hour),
                    layout.z_at(half_hour),
                ],
                [1.0, 1.0, -config.max_charge_power_mw],
                lower=-np.inf,
                upper=0.0,
            )
            accumulator.add_row(
                [
                    layout.p1d_at(half_hour),
                    layout.p2d_at(hour),
                    layout.z_at(half_hour),
                ],
                [1.0, 1.0, config.max_discharge_power_mw],
                lower=-np.inf,
                upper=config.max_discharge_power_mw,
            )
        return accumulator.to_linear_constraint()
