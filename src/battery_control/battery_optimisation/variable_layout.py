from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class VariableLayout:
    """Index map for the flat MILP vector: p1c, p1d, p2c, p2d, soc, then binary z."""

    half_hour_count: int
    hour_count: int
    p1c: slice
    p1d: slice
    p2c: slice
    p2d: slice
    soc: slice
    z: slice

    @property
    def variable_count(self) -> int:
        """Length of the flat decision vector.

        Returns:
            int: ``4N + 2H + N + 1`` for ``N`` half-hours and ``H`` hours.
        """
        return (
            2 * self.half_hour_count
            + 2 * self.hour_count
            + (self.half_hour_count + 1)
            + self.half_hour_count
        )

    @classmethod
    def from_counts(cls, half_hour_count: int, hour_count: int) -> "VariableLayout":
        """Build contiguous index slices from interval counts.

        Args:
            half_hour_count (int): Number of Market 1 half-hours ``N``.
            hour_count (int): Number of Market 2 clock hours ``H``.

        Returns:
            VariableLayout: Slice map for each decision block.
        """
        offset: int = 0
        p1c = slice(offset, offset + half_hour_count)
        offset += half_hour_count
        p1d = slice(offset, offset + half_hour_count)
        offset += half_hour_count
        p2c = slice(offset, offset + hour_count)
        offset += hour_count
        p2d = slice(offset, offset + hour_count)
        offset += hour_count
        soc = slice(offset, offset + half_hour_count + 1)
        offset += half_hour_count + 1
        z = slice(offset, offset + half_hour_count)
        return cls(
            half_hour_count=half_hour_count,
            hour_count=hour_count,
            p1c=p1c,
            p1d=p1d,
            p2c=p2c,
            p2d=p2d,
            soc=soc,
            z=z,
        )

    def integrality_vector(self) -> np.ndarray:
        """Integrality flags for mode binaries.

        Returns:
            np.ndarray: ``uint8`` flags; ``1`` on mode binaries ``z`` only.
        """
        vector: np.ndarray = np.zeros(self.variable_count, dtype=np.uint8)
        vector[self.z] = 1
        return vector

    def p1c_at(self, half_hour: int) -> int:
        """Index of Market 1 charge power at a half-hour.

        Args:
            half_hour (int): Half-hour index.

        Returns:
            int: Position in the flat decision vector.
        """
        return self.p1c.start + half_hour

    def p1d_at(self, half_hour: int) -> int:
        """Index of Market 1 discharge power at a half-hour.

        Args:
            half_hour (int): Half-hour index.

        Returns:
            int: Position in the flat decision vector.
        """
        return self.p1d.start + half_hour

    def p2c_at(self, hour: int) -> int:
        """Index of Market 2 charge power at a clock hour.

        Args:
            hour (int): Hour index.

        Returns:
            int: Position in the flat decision vector.
        """
        return self.p2c.start + hour

    def p2d_at(self, hour: int) -> int:
        """Index of Market 2 discharge power at a clock hour.

        Args:
            hour (int): Hour index.

        Returns:
            int: Position in the flat decision vector.
        """
        return self.p2d.start + hour

    def soc_at(self, boundary: int) -> int:
        """Index of state of charge at an interval boundary.

        Args:
            boundary (int): Boundary index from ``0`` through ``N``.

        Returns:
            int: Position in the flat decision vector.
        """
        return self.soc.start + boundary

    def z_at(self, half_hour: int) -> int:
        """Index of the charge/discharge mode binary at a half-hour.

        Args:
            half_hour (int): Half-hour index.

        Returns:
            int: Position in the flat decision vector.
        """
        return self.z.start + half_hour