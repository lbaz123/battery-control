import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from battery_control.data_loader.market_prices.constants import (
    PRICE_COLUMN,
    TIMESTAMP_COLUMN,
)
from battery_control.data_loader.market_prices.market_prices import MarketPrices
from battery_control.data_loader.market_prices.market_prices_loader import (
    MarketPricesLoader,
)


class TestMarketPricesLoader(unittest.TestCase):
    loader: MarketPricesLoader

    def setUp(self) -> None:
        self.loader = MarketPricesLoader()

    @patch(
        "battery_control.data_loader.market_prices.market_prices_loader.pd.ExcelFile"
    )
    @patch(
        "battery_control.data_loader.market_prices.market_prices_loader.pd.read_excel"
    )
    def test_loads_both_markets_preserving_order(
        self,
        mock_read_excel: MagicMock,
        mock_excel_file: MagicMock,
    ) -> None:
        mock_excel_file.return_value = MagicMock(
            sheet_names=["Half-hourly data", "Hourly data"]
        )
        half_hourly: pd.DataFrame = pd.DataFrame(
            [
                [pd.NaT, "Market 1 Price [£/MWh]"],
                ["2018-01-01 00:00:00", 48.47],
                ["2018-01-01 00:30:00", 49.81],
            ]
        )
        hourly: pd.DataFrame = pd.DataFrame(
            [
                [pd.NaT, "Market 2 Price [£/MWh]"],
                ["2018-01-01 00:00:00", 51.89],
                ["2018-01-01 01:00:00", 55.49],
            ]
        )

        def read_side_effect(
            path: object,
            sheet_name: str,
            header: None = None,
        ) -> pd.DataFrame:
            if sheet_name == "Half-hourly data":
                return half_hourly
            return hourly

        mock_read_excel.side_effect = read_side_effect

        prices: MarketPrices = self.loader.load("market_prices.xlsx")

        self.assertEqual(
            list(prices.market_1_half_hourly.columns),
            [
                TIMESTAMP_COLUMN,
                PRICE_COLUMN,
            ],
        )
        self.assertEqual(len(prices.market_1_half_hourly), 2)
        self.assertEqual(len(prices.market_2_hourly), 2)
        self.assertEqual(
            prices.market_1_half_hourly[PRICE_COLUMN].tolist(),
            [48.47, 49.81],
        )
        self.assertEqual(
            prices.market_2_hourly[PRICE_COLUMN].tolist(),
            [51.89, 55.49],
        )

    @patch(
        "battery_control.data_loader.market_prices.market_prices_loader.pd.ExcelFile"
    )
    @patch(
        "battery_control.data_loader.market_prices.market_prices_loader.pd.read_excel"
    )
    def test_timestamp_column_is_datetime64(
        self,
        mock_read_excel: MagicMock,
        mock_excel_file: MagicMock,
    ) -> None:
        mock_excel_file.return_value = MagicMock(
            sheet_names=["Half-hourly data", "Hourly data"]
        )
        half_hourly: pd.DataFrame = pd.DataFrame(
            [
                [pd.NaT, "Market 1 Price [£/MWh]"],
                ["2018-01-01 00:00:00", 1.0],
            ]
        )
        hourly: pd.DataFrame = pd.DataFrame(
            [
                [pd.NaT, "Market 2 Price [£/MWh]"],
                ["2018-01-01 00:00:00", 2.0],
            ]
        )

        def read_side_effect(
            path: object,
            sheet_name: str,
            header: None = None,
        ) -> pd.DataFrame:
            if sheet_name == "Half-hourly data":
                return half_hourly
            return hourly

        mock_read_excel.side_effect = read_side_effect

        prices: MarketPrices = self.loader.load("market_prices.xlsx")
        timestamps: pd.Series = prices.market_1_half_hourly[TIMESTAMP_COLUMN]
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(timestamps))
