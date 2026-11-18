"""Load half-hourly and hourly market price series from the prices workbook."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

SHEET_HALF_HOURLY = "Half-hourly data"
SHEET_HOURLY = "Hourly data"
TIMESTAMP_COLUMN = "timestamp"
PRICE_COLUMN = "price_gbp_per_mwh"


class MarketPricesLoadError(ValueError):
    """Raised when the market prices workbook cannot be parsed."""


@dataclass(frozen=True)
class MarketPrices:
    market_1_half_hourly: pd.DataFrame
    market_2_hourly: pd.DataFrame


def load_market_prices(path: Path | str) -> MarketPrices:
    """Load Market 1 and Market 2 price series without resampling or alignment."""
    path = Path(path)
    workbook = pd.ExcelFile(path)
    half_hourly_sheet = _resolve_sheet_name(
        workbook.sheet_names,
        SHEET_HALF_HOURLY,
        must_contain=("half", "hourly"),
    )
    hourly_sheet = _resolve_sheet_name(
        workbook.sheet_names,
        SHEET_HOURLY,
        must_contain=("hourly",),
        exclude=("half",),
    )
    market_1 = _read_price_sheet(path, half_hourly_sheet)
    market_2 = _read_price_sheet(path, hourly_sheet)
    return MarketPrices(
        market_1_half_hourly=market_1,
        market_2_hourly=market_2,
    )


def _resolve_sheet_name(
    sheet_names: list[str],
    exact_name: str,
    must_contain: tuple[str, ...],
    exclude: tuple[str, ...] = (),
) -> str:
    if exact_name in sheet_names:
        return exact_name
    lowered = [name.lower() for name in sheet_names]
    if exact_name.lower() in lowered:
        return sheet_names[lowered.index(exact_name.lower())]
    matches = [
        name
        for name in sheet_names
        if all(token in name.lower() for token in must_contain)
        and all(token not in name.lower() for token in exclude)
    ]
    if len(matches) == 1:
        return matches[0]
    msg = f"Could not resolve worksheet {exact_name!r} in {sheet_names!r}"
    raise MarketPricesLoadError(msg)


def _read_price_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    if raw.shape[1] < 2:
        msg = f"Worksheet {sheet_name!r} must have at least two columns"
        raise MarketPricesLoadError(msg)
    timestamp_series = raw.iloc[:, 0]
    price_series = raw.iloc[:, 1]
    timestamps = pd.to_datetime(timestamp_series, errors="coerce")
    prices = pd.to_numeric(price_series, errors="coerce")
    valid = timestamps.notna() & prices.notna()
    frame = pd.DataFrame(
        {
            TIMESTAMP_COLUMN: timestamps.loc[valid].reset_index(drop=True),
            PRICE_COLUMN: prices.loc[valid].reset_index(drop=True),
        }
    )
    if frame.empty:
        msg = f"No price observations found on worksheet {sheet_name!r}"
        raise MarketPricesLoadError(msg)
    return frame
