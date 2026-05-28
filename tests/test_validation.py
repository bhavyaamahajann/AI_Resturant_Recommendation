import pytest
from pydantic import ValidationError

from src.data.models import BudgetTier
from src.data.preferences import UserPreferences


def test_valid_preferences():
    prefs = UserPreferences(
        location="Bangalore",
        budget=BudgetTier.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
        extras=["family-friendly"],
        top_n=5,
    )
    assert prefs.location == "Bangalore"
    assert prefs.top_n == 5


def test_empty_location_rejected():
    with pytest.raises(ValidationError):
        UserPreferences(
            location="  ",
            budget=BudgetTier.LOW,
            cuisine="Italian",
        )


def test_empty_cuisine_rejected():
    with pytest.raises(ValidationError):
        UserPreferences(
            location="Bangalore",
            budget=BudgetTier.LOW,
            cuisine="",
        )


def test_invalid_budget():
    with pytest.raises(ValidationError):
        UserPreferences(
            location="Bangalore",
            budget="expensive",
            cuisine="Italian",
        )


def test_min_rating_out_of_range():
    with pytest.raises(ValidationError) as exc:
        UserPreferences(
            location="Bangalore",
            budget=BudgetTier.LOW,
            cuisine="Italian",
            min_rating=5.5,
        )
    assert "min_rating" in str(exc.value)


def test_top_n_zero_rejected():
    with pytest.raises(ValidationError):
        UserPreferences(
            location="Bangalore",
            budget=BudgetTier.LOW,
            cuisine="Italian",
            top_n=0,
        )


def test_top_n_over_max_rejected():
    with pytest.raises(ValidationError):
        UserPreferences(
            location="Bangalore",
            budget=BudgetTier.LOW,
            cuisine="Italian",
            top_n=21,
        )


def test_extras_truncated():
    prefs = UserPreferences(
        location="Bangalore",
        budget=BudgetTier.LOW,
        cuisine="Italian",
        extras=["x" * 600],
    )
    assert len(prefs.extras[0]) <= 500
