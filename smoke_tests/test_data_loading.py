import unittest
from pathlib import Path

import pandas as pd

from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.data_loader.battery_config.battery_config_loader import (
    BatteryConfigLoader,
)
from battery_control.data_loader.market_prices.constants import (
    PRICE_COLUMN,
    TIMESTAMP_COLUMN,
)
from battery_control.data_loader.market_prices.market_prices import MarketPrices
from battery_control.data_loader.market_prices.market_prices_loader import (
    MarketPricesLoader,
)

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
BATTERY_SPEC_PATH: Path = REPO_ROOT / "data" / "battery_specification.xlsx"
MARKET_PRICES_PATH: Path = REPO_ROOT / "data" / "market_prices.xlsx"


class TestDataLoadingSmoke(unittest.TestCase):
    def test_battery_specification_loads(self) -> None:
        config: BatteryConfig = BatteryConfigLoader().load(BATTERY_SPEC_PATH)
        self.assertEqual(config.max_charge_power_mw, 2.0)
        self.assertEqual(config.max_discharge_power_mw, 2.0)
        self.assertEqual(config.energy_capacity_mwh, 4.0)
        self.assertEqual(config.charging_efficiency, 0.95)
        self.assertEqual(config.discharging_efficiency, 0.95)

    def test_market_prices_load_with_expected_shape_and_first_row(self) -> None:
        prices: MarketPrices = MarketPricesLoader().load(MARKET_PRICES_PATH)

        self.assertEqual(prices.market_1_half_hourly.shape, (52608, 2))
        self.assertEqual(prices.market_2_hourly.shape, (26304, 2))

        first_half_hour: pd.Series = prices.market_1_half_hourly.iloc[0]
        self.assertEqual(
            first_half_hour[TIMESTAMP_COLUMN],
            pd.Timestamp("2018-01-01 00:00:00"),
        )
        self.assertEqual(first_half_hour[PRICE_COLUMN], 48.47)

        first_hour: pd.Series = prices.market_2_hourly.iloc[0]
        self.assertEqual(
            first_hour[TIMESTAMP_COLUMN],
            pd.Timestamp("2018-01-01 00:00:00"),
        )
        self.assertEqual(first_hour[PRICE_COLUMN], 51.89)
