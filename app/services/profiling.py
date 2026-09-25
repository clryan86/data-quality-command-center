from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    columns: list[dict[str, Any]] = []
    for name in df.columns:
        series = df[name]
        non_null = series.dropna()
        item: dict[str, Any] = {
            "name": str(name),
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_percent": round(float(series.isna().mean() * 100), 2),
            "unique_count": int(non_null.nunique(dropna=True)),
            "duplicate_count": int(non_null.duplicated().sum()),
        }
        if pd.api.types.is_numeric_dtype(series):
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if len(numeric):
                item.update({
                    "min": _safe_number(numeric.min()),
                    "max": _safe_number(numeric.max()),
                    "mean": _safe_number(numeric.mean()),
                    "median": _safe_number(numeric.median()),
                    "std": _safe_number(numeric.std(ddof=0)),
                })
        else:
            values = non_null.astype(str)
            if len(values):
                lengths = values.str.len()
                item.update({
                    "min_length": int(lengths.min()),
                    "max_length": int(lengths.max()),
                    "sample_values": values.head(5).tolist(),
                })
        columns.append(item)

    duplicate_rows = int(df.duplicated().sum())
    completeness = 100.0 if df.size == 0 else (1 - df.isna().sum().sum() / df.size) * 100
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "duplicate_rows": duplicate_rows,
        "completeness_percent": round(float(completeness), 2),
        "columns": columns,
    }


def numeric_anomalies(df: pd.DataFrame, z_threshold: float = 3.0) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    for column in df.select_dtypes(include=[np.number]).columns:
        series = pd.to_numeric(df[column], errors="coerce")
        mean = series.mean()
        std = series.std(ddof=0)
        if pd.isna(std) or std == 0:
            continue
        z = ((series - mean) / std).abs()
        indices = z[z > z_threshold].index.tolist()
        if indices:
            anomalies.append({
                "column": str(column),
                "count": len(indices),
                "row_indices": [int(i) if isinstance(i, (int, np.integer)) else str(i) for i in indices[:25]],
                "threshold": z_threshold,
            })
    return anomalies


def _safe_number(value: Any) -> float | int | None:
    if pd.isna(value):
        return None
    value = value.item() if hasattr(value, "item") else value
    if isinstance(value, float):
        return round(value, 4)
    return int(value) if isinstance(value, np.integer) else value
