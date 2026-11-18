"""Prepare January 2018 market price arrays for optimisation.

Pairing is by observation index, not timestamp join: Market 1 rows ``2h`` and
``2h + 1`` correspond to Market 2 row ``h``. The supplied series contain
daylight-saving duplicate timestamps and fractional-second anomalies, so we
restrict the initial model to January 2018 and align on loader row order
(after invalid rows are dropped during ingestion).
"""

import numpy as np
import pandas as pd

from battery_control.data_loader.market_prices.constants import (
    PRICE_COLUMN,
    TIMESTAMP_COLUMN,
)
from battery_control.data_loader.market_prices.market_prices import MarketPrices
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import (
    JANUARY_2018_END_MARKET_1,
    JANUARY_2018_END_MARKET_2,
    JANUARY_2018_START,
    MARKET_1_INTERVAL,
    MARKET_1_JANUARY_OBSERVATIONS,
    MARKET_2_INTERVAL,
    MARKET_2_JANUARY_OBSERVATIONS,
)


class MarketPricesAligner:
    """Extracts and validates January 2018 prices from loaded market data."""

    def align(self, prices: MarketPrices) -> AlignedMarketPrices:
        market_1: pd.DataFrame = prices.market_1_half_hourly
        market_2: pd.DataFrame = prices.market_2_hourly
        self._require_rows_at_least(
            market_1,
            MARKET_1_JANUARY_OBSERVATIONS,
            "Market 1",
        )
        self._require_rows_at_least(
            market_2,
            MARKET_2_JANUARY_OBSERVATIONS,
            "Market 2",
        )
        self._require_start_timestamp(market_1, "Market 1")
        self._require_start_timestamp(market_2, "Market 2")

        january_1: pd.DataFrame = market_1.iloc[:MARKET_1_JANUARY_OBSERVATIONS]
        january_2: pd.DataFrame = market_2.iloc[:MARKET_2_JANUARY_OBSERVATIONS]
        self._require_regular_timestamps(
            january_1[TIMESTAMP_COLUMN],
            MARKET_1_INTERVAL,
            JANUARY_2018_END_MARKET_1,
            "Market 1",
        )
        self._require_regular_timestamps(
            january_2[TIMESTAMP_COLUMN],
            MARKET_2_INTERVAL,
            JANUARY_2018_END_MARKET_2,
            "Market 2",
        )

        market_1_prices: np.ndarray = january_1[PRICE_COLUMN].to_numpy(
            dtype=np.float64,
            copy=True,
        )
        market_2_prices: np.ndarray = january_2[PRICE_COLUMN].to_numpy(
            dtype=np.float64,
            copy=True,
        )
        return AlignedMarketPrices(
            market_1_prices_gbp_per_mwh=market_1_prices,
            market_2_prices_gbp_per_mwh=market_2_prices,
        )

    def _require_rows_at_least(
        self,
        frame: pd.DataFrame,
        minimum: int,
        market_name: str,
    ) -> None:
        if len(frame) < minimum:
            msg = (
                f"{market_name} has {len(frame)} observations; "
                f"need at least {minimum} for January 2018"
            )
            raise ValueError(msg)

    def _require_start_timestamp(
        self,
        frame: pd.DataFrame,
        market_name: str,
    ) -> None:
        first: object = frame.iloc[0][TIMESTAMP_COLUMN]
        timestamp: pd.Timestamp = pd.Timestamp(first)
        if timestamp != JANUARY_2018_START:
            msg = (
                f"{market_name} must start at {JANUARY_2018_START!s}, got {timestamp!s}"
            )
            raise ValueError(msg)

    def _require_regular_timestamps(
        self,
        timestamps: pd.Series,
        interval: pd.Timedelta,
        expected_end: pd.Timestamp,
        market_name: str,
    ) -> None:
        if timestamps.iloc[0] != JANUARY_2018_START:
            msg = f"{market_name} January window must start at {JANUARY_2018_START!s}"
            raise ValueError(msg)
        if timestamps.iloc[-1] != expected_end:
            msg = (
                f"{market_name} January window must end at {expected_end!s}, "
                f"got {timestamps.iloc[-1]!s}"
            )
            raise ValueError(msg)
        deltas: pd.Series = timestamps.diff().iloc[1:]
        mismatched: pd.Series = deltas != interval
        if mismatched.any():
            bad_index: int = int(mismatched.idxmax())
            msg = (
                f"{market_name} timestamps are not evenly spaced by {interval!s} "
                f"(gap or duplicate near index {bad_index})"
            )
            raise ValueError(msg)
