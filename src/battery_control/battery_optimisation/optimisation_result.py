from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class OptimisationResult:
    """Optimal half-hourly battery trading plan for the aligned price window."""

    market_1_charge_mw: np.ndarray
    market_1_discharge_mw: np.ndarray
    market_2_charge_mw: np.ndarray
    market_2_discharge_mw: np.ndarray
    state_of_charge_mwh: np.ndarray
    total_trading_profit_gbp: float
    solver_status: int
    solver_message: str
