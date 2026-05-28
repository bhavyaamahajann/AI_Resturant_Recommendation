import json
import time
from pathlib import Path

import pytest

from config.settings import get_settings
from src.data.models import BudgetTier
from src.data.preferences import UserPreferences
from src.data.store import RestaurantStore
from src.services.filter import CandidateFilterService, NoCandidatesError, _matches_cuisines
from src.data.models import Restaurant

def _matches_cuisine(restaurant: Restaurant, cuisine: str) -> bool:
    return _matches_cuisines(restaurant, [cuisine])

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "restaurants_small.parquet"


@pytest.fixture
def filter_service(small_store: RestaurantStore) -> CandidateFilterService:
    return CandidateFilterService(small_store, settings=get_settings())


class TestMatchesCuisine:
    def test_exact_match(self):
        r = Restaurant(
            id="1",
            name="X",
            location="A",
            location_normalized="Bangalore",
            cuisines=["Italian"],
            rating=4.0,
            budget_tier=BudgetTier.MEDIUM,
        )
        assert _matches_cuisine(r, "Italian") is True

    def test_no_substring_false_positive(self):
        r = Restaurant(
            id="1",
            name="X",
            location="A",
            location_normalized="Bangalore",
            cuisines=["North Indian"],
            rating=4.0,
            budget_tier=BudgetTier.MEDIUM,
        )
        assert _matches_cuisine(r, "Thai") is False
        assert _matches_cuisine(r, "ai") is False


class TestCandidateFilter:
    def test_strict_match_bangalore_italian(self, filter_service):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetTier.MEDIUM,
            cuisine="Italian",
        )
        result = filter_service.get_candidates(prefs)
        assert 1 <= len(result.restaurants) <= 30
        assert all(_matches_cuisine(r, "Italian") for r in result.restaurants)
        assert result.metadata.filters_relaxed == []

    def test_relax_cuisine_when_no_match(self, filter_service):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetTier.LOW,
            cuisine="Mexican",
        )
        result = filter_service.get_candidates(prefs)
        assert len(result.restaurants) > 0
        assert "cuisine" in result.metadata.filters_relaxed

    def test_relax_budget_when_needed(self, filter_service):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetTier.HIGH,
            cuisine="Chinese",
            min_rating=3.0,
        )
        result = filter_service.get_candidates(prefs)
        assert len(result.restaurants) >= 1

    def test_no_candidates_unknown_location(self, filter_service):
        prefs = UserPreferences(
            location="Atlantis",
            budget=BudgetTier.LOW,
            cuisine="Italian",
        )
        with pytest.raises(NoCandidatesError) as exc:
            filter_service.get_candidates(prefs)
        assert exc.value.suggestions

    def test_few_matches_warning(self, filter_service):
        prefs = UserPreferences(
            location="Delhi",
            budget=BudgetTier.LOW,
            cuisine="North Indian",
            min_rating=4.0,
        )
        result = filter_service.get_candidates(prefs)
        assert len(result.restaurants) < 3
        assert any("Only" in w for w in result.metadata.warnings)

    def test_min_rating_strict(self, filter_service):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetTier.MEDIUM,
            cuisine="Italian",
            min_rating=4.9,
        )
        result = filter_service.get_candidates(prefs)
        assert len(result.restaurants) >= 1
        assert all(r.rating >= 4.9 for r in result.restaurants)

    def test_sort_by_rating_desc(self, filter_service):
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetTier.MEDIUM,
            cuisine="Italian",
        )
        result = filter_service.get_candidates(prefs)
        ratings = [r.rating for r in result.restaurants]
        assert ratings == sorted(ratings, reverse=True)

    def test_cap_at_candidate_limit(self, small_store):
        many = []
        for i in range(40):
            many.append(
                Restaurant(
                    id=f"bulk{i}",
                    name=f"R{i}",
                    location="BulkArea",
                    location_normalized="Bangalore",
                    cuisines=["Italian"],
                    rating=4.0 + (i % 10) * 0.01,
                    cost_estimate=500.0,
                    budget_tier=BudgetTier.MEDIUM,
                )
            )
        store = RestaurantStore(small_store.get_all() + many)
        service = CandidateFilterService(store, settings=get_settings())
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetTier.MEDIUM,
            cuisine="Italian",
        )
        result = service.get_candidates(prefs)
        assert len(result.restaurants) == get_settings().candidate_limit
        assert result.metadata.total_matches_before_cap > get_settings().candidate_limit


class TestFilterPerformance:
    @pytest.mark.skipif(
        not Path(get_settings().data_path).exists(),
        reason="Full parquet not ingested",
    )
    def test_filter_under_100ms(self):
        store = RestaurantStore.from_parquet()
        service = CandidateFilterService(store)
        prefs = UserPreferences(
            location="Bangalore",
            budget=BudgetTier.MEDIUM,
            cuisine="Italian",
            min_rating=4.0,
        )
        start = time.perf_counter()
        service.get_candidates(prefs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 100, f"Filter took {elapsed_ms:.1f}ms"
