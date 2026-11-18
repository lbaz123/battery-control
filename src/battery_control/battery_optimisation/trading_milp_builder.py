"""Mixed-integer linear program for parallel trading on two markets.

Half-hour index ``i`` pairs with hourly index ``h = i // 2``. Market 2 charge and
discharge powers ``p2c[h]`` and ``p2d[h]`` apply to *both* half-hours in that
hour in power limits, SOC dynamics and revenue (each half-hour earns
``(p2d[h] - p2c[h]) * price2[h] * dt``).

Decision vector layout (length ``4N + 2H + 1``):

- ``p1c[0:N]``, ``p1d[0:N]`` — Market 1 powers (MW)
- ``p2c[0:H]``, ``p2d[0:H]`` — Market 2 hourly powers (MW)
- ``soc[0:N+1]`` — state of charge at each half-hour boundary (MWh)
- ``z[0:N]`` — binary charge mode (1 = charging allowed, 0 = discharging)

``soc[0]`` and ``soc[N]`` are fixed to 50% capacity via bounds. Dynamics use
charging efficiency on energy in and discharging efficiency on energy out.
"""

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.optimize import Bounds, LinearConstraint

from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS


@dataclass(frozen=True)
class TradingMilpProblem:
    objective: np.ndarray
    integrality: np.ndarray
    bounds: Bounds
    constraints: LinearConstraint
    half_hour_count: int
    hour_count: int


class TradingMilpBuilder:
    """Builds a sparse MILP for battery trading over aligned market prices."""

    INITIAL_SOC_FRACTION: float = 0.5

    def build(
        self,
        config: BatteryConfig,
        prices: AlignedMarketPrices,
    ) -> TradingMilpProblem:
        half_hour_count: int = len(prices.market_1_prices_gbp_per_mwh)
        hour_count: int = len(prices.market_2_prices_gbp_per_mwh)
        if half_hour_count != 2 * hour_count:
            msg = (
                "Aligned Market 1 length must be twice Market 2 length, "
                f"got {half_hour_count} and {hour_count}"
            )
            raise ValueError(msg)

        layout: _VariableLayout = _VariableLayout.from_counts(
            half_hour_count,
            hour_count,
        )
        duration_hours: float = MARKET_1_INTERVAL_HOURS
        terminal_soc: float = self.INITIAL_SOC_FRACTION * config.energy_capacity_mwh

        objective: np.ndarray = self._build_objective(
            prices,
            layout,
            duration_hours,
        )
        integrality: np.ndarray = layout.integrality_vector()
        bounds: Bounds = self._build_bounds(config, layout, terminal_soc)
        constraints: LinearConstraint = self._build_constraints(
            config,
            layout,
            duration_hours,
        )
        return TradingMilpProblem(
            objective=objective,
            integrality=integrality,
            bounds=bounds,
            constraints=constraints,
            half_hour_count=half_hour_count,
            hour_count=hour_count,
        )

    def round_binary_modes(
        self,
        decision_vector: np.ndarray,
        half_hour_count: int,
        hour_count: int,
    ) -> np.ndarray:
        layout: _VariableLayout = _VariableLayout.from_counts(
            half_hour_count,
            hour_count,
        )
        rounded: np.ndarray = decision_vector.copy()
        rounded[layout.z] = np.rint(rounded[layout.z])
        return rounded

    def unpack_solution(
        self,
        decision_vector: np.ndarray,
        half_hour_count: int,
        hour_count: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        layout: _VariableLayout = _VariableLayout.from_counts(
            half_hour_count,
            hour_count,
        )
        return (
            decision_vector[layout.p1c].copy(),
            decision_vector[layout.p1d].copy(),
            decision_vector[layout.p2c].copy(),
            decision_vector[layout.p2d].copy(),
            decision_vector[layout.soc].copy(),
        )

    def total_profit_gbp(
        self,
        decision_vector: np.ndarray,
        prices: AlignedMarketPrices,
        half_hour_count: int,
        hour_count: int,
    ) -> float:
        layout: _VariableLayout = _VariableLayout.from_counts(
            half_hour_count,
            hour_count,
        )
        duration_hours: float = MARKET_1_INTERVAL_HOURS
        p1c = decision_vector[layout.p1c]
        p1d = decision_vector[layout.p1d]
        p2c = decision_vector[layout.p2c]
        p2d = decision_vector[layout.p2d]
        profit: float = 0.0
        for half_hour in range(half_hour_count):
            hour: int = half_hour // 2
            profit += (
                (p1d[half_hour] - p1c[half_hour])
                * prices.market_1_prices_gbp_per_mwh[half_hour]
                + (p2d[hour] - p2c[hour]) * prices.market_2_prices_gbp_per_mwh[hour]
            ) * duration_hours
        return float(profit)

    def _build_objective(
        self,
        prices: AlignedMarketPrices,
        layout: "_VariableLayout",
        duration_hours: float,
    ) -> np.ndarray:
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

    def _build_bounds(
        self,
        config: BatteryConfig,
        layout: "_VariableLayout",
        terminal_soc: float,
    ) -> Bounds:
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

    def _build_constraints(
        self,
        config: BatteryConfig,
        layout: "_VariableLayout",
        duration_hours: float,
    ) -> LinearConstraint:
        rows: list[int] = []
        columns: list[int] = []
        values: list[float] = []
        lower_bounds: list[float] = []
        upper_bounds: list[float] = []
        row_index: int = 0

        for half_hour in range(layout.half_hour_count):
            hour: int = half_hour // 2
            soc_row: int = row_index
            row_index += 1
            rows.extend(
                [
                    soc_row,
                    soc_row,
                    soc_row,
                    soc_row,
                    soc_row,
                    soc_row,
                ]
            )
            columns.extend(
                [
                    layout.soc_at(half_hour + 1),
                    layout.soc_at(half_hour),
                    layout.p1c_at(half_hour),
                    layout.p2c_at(hour),
                    layout.p1d_at(half_hour),
                    layout.p2d_at(hour),
                ]
            )
            values.extend(
                [
                    1.0,
                    -1.0,
                    -config.charging_efficiency * duration_hours,
                    -config.charging_efficiency * duration_hours,
                    duration_hours / config.discharging_efficiency,
                    duration_hours / config.discharging_efficiency,
                ]
            )
            lower_bounds.append(0.0)
            upper_bounds.append(0.0)

            charge_mode_row: int = row_index
            row_index += 1
            rows.extend(
                [
                    charge_mode_row,
                    charge_mode_row,
                    charge_mode_row,
                ]
            )
            columns.extend(
                [
                    layout.p1c_at(half_hour),
                    layout.p2c_at(hour),
                    layout.z_at(half_hour),
                ]
            )
            values.extend(
                [
                    1.0,
                    1.0,
                    -config.max_charge_power_mw,
                ]
            )
            lower_bounds.append(-np.inf)
            upper_bounds.append(0.0)

            discharge_mode_row: int = row_index
            row_index += 1
            rows.extend(
                [
                    discharge_mode_row,
                    discharge_mode_row,
                    discharge_mode_row,
                ]
            )
            columns.extend(
                [
                    layout.p1d_at(half_hour),
                    layout.p2d_at(hour),
                    layout.z_at(half_hour),
                ]
            )
            values.extend([1.0, 1.0, config.max_discharge_power_mw])
            lower_bounds.append(-np.inf)
            upper_bounds.append(config.max_discharge_power_mw)

        matrix: sp.csr_matrix = sp.csr_matrix(
            (values, (rows, columns)),
            shape=(row_index, layout.variable_count),
        )
        return LinearConstraint(matrix, np.array(lower_bounds), np.array(upper_bounds))


@dataclass(frozen=True)
class _VariableLayout:
    half_hour_count: int
    hour_count: int
    p1c: slice
    p1d: slice
    p2c: slice
    p2d: slice
    soc: slice
    z: slice

    @property
    def variable_count(self) -> int:
        return 4 * self.half_hour_count + 2 * self.hour_count + 1

    @classmethod
    def from_counts(cls, half_hour_count: int, hour_count: int) -> "_VariableLayout":
        offset: int = 0
        p1c = slice(offset, offset + half_hour_count)
        offset += half_hour_count
        p1d = slice(offset, offset + half_hour_count)
        offset += half_hour_count
        p2c = slice(offset, offset + hour_count)
        offset += hour_count
        p2d = slice(offset, offset + hour_count)
        offset += hour_count
        soc = slice(offset, offset + half_hour_count + 1)
        offset += half_hour_count + 1
        z = slice(offset, offset + half_hour_count)
        return cls(
            half_hour_count=half_hour_count,
            hour_count=hour_count,
            p1c=p1c,
            p1d=p1d,
            p2c=p2c,
            p2d=p2d,
            soc=soc,
            z=z,
        )

    def integrality_vector(self) -> np.ndarray:
        vector: np.ndarray = np.zeros(self.variable_count, dtype=np.uint8)
        vector[self.z] = 1
        return vector

    def p1c_at(self, half_hour: int) -> int:
        return self.p1c.start + half_hour

    def p1d_at(self, half_hour: int) -> int:
        return self.p1d.start + half_hour

    def p2c_at(self, hour: int) -> int:
        return self.p2c.start + hour

    def p2d_at(self, hour: int) -> int:
        return self.p2d.start + hour

    def soc_at(self, boundary: int) -> int:
        return self.soc.start + boundary

    def z_at(self, half_hour: int) -> int:
        return self.z.start + half_hour
