import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from battery_control.battery_config import (
    BatteryConfigLoadError,
    load_battery_config,
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


class TestLoadBatteryConfig(unittest.TestCase):
    @patch("battery_control.battery_config.pd.read_excel")
    def test_loads_dispatch_parameters_from_labels(
        self, mock_read_excel: MagicMock
    ) -> None:
        mock_read_excel.return_value = _spec_frame()
        config = load_battery_config("battery_specification.xlsx")
        self.assertEqual(config.max_charge_power_mw, 2.0)
        self.assertEqual(config.max_discharge_power_mw, 2.0)
        self.assertEqual(config.energy_capacity_mwh, 4.0)
        self.assertEqual(config.charging_efficiency, 0.95)
        self.assertEqual(config.discharging_efficiency, 0.95)

    @patch("battery_control.battery_config.pd.read_excel")
    def test_raises_when_required_label_missing(
        self, mock_read_excel: MagicMock
    ) -> None:
        frame = _spec_frame().drop(index=4).reset_index(drop=True)
        mock_read_excel.return_value = frame
        with self.assertRaises(BatteryConfigLoadError):
            load_battery_config("battery_specification.xlsx")

    @patch("battery_control.battery_config.pd.read_excel")
    def test_raises_when_power_not_positive(self, mock_read_excel: MagicMock) -> None:
        frame = _spec_frame()
        frame.iat[1, 1] = 0.0
        mock_read_excel.return_value = frame
        with self.assertRaises(BatteryConfigLoadError):
            load_battery_config("battery_specification.xlsx")

    @patch("battery_control.battery_config.pd.read_excel")
    def test_raises_when_energy_loss_out_of_range(
        self, mock_read_excel: MagicMock
    ) -> None:
        frame = _spec_frame()
        frame.iat[4, 1] = 1.0
        mock_read_excel.return_value = frame
        with self.assertRaises(BatteryConfigLoadError):
            load_battery_config("battery_specification.xlsx")
