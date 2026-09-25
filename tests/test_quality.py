import pandas as pd

from app.services.profiling import numeric_anomalies, profile_dataframe
from app.services.quality import evaluate_rules


def test_profile_dataframe_reports_shape_and_nulls():
    df = pd.DataFrame({"id": [1, 2, 3], "email": ["a@x.com", None, "c@x.com"]})
    profile = profile_dataframe(df)
    assert profile["row_count"] == 3
    assert profile["column_count"] == 2
    email = next(c for c in profile["columns"] if c["name"] == "email")
    assert email["null_count"] == 1
    assert email["null_percent"] == 33.33


def test_rule_engine_detects_multiple_rule_types():
    df = pd.DataFrame({
        "id": [1, 1, 3],
        "age": [20, 200, 30],
        "email": ["a@example.com", "broken", None],
        "status": ["active", "active", "bad"],
    })
    rules = [
        {"name": "IDs unique", "type": "unique", "column": "id"},
        {"name": "Age range", "type": "range", "column": "age", "min": 0, "max": 120},
        {"name": "Email format", "type": "regex", "column": "email", "pattern": "[^@]+@[^@]+\\.[^@]+"},
        {"name": "Known status", "type": "allowed_values", "column": "status", "values": ["active", "inactive"]},
    ]
    result = evaluate_rules(df, rules)
    assert result["failed"] == 4
    assert result["total_violations"] >= 5
    assert result["score"] == 0.0


def test_numeric_anomaly_finds_extreme_value():
    df = pd.DataFrame({"amount": [10] * 30 + [10000]})
    anomalies = numeric_anomalies(df, z_threshold=3.0)
    assert anomalies[0]["column"] == "amount"
    assert anomalies[0]["count"] == 1
