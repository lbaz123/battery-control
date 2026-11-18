from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint


@dataclass(frozen=True)
class TradingMilpProblem:
    objective: np.ndarray
    integrality: np.ndarray
    bounds: Bounds
    constraints: LinearConstraint
    half_hour_count: int
    hour_count: int