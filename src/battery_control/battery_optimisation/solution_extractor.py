import numpy as np

from battery_control.battery_optimisation.variable_layout import VariableLayout


class SolutionExtractor:
    """Maps a MILP decision vector to dispatches, SOC and objective profit."""

    def round_binary_modes(
        self,
        decision_vector: np.ndarray,
        layout: VariableLayout,
    ) -> np.ndarray:
        rounded: np.ndarray = decision_vector.copy()
        rounded[layout.z] = np.rint(rounded[layout.z])
        return rounded

    def unpack_dispatch(
        self,
        decision_vector: np.ndarray,
        layout: VariableLayout,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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
        return float(-objective @ decision_vector)