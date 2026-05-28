"""User preference and candidate list models (Phase 2)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from config.settings import get_settings
from src.data.models import BudgetTier, Restaurant


class UserPreferences(BaseModel):
    location: str = Field(..., min_length=1)
    # Backward compatible: older clients send a tier ("low"/"medium"/"high")
    # New UI (Phase 6A) sends a numeric budget amount (approx cost for two).
    budget: Optional[BudgetTier] = None
    budget_amount: Optional[float] = Field(default=None, ge=100, le=10000)
    cuisines: list[str] = Field(..., min_length=1)
    min_rating: Optional[float] = None
    extras: list[str] = Field(default_factory=list)
    top_n: int = 5

    @model_validator(mode="before")
    @classmethod
    def map_cuisine_to_cuisines(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "cuisine" in data and "cuisines" not in data:
                c_val = data["cuisine"]
                if isinstance(c_val, str):
                    data["cuisines"] = [c.strip() for c in c_val.split(",") if c.strip()]
                elif isinstance(c_val, list):
                    data["cuisines"] = c_val
        return data

    @field_validator("location", mode="before")
    @classmethod
    def strip_required_strings(cls, v: object) -> str:
        if v is None:
            raise ValueError("field is required")
        s = str(v).strip()
        if not s:
            raise ValueError("field cannot be empty")
        return s

    @field_validator("min_rating")
    @classmethod
    def validate_min_rating(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if not 0 <= v <= 5:
            raise ValueError("min_rating must be between 0 and 5")
        return v

    @field_validator("top_n")
    @classmethod
    def validate_top_n(cls, v: int) -> int:
        if v < 1:
            raise ValueError("top_n must be at least 1")
        if v > 20:
            raise ValueError("top_n cannot exceed 20")
        return v

    @field_validator("budget_amount")
    @classmethod
    def coerce_budget_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        return float(v)

    @field_validator("budget", mode="before")
    @classmethod
    def allow_empty_budget_tier(cls, v: object) -> object:
        # Allow null/"" for new UI; numeric budget will be used instead.
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("cuisines", mode="before")
    @classmethod
    def normalize_cuisines(cls, v: object) -> list[str]:
        if v is None:
            raise ValueError("cuisines is required")
        if isinstance(v, str):
            items = [v]
        else:
            items = list(v)
        max_len = get_settings().max_field_length
        normalized = [str(item).strip()[:max_len] for item in items if str(item).strip()]
        if not normalized:
            raise ValueError("at least one cuisine is required")
        return normalized

    @field_validator("location", mode="before")
    @classmethod
    def strip_location(cls, v: object) -> str:
        return cls.strip_required_strings(v)

    @field_validator("budget_amount", "budget")
    @classmethod
    def budget_presence_check(cls, v, info):
        # No-op: cross-field validation is handled below in model validator style.
        return v

    @field_validator("top_n")
    @classmethod
    def ensure_budget_present(cls, v: int, info):  # type: ignore[override]
        return v

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):  # type: ignore[override]
        inst = super().model_validate(obj, *args, **kwargs)
        if inst.budget is None and inst.budget_amount is None:
            raise ValueError("Either budget (tier) or budget_amount must be provided")
        return inst

    @field_validator("extras", mode="before")
    @classmethod
    def normalize_extras(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            items = [v]
        else:
            items = list(v)
        max_len = get_settings().max_field_length
        return [str(item).strip()[:max_len] for item in items if str(item).strip()]


class CandidateMetadata(BaseModel):
    total_matches_before_cap: int = 0
    candidates_returned: int = 0
    filters_relaxed: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class CandidateList(BaseModel):
    preferences: UserPreferences
    restaurants: list[Restaurant]
    metadata: CandidateMetadata
