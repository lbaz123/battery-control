import unittest

import numpy as np

from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.battery_optimisation.solution_extractor import SolutionExtractor
from battery_control.battery_optimisation.trading_milp_builder import TradingMilpBuilder
from battery_control.battery_optimisation.variable_layout import VariableLayout
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices
from battery_control.market_alignment.constants import MARKET_1_INTERVAL_HOURS
from tests.battery_control.battery_optimisation.test_support import revenue_from_markets


def _result_like(
    layout: VariableLayout,
    decision_vector: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    extractor = SolutionExtractor()
    return extractor.unpack_dispatch(decision_vector, layout)


class TestSolutionExtractor(unittest.TestCase):
    def test_profit_from_objective_matches_market_revenue(self) -> None:
        layout: VariableLayout = VariableLayout.from_counts(2, 1)
        prices: AlignedMarketPrices = AlignedMarketPrices(
            market_1_prices_gbp_per_mwh=np.array([2.0, 8.0]),
            market_2_prices_gbp_per_mwh=np.array([1.0]),
        )
        objective = TradingMilpBuilder._build_objective_coefficients(
            prices,
            layout,
            MARKET_1_INTERVAL_HOURS,
        )
        decision: np.ndarray = np.zeros(layout.variable_count)
        decision[layout.p1c_at(0)] = 1.0
        decision[layout.p1d_at(1)] = 2.0
        decision[layout.p2d_at(0)] = 0.5
        extractor = SolutionExtractor()
        profit: float = extractor.profit_from_decision_vector(objective, decision)
        (
            p1c,
            p1d,
            p2c,
            p2d,
            soc,
        ) = _result_like(layout, decision)
        stub: OptimisationResult = OptimisationResult(
            market_1_charge_mw=p1c,
            market_1_discharge_mw=p1d,
            market_2_charge_mw=p2c,
            market_2_discharge_mw=p2d,
            state_of_charge_mwh=soc,
            total_trading_profit_gbp=profit,
            solver_status=0,
            solver_message="",
        )
        self.assertAlmostEqual(profit, revenue_from_markets(stub, prices), places=9)
