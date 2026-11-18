import unittest
from pathlib import Path

from battery_control.data_loader.market_prices.market_prices_loader import (
    MarketPricesLoader,
)
from battery_control.market_alignment.constants import (
    MARKET_1_JANUARY_OBSERVATIONS,
    MARKET_2_JANUARY_OBSERVATIONS,
)
from battery_control.market_alignment.market_prices_aligner import MarketPricesAligner

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
MARKET_PRICES_PATH: Path = REPO_ROOT / "data" / "market_prices.xlsx"


class TestMarketAlignmentSmoke(unittest.TestCase):
    def test_aligns_january_2018_from_committed_workbook(self) -> None:
        prices = MarketPricesLoader().load(MARKET_PRICES_PATH)
        aligned = MarketPricesAligner().align(prices)
        self.assertEqual(
            aligned.market_1_prices_gbp_per_mwh.shape,
            (MARKET_1_JANUARY_OBSERVATIONS,),
        )
        self.assertEqual(
            aligned.market_2_prices_gbp_per_mwh.shape,
            (MARKET_2_JANUARY_OBSERVATIONS,),
        )
        self.assertEqual(aligned.market_1_prices_gbp_per_mwh[0], 48.47)
        self.assertEqual(aligned.market_2_prices_gbp_per_mwh[0], 51.89)
