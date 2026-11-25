import pandas as pd

JANUARY_2018_START: pd.Timestamp = pd.Timestamp("2018-01-01 00:00:00")
JANUARY_2018_END_MARKET_1: pd.Timestamp = pd.Timestamp("2018-01-31 23:30:00")
JANUARY_2018_END_MARKET_2: pd.Timestamp = pd.Timestamp("2018-01-31 23:00:00")

MARKET_1_INTERVAL_HOURS: float = 0.5
MARKET_2_INTERVAL_HOURS: float = 1.0

MARKET_1_INTERVAL: pd.Timedelta = pd.Timedelta(hours=MARKET_1_INTERVAL_HOURS)
MARKET_2_INTERVAL: pd.Timedelta = pd.Timedelta(hours=MARKET_2_INTERVAL_HOURS)


def january_observation_count(
    start: pd.Timestamp,
    end: pd.Timestamp,
    interval: pd.Timedelta,
) -> int:
    """Count grid points from ``start`` through ``end`` at ``interval`` spacing.

    Args:
        start (pd.Timestamp): First timestamp (inclusive).
        end (pd.Timestamp): Last timestamp (inclusive).
        interval (pd.Timedelta): Spacing between observations.

    Returns:
        int: Number of observations on the grid.
    """
    return len(pd.date_range(start, end, freq=interval))
