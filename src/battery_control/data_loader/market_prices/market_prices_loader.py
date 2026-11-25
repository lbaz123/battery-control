from pathlib import Path

import pandas as pd

from battery_control.data_loader.market_prices.constants import (
    PRICE_COLUMN,
    SHEET_HALF_HOURLY,
    SHEET_HOURLY,
    TIMESTAMP_COLUMN,
)
from battery_control.data_loader.market_prices.market_prices import MarketPrices
from battery_control.data_loader.market_prices.market_prices_load_error import (
    MarketPricesLoadError,
)


class MarketPricesLoader:
    """Reads Market 1 and Market 2 price series without resampling or alignment."""

    def load(self, path: Path | str) -> MarketPrices:
        """Load both market worksheets without alignment or resampling.

        Args:
            path (Path | str): Path to ``market_prices.xlsx``.

        Returns:
            MarketPrices: Half-hourly and hourly price tables.

        Raises:
            MarketPricesLoadError: If sheets cannot be resolved or are empty.
        """
        prices_path: Path = Path(path)
        with pd.ExcelFile(prices_path) as workbook:
            half_hourly_sheet: str = self._resolve_sheet_name(
                workbook.sheet_names,
                SHEET_HALF_HOURLY,
                must_contain=("half", "hourly"),
            )
            hourly_sheet: str = self._resolve_sheet_name(
                workbook.sheet_names,
                SHEET_HOURLY,
                must_contain=("hourly",),
                exclude=("half",),
            )
            market_1: pd.DataFrame = self._read_price_sheet(
                workbook,
                half_hourly_sheet,
            )
            market_2: pd.DataFrame = self._read_price_sheet(workbook, hourly_sheet)
        return MarketPrices(
            market_1_half_hourly=market_1,
            market_2_hourly=market_2,
        )

    def _resolve_sheet_name(
        self,
        sheet_names: list[str],
        exact_name: str,
        must_contain: tuple[str, ...],
        exclude: tuple[str, ...] = (),
    ) -> str:
        """Resolve a worksheet name by exact match or unique keyword match.

        Args:
            sheet_names (list[str]): Names in the workbook.
            exact_name (str): Preferred sheet name from constants.
            must_contain (tuple[str, ...]): Substrings required in a fallback match.
            exclude (tuple[str, ...]): Substrings that disqualify a fallback match.

        Returns:
            str: Resolved worksheet name.

        Raises:
            MarketPricesLoadError: If no unique match is found.
        """
        if exact_name in sheet_names:
            return exact_name
        lowered: list[str] = [name.lower() for name in sheet_names]
        if exact_name.lower() in lowered:
            return sheet_names[lowered.index(exact_name.lower())]
        matches: list[str] = [
            name
            for name in sheet_names
            if all(token in name.lower() for token in must_contain)
            and all(token not in name.lower() for token in exclude)
        ]
        if len(matches) == 1:
            return matches[0]
        msg: str = f"Could not resolve worksheet {exact_name!r} in {sheet_names!r}"
        raise MarketPricesLoadError(msg)

    def _read_price_sheet(
        self,
        workbook: pd.ExcelFile,
        sheet_name: str,
    ) -> pd.DataFrame:
        """Read timestamp and price columns, dropping invalid rows.

        Args:
            workbook (pd.ExcelFile): Open market prices workbook.
            sheet_name (str): Worksheet to read.

        Returns:
            pd.DataFrame: Timestamp and price columns in loader row order.

        Raises:
            MarketPricesLoadError: If the sheet is too narrow or has no valid rows.
        """
        raw: pd.DataFrame = pd.read_excel(workbook, sheet_name=sheet_name, header=None)
        if raw.shape[1] < 2:
            msg: str = f"Worksheet {sheet_name!r} must have at least two columns"
            raise MarketPricesLoadError(msg)
        timestamp_series: pd.Series = raw.iloc[:, 0]
        price_series: pd.Series = raw.iloc[:, 1]
        timestamps: pd.Series = pd.to_datetime(timestamp_series, errors="coerce")
        prices: pd.Series = pd.to_numeric(price_series, errors="coerce")
        valid: pd.Series = timestamps.notna() & prices.notna()
        frame: pd.DataFrame = pd.DataFrame(
            {
                TIMESTAMP_COLUMN: timestamps.loc[valid].reset_index(drop=True),
                PRICE_COLUMN: prices.loc[valid].reset_index(drop=True),
            }
        )
        if frame.empty:
            msg = f"No price observations found on worksheet {sheet_name!r}"
            raise MarketPricesLoadError(msg)
        return frame
