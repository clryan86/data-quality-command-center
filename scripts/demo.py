from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.io import read_dataset
from app.services.profiling import numeric_anomalies, profile_dataframe
from app.services.quality import evaluate_rules

root = ROOT
data_path = root / "sample_data" / "customers.csv"
rules_path = root / "sample_data" / "customer_rules.json"
df = read_dataset(data_path.name, data_path.read_bytes())
print(json.dumps({
    "profile": profile_dataframe(df),
    "anomalies": numeric_anomalies(df),
    "quality": evaluate_rules(df, json.loads(rules_path.read_text())),
}, indent=2, default=str))
