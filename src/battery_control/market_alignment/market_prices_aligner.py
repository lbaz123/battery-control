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
    MARKET_2_INTERVAL,
    january_observation_count,
)
from battery_control.market_alignment.market_prices_alignment_error import (
    MarketPricesAlignmentError,
)


class MarketPricesAligner:
    """Extracts and validates January 2018 prices from loaded market data."""

    def align(self, prices: MarketPrices) -> AlignedMarketPrices:
        january_1: pd.DataFrame = self._january_window(
            prices.market_1_half_hourly,
            "Market 1",
            JANUARY_2018_START,
            JANUARY_2018_END_MARKET_1,
            MARKET_1_INTERVAL,
        )
        january_2: pd.DataFrame = self._january_window(
            prices.market_2_hourly,
            "Market 2",
            JANUARY_2018_START,
            JANUARY_2018_END_MARKET_2,
            MARKET_2_INTERVAL,
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

    def _january_window(
        self,
        frame: pd.DataFrame,
        market_name: str,
        start: pd.Timestamp,
        end: pd.Timestamp,
        interval: pd.Timedelta,
    ) -> pd.DataFrame:
        expected_count: int = january_observation_count(start, end, interval)
        if len(frame) < expected_count:
            msg = (
                f"{market_name} has {len(frame)} observations; "
                f"need {expected_count} from {start!s} through {end!s}"
            )
            raise MarketPricesAlignmentError(msg)
        first: pd.Timestamp = pd.Timestamp(frame.iloc[0][TIMESTAMP_COLUMN])
        if first != start:
            msg = f"{market_name} must start at {start!s}, got {first!s}"
            raise MarketPricesAlignmentError(msg)
        window: pd.DataFrame = frame.iloc[:expected_count]
        last: pd.Timestamp = pd.Timestamp(window.iloc[-1][TIMESTAMP_COLUMN])
        if last != end:
            msg = f"{market_name} must end at {end!s}, got {last!s}"
            raise MarketPricesAlignmentError(msg)
        expected_timestamps: pd.DatetimeIndex = pd.date_range(
            start,
            end,
            freq=interval,
        )
        actual_timestamps: pd.DatetimeIndex = pd.DatetimeIndex(
            window[TIMESTAMP_COLUMN],
        )
        if not expected_timestamps.equals(actual_timestamps):
            msg = (
                f"{market_name} timestamps do not match the expected sequence "
                f"from {start!s} through {end!s} at {interval!s} spacing"
            )
            raise MarketPricesAlignmentError(msg)
        return window
