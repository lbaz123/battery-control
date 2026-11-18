import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.data_loader.battery_config.battery_config_load_error import (
    BatteryConfigLoadError,
)
from battery_control.data_loader.battery_config.battery_config_loader import (
    BatteryConfigLoader,
)


def _spec_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [None, "Values", "Units", "Description"],
            ["Max charging rate", 2.0, "MW", ""],
            ["Max discharging rate", 2.0, "MW", ""],
            ["Max storage volume", 4.0, "MWh", ""],
            ["Battery charging efficiency", 0.05, "-", ""],
            ["Battery discharging efficiency", 0.05, "-", ""],
        ]
    )


class TestBatteryConfigLoader(unittest.TestCase):
    loader: BatteryConfigLoader

    def setUp(self) -> None:
        self.loader = BatteryConfigLoader()

    @patch(
        "battery_control.data_loader.battery_config.battery_config_loader.pd.read_excel"
    )
    def test_loads_dispatch_parameters_from_labels(
        self, mock_read_excel: MagicMock
    ) -> None:
        mock_read_excel.return_value = _spec_frame()
        config: BatteryConfig = self.loader.load("battery_specification.xlsx")
        self.assertEqual(config.max_charge_power_mw, 2.0)
        self.assertEqual(config.max_discharge_power_mw, 2.0)
        self.assertEqual(config.energy_capacity_mwh, 4.0)
        self.assertEqual(config.charging_efficiency, 0.95)
        self.assertEqual(config.discharging_efficiency, 0.95)

    @patch(
        "battery_control.data_loader.battery_config.battery_config_loader.pd.read_excel"
    )
    def test_raises_when_required_label_missing(
        self, mock_read_excel: MagicMock
    ) -> None:
        frame: pd.DataFrame = _spec_frame().drop(index=4).reset_index(drop=True)
        mock_read_excel.return_value = frame
        with self.assertRaises(BatteryConfigLoadError):
            self.loader.load("battery_specification.xlsx")
