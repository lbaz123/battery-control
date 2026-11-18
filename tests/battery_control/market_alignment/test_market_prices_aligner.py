import unittest

import numpy as np
import pandas as pd

from battery_control.data_loader.market_prices.constants import (
    PRICE_COLUMN,
    TIMESTAMP_COLUMN,
)
from battery_control.data_loader.market_prices.market_prices import MarketPrices
from battery_control.market_alignment.constants import (
    JANUARY_2018_START,
    MARKET_1_JANUARY_OBSERVATIONS,
    MARKET_2_JANUARY_OBSERVATIONS,
)
from battery_control.market_alignment.market_prices_aligner import MarketPricesAligner


def _market_prices(
    market_1: pd.DataFrame,
    market_2: pd.DataFrame,
) -> MarketPrices:
    return MarketPrices(
        market_1_half_hourly=market_1,
        market_2_hourly=market_2,
    )


def _january_market_1(extra_rows: int = 0) -> pd.DataFrame:
    timestamps: pd.DatetimeIndex = pd.date_range(
        JANUARY_2018_START,
        periods=MARKET_1_JANUARY_OBSERVATIONS + extra_rows,
        freq="30min",
    )
    prices: list[float] = [float(index) for index in range(len(timestamps))]
    return pd.DataFrame({TIMESTAMP_COLUMN: timestamps, PRICE_COLUMN: prices})


def _january_market_2(extra_rows: int = 0) -> pd.DataFrame:
    timestamps: pd.DatetimeIndex = pd.date_range(
        JANUARY_2018_START,
        periods=MARKET_2_JANUARY_OBSERVATIONS + extra_rows,
        freq="1h",
    )
    prices: list[float] = [100.0 + index for index in range(len(timestamps))]
    return pd.DataFrame({TIMESTAMP_COLUMN: timestamps, PRICE_COLUMN: prices})


class TestMarketPricesAligner(unittest.TestCase):
    aligner: MarketPricesAligner

    def setUp(self) -> None:
        self.aligner = MarketPricesAligner()

    def test_january_selection_and_observation_counts(self) -> None:
        prices: MarketPrices = _market_prices(
            _january_market_1(extra_rows=10),
            _january_market_2(extra_rows=5),
        )
        aligned = self.aligner.align(prices)
        self.assertEqual(aligned.market_1_prices_gbp_per_mwh.shape, (1488,))
        self.assertEqual(aligned.market_2_prices_gbp_per_mwh.shape, (744,))

    def test_two_to_one_index_pairing(self) -> None:
        market_1: pd.DataFrame = _january_market_1()
        market_2: pd.DataFrame = _january_market_2()
        for hour in range(5):
            market_1.loc[2 * hour, PRICE_COLUMN] = 10.0 + hour
            market_1.loc[2 * hour + 1, PRICE_COLUMN] = 20.0 + hour
            market_2.loc[hour, PRICE_COLUMN] = 1000.0 + hour
        aligned = self.aligner.align(_market_prices(market_1, market_2))
        for hour in range(5):
            self.assertEqual(aligned.market_1_prices_gbp_per_mwh[2 * hour], 10.0 + hour)
            self.assertEqual(
                aligned.market_1_prices_gbp_per_mwh[2 * hour + 1],
                20.0 + hour,
            )
            self.assertEqual(aligned.market_2_prices_gbp_per_mwh[hour], 1000.0 + hour)

    def test_original_price_ordering_preserved(self) -> None:
        market_1: pd.DataFrame = _january_market_1()
        market_2: pd.DataFrame = _january_market_2()
        aligned = self.aligner.align(_market_prices(market_1, market_2))
        expected_1: np.ndarray = market_1.iloc[:MARKET_1_JANUARY_OBSERVATIONS][
            PRICE_COLUMN
        ].to_numpy(dtype=np.float64)
        expected_2: np.ndarray = market_2.iloc[:MARKET_2_JANUARY_OBSERVATIONS][
            PRICE_COLUMN
        ].to_numpy(dtype=np.float64)
        np.testing.assert_array_equal(
            aligned.market_1_prices_gbp_per_mwh,
            expected_1,
        )
        np.testing.assert_array_equal(
            aligned.market_2_prices_gbp_per_mwh,
            expected_2,
        )

    def test_negative_prices_preserved(self) -> None:
        market_1: pd.DataFrame = _january_market_1()
        market_2: pd.DataFrame = _january_market_2()
        market_1.loc[10, PRICE_COLUMN] = -12.5
        market_2.loc[4, PRICE_COLUMN] = -3.25
        aligned = self.aligner.align(_market_prices(market_1, market_2))
        self.assertEqual(aligned.market_1_prices_gbp_per_mwh[10], -12.5)
        self.assertEqual(aligned.market_2_prices_gbp_per_mwh[4], -3.25)

    def test_raises_when_start_timestamp_is_wrong(self) -> None:
        market_1: pd.DataFrame = _january_market_1()
        market_2: pd.DataFrame = _january_market_2()
        market_1.loc[0, TIMESTAMP_COLUMN] = pd.Timestamp("2018-01-02 00:00:00")
        with self.assertRaises(ValueError):
            self.aligner.align(_market_prices(market_1, market_2))

    def test_raises_when_insufficient_observations(self) -> None:
        market_1: pd.DataFrame = _january_market_1()[:100]
        market_2: pd.DataFrame = _january_market_2()
        with self.assertRaises(ValueError):
            self.aligner.align(_market_prices(market_1, market_2))

    def test_raises_when_market_1_timestamps_have_gap(self) -> None:
        market_1: pd.DataFrame = _january_market_1()
        shifted: pd.Timestamp = market_1.loc[50, TIMESTAMP_COLUMN] + pd.Timedelta(
            hours=1
        )
        market_1.loc[51:, TIMESTAMP_COLUMN] = pd.date_range(
            shifted,
            periods=len(market_1) - 51,
            freq="30min",
        )
        market_2: pd.DataFrame = _january_market_2()
        with self.assertRaises(ValueError):
            self.aligner.align(_market_prices(market_1, market_2))

    def test_raises_when_january_window_ends_in_february(self) -> None:
        market_1: pd.DataFrame = pd.DataFrame(
            {
                TIMESTAMP_COLUMN: pd.date_range(
                    JANUARY_2018_START,
                    periods=MARKET_1_JANUARY_OBSERVATIONS,
                    freq="30min",
                )
                + pd.Timedelta(hours=1),
                PRICE_COLUMN: 1.0,
            }
        )
        market_2: pd.DataFrame = _january_market_2()
        with self.assertRaises(ValueError):
            self.aligner.align(_market_prices(market_1, market_2))
