from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class BudgetTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Restaurant(BaseModel):
    id: str
    name: str
    location: str
    location_normalized: str
    cuisines: list[str] = Field(default_factory=list)
    rating: float
    cost_estimate: Optional[float] = None
    budget_tier: BudgetTier
    raw_attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator("cuisines", mode="before")
    @classmethod
    def ensure_cuisines_list(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [str(v)]

    @property
    def primary_cuisine(self) -> str:
        return self.cuisines[0] if self.cuisines else ""
