from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from battery_control.battery_optimisation.optimisation_result import OptimisationResult
from battery_control.data_loader.battery_config.battery_config import BatteryConfig
from battery_control.market_alignment.constants import (
    JANUARY_2018_END_MARKET_1,
    JANUARY_2018_START,
    MARKET_1_INTERVAL,
    january_observation_count,
)
from battery_control.results.trading_revenue import TradingRevenue

RESULTS_CSV_NAME: str = "january_2018_results.csv"
RESULTS_PLOT_NAME: str = "january_2018_results.png"
DISPATCH_HALF_HOURS: int = 48 * 2


def write_results_csv(frame: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)


def plot_results_png(frame: pd.DataFrame, output_path: Path) -> None:
    dispatch_end: int = min(DISPATCH_HALF_HOURS, len(frame))
    dispatch_slice: pd.DataFrame = frame.iloc[:dispatch_end]
    market_1_net: pd.Series = (
        dispatch_slice["market_1_discharge_mw"] - dispatch_slice["market_1_charge_mw"]
    )
    market_2_net: pd.Series = (
        dispatch_slice["market_2_discharge_mw"] - dispatch_slice["market_2_charge_mw"]
    )
    interval_revenue: pd.Series = (
        frame["market_1_revenue_gbp"] + frame["market_2_revenue_gbp"]
    )
    revenue_frame: pd.DataFrame = pd.DataFrame(
        {
            "interval_start": frame["interval_start"],
            "interval_revenue_gbp": interval_revenue,
        }
    )
    revenue_frame["calendar_date"] = revenue_frame["interval_start"].dt.normalize()
    daily_profit: pd.Series = revenue_frame.groupby("calendar_date", sort=True)[
        "interval_revenue_gbp"
    ].sum()
    cumulative_daily_profit: pd.Series = daily_profit.cumsum()

    fig, (dispatch_axis, profit_axis) = plt.subplots(
        2,
        1,
        figsize=(10, 8),
        constrained_layout=True,
    )
    dispatch_axis.axhline(0.0, color="black", linewidth=0.8, linestyle="--")
    dispatch_axis.plot(
        dispatch_slice["interval_start"],
        market_1_net,
        label="Market 1 net dispatch (MW)",
        linewidth=1.2,
    )
    dispatch_axis.plot(
        dispatch_slice["interval_start"],
        market_2_net,
        label="Market 2 net dispatch (MW)",
        linewidth=1.2,
    )
    dispatch_axis.set_title("Battery dispatch — first 48 hours of January 2018")
    dispatch_axis.set_xlabel("Time")
    dispatch_axis.set_ylabel("Net power (MW); positive = discharge / sell")
    dispatch_axis.legend(loc="best")
    dispatch_axis.tick_params(axis="x", rotation=25)

    profit_axis.plot(
        cumulative_daily_profit.index,
        cumulative_daily_profit.values,
        label="Cumulative daily trading profit",
        linewidth=1.5,
        color="tab:green",
    )
    profit_axis.set_title("Cumulative trading profit — January 2018")
    profit_axis.set_xlabel("Date")
    profit_axis.set_ylabel("Cumulative profit (£)")
    profit_axis.legend(loc="best")
    profit_axis.tick_params(axis="x", rotation=25)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def print_run_summary(
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
