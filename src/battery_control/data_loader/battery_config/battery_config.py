from dataclasses import dataclass


# Frozen: configuration must not change after parsing (hashable, safe to pass around).
@dataclass(frozen=True)
class BatteryConfig:
    max_charge_power_mw: float
    max_discharge_power_mw: float
    energy_capacity_mwh: float
    charging_efficiency: float
    discharging_efficiency: float
