"""Mixed-integer linear program for parallel trading on two markets.

Half-hour index ``i`` pairs with hourly index ``h = i // 2``. Market 2 charge and
discharge powers ``p2c[h]`` and ``p2d[h]`` apply to *both* half-hours in that
hour in power limits, SOC dynamics and revenue (each half-hour earns
``(p2d[h] - p2c[h]) * price2[h] * dt``).

Decision vector layout — see :class:`VariableLayout`.

Decision vector length is ``4N + 2H + N + 1``: ``N`` each for Market 1
powers and binaries, ``H`` each for Market 2 powers, and ``N + 1`` SOC
values (see :meth:`VariableLayout.variable_count`).

``soc[0]`` and ``soc[N]`` are fixed to 50% capacity via bounds.
"""

import numpy as np
from scipy.optimize import Bounds

from battery_control.battery_optimisation.constraint_builder import ConstraintBuilder
from battery_control.battery_optimisation.trading_milp_problem import TradingMilpProblem
from battery_control.battery_optimisation.variable_layout import VariableLayout
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS


class TradingMilpBuilder:
    """Assembles objective, bounds and constraints for the trading MILP."""

    INITIAL_SOC_FRACTION: float = 0.5

    def __init__(self) -> None:
        """Create a builder with a :class:`ConstraintBuilder`."""
        self._constraint_builder: ConstraintBuilder = ConstraintBuilder()

    def build(
        self,
        config: BatteryConfig,
        prices: AlignedMarketPrices,
    ) -> TradingMilpProblem:
        """Construct a complete MILP from configuration and aligned prices.

        Args:
            config (BatteryConfig): Battery parameters.
            prices (AlignedMarketPrices): January prices (Market 1 length 2× Market 2).

        Returns:
            TradingMilpProblem: Objective, bounds, constraints, and variable layout.

        Raises:
            ValueError: If Market 1 length is not twice Market 2 length.
        """
        half_hour_count: int = len(prices.market_1_prices_gbp_per_mwh)
        hour_count: int = len(prices.market_2_prices_gbp_per_mwh)
        if half_hour_count != 2 * hour_count:
            msg = (
                "Aligned Market 1 length must be twice Market 2 length, "
                f"got {half_hour_count} and {hour_count}"
            )
            raise ValueError(msg)

        layout: VariableLayout = VariableLayout.from_counts(
            half_hour_count,
            hour_count,
        )
        duration_hours: float = MARKET_1_INTERVAL_HOURS
        terminal_soc: float = self.INITIAL_SOC_FRACTION * config.energy_capacity_mwh
        return TradingMilpProblem(
            objective=self._build_objective_coefficients(
                prices,
                layout,
                duration_hours,
            ),
            integrality=layout.integrality_vector(),
            bounds=self._build_variable_bounds(config, layout, terminal_soc),
            constraints=self._constraint_builder.build(
                config,
                layout,
                duration_hours,
            ),
            layout=layout,
            half_hour_count=half_hour_count,
            hour_count=hour_count,
        )

    @staticmethod
    def _build_objective_coefficients(
        prices: AlignedMarketPrices,
        layout: VariableLayout,
        duration_hours: float,
    ) -> np.ndarray:
        """Minimisation coefficients (negated trading profit per interval).

        Args:
            prices (AlignedMarketPrices): Aligned half-hourly and hourly prices.
            layout (VariableLayout): Decision vector index map.
            duration_hours (float): Half-hour length in hours.

        Returns:
            np.ndarray: Objective coefficients, length ``variable_count``.
        """
        objective: np.ndarray = np.zeros(layout.variable_count, dtype=np.float64)
        for half_hour in range(layout.half_hour_count):
            hour: int = half_hour // 2
            price_1: float = float(prices.market_1_prices_gbp_per_mwh[half_hour])
            objective[layout.p1c_at(half_hour)] += price_1 * duration_hours
            objective[layout.p1d_at(half_hour)] -= price_1 * duration_hours
            price_2: float = float(prices.market_2_prices_gbp_per_mwh[hour])
            objective[layout.p2c_at(hour)] += price_2 * duration_hours
            objective[layout.p2d_at(hour)] -= price_2 * duration_hours
        return objective

    @staticmethod
    def _build_variable_bounds(
        config: BatteryConfig,
        layout: VariableLayout,
        terminal_soc: float,
    ) -> Bounds:
        """Box limits for powers, SOC, mode binaries, and fixed start/end SOC.

        Args:
            config (BatteryConfig): Battery parameters.
            layout (VariableLayout): Decision vector index map.
            terminal_soc (float): Fixed SOC (MWh) at the first and last boundary.

        Returns:
            Bounds: SciPy per-variable lower and upper limits.
        """
        lower: np.ndarray = np.zeros(layout.variable_count, dtype=np.float64)
        upper: np.ndarray = np.full(
            layout.variable_count,
            np.inf,
            dtype=np.float64,
        )
        power_cap: float = max(
            config.max_charge_power_mw,
            config.max_discharge_power_mw,
        )
        upper[layout.p1c] = power_cap
        upper[layout.p1d] = power_cap
        upper[layout.p2c] = power_cap
        upper[layout.p2d] = power_cap
        lower[layout.soc] = 0.0
        upper[layout.soc] = config.energy_capacity_mwh
        lower[layout.soc_at(0)] = terminal_soc
        upper[layout.soc_at(0)] = terminal_soc
        lower[layout.soc_at(layout.half_hour_count)] = terminal_soc
        upper[layout.soc_at(layout.half_hour_count)] = terminal_soc
        upper[layout.z] = 1.0
        return Bounds(lower, upper)