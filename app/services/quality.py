from __future__ import annotations

import re
from typing import Any

import pandas as pd

SUPPORTED_RULES = {"not_null", "unique", "range", "regex", "allowed_values", "row_count"}


def evaluate_rules(df: pd.DataFrame, rules: list[dict[str, Any]]) -> dict[str, Any]:
    results = [_evaluate_rule(df, rule, index) for index, rule in enumerate(rules)]
    passed = sum(1 for result in results if result["passed"])
    failed = len(results) - passed
    total_violations = sum(int(result["violation_count"]) for result in results)
    score = round((passed / len(results) * 100), 2) if results else 100.0
    return {"score": score, "passed": passed, "failed": failed, "total_violations": total_violations, "rules": results}


def _evaluate_rule(df: pd.DataFrame, rule: dict[str, Any], index: int) -> dict[str, Any]:
    rule_type = str(rule.get("type", "")).strip()
    name = str(rule.get("name") or f"Rule {index + 1}")
    if rule_type not in SUPPORTED_RULES:
        return _result(name, rule_type, False, len(df), f"Unsupported rule type: {rule_type}")

    if rule_type == "row_count":
        minimum = int(rule.get("min", 0))
        maximum = rule.get("max")
        ok = len(df) >= minimum and (maximum is None or len(df) <= int(maximum))
        return _result(name, rule_type, ok, 0 if ok else 1, f"rows={len(df)}, expected min={minimum}, max={maximum}")

    column = str(rule.get("column", ""))
    if column not in df.columns:
        return _result(name, rule_type, False, len(df), f"Missing column: {column}")
    series = df[column]

    if rule_type == "not_null":
        violations = series.isna()
    elif rule_type == "unique":
        violations = series.notna() & series.duplicated(keep=False)
    elif rule_type == "range":
        numeric = pd.to_numeric(series, errors="coerce")
        violations = numeric.isna()
        if "min" in rule:
            violations |= numeric < float(rule["min"])
        if "max" in rule:
            violations |= numeric > float(rule["max"])
    elif rule_type == "regex":
        pattern = re.compile(str(rule.get("pattern", ".*")))
        violations = series.notna() & ~series.astype(str).map(lambda value: bool(pattern.fullmatch(value)))
    elif rule_type == "allowed_values":
        allowed = set(rule.get("values", []))
        violations = series.notna() & ~series.isin(allowed)
    else:
        raise AssertionError(rule_type)

    indexes = [int(i) if isinstance(i, int) else str(i) for i in df.index[violations].tolist()[:25]]
    count = int(violations.sum())
    result = _result(name, rule_type, count == 0, count, f"{count} violation(s) in '{column}'")
    result["column"] = column
    result["sample_rows"] = indexes
    return result


def _result(name: str, rule_type: str, passed: bool, count: int, detail: str) -> dict[str, Any]:
    return {"name": name, "type": rule_type, "passed": passed, "violation_count": int(count), "detail": detail}
