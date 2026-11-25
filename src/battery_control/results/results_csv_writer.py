from pathlib import Path

import numpy as np
import pandas as pd


class ResultsCsvWriter:
    """Writes the results table to CSV."""

    @staticmethod
    def _normalize_signed_zeros(frame: pd.DataFrame) -> pd.DataFrame:
        """Replace ``-0.0`` with ``0.0`` in numeric columns.

        Args:
            frame (pd.DataFrame): Results table before export.

        Returns:
            pd.DataFrame: Copy with signed zeros normalised.
        """
        normalized: pd.DataFrame = frame.copy()
        for column in normalized.select_dtypes(include=np.number).columns:
            values: np.ndarray = normalized[column].to_numpy(
                dtype=np.float64,
                copy=True,
            )
            values[values == 0.0] = 0.0
            normalized[column] = values
        return normalized

    def write(self, frame: pd.DataFrame, output_path: Path) -> Path:
        """Write the results table to CSV.

        Args:
            frame (pd.DataFrame): Results table to export.
            output_path (Path): Destination ``.csv`` file.

        Returns:
            Path: ``output_path`` after the file is written.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._normalize_signed_zeros(frame).to_csv(output_path, index=False)
        return output_path
