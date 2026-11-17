import importlib
import sys
import unittest


class TestImport(unittest.TestCase):
    def test_package_imports(self) -> None:
        # tests/battery_control mirrors src/battery_control and would shadow imports.
        sys.path[:] = [p for p in sys.path if not p.rstrip("/").endswith("tests")]
        sys.modules.pop("battery_control", None)
        battery_control = importlib.import_module("battery_control")
        self.assertEqual(battery_control.__version__, "0.1.0")
