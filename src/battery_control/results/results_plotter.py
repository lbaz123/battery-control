from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from battery_control.results.constants import (
    DISPATCH_PLOT_HALF_HOURS,
    DISPATCH_PLOT_HOURS,
)


class ResultsPlotter:
    """Writes the two-panel January results PNG from a results table."""

    def save(self, frame: pd.DataFrame, output_path: Path) -> Path:
        """Write the two-panel dispatch and cumulative-profit PNG.

        Args:
            frame (pd.DataFrame): Results table from :class:`ResultsTableBuilder`.
            output_path (Path): Destination ``.png`` file.

        Returns:
            Path: ``output_path`` after the file is written.
        """
        dispatch_end: int = min(DISPATCH_PLOT_HALF_HOURS, len(frame))
        dispatch_slice: pd.DataFrame = frame.iloc[:dispatch_end]
        market_1_net: pd.Series = (
            dispatch_slice["market_1_discharge_mw"]
            - dispatch_slice["market_1_charge_mw"]
        )
        market_2_net: pd.Series = (
            dispatch_slice["market_2_discharge_mw"]
            - dispatch_slice["market_2_charge_mw"]
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
        dispatch_axis.set_title(
            f"Battery dispatch — first {DISPATCH_PLOT_HOURS} hours of January 2018",
        )
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
        return output_path
