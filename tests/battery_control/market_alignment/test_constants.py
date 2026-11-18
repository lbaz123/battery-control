import unittest

from battery_control.market_alignment.constants import (
    JANUARY_2018_END_MARKET_1,
    JANUARY_2018_END_MARKET_2,
    JANUARY_2018_START,
    MARKET_1_INTERVAL,
    MARKET_2_INTERVAL,
    january_observation_count,
)


class TestJanuaryObservationCount(unittest.TestCase):
    def test_counts_half_hours_in_january_2018_for_market_1(self) -> None:
        count: int = january_observation_count(
            JANUARY_2018_START,
            JANUARY_2018_END_MARKET_1,
            MARKET_1_INTERVAL,
        )
        self.assertEqual(count, 31 * 24 * 2)

    def test_counts_hours_in_january_2018_for_market_2(self) -> None:
        count: int = january_observation_count(
            JANUARY_2018_START,
            JANUARY_2018_END_MARKET_2,
            MARKET_2_INTERVAL,
        )
        self.assertEqual(count, 31 * 24)
