from pathlib import Path

import numpy as np
import pandas as pd


def _normalize_signed_zeros(frame: pd.DataFrame) -> pd.DataFrame:
    """Replace ``-0.0`` with ``0.0`` so the CSV is easier to read and diff."""
    normalized: pd.DataFrame = frame.copy()
    for column in normalized.select_dtypes(include=np.number).columns:
        values: np.ndarray = normalized[column].to_numpy(dtype=np.float64, copy=True)
        values[values == 0.0] = 0.0
        normalized[column] = values
    return normalized


class ResultsCsvWriter:
    """Writes the results table to CSV."""

    def write(self, frame: pd.DataFrame, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _normalize_signed_zeros(frame).to_csv(output_path, index=False)
        return output_path
