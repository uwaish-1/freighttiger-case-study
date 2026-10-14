# FreightTiger Shipping Cost Anomaly Detection

A Python-based pipeline to identify unusual weekly shipping costs and check whether the detected cost increase can be explained using operational context notes.

## 1. Approach

The pipeline follows these steps:

1. Load shipment records from `shipment_records.csv`.
2. Calculate shipping cost per tonne-km.
3. Aggregate shipments by route and week.
4. Compare each week's cost with:
   - The route's previous 8-week average.
   - Other routes of the same `route_type` during the same week.
5. Flag unusual cost increases.
6. Search `context_notes.csv` for a relevant explanation.
7. Mark an anomaly as `No (justified)` only when a supporting context note is found.
8. Generate the final result in `output/final_output.csv`.

## 2. Cost Calculation

The cost per tonne-km is calculated as:

```text
freight_cost_inr / (quantity_tonnes × distance_km)
```

Weekly cost is calculated using the total freight cost divided by the total tonne-km for that route and week.

## 3. Anomaly Detection

A weekly record is considered anomalous when its cost is at least **20% higher** than either:

- Its own historical average, or
- The average of similar routes in the same week.

The historical comparison uses the previous 8 weeks and excludes the current week.

For the first few weeks, when fewer than 8 previous weeks are available, all available previous weeks are used.

The case study does not explicitly provide a numerical anomaly threshold, so the **20% threshold is an implementation choice based on the supplied sample output**.

For the "similar routes" comparison, `route_type` is used as the available proxy for similar-length routes.

## 4. Context / RAG Layer

Context notes are used only after a deterministic anomaly has been detected.

The system searches for notes based on:

- Route
- Date/week
- Route-wide context

A note is used as a justification only when it provides a genuine reason for the cost increase.

The system does not create explanations when there is no supporting note.

For example:

- `N002` explains the Ahmedabad-Mumbai cost increase because of a temporary festival-related surcharge.
- `N001` explains the Chennai-Bangalore increase during the flooding period.
- Notes describing stable conditions or no significant disruption are not treated as justifications.

## 5. Output

The final output contains:

| Column | Description |
|---|---|
| `route` | Shipping route |
| `week_of` | Monday-starting week |
| `cost_per_tonne_km` | Weekly shipping cost per tonne-km |
| `vs_own_history` | Difference from the route's historical average |
| `vs_similar_routes` | Difference from similar routes |
| `flagged` | `Yes`, `No`, or `No (justified)` |
| `matched_note_id` | Supporting context note, if available |
| `reason` | Explanation for the result |

## 6. Current Results

The pipeline produces **728 weekly route records**.

Current result:

```text
Normal             708
Unexplained         17
Justified            3
Total              728
```

The three justified anomalies are supported by context notes:

- Ahmedabad-Mumbai — N002
- Chennai-Bangalore — N001
- Chennai-Bangalore — N001

## 7. Project Structure

```text
case-study/
│
├── data/
│   ├── shipment_records.csv
│   ├── context_notes.csv
│   └── sample_output_format_v2.csv
│
├── src/
│   ├── preprocessing.py
│   ├── weekly_aggregation.py
│   ├── anomaly_history.py
│   ├── similar_routes.py
│   ├── anomaly_detector.py
│   ├── rag_retriever.py
│   └── main.py
│
├── tests/
│   └── test_pipeline.py
│
├── output/
│   └── final_output.csv
│
├── logs/
│   └── run_log.json
│
├── README.md
├── requirements.txt
└── pyproject.toml
```

## 8. How to Run

Create and activate the virtual environment:

```powershell
uv venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
uv sync
```

Run the pipeline:

```powershell
python src/main.py
```

Run the tests:

```powershell
pytest -q
```

## 9. Testing

The project includes automated tests covering:

- Input data loading
- Weekly aggregation
- Historical comparison
- Similar-route comparison
- Context-note justification
- Anomaly detection
- Final output format

Current test result:

```text
10 passed
```

## 10. Reproducibility

Each pipeline run generates:

```text
logs/run_log.json
```

The log records the input size, output size, result summary, history window, and anomaly threshold.

The pipeline produces the same output when run repeatedly on the same input data.