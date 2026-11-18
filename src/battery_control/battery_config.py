"""Load dispatch-relevant battery parameters from the specification workbook."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

LABEL_MAX_CHARGE_POWER = "Max charging rate"
LABEL_MAX_DISCHARGE_POWER = "Max discharging rate"
LABEL_ENERGY_CAPACITY = "Max storage volume"
LABEL_CHARGE_ENERGY_LOSS = "Battery charging efficiency"
LABEL_DISCHARGE_ENERGY_LOSS = "Battery discharging efficiency"

ENERGY_LOSS_ASSUMPTION = (
    "Specification values labelled as charging/discharging 'efficiency' are "
    "fractional energy losses; efficiency in each direction is 1 minus that loss."
)


class BatteryConfigLoadError(ValueError):
    """Raised when the battery specification workbook cannot be parsed or validated."""


@dataclass(frozen=True)
class BatteryConfig:
    max_charge_power_mw: float
    max_discharge_power_mw: float
    energy_capacity_mwh: float
    charging_efficiency: float
    discharging_efficiency: float


def load_battery_config(path: Path | str) -> BatteryConfig:
    """Load and validate :class:`BatteryConfig` from the specification workbook."""
    path = Path(path)
    frame = pd.read_excel(path, sheet_name=0, header=None)
    label_to_value = _parse_label_value_table(frame)

    charge_mw = _require_label(label_to_value, LABEL_MAX_CHARGE_POWER)
    discharge_mw = _require_label(label_to_value, LABEL_MAX_DISCHARGE_POWER)
    capacity_mwh = _require_label(label_to_value, LABEL_ENERGY_CAPACITY)
    charge_loss = _require_label(label_to_value, LABEL_CHARGE_ENERGY_LOSS)
    discharge_loss = _require_label(label_to_value, LABEL_DISCHARGE_ENERGY_LOSS)

    _validate_positive("Max charging rate", charge_mw)
    _validate_positive("Max discharging rate", discharge_mw)
    _validate_positive("Max storage volume", capacity_mwh)
    _validate_energy_loss("Battery charging efficiency", charge_loss)
    _validate_energy_loss("Battery discharging efficiency", discharge_loss)

    return BatteryConfig(
        max_charge_power_mw=charge_mw,
        max_discharge_power_mw=discharge_mw,
        energy_capacity_mwh=capacity_mwh,
        charging_efficiency=1.0 - charge_loss,
        discharging_efficiency=1.0 - discharge_loss,
    )


def _parse_label_value_table(frame: pd.DataFrame) -> dict[str, float]:
    value_col, label_col, header_row = _locate_label_value_columns(frame)
    label_to_value: dict[str, float] = {}
    for row_index in range(header_row + 1, len(frame)):
        raw_label = frame.iat[row_index, label_col]
        if not isinstance(raw_label, str) or not raw_label.strip():
            continue
        raw_value = frame.iat[row_index, value_col]
        if pd.isna(raw_value):
            continue
        label_to_value[raw_label.strip()] = float(raw_value)
    return label_to_value


def _locate_label_value_columns(frame: pd.DataFrame) -> tuple[int, int, int]:
    scan_rows = min(len(frame), 10)
    for row_index in range(scan_rows):
        for col_index in range(frame.shape[1]):
            cell = frame.iat[row_index, col_index]
            if isinstance(cell, str) and cell.strip() == "Values":
                label_col = col_index - 1
                if label_col < 0:
                    msg = "Battery specification header has no label column"
                    raise BatteryConfigLoadError(msg)
                return col_index, label_col, row_index
    msg = "Battery specification workbook does not contain a 'Values' column header"
    raise BatteryConfigLoadError(msg)


def _require_label(label_to_value: dict[str, float], label: str) -> float:
    if label not in label_to_value:
        msg = f"Missing required battery parameter: {label!r}"
        raise BatteryConfigLoadError(msg)
    return label_to_value[label]


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        msg = f"{name} must be positive, got {value}"
        raise BatteryConfigLoadError(msg)


def _validate_energy_loss(name: str, value: float) -> None:
    if value < 0 or value >= 1:
        msg = f"{name} energy loss must be in [0, 1), got {value}"
        raise BatteryConfigLoadError(msg)
