import pandas as pd


SHIPMENT_FILE = "data/shipment_records.csv"


def load_shipments(path: str = SHIPMENT_FILE) -> pd.DataFrame:
    """
    Load and validate the shipment dataset.
    """

    df = pd.read_csv(path)

    # Convert shipment date to datetime
    df["shipment_date"] = pd.to_datetime(
        df["shipment_date"],
        errors="raise"
    )

    # Create route identifier
    df["route"] = (
        df["origin"]
        + "-"
        + df["destination"]
    )

    # Calculate cost per tonne-km
    df["cost_per_tonne_km"] = (
        df["freight_cost_inr"]
        / (
            df["quantity_tonnes"]
            * df["distance_km"]
        )
    )

    # Calculate Monday-starting week
    df["week_of"] = (
        df["shipment_date"]
        - pd.to_timedelta(
            df["shipment_date"].dt.weekday,
            unit="D"
        )
    )

    return df


def main():
    df = load_shipments()

    print("\n" + "=" * 70)
    print("PREPROCESSED DATA")
    print("=" * 70)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nSample:")
    print(
        df[
            [
                "shipment_id",
                "route",
                "route_type",
                "quantity_tonnes",
                "distance_km",
                "freight_cost_inr",
                "shipment_date",
                "week_of",
                "cost_per_tonne_km",
            ]
        ].head(10).to_string(index=False)
    )

    print("\nCost per tonne-km statistics:")
    print(df["cost_per_tonne_km"].describe())

    print("\nWeek range:")
    print(
        df["week_of"].min(),
        "to",
        df["week_of"].max()
    )


if __name__ == "__main__":
    main()