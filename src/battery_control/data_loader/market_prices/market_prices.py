from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketPrices:
    market_1_half_hourly: pd.DataFrame
    market_2_hourly: pd.DataFrame
