import pandas as pd

from preprocessing import load_shipments


def create_weekly_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate shipment records into route-week observations.

    Weekly cost per tonne-km is calculated using:

        total freight cost
        ------------------
        total tonne-km

    where:

        tonne-km = quantity_tonnes * distance_km
    """

    df = df.copy()

    # Calculate tonne-km for each shipment
    df["tonne_km"] = (
        df["quantity_tonnes"]
        * df["distance_km"]
    )

    # Aggregate by route and week
    weekly = (
        df.groupby(
            [
                "route",
                "route_type",
                "week_of",
            ],
            as_index=False
        )
        .agg(
            total_freight_cost_inr=(
                "freight_cost_inr",
                "sum"
            ),
            total_tonne_km=(
                "tonne_km",
                "sum"
            ),
            shipment_count=(
                "shipment_id",
                "count"
            ),
        )
    )

    # Calculate weekly cost per tonne-km
    weekly["cost_per_tonne_km"] = (
        weekly["total_freight_cost_inr"]
        / weekly["total_tonne_km"]
    )

    return weekly


def main():
    shipments = load_shipments()

    weekly = create_weekly_data(shipments)

    print("\n" + "=" * 70)
    print("WEEKLY AGGREGATION")
    print("=" * 70)

    print("\nShape:")
    print(weekly.shape)

    print("\nColumns:")
    print(weekly.columns.tolist())

    print("\nFirst 20 rows:")
    print(
        weekly.head(20).to_string(index=False)
    )

    print("\nWeekly cost statistics:")
    print(
        weekly["cost_per_tonne_km"].describe()
    )

    print("\nNumber of weeks:")
    print(weekly["week_of"].nunique())

    print("\nRows per route:")
    print(
        weekly.groupby("route")
        .size()
        .sort_values(ascending=False)
    )


if __name__ == "__main__":
    main()