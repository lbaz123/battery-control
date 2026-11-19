from pathlib import Path

from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.constants import (
    JANUARY_2018_END_MARKET_1,
    JANUARY_2018_START,
    MARKET_1_INTERVAL,
    january_observation_count,
)
from battery_control.results.trading_revenue import TradingRevenue


class RunSummaryPrinter:
    """Prints a concise stdout summary of a January optimisation run."""

    def print_summary(
        self,
        config: BatteryConfig,
        result: OptimisationResult,
        revenue: TradingRevenue,
        csv_path: Path,
        plot_path: Path,
    ) -> None:
        interval_count: int = january_observation_count(
            JANUARY_2018_START,
            JANUARY_2018_END_MARKET_1,
            MARKET_1_INTERVAL,
        )
        lines: list[str] = [
            "=== Battery control — January 2018 MILP ===",
            (
                f"Period optimised: {JANUARY_2018_START} → {JANUARY_2018_END_MARKET_1} "
                f"({interval_count} half-hour intervals)"
            ),
            (
                f"Battery: max charge {config.max_charge_power_mw:.1f} MW, "
                f"max discharge {config.max_discharge_power_mw:.1f} MW, "
                f"capacity {config.energy_capacity_mwh:.1f} MWh, "
                f"charging efficiency {config.charging_efficiency:.2f}, "
                f"discharging efficiency {config.discharging_efficiency:.2f}"
            ),
            f"Market 1 trading profit:  £{revenue.market_1_trading_profit_gbp:,.2f}",
            f"Market 2 trading profit:  £{revenue.market_2_trading_profit_gbp:,.2f}",
            f"Total trading profit:     £{result.total_trading_profit_gbp:,.2f}",
            f"Solver status: {result.solver_status} ({result.solver_message})",
            "Outputs:",
            f"  {csv_path}",
            f"  {plot_path}",
        ]
        print("\n".join(lines))
