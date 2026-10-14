import pandas as pd


SHIPMENT_FILE = "data/shipment_records.csv"
CONTEXT_FILE = "data/context_notes.csv"


def main():
    shipments = pd.read_csv(SHIPMENT_FILE)
    notes = pd.read_csv(CONTEXT_FILE)

    # ---------------------------------------------------------
    # 1. Shipment date range
    # ---------------------------------------------------------

    shipments["shipment_date"] = pd.to_datetime(shipments["shipment_date"])

    print("\n" + "=" * 70)
    print("SHIPMENT DATE RANGE")
    print("=" * 70)

    print("Minimum date:", shipments["shipment_date"].min())
    print("Maximum date:", shipments["shipment_date"].max())

    # ---------------------------------------------------------
    # 2. Unique routes
    # ---------------------------------------------------------

    shipments["route"] = (
        shipments["origin"] + "-" + shipments["destination"]
    )

    print("\n" + "=" * 70)
    print("ROUTES")
    print("=" * 70)

    print("Number of unique routes:", shipments["route"].nunique())

    print("\nRoutes:")
    for route in sorted(shipments["route"].unique()):
        print(" -", route)

    # ---------------------------------------------------------
    # 3. Route types
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("ROUTE TYPES")
    print("=" * 70)

    print("Number of route types:", shipments["route_type"].nunique())

    print("\nRoute types:")
    for route_type in sorted(shipments["route_type"].unique()):
        print(" -", route_type)

    # ---------------------------------------------------------
    # 4. Records per route
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SHIPMENTS PER ROUTE")
    print("=" * 70)

    route_counts = (
        shipments
        .groupby("route")
        .size()
        .sort_values(ascending=False)
    )

    print(route_counts)

    # ---------------------------------------------------------
    # 5. Full context notes
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("CONTEXT NOTES")
    print("=" * 70)

    for _, row in notes.iterrows():
        print(f"\nNote ID      : {row['note_id']}")
        print(f"Date         : {row['date']}")
        print(f"Applies to   : {row['applies_to']}")
        print(f"Note         : {row['note']}")

    # ---------------------------------------------------------
    # 6. Route types by route
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("ROUTE → ROUTE TYPE")
    print("=" * 70)

    route_mapping = (
        shipments[
            ["route", "route_type"]
        ]
        .drop_duplicates()
        .sort_values("route")
    )

    print(route_mapping.to_string(index=False))


if __name__ == "__main__":
    main()