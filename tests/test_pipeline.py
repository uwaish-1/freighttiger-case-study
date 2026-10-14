import pandas as pd

from preprocessing import load_shipments
from weekly_aggregation import create_weekly_data
from anomaly_history import calculate_history_comparison
from similar_routes import calculate_similar_route_comparison
from anomaly_detector import detect_anomalies
from rag_retriever import (
    load_context_notes,
    retrieve_candidate_notes,
    validate_justification,
)
from main import build_final_output


def build_pipeline_data():
    """Build the deterministic pipeline used by multiple tests."""

    shipments = load_shipments()
    weekly = create_weekly_data(shipments)
    history = calculate_history_comparison(weekly)
    peer = calculate_similar_route_comparison(history)
    anomalies = detect_anomalies(peer)

    return shipments, weekly, history, peer, anomalies


def test_shipment_data_loads():
    shipments = load_shipments()

    assert len(shipments) == 2940

    required_columns = {
        "route",
        "route_type",
        "cost_per_tonne_km",
        "week_of",
    }

    assert required_columns.issubset(shipments.columns)


def test_weekly_aggregation():
    shipments = load_shipments()
    weekly = create_weekly_data(shipments)

    assert len(weekly) == 728

    required_columns = {
        "route",
        "route_type",
        "week_of",
        "total_freight_cost_inr",
        "total_tonne_km",
        "shipment_count",
        "cost_per_tonne_km",
    }

    assert required_columns.issubset(weekly.columns)


def test_history_excludes_current_week():
    shipments = load_shipments()
    weekly = create_weekly_data(shipments)
    history = calculate_history_comparison(weekly)

    route_data = (
        history[
            history["route"] == "Ahmedabad-Mumbai"
        ]
        .sort_values("week_of")
        .reset_index(drop=True)
    )

    # First week has no previous history.
    assert pd.isna(route_data.loc[0, "history_avg"])

    # Second week should compare against the first week only.
    expected = route_data.loc[0, "cost_per_tonne_km"]

    assert abs(
        route_data.loc[1, "history_avg"] - expected
    ) < 1e-9


def test_similar_route_comparison_excludes_current_route():
    shipments = load_shipments()
    weekly = create_weekly_data(shipments)
    history = calculate_history_comparison(weekly)
    peer = calculate_similar_route_comparison(history)

    row = peer[
        (peer["route"] == "Ahmedabad-Mumbai")
        & (peer["week_of"] == pd.Timestamp("2024-01-01"))
    ].iloc[0]

    # Ahmedabad-Mumbai is Medium.
    medium_routes = peer[
        (peer["week_of"] == pd.Timestamp("2024-01-01"))
        & (peer["route_type"] == "Medium")
        & (peer["route"] != "Ahmedabad-Mumbai")
    ]

    expected = medium_routes["cost_per_tonne_km"].mean()

    assert abs(
        row["similar_routes_avg"] - expected
    ) < 1e-9


def test_n002_is_valid_justification():
    notes = load_context_notes()

    candidates = retrieve_candidate_notes(
        route="Ahmedabad-Mumbai",
        week_of=pd.Timestamp("2025-01-20"),
        notes=notes,
    )

    result = validate_justification(
        route="Ahmedabad-Mumbai",
        week_of=pd.Timestamp("2025-01-20"),
        candidates=candidates,
    )

    assert result["justified"] is True
    assert result["matched_note_id"] == "N002"


def test_n006_is_not_a_justification():
    notes = load_context_notes()

    candidates = retrieve_candidate_notes(
        route="Mumbai-Pune",
        week_of=pd.Timestamp("2025-09-15"),
        notes=notes,
    )

    result = validate_justification(
        route="Mumbai-Pune",
        week_of=pd.Timestamp("2025-09-15"),
        candidates=candidates,
    )

    assert result["justified"] is False
    assert result["matched_note_id"] == ""


def test_n001_event_window():
    notes = load_context_notes()

    # Inside the flooding period.
    candidates = retrieve_candidate_notes(
        route="Chennai-Bangalore",
        week_of=pd.Timestamp("2025-03-03"),
        notes=notes,
    )

    result = validate_justification(
        route="Chennai-Bangalore",
        week_of=pd.Timestamp("2025-03-03"),
        candidates=candidates,
    )

    assert result["justified"] is True
    assert result["matched_note_id"] == "N001"

    # After the flooding period.
    candidates = retrieve_candidate_notes(
        route="Chennai-Bangalore",
        week_of=pd.Timestamp("2025-03-17"),
        notes=notes,
    )

    result = validate_justification(
        route="Chennai-Bangalore",
        week_of=pd.Timestamp("2025-03-17"),
        candidates=candidates,
    )

    assert result["justified"] is False


def test_sample_anomaly_cases():
    _, _, _, _, anomalies = build_pipeline_data()

    cases = [
        (
            "Delhi-Jaipur",
            "2024-11-11",
            "Yes",
        ),
        (
            "Ahmedabad-Mumbai",
            "2025-01-20",
            "Yes",
        ),
        (
            "Mumbai-Pune",
            "2025-09-15",
            "Yes",
        ),
    ]

    for route, week, expected_flag in cases:

        row = anomalies[
            (anomalies["route"] == route)
            & (
                anomalies["week_of"]
                == pd.Timestamp(week)
            )
        ].iloc[0]

        assert row["flagged"] == expected_flag


def test_final_output_schema():
    output = build_final_output()

    expected_columns = [
        "route",
        "week_of",
        "cost_per_tonne_km",
        "vs_own_history",
        "vs_similar_routes",
        "flagged",
        "matched_note_id",
        "reason",
    ]

    assert list(output.columns) == expected_columns
    assert len(output) == 728


def test_final_output_sample_cases():
    output = build_final_output()

    ahmedabad = output[
        (output["route"] == "Ahmedabad-Mumbai")
        & (output["week_of"] == "2025-01-20")
    ].iloc[0]

    assert ahmedabad["flagged"] == "No (justified)"
    assert ahmedabad["matched_note_id"] == "N002"

    delhi = output[
        (output["route"] == "Delhi-Jaipur")
        & (output["week_of"] == "2024-11-11")
    ].iloc[0]

    assert delhi["flagged"] == "Yes"
    assert delhi["matched_note_id"] == ""

    mumbai = output[
        (output["route"] == "Mumbai-Pune")
        & (output["week_of"] == "2025-09-15")
    ].iloc[0]

    assert mumbai["flagged"] == "Yes"
    assert mumbai["matched_note_id"] == ""