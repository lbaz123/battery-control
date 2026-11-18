import pandas as pd

from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import (
    JANUARY_2018_START,
    MARKET_1_INTERVAL,
)
from battery_control.results.trading_revenue import TradingRevenue


def build_january_results_table(
    result: OptimisationResult,
    prices: AlignedMarketPrices,
    revenue: TradingRevenue,
) -> pd.DataFrame:
    """Half-hourly January results for CSV export and plotting."""
    half_hour_count: int = len(prices.market_1_prices_gbp_per_mwh)
    interval_starts: pd.DatetimeIndex = pd.date_range(
        JANUARY_2018_START,
        periods=half_hour_count,
        freq=MARKET_1_INTERVAL,
    )
    market_2_charge: list[float] = []
    market_2_discharge: list[float] = []
    net_power: list[float] = []
    for half_hour in range(half_hour_count):
        hour: int = half_hour // 2
        m1c: float = float(result.market_1_charge_mw[half_hour])
        m1d: float = float(result.market_1_discharge_mw[half_hour])
        m2c: float = float(result.market_2_charge_mw[hour])
        m2d: float = float(result.market_2_discharge_mw[hour])
        market_2_charge.append(m2c)
        market_2_discharge.append(m2d)
        net_power.append((m1d + m2d) - (m1c + m2c))
    return pd.DataFrame(
        {
            "interval_start": interval_starts,
            "market_1_charge_mw": result.market_1_charge_mw,
            "market_1_discharge_mw": result.market_1_discharge_mw,
            "market_2_charge_mw": market_2_charge,
            "market_2_discharge_mw": market_2_discharge,
            "net_battery_power_mw": net_power,
            "soc_start_mwh": result.state_of_charge_mwh[:-1],
            "soc_end_mwh": result.state_of_charge_mwh[1:],
            "market_1_revenue_gbp": revenue.market_1_half_hour_revenue_gbp,
            "market_2_revenue_gbp": revenue.market_2_half_hour_revenue_gbp,
        }
    )
