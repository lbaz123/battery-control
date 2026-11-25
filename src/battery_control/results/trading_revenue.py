from dataclasses import dataclass
from typing import Self

import numpy as np

from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS


@dataclass(frozen=True)
class TradingRevenue:
    """Trading profit split by market from optimal dispatch and prices.

    Attributes:
        market_1_trading_profit_gbp (float): Sum of Market 1 interval revenues (GBP).
        market_2_trading_profit_gbp (float): Sum of Market 2 interval revenues (GBP).
        market_1_half_hour_revenue_gbp (np.ndarray): Per half-hour Market 1 (GBP).
        market_2_half_hour_revenue_gbp (np.ndarray): Per half-hour Market 2 (GBP).
    """

    market_1_trading_profit_gbp: float
    market_2_trading_profit_gbp: float
    market_1_half_hour_revenue_gbp: np.ndarray
    market_2_half_hour_revenue_gbp: np.ndarray

    @property
    def total_trading_profit_gbp(self) -> float:
        """Combined trading profit across both markets.

        Returns:
            float: Total profit in GBP.
        """
        return self.market_1_trading_profit_gbp + self.market_2_trading_profit_gbp

    @classmethod
    def from_optimisation(
        cls,
        result: OptimisationResult,
        prices: AlignedMarketPrices,
    ) -> Self:
        """Compute interval and market-total revenue from an optimisation result.

        Args:
            result (OptimisationResult): Optimal dispatch and SOC from the MILP.
            prices (AlignedMarketPrices): Aligned January prices.

        Returns:
            TradingRevenue: Per-interval and per-market profit breakdown.
        """
        duration_hours: float = MARKET_1_INTERVAL_HOURS
        half_hour_count: int = len(prices.market_1_prices_gbp_per_mwh)
        market_1_half_hour: np.ndarray = np.zeros(half_hour_count, dtype=np.float64)
        market_2_half_hour: np.ndarray = np.zeros(half_hour_count, dtype=np.float64)
        for half_hour in range(half_hour_count):
            hour: int = half_hour // 2
            market_1_half_hour[half_hour] = (
                (
                    result.market_1_discharge_mw[half_hour]
                    - result.market_1_charge_mw[half_hour]
                )
                * prices.market_1_prices_gbp_per_mwh[half_hour]
                * duration_hours
            )
            market_2_half_hour[half_hour] = (
                (result.market_2_discharge_mw[hour] - result.market_2_charge_mw[hour])
                * prices.market_2_prices_gbp_per_mwh[hour]
                * duration_hours
            )
        return cls(
            market_1_trading_profit_gbp=float(np.sum(market_1_half_hour)),
            market_2_trading_profit_gbp=float(np.sum(market_2_half_hour)),
            market_1_half_hour_revenue_gbp=market_1_half_hour,
            market_2_half_hour_revenue_gbp=market_2_half_hour,
        )
