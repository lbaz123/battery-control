import unittest

import numpy as np
import scipy.sparse as sp

from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.battery_optimisation.trading_milp_builder import TradingMilpBuilder
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS


def aligned_prices(
    market_1_prices: list[float],
    market_2_prices: list[float],
) -> AlignedMarketPrices:
    return AlignedMarketPrices(
        market_1_prices_gbp_per_mwh=np.asarray(market_1_prices, dtype=np.float64),
        market_2_prices_gbp_per_mwh=np.asarray(market_2_prices, dtype=np.float64),
    )


def toy_battery_config(
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


def expected_terminal_state_of_charge(energy_capacity_mwh: float) -> float:
    return TradingMilpBuilder.INITIAL_SOC_FRACTION * energy_capacity_mwh


def constraint_row_coefficients(
    matrix: sp.csr_matrix,
    row: int,
) -> dict[int, float]:
    csr: sp.csr_matrix = matrix.tocsr()
    sparse_row = csr.getrow(row)
    return dict(zip(sparse_row.indices, sparse_row.data, strict=True))


def revenue_from_markets(
    result: OptimisationResult,
    prices: AlignedMarketPrices,
) -> float:
    duration_hours: float = MARKET_1_INTERVAL_HOURS
    profit: float = 0.0
    for half_hour in range(len(prices.market_1_prices_gbp_per_mwh)):
        hour: int = half_hour // 2
        profit += (
            (
                result.market_1_discharge_mw[half_hour]
                - result.market_1_charge_mw[half_hour]
            )
            * prices.market_1_prices_gbp_per_mwh[half_hour]
            + (result.market_2_discharge_mw[hour] - result.market_2_charge_mw[hour])
            * prices.market_2_prices_gbp_per_mwh[hour]
        ) * duration_hours
    return float(profit)


def assert_solution_consistent(
    case: unittest.TestCase,
    result: OptimisationResult,
    config: BatteryConfig,
    prices: AlignedMarketPrices,
    tol: float = 1e-4,
) -> None:
    duration_hours: float = MARKET_1_INTERVAL_HOURS
    case.assertAlmostEqual(
        result.total_trading_profit_gbp,
        revenue_from_markets(result, prices),
        places=4,
    )
    for boundary_index in range(len(result.state_of_charge_mwh)):
        soc_value: float = float(result.state_of_charge_mwh[boundary_index])
        case.assertGreaterEqual(soc_value, -tol)
        case.assertLessEqual(soc_value, config.energy_capacity_mwh + tol)
    for half_hour in range(len(prices.market_1_prices_gbp_per_mwh)):
        hour: int = half_hour // 2
        total_charge: float = (
            result.market_1_charge_mw[half_hour] + result.market_2_charge_mw[hour]
        )
        total_discharge: float = (
            result.market_1_discharge_mw[half_hour] + result.market_2_discharge_mw[hour]
        )
        case.assertLessEqual(total_charge, config.max_charge_power_mw + tol)
        case.assertLessEqual(total_discharge, config.max_discharge_power_mw + tol)
        case.assertLessEqual(total_charge * total_discharge, tol)
        expected_soc: float = (
            result.state_of_charge_mwh[half_hour]
            + config.charging_efficiency * total_charge * duration_hours
            - total_discharge * duration_hours / config.discharging_efficiency
        )
        case.assertAlmostEqual(
            result.state_of_charge_mwh[half_hour + 1],
            expected_soc,
            delta=tol,
        )