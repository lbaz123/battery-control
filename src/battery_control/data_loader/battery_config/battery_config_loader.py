from pathlib import Path

import pandas as pd

from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.data_loader.battery_config.battery_config_load_error import (
    BatteryConfigLoadError,
)
from battery_control.data_loader.battery_config.constants import (
    LABEL_CHARGE_ENERGY_LOSS,
    LABEL_DISCHARGE_ENERGY_LOSS,
    LABEL_ENERGY_CAPACITY,
    LABEL_MAX_CHARGE_POWER,
    LABEL_MAX_DISCHARGE_POWER,
)


class BatteryConfigLoader:
    """Reads dispatch parameters from the battery specification workbook."""

    def load(self, path: Path | str) -> BatteryConfig:
        config_path: Path = Path(path)
        with pd.ExcelFile(config_path) as workbook:
            frame: pd.DataFrame = pd.read_excel(workbook, sheet_name=0, header=None)
        label_to_value: dict[str, float] = self._parse_label_value_table(frame)

        charge_mw: float = self._require_label(label_to_value, LABEL_MAX_CHARGE_POWER)
        discharge_mw: float = self._require_label(
            label_to_value, LABEL_MAX_DISCHARGE_POWER
        )
        capacity_mwh: float = self._require_label(label_to_value, LABEL_ENERGY_CAPACITY)
        charge_loss: float = self._require_label(
            label_to_value, LABEL_CHARGE_ENERGY_LOSS
        )
        discharge_loss: float = self._require_label(
            label_to_value,
            LABEL_DISCHARGE_ENERGY_LOSS,
        )

        return BatteryConfig(
            max_charge_power_mw=charge_mw,
            max_discharge_power_mw=discharge_mw,
            energy_capacity_mwh=capacity_mwh,
            charging_efficiency=1.0 - charge_loss,
            discharging_efficiency=1.0 - discharge_loss,
        )

    def _parse_label_value_table(self, frame: pd.DataFrame) -> dict[str, float]:
        value_col: int
        label_col: int
        header_row: int
        value_col, label_col, header_row = self._locate_label_value_columns(frame)
        label_to_value: dict[str, float] = {}
        for row_index in range(header_row + 1, len(frame)):
            raw_label: object = frame.iat[row_index, label_col]
            if not isinstance(raw_label, str) or not raw_label.strip():
                continue
            raw_value: object = frame.iat[row_index, value_col]
            if pd.isna(raw_value):
                continue
            label_to_value[raw_label.strip()] = float(raw_value)
        return label_to_value

    def _locate_label_value_columns(self, frame: pd.DataFrame) -> tuple[int, int, int]:
        scan_rows: int = min(len(frame), 10)
        for row_index in range(scan_rows):
            for col_index in range(frame.shape[1]):
                cell: object = frame.iat[row_index, col_index]
                if isinstance(cell, str) and cell.strip() == "Values":
                    label_col: int = col_index - 1
                    if label_col < 0:
                        msg: str = "Battery specification header has no label column"
                        raise BatteryConfigLoadError(msg)
                    return col_index, label_col, row_index
        msg = "Battery specification workbook does not contain a 'Values' column header"
        raise BatteryConfigLoadError(msg)

    def _require_label(self, label_to_value: dict[str, float], label: str) -> float:
        if label not in label_to_value:
            msg = f"Missing required battery parameter: {label!r}"
            raise BatteryConfigLoadError(msg)
        return label_to_value[label]
