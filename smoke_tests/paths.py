from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
BATTERY_SPEC_PATH: Path = REPO_ROOT / "data" / "battery_specification.xlsx"
MARKET_PRICES_PATH: Path = REPO_ROOT / "data" / "market_prices.xlsx"
