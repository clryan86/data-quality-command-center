from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def client(tmp_path: Path) -> TestClient:
    settings = Settings(database_path=tmp_path / "quality.db", upload_dir=tmp_path / "uploads")
    return TestClient(create_app(settings))


def test_end_to_end_quality_flow(tmp_path):
    c = client(tmp_path)
    csv = b"id,email,age,status\n1,a@example.com,30,active\n2,bad,200,active\n2,c@example.com,25,bad\n"
    uploaded = c.post("/api/datasets?name=Customer%20Feed", files={"file": ("customers.csv", csv, "text/csv")})
    assert uploaded.status_code == 201
    dataset_id = uploaded.json()["id"]
    assert uploaded.json()["profile"]["row_count"] == 3

    rules = c.post("/api/rule-sets", json={"name": "Customer Contract", "rules": [
        {"name": "ID unique", "type": "unique", "column": "id"},
        {"name": "Email valid", "type": "regex", "column": "email", "pattern": "[^@]+@[^@]+\\.[^@]+"},
        {"name": "Age valid", "type": "range", "column": "age", "min": 0, "max": 120},
        {"name": "Status valid", "type": "allowed_values", "column": "status", "values": ["active", "inactive"]},
    ]})
    assert rules.status_code == 201
    rule_set_id = rules.json()["id"]

    run = c.post("/api/quality-runs", json={"dataset_id": dataset_id, "rule_set_id": rule_set_id})
    assert run.status_code == 201
    body = run.json()
    assert body["failed"] == 4
    assert body["total_violations"] >= 5

    metrics = c.get("/api/metrics").json()
    assert metrics["datasets"] == 1
    assert metrics["rule_sets"] == 1
    assert metrics["quality_runs"] == 1


def test_rejects_unsupported_file(tmp_path):
    c = client(tmp_path)
    response = c.post("/api/datasets", files={"file": ("data.exe", b"nope", "application/octet-stream")})
    assert response.status_code == 422
