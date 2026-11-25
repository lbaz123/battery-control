from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AlignedMarketPrices:
    """January 2018 prices as NumPy arrays in loader row order.

    Attributes:
        market_1_prices_gbp_per_mwh (np.ndarray): Half-hourly prices (GBP/MWh).
        market_2_prices_gbp_per_mwh (np.ndarray): Hourly prices (GBP/MWh).
    """

    market_1_prices_gbp_per_mwh: np.ndarray
    market_2_prices_gbp_per_mwh: np.ndarray
