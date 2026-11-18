from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AlignedMarketPrices:
    """January 2018 market prices as contiguous numeric arrays in loader row order."""

    market_1_prices_gbp_per_mwh: np.ndarray
    market_2_prices_gbp_per_mwh: np.ndarray
