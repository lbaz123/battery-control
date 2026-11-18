from __future__ import annotations

import unittest

import battery_control


class TestSmokeImport(unittest.TestCase):
    def test_package_imports(self) -> None:
        version: str = battery_control.__version__
        self.assertEqual(version, "0.1.0")
