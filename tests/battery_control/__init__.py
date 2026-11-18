import sys
from pathlib import Path

# tests/battery_control mirrors src/battery_control and may shadow the package.
_src: Path = Path(__file__).resolve().parents[2] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
_shadow = sys.modules.get("battery_control")
if _shadow is not None:
    shadow_file: str = (getattr(_shadow, "__file__", None) or "").replace("\\", "/")
    if "/tests/" in shadow_file:
        del sys.modules["battery_control"]
