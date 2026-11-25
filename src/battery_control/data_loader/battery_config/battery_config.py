from dataclasses import dataclass


@dataclass(frozen=True)
class BatteryConfig:
    """Frozen dispatch parameters for optimisation and reporting.

    Attributes:
        max_charge_power_mw (float): Maximum charge power (MW).
        max_discharge_power_mw (float): Maximum discharge power (MW).
        energy_capacity_mwh (float): Usable energy capacity (MWh).
        charging_efficiency (float): Charging efficiency in ``(0, 1]``.
        discharging_efficiency (float): Discharging efficiency in ``(0, 1]``.
    """

    max_charge_power_mw: float
    max_discharge_power_mw: float
    energy_capacity_mwh: float
    charging_efficiency: float
    discharging_efficiency: float
