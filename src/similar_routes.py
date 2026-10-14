import pandas as pd

from anomaly_history import calculate_history_comparison
from weekly_aggregation import create_weekly_data
from preprocessing import load_shipments


def calculate_similar_route_comparison(
    df: pd.DataFrame,
) -> pd.DataFrame:
    result = df.copy()

    # Average cost for other routes with the same route_type
    # during the same week.
    peer_average = (
        result.groupby(["week_of", "route_type"])["cost_per_tonne_km"]
        .transform("mean")
    )

    # Exclude the current route from the peer average.
    group_size = (
        result.groupby(["week_of", "route_type"])["route"]
        .transform("count")
    )

    result["peer_sum"] = peer_average * group_size

    result["similar_routes_avg"] = (
        result["peer_sum"] - result["cost_per_tonne_km"]
    ) / (group_size - 1)

    result.loc[group_size <= 1, "similar_routes_avg"] = pd.NA

    result["vs_similar_routes_pct"] = (
        (result["cost_per_tonne_km"] - result["similar_routes_avg"])
        / result["similar_routes_avg"]
        * 100
    )

    return result.drop(columns=["peer_sum"])


def main():
    shipments = load_shipments()
    weekly = create_weekly_data(shipments)

    history = calculate_history_comparison(weekly)
    result = calculate_similar_route_comparison(history)

    print("\n" + "=" * 70)
    print("SIMILAR-ROUTE COMPARISON")
    print("=" * 70)

    print("\nColumns:")
    print(result.columns.tolist())

    print("\nFirst 20 rows:")
    print(
        result[
            [
                "route",
                "route_type",
                "week_of",
                "cost_per_tonne_km",
                "similar_routes_avg",
                "vs_similar_routes_pct",
            ]
        ].head(20).to_string(index=False)
    )

    print("\nRows without similar-route comparison:")
    print(result["similar_routes_avg"].isna().sum())

    print("\nRows with similar-route comparison:")
    print(result["similar_routes_avg"].notna().sum())


if __name__ == "__main__":
    main()