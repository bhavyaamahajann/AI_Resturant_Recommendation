from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.data.models import Restaurant
from src.data.preferences import CandidateMetadata


class LLMRecommendationItem(BaseModel):
    """Raw parsed item returned by the LLM."""
    restaurant_id: str
    rank: int
    explanation: str


class LLMRecommendationResponse(BaseModel):
    """Raw parsed response from the LLM."""
    summary: Optional[str] = None
    recommendations: list[LLMRecommendationItem] = Field(default_factory=list)


class RecommendationResultItem(BaseModel):
    """Enriched recommendation item combining LLM output with store data."""
    rank: int
    restaurant_id: str
    name: str
    cuisine: str
    rating: float
    estimated_cost: Optional[float] = None
    explanation: str

    @classmethod
    def from_llm_and_restaurant(
        cls, llm_item: LLMRecommendationItem, restaurant: Restaurant
    ) -> RecommendationResultItem:
        return cls(
            rank=llm_item.rank,
            restaurant_id=restaurant.id,
            name=restaurant.name,
            cuisine=restaurant.primary_cuisine,
            rating=restaurant.rating,
            estimated_cost=restaurant.cost_estimate,
            explanation=llm_item.explanation,
        )


class RecommendationResult(BaseModel):
    """Final output containing enriched recommendations and metadata."""
    summary: Optional[str] = None
    recommendations: list[RecommendationResultItem] = Field(default_factory=list)
    metadata: CandidateMetadata
