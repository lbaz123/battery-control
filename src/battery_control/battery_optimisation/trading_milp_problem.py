from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint

from battery_control.battery_optimisation.variable_layout import VariableLayout


@dataclass(frozen=True)
class TradingMilpProblem:
    objective: np.ndarray
    integrality: np.ndarray
    bounds: Bounds
    constraints: LinearConstraint
    layout: VariableLayout
    half_hour_count: int
    hour_count: int
