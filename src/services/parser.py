import json
import logging
from typing import Optional

from pydantic import ValidationError

from src.data.llm_models import (
    LLMRecommendationResponse,
    RecommendationResult,
    RecommendationResultItem,
)
from src.data.models import Restaurant
from src.data.preferences import CandidateList, UserPreferences


class LLMParser:
    """Parses LLM responses and handles deterministic fallbacks."""

    @staticmethod
    def parse_and_enrich(
        llm_response_text: str,
        candidates: CandidateList,
        preferences: UserPreferences,
    ) -> RecommendationResult:
        """
        Parses the JSON response from the LLM, validates IDs, and enriches with store data.
        Falls back to a deterministic ranking on failure.
        """
        try:
            raw_json = LLMParser._extract_json(llm_response_text)
            data = json.loads(raw_json)
            parsed_response = LLMRecommendationResponse.model_validate(data)
            return LLMParser._enrich(parsed_response, candidates, preferences)
        except (json.JSONDecodeError, ValidationError) as e:
            logging.warning(f"Failed to parse LLM response: {e}. Using fallback.")
            return LLMParser.deterministic_fallback(candidates, preferences)

    @staticmethod
    def _extract_json(text: str) -> str:
        """Strips markdown fences if present (EC-LLM-11)."""
        text = text.strip()
        start_idx = text.find("```")
        if start_idx != -1:
            nl_idx = text.find("\n", start_idx)
            if nl_idx != -1:
                end_idx = text.find("```", nl_idx)
                if end_idx != -1:
                    return text[nl_idx + 1 : end_idx].strip()
        return text

    @staticmethod
    def _enrich(
        parsed_response: LLMRecommendationResponse,
        candidates: CandidateList,
        preferences: UserPreferences,
    ) -> RecommendationResult:
        """Enriches the raw LLM response with full restaurant details."""
        candidate_dict: dict[str, Restaurant] = {
            r.id: r for r in candidates.restaurants
        }
        name_dict: dict[str, Restaurant] = {
            r.name.lower(): r for r in candidates.restaurants
        }

        enriched_items: list[RecommendationResultItem] = []
        seen_ids: set[str] = set()

        for raw_item in parsed_response.recommendations:
            r_id = raw_item.restaurant_id
            restaurant: Optional[Restaurant] = None

            if r_id in candidate_dict:
                restaurant = candidate_dict[r_id]
            else:
                # Name-only match fallback (EC-LLM-20)
                name_key = r_id.lower()
                if name_key in name_dict:
                    restaurant = name_dict[name_key]
                else:
                    logging.warning(
                        f"Hallucinated or unknown restaurant ID/name: {r_id}"
                    )
                    continue

            # Dedupe (EC-LLM-15)
            if restaurant.id in seen_ids:
                continue
            seen_ids.add(restaurant.id)

            enriched_items.append(
                RecommendationResultItem.from_llm_and_restaurant(raw_item, restaurant)
            )

        # Truncate to top_n (EC-LLM-18)
        enriched_items = enriched_items[: preferences.top_n]

        # Re-number ranks sequentially (EC-LLM-16)
        for i, item in enumerate(enriched_items, 1):
            item.rank = i

        # If empty after filtering hallucinations, fallback
        if not enriched_items:
            logging.warning("All LLM recommendations were invalid. Using fallback.")
            return LLMParser.deterministic_fallback(candidates, preferences)

        return RecommendationResult(
            summary=parsed_response.summary,
            recommendations=enriched_items,
            metadata=candidates.metadata,
        )

    @staticmethod
    def deterministic_fallback(
        candidates: CandidateList,
        preferences: UserPreferences,
    ) -> RecommendationResult:
        """Deterministic ranking fallback if LLM parsing fails entirely (EC-LLM-21)."""
        # Candidates are already sorted by the filter service
        top_matches = candidates.restaurants[: preferences.top_n]
        items: list[RecommendationResultItem] = []
        
        for i, r in enumerate(top_matches, 1):
            rating_str = f"{r.rating:.1f}" if r.rating is not None else "N/A"
            cuisine_str = ", ".join(preferences.cuisines)
            explanation = f"Matches your {cuisine_str} preference(s) in {preferences.location} with rating {rating_str}."
            items.append(
                RecommendationResultItem(
                    rank=i,
                    restaurant_id=r.id,
                    name=r.name,
                    cuisine=r.primary_cuisine,
                    rating=r.rating,
                    estimated_cost=r.cost_estimate,
                    explanation=explanation,
                )
            )

        metadata = candidates.metadata
        metadata.warnings.append("AI generation failed; displaying top-rated matches.")
        
        # Adding a custom attribute to track fallback for testing/UI
        if not hasattr(metadata, "llm_fallback"):
            # Since CandidateMetadata doesn't have llm_fallback explicitly as per models,
            # We can rely on warnings or add it to extra dict if needed.
            pass

        cuisine_str = ", ".join(preferences.cuisines)
        return RecommendationResult(
            summary=f"Top picks in {preferences.location} for {cuisine_str}.",
            recommendations=items,
            metadata=metadata,
        )
