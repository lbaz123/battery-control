import unittest

from battery_control.battery_optimisation.variable_layout import VariableLayout


class TestVariableLayout(unittest.TestCase):
    def test_variable_count_for_two_half_hours(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(
            half_hour_count=2,
            hour_count=1,
        )
        self.assertEqual(layout.variable_count, 11)

    def test_integrality_marks_only_binary_slice(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(2, 1)
        integrality = layout.integrality_vector()
        self.assertEqual(integrality.sum(), 2)
        self.assertTrue(integrality[layout.z_at(0)])
        self.assertTrue(integrality[layout.z_at(1)])

    def test_index_helpers_match_slices(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(4, 2)
        self.assertEqual(layout.p1c_at(2), layout.p1c.start + 2)
        self.assertEqual(layout.soc_at(4), layout.soc.start + 4)