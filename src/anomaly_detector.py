import pandas as pd

from preprocessing import load_shipments
from weekly_aggregation import create_weekly_data
from anomaly_history import calculate_history_comparison
from similar_routes import calculate_similar_route_comparison


ANOMALY_THRESHOLD_PCT = 20.0


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    # A route is an anomaly candidate when its cost is rising
    # and is at least 20% above either:
    #   1. its own trailing history, or
    #   2. similar routes in the same week.
    #
    # The 20% threshold is an implementation choice inferred
    # from the supplied sample output. The case study itself
    # does not specify a numeric threshold.

    result["flagged"] = (
        (result["vs_own_history_pct"] >= ANOMALY_THRESHOLD_PCT)
        |
        (result["vs_similar_routes_pct"] >= ANOMALY_THRESHOLD_PCT)
    )

    result["flagged"] = result["flagged"].map(
        {True: "Yes", False: "No"}
    )

    return result


def main():
    shipments = load_shipments()
    weekly = create_weekly_data(shipments)

    history = calculate_history_comparison(weekly)
    compared = calculate_similar_route_comparison(history)

    result = detect_anomalies(compared)

    print("\n" + "=" * 70)
    print("ANOMALY DETECTION")
    print("=" * 70)

    print("\nThreshold:")
    print(f"{ANOMALY_THRESHOLD_PCT:.1f}%")

    print("\nFlagged rows:")
    flagged = result[result["flagged"] == "Yes"]

    print(f"Total flagged: {len(flagged)}")

    print(
        flagged[
            [
                "route",
                "week_of",
                "cost_per_tonne_km",
                "vs_own_history_pct",
                "vs_similar_routes_pct",
                "flagged",
            ]
        ]
        .sort_values("week_of")
        .head(30)
        .to_string(index=False)
    )

    print("\nFlag distribution:")
    print(result["flagged"].value_counts())


if __name__ == "__main__":
    main()