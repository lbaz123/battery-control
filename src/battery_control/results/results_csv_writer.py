from pathlib import Path

import pandas as pd

RESULTS_CSV_NAME: str = "january_2018_results.csv"


class ResultsCsvWriter:
    """Writes the results table to CSV."""

    def write(self, frame: pd.DataFrame, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output_path, index=False)
        return output_path
