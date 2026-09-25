from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

SUPPORTED = {".csv", ".json", ".jsonl"}


def read_dataset(filename: str, payload: bytes) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError("Supported file types: .csv, .json, .jsonl")
    if suffix == ".csv":
        return pd.read_csv(io.BytesIO(payload))
    if suffix == ".jsonl":
        return pd.read_json(io.BytesIO(payload), lines=True)
    return pd.read_json(io.BytesIO(payload))
