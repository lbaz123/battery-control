import numpy as np

from battery_control.battery_optimisation.variable_layout import VariableLayout


class SolutionExtractor:
    """Maps a MILP decision vector to dispatches, SOC and objective profit."""

    def round_binary_modes(
        self,
        decision_vector: np.ndarray,
        layout: VariableLayout,
    ) -> np.ndarray:
        """Snap mode binaries to ``0`` or ``1`` after the relaxed solve.

        Args:
            decision_vector (np.ndarray): Solver decision vector.
            layout (VariableLayout): Decision vector index map.

        Returns:
            np.ndarray: Copy of ``decision_vector`` with ``z`` values rounded.
        """
        rounded: np.ndarray = decision_vector.copy()
        rounded[layout.z] = np.rint(rounded[layout.z])
        return rounded

    def unpack_dispatch(
        self,
        decision_vector: np.ndarray,
        layout: VariableLayout,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split the decision vector into power and SOC arrays.

        Args:
            decision_vector (np.ndarray): Solver decision vector.
            layout (VariableLayout): Decision vector index map.

        Returns:
            tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
            Market 1 charge, Market 1 discharge, Market 2 charge,
            Market 2 discharge, and SOC at boundaries (all MW or MWh).
        """
        return (
            decision_vector[layout.p1c].copy(),
            decision_vector[layout.p1d].copy(),
            decision_vector[layout.p2c].copy(),
            decision_vector[layout.p2d].copy(),
            decision_vector[layout.soc].copy(),
        )

    def profit_from_decision_vector(
        self,
        objective: np.ndarray,
        decision_vector: np.ndarray,
    ) -> float:
        """Compute trading profit from the minimisation objective.

        Args:
            objective (np.ndarray): Objective coefficients (negated profit).
            decision_vector (np.ndarray): Solver decision vector.

        Returns:
            float: Total trading profit in GBP.
        """
        return float(-objective @ decision_vector)