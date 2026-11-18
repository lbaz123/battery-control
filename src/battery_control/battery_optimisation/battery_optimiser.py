import numpy as np
from scipy.optimize import milp

from battery_control.battery_optimisation.battery_optimisation_error import (
    BatteryOptimisationError,
)
from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.battery_optimisation.trading_milp_builder import (
    TradingMilpBuilder,
    TradingMilpProblem,
)
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.aligned_market_prices import AlignedMarketPrices


class BatteryOptimiser:
    """Solves the January trading MILP using SciPy HiGHS."""

    def __init__(self) -> None:
        self._builder: TradingMilpBuilder = TradingMilpBuilder()

    def optimise(
        self,
        config: BatteryConfig,
        prices: AlignedMarketPrices,
    ) -> OptimisationResult:
        problem: TradingMilpProblem = self._builder.build(config, prices)
        result = milp(
            problem.objective,
            integrality=problem.integrality,
            bounds=problem.bounds,
            constraints=problem.constraints,
        )
        if not result.success:
            message: str = getattr(result, "message", "") or "MILP solver failed"
            raise BatteryOptimisationError(message)
        decision_vector: np.ndarray = self._builder.round_binary_modes(
            np.asarray(result.x, dtype=np.float64),
            problem.half_hour_count,
            problem.hour_count,
        )

        (
            market_1_charge,
            market_1_discharge,
            market_2_charge,
            market_2_discharge,
            state_of_charge,
        ) = self._builder.unpack_solution(
            decision_vector,
            problem.half_hour_count,
            problem.hour_count,
        )
        profit: float = self._builder.total_profit_gbp(
            decision_vector,
            prices,
            problem.half_hour_count,
            problem.hour_count,
        )
        status: int = int(getattr(result, "status", 0))
        solver_message: str = str(getattr(result, "message", ""))
        return OptimisationResult(
            market_1_charge_mw=market_1_charge,
            market_1_discharge_mw=market_1_discharge,
            market_2_charge_mw=market_2_charge,
            market_2_discharge_mw=market_2_discharge,
            state_of_charge_mwh=state_of_charge,
            total_trading_profit_gbp=profit,
            solver_status=status,
            solver_message=solver_message,
        )
