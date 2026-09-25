from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RuleSetCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    rules: list[dict[str, Any]] = Field(min_length=1)


class QualityRunRequest(BaseModel):
    dataset_id: int
    rule_set_id: int


class RuleSetResponse(BaseModel):
    id: int
    name: str
    rules: list[dict[str, Any]]
    created_at: str


class QualityRunResponse(BaseModel):
    id: int
    dataset_id: int
    dataset_name: str
    rule_set_id: int
    rule_set_name: str
    score: float
    passed: int
    failed: int
    total_violations: int
    result: dict[str, Any]
    created_at: str
