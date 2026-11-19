from pathlib import Path

import pandas as pd

DISPATCH_HALF_HOURS: int = 48 * 2


class ResultsPlotter:
    """Writes the two-panel January results PNG from a results table."""

    def save(self, frame: pd.DataFrame, output_path: Path) -> Path:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        dispatch_end: int = min(DISPATCH_HALF_HOURS, len(frame))
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
        return output_path
