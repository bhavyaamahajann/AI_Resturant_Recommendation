"""Candidate filter service with relaxation policy (FR-4, Phase 2)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from config.settings import Settings, get_settings
from src.data.models import BudgetTier, Restaurant
from src.data.preferences import CandidateList, CandidateMetadata, UserPreferences
from src.data.store import RestaurantStore

# Target cost midpoints for sort tie-break (EC-FILTER-13)
_BUDGET_COST_MIDPOINTS: dict[BudgetTier, float] = {
    BudgetTier.LOW: 200.0,
    BudgetTier.MEDIUM: 500.0,
    BudgetTier.HIGH: 1000.0,
}

_MIN_LOCATION_FUZZY_LEN = 4


class NoCandidatesError(Exception):
    """Raised when no restaurants match even after relaxation (EC-FILTER-04)."""

    def __init__(self, message: str, suggestions: list[str] | None = None) -> None:
        super().__init__(message)
        self.suggestions = suggestions or []


@dataclass
class _FilterFlags:
    apply_cuisine: bool = True
    apply_budget: bool = True
    apply_min_rating: bool = True
    min_rating_override: Optional[float] = None


class CandidateFilterService:
    def __init__(
        self,
        store: RestaurantStore,
        settings: Settings | None = None,
    ) -> None:
        self._store = store
        self._settings = settings or get_settings()

    def get_candidates(self, preferences: UserPreferences) -> CandidateList:
        """
        Filter restaurants by preferences with relaxation (EC-FILTER-01–04).

        Order: location → cuisine → min_rating → budget → sort → cap.
        """
        relaxed: list[str] = []
        warnings: list[str] = []

        pool = self._filter_by_location(preferences.location)
        if not pool:
            raise NoCandidatesError(
                f"No restaurants found for location '{preferences.location}'.",
                suggestions=self._location_suggestions(),
            )

        flags = _FilterFlags()
        matched = self._apply_filters(pool, preferences, flags)
        total_before_cap = len(matched)

        if not matched:
            flags.apply_cuisine = False
            relaxed.append("cuisine")
            matched = self._apply_filters(pool, preferences, flags)
            total_before_cap = len(matched)

        if not matched:
            flags.apply_budget = False
            relaxed.append("budget")
            matched = self._apply_filters(pool, preferences, flags)
            total_before_cap = len(matched)

        if not matched and preferences.min_rating is not None:
            reduced = max(0.0, preferences.min_rating - 0.5)
            flags.min_rating_override = reduced
            relaxed.append("min_rating")
            matched = self._apply_filters(pool, preferences, flags)
            total_before_cap = len(matched)
            if matched:
                warnings.append(
                    f"Minimum rating relaxed to {reduced} to find matches."
                )

        if not matched:
            raise NoCandidatesError(
                "No restaurants matched your preferences even after relaxing filters.",
                suggestions=self._location_suggestions()
                + self._cuisine_suggestions(preferences),
            )

        if relaxed:
            warnings.append(
                "Some filters were relaxed: " + ", ".join(relaxed) + "."
            )

        if len(matched) < 3:
            warnings.append(
                f"Only {len(matched)} restaurant(s) matched your criteria."
            )

        sorted_matches = self._sort_matches(matched, preferences)
        capped = sorted_matches[: self._settings.candidate_limit]

        if total_before_cap > self._settings.candidate_limit:
            warnings.append(
                f"Showing top {len(capped)} of {total_before_cap} matches."
            )

        metadata = CandidateMetadata(
            total_matches_before_cap=total_before_cap,
            candidates_returned=len(capped),
            filters_relaxed=relaxed,
            warnings=warnings,
        )

        return CandidateList(
            preferences=preferences,
            restaurants=capped,
            metadata=metadata,
        )

    def _filter_by_location(self, location: str) -> list[Restaurant]:
        """EC-FILTER-07: prefer exact city/area match; fuzzy only for longer keys."""
        key = location.strip().lower()
        if not key:
            return []

        exact: list[Restaurant] = []
        for r in self._store.get_all():
            if r.location_normalized.lower() == key or r.location.lower() == key:
                exact.append(r)

        if exact:
            return exact

        if len(key) >= _MIN_LOCATION_FUZZY_LEN:
            return self._store.filter_by_location(location)

        return []

    def _apply_filters(
        self,
        pool: list[Restaurant],
        preferences: UserPreferences,
        flags: _FilterFlags,
    ) -> list[Restaurant]:
        result = pool

        if flags.apply_cuisine:
            result = [r for r in result if _matches_cuisines(r, preferences.cuisines)]

        min_rating = (
            flags.min_rating_override
            if flags.min_rating_override is not None
            else preferences.min_rating
        )
        if flags.apply_min_rating and min_rating is not None:
            result = [r for r in result if r.rating >= min_rating]

        if flags.apply_budget:
            # Phase 6A: support numeric budget filtering (approx cost for two).
            if preferences.budget_amount is not None:
                amount = float(preferences.budget_amount)
                result = [
                    r
                    for r in result
                    if (r.cost_estimate is not None and r.cost_estimate <= amount)
                ]
            elif preferences.budget is not None:
                result = [r for r in result if r.budget_tier == preferences.budget]

        return result

    def _sort_matches(
        self, restaurants: list[Restaurant], preferences: UserPreferences
    ) -> list[Restaurant]:
        # Prefer numeric budget as the target when provided, else fall back to tier midpoint.
        if preferences.budget_amount is not None:
            target = float(preferences.budget_amount)
        else:
            tier = preferences.budget or BudgetTier.MEDIUM
            target = _BUDGET_COST_MIDPOINTS[tier]

        def sort_key(r: Restaurant) -> tuple:
            cost = r.cost_estimate
            cost_distance = abs(cost - target) if cost is not None else float("inf")
            return (-r.rating, cost_distance, r.name.lower())

        return sorted(restaurants, key=sort_key)

    def _location_suggestions(self) -> list[str]:
        return self._store.known_locations(5)

    def _cuisine_suggestions(self, preferences: UserPreferences) -> list[str]:
        pool = self._filter_by_location(preferences.location)
        cuisines: set[str] = set()
        for r in pool[:50]:
            cuisines.update(r.cuisines)
        return sorted(cuisines)[:5]


def _matches_cuisines(restaurant: Restaurant, cuisines: list[str]) -> bool:
    """EC-FILTER-06: exact or word-boundary match per cuisine token (not 'italian' in 'pizza')."""
    if not cuisines:
        return True

    for cuisine in cuisines:
        key = cuisine.strip().lower()
        if not key:
            continue

        for c in restaurant.cuisines:
            c_lower = c.lower()
            if c_lower == key:
                return True
            # Word-boundary match for multi-word types (e.g. "Indian" in "North Indian")
            if len(key) >= 3 and re.search(rf"\b{re.escape(key)}\b", c_lower):
                return True
    return False
