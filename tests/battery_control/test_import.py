from __future__ import annotations

import importlib
import sys
import types
import unittest


class TestImport(unittest.TestCase):
    def test_package_imports(self) -> None:
        # tests/battery_control mirrors src/battery_control and would shadow imports.
        sys.path[:] = [p for p in sys.path if not p.rstrip("/").endswith("tests")]
        sys.modules.pop("battery_control", None)
        module: types.ModuleType = importlib.import_module("battery_control")
        version: str = getattr(module, "__version__")
        self.assertEqual(version, "0.1.0")
