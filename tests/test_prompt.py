import json
from src.data.models import BudgetTier, Restaurant
from src.data.preferences import UserPreferences
from src.services.prompt import PromptBuilder


def test_prompt_builder():
    prefs = UserPreferences(
        location="Bangalore",
        budget=BudgetTier.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
        extras=["outdoor seating"],
        top_n=3
    )

    r1 = Restaurant(
        id="123",
        name="Test Trattoria",
        location="Bangalore",
        location_normalized="bangalore",
        cuisines=["Italian"],
        rating=4.5,
        cost_estimate=1000,
        budget_tier=BudgetTier.MEDIUM
    )

    messages = PromptBuilder.build(prefs, [r1], 3)
    
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "You MUST ONLY recommend restaurants from the provided CANDIDATES list." in messages[0]["content"]
    assert "restaurant_id" in messages[0]["content"]
    
    assert messages[1]["role"] == "user"
    assert "Bangalore" in messages[1]["content"]
    assert "Italian" in messages[1]["content"]
    assert "Test Trattoria" in messages[1]["content"]
    assert "outdoor seating" in messages[1]["content"]
