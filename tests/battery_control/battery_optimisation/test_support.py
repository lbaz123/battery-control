import unittest

from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS


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
            + (
                result.market_2_discharge_mw[hour] - result.market_2_charge_mw[hour]
            )
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
    for half_hour in range(len(prices.market_1_prices_gbp_per_mwh)):
        hour: int = half_hour // 2
        total_charge: float = (
            result.market_1_charge_mw[half_hour] + result.market_2_charge_mw[hour]
        )
        total_discharge: float = (
            result.market_1_discharge_mw[half_hour]
            + result.market_2_discharge_mw[hour]
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