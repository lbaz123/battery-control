from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketPrices:
    """Loaded market price tables in loader row order (not yet aligned).

    Attributes:
        market_1_half_hourly (pd.DataFrame): Half-hourly timestamps and prices.
        market_2_hourly (pd.DataFrame): Hourly timestamps and prices.
    """

    market_1_half_hourly: pd.DataFrame
    market_2_hourly: pd.DataFrame
