import json
from typing import Any

from src.data.models import Restaurant
from src.data.preferences import UserPreferences


class PromptBuilder:
    """Builds prompts for the LLM recommendation engine."""

    SCHEMA_INSTRUCTION = """
You must respond with valid JSON matching exactly this schema:
{
  "summary": "string (optional overview of the recommendations)",
  "recommendations": [
    {
      "restaurant_id": "string (MUST exactly match an ID from the CANDIDATES list)",
      "rank": "integer (1 to top_n)",
      "explanation": "string (why this matches the user's preferences, citing cuisine, rating, or cost)"
    }
  ]
}
"""

    SYSTEM_PROMPT = f"""You are a restaurant recommendation assistant.
Your job is to recommend the best restaurants based on the user's preferences.
You MUST ONLY recommend restaurants from the provided CANDIDATES list.
Do not invent or hallucinate any restaurants.
Rank the results by fit to the user's preferences, paying special attention to any "extras" mentioned.
{SCHEMA_INSTRUCTION}"""

    @staticmethod
    def build(
        preferences: UserPreferences,
        candidates: list[Restaurant],
        top_n: int,
    ) -> list[dict[str, str]]:
        """
        Builds the messages array for the chat completion API.
        """
        # Create a simplified candidate list to save tokens
        candidate_json: list[dict[str, Any]] = []
        for c in candidates:
            candidate_json.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "cuisine": c.primary_cuisine,
                    "rating": c.rating,
                    "cost": c.cost_estimate,
                }
            )

        # Build preferences dict, ignoring None/empty values
        prefs_json: dict[str, Any] = {
            "location": preferences.location,
            "cuisines": preferences.cuisines,
        }
        if preferences.budget_amount is not None:
            prefs_json["budget_amount"] = preferences.budget_amount
        elif preferences.budget is not None:
            prefs_json["budget_tier"] = preferences.budget.value
        if preferences.min_rating is not None:
            prefs_json["min_rating"] = preferences.min_rating
        if preferences.extras:
            prefs_json["extras"] = preferences.extras

        user_content = f"""
PREFERENCES:
{json.dumps(prefs_json, indent=2)}

CANDIDATES:
{json.dumps(candidate_json, indent=2)}

INSTRUCTIONS:
Return the top {top_n} restaurants from the CANDIDATES list that best match the PREFERENCES.
"""

        return [
            {"role": "system", "content": PromptBuilder.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
