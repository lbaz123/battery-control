from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class OptimisationResult:
    """Optimal trading plan for the aligned price window.

    Attributes:
        market_1_charge_mw (np.ndarray): Market 1 charge per half-hour (MW).
        market_1_discharge_mw (np.ndarray): Market 1 discharge per half-hour (MW).
        market_2_charge_mw (np.ndarray): Market 2 charge per hour (MW).
        market_2_discharge_mw (np.ndarray): Market 2 discharge per hour (MW).
        state_of_charge_mwh (np.ndarray): SOC at each interval boundary (MWh).
        total_trading_profit_gbp (float): Sum of interval profit (GBP).
        solver_status (int): HiGHS status code from SciPy.
        solver_message (str): HiGHS message from SciPy.
    """

    market_1_charge_mw: np.ndarray
    market_1_discharge_mw: np.ndarray
    market_2_charge_mw: np.ndarray
    market_2_discharge_mw: np.ndarray
    state_of_charge_mwh: np.ndarray
    total_trading_profit_gbp: float
    solver_status: int
    solver_message: str
