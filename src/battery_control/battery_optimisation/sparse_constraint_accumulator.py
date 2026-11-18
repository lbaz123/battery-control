import numpy as np
import scipy.sparse as sp
from scipy.optimize import LinearConstraint


class SparseConstraintAccumulator:
    """Collects COO constraint rows for a single sparse ``LinearConstraint``."""

    def __init__(self, variable_count: int) -> None:
        self._variable_count: int = variable_count
        self._rows: list[int] = []
        self._columns: list[int] = []
        self._values: list[float] = []
        self._lower_bounds: list[float] = []
        self._upper_bounds: list[float] = []
        self._next_row: int = 0

    def add_row(
        self,
        columns: list[int],
        coefficients: list[float],
        *,
        lower: float,
        upper: float,
    ) -> None:
        row: int = self._next_row
        self._next_row += 1
        self._rows.extend([row] * len(columns))
        self._columns.extend(columns)
        self._values.extend(coefficients)
        self._lower_bounds.append(lower)
        self._upper_bounds.append(upper)

    def to_linear_constraint(self) -> LinearConstraint:
        matrix: sp.csr_matrix = sp.csr_matrix(
            (self._values, (self._rows, self._columns)),
            shape=(self._next_row, self._variable_count),
        )
        return LinearConstraint(
            matrix,
            np.asarray(self._lower_bounds, dtype=np.float64),
            np.asarray(self._upper_bounds, dtype=np.float64),
        )
