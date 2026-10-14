import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from preprocessing import load_shipments
from weekly_aggregation import create_weekly_data
from anomaly_history import calculate_history_comparison
from similar_routes import calculate_similar_route_comparison
from anomaly_detector import detect_anomalies
from rag_retriever import load_context_notes, explain_anomaly


def clean_text(text: str) -> str:
    """Normalize spacing in source-derived text for final output."""

    replacements = {
        "limitedtruck": "limited truck",
        "reasonfor": "reason for",
        "cost risefor": "cost rise for",
        "flaggedfor": "flagged for",
    }

    text = str(text).strip()

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())


def format_history_pct(value):
    if pd.isna(value):
        return ""
    return f"{value:+.1f}% vs this route's past average"


def format_similar_pct(value):
    if pd.isna(value):
        return ""
    return f"{value:+.1f}% vs similar-length routes this week"


def build_final_output() -> pd.DataFrame:
    # ---------------------------------------------------------
    # 1. Load raw shipment data
    # ---------------------------------------------------------
    shipments = load_shipments()

    # ---------------------------------------------------------
    # 2. Aggregate shipments into route-week level
    # ---------------------------------------------------------
    weekly = create_weekly_data(shipments)

    # ---------------------------------------------------------
    # 3. Compare against trailing 8-week route history
    # ---------------------------------------------------------
    history = calculate_history_comparison(weekly)

    # ---------------------------------------------------------
    # 4. Compare against other routes of same route type
    # ---------------------------------------------------------
    peer_comparison = calculate_similar_route_comparison(history)

    # ---------------------------------------------------------
    # 5. Deterministic anomaly detection
    # ---------------------------------------------------------
    anomalies = detect_anomalies(peer_comparison)

    # ---------------------------------------------------------
    # 6. Load context notes
    # ---------------------------------------------------------
    notes = load_context_notes()

    # ---------------------------------------------------------
    # 7. Build final explanations
    # ---------------------------------------------------------
    final_rows = []

    for _, row in anomalies.iterrows():

        route = row["route"]
        week_of = row["week_of"]

        # Only investigate context when the deterministic
        # detector considers the row anomalous.
        if row["flagged"] == "Yes":

            explanation = explain_anomaly(
                route=route,
                week_of=week_of,
                notes=notes,
            )

            if explanation["justified"]:
                flagged = "No (justified)"
                matched_note_id = explanation["matched_note_id"]

                reason = (
                    f"Matches note {matched_note_id} dated "
                    f"{notes.loc[
                        notes['note_id'] == matched_note_id, 'date'
                    ].iloc[0].date()}: "
                    f"{clean_text(explanation['reason'])}"
                )

            else:
                flagged = "Yes"
                matched_note_id = ""

                if explanation["reason"] == "No relevant context note found.":
                    reason = clean_text(
                        "No matching note found for this route or date range. "
                        "Cost rise looks unexplained and worth a human review."
                    )
                else:
                    reason = clean_text(
                        "The closest context note does not provide a genuine "
                        "reason for the cost rise. No genuine justification "
                        "found; flagged for review."
                    )

        else:
            flagged = "No"
            matched_note_id = ""
            reason = ""

        final_rows.append(
            {
                "route": route,
                "week_of": week_of.strftime("%Y-%m-%d"),
                "cost_per_tonne_km": round(
                    row["cost_per_tonne_km"], 2
                ),
                "vs_own_history": format_history_pct(
                    row["vs_own_history_pct"]
                ),
                "vs_similar_routes": format_similar_pct(
                    row["vs_similar_routes_pct"]
                ),
                "flagged": flagged,
                "matched_note_id": matched_note_id,
                "reason": reason,
            }
        )

    return pd.DataFrame(final_rows)

def write_run_log(
    shipments: pd.DataFrame,
    weekly: pd.DataFrame,
    final_output: pd.DataFrame,
):
    """Write reproducibility and execution metadata."""

    log = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "shipment_rows": int(len(shipments)),
            "weekly_rows": int(len(weekly)),
        },
        "output": {
            "rows": int(len(final_output)),
            "normal": int(
                (final_output["flagged"] == "No").sum()
            ),
            "justified": int(
                (
                    final_output["flagged"]
                    == "No (justified)"
                ).sum()
            ),
            "unexplained": int(
                (
                    final_output["flagged"]
                    == "Yes"
                ).sum()
            ),
        },
        "configuration": {
            "history_window_weeks": 8,
            "anomaly_threshold_pct": 20.0,
        },
    }

    Path("logs").mkdir(exist_ok=True)

    with open(
        "logs/run_log.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            log,
            file,
            indent=2,
        )
def main():
    print("=" * 80)
    print("FREIGHTTIGER SHIPPING COST ANOMALY PIPELINE")
    print("=" * 80)

    # Load input data for run metadata
    shipments = load_shipments()
    weekly = create_weekly_data(shipments)

    # Build final output
    final_output = build_final_output()

    output_path = "output/final_output.csv"

    final_output.to_csv(
        output_path,
        index=False,
    )

    # Write reproducibility / execution log
    write_run_log(
        shipments=shipments,
        weekly=weekly,
        final_output=final_output,
    )

    print()
    print(f"Final output written to: {output_path}")
    print("Run log written to: logs/run_log.json")
    print(f"Rows: {len(final_output)}")
    print()

    print("Flag summary:")
    print(final_output["flagged"].value_counts())
    print()

    print("Flagged / justified cases:")
    print(
        final_output[
            final_output["flagged"] != "No"
        ].to_string(index=False)
    )

    print()
    print("First 10 output rows:")
    print(final_output.head(10).to_string(index=False))


if __name__ == "__main__":
    main()