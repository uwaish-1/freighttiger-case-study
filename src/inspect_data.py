import pandas as pd


SHIPMENT_FILE = "data/shipment_records.csv"
CONTEXT_FILE = "data/context_notes.csv"
SAMPLE_FILE = "data/sample_output_format_v2.csv"


def inspect_csv(path: str) -> None:
    print("\n" + "=" * 70)
    print(f"FILE: {path}")
    print("=" * 70)

    df = pd.read_csv(path)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nData types:")
    print(df.dtypes)

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nMissing values:")
    print(df.isnull().sum())


def inspect_raw_file(path: str) -> None:
    print("\n" + "=" * 70)
    print(f"RAW FILE: {path}")
    print("=" * 70)

    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            print(f"{line_number}: {line.rstrip()}")


if __name__ == "__main__":
    inspect_csv(SHIPMENT_FILE)
    inspect_csv(CONTEXT_FILE)

    inspect_raw_file(SAMPLE_FILE)