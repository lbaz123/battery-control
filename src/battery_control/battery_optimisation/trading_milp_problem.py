from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint

from battery_control.battery_optimisation.variable_layout import VariableLayout


@dataclass(frozen=True)
class TradingMilpProblem:
    """Inputs for ``scipy.optimize.milp`` (minimise ``objective @ x``).

    Attributes:
        objective (np.ndarray): Minimisation coefficients (negated profit).
        integrality (np.ndarray): ``1`` where variables are integer.
        bounds (Bounds): Per-variable lower and upper limits.
        constraints (LinearConstraint): Sparse linear constraints.
        layout (VariableLayout): Decision vector index map.
        half_hour_count (int): Number of Market 1 half-hours ``N``.
        hour_count (int): Number of Market 2 hours ``H``.
    """

    objective: np.ndarray
    integrality: np.ndarray
    bounds: Bounds
    constraints: LinearConstraint
    layout: VariableLayout
    half_hour_count: int
    hour_count: int