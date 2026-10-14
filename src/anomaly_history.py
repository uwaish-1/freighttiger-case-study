import pandas as pd

from weekly_aggregation import create_weekly_data
from preprocessing import load_shipments


HISTORY_WEEKS = 8


def calculate_history_comparison(weekly: pd.DataFrame) -> pd.DataFrame:
    df = weekly.copy()

    df = df.sort_values(["route", "week_of"]).reset_index(drop=True)

    df["history_avg"] = (
        df.groupby("route")["cost_per_tonne_km"]
        .transform(
            lambda series:
            series.shift(1)
            .rolling(window=HISTORY_WEEKS, min_periods=1)
            .mean()
        )
    )

    df["vs_own_history_pct"] = (
        (df["cost_per_tonne_km"] - df["history_avg"])
        / df["history_avg"]
        * 100
    )

    return df
    # Percentage difference from historical average
    df["vs_own_history_pct"] = (
        (
            df["cost_per_tonne_km"]
            - df["history_avg"]
        )
        / df["history_avg"]
        * 100
    )

    return df


def main():
    shipments = load_shipments()

    weekly = create_weekly_data(
        shipments
    )

    result = calculate_history_comparison(
        weekly
    )

    print("\n" + "=" * 70)
    print("8-WEEK HISTORICAL COMPARISON")
    print("=" * 70)

    print("\nColumns:")
    print(result.columns.tolist())

    print("\nFirst 20 rows:")
    print(
        result[
            [
                "route",
                "week_of",
                "cost_per_tonne_km",
                "history_avg",
                "vs_own_history_pct",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print("\nRows without enough historical data:")
    print(
        result["history_avg"]
        .isna()
        .sum()
    )

    print("\nRows with a complete 8-week history:")
    print(
        result["history_avg"]
        .notna()
        .sum()
    )


if __name__ == "__main__":
    main()