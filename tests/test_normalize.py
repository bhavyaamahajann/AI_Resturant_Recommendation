import pytest

from config.settings import Settings
from src.data.models import BudgetTier
from src.ingest.normalize import (
    assign_budget_tiers,
    dedupe_restaurants,
    extract_city,
    load_field_mapping,
    normalize_row,
    parse_cost,
    parse_rating,
    split_cuisines,
    validate_ingest_ratio,
)
from src.data.models import Restaurant


@pytest.fixture
def mapping():
    return load_field_mapping()


@pytest.fixture
def settings():
    return Settings(
        budget_low_percentile=33.0,
        budget_medium_percentile=66.0,
        min_city_rows_for_percentiles=10,
        max_field_length=500,
    )


class TestParseRating:
    def test_standard_format(self):
        assert parse_rating("4.1/5") == 4.1

    def test_spaced_format(self):
        assert parse_rating("3.9 /5") == 3.9

    def test_new_is_invalid(self):
        assert parse_rating("NEW") is None

    def test_empty(self):
        assert parse_rating("") is None


class TestParseCost:
    def test_integer_string(self):
        assert parse_cost("800") == 800.0

    def test_comma_separated(self):
        assert parse_cost("1,200") == 1200.0

    def test_range_midpoint(self):
        assert parse_cost("300-500") == 400.0

    def test_missing(self):
        assert parse_cost(None) is None


class TestSplitCuisines:
    def test_multi_cuisine(self):
        assert split_cuisines("North Indian, Mughlai, Chinese") == [
            "North Indian",
            "Mughlai",
            "Chinese",
        ]


class TestNormalizeRow:
    def test_valid_row(self, mapping, settings):
        row = {
            "name": "Jalsa",
            "address": "942, Banashankari, Bangalore",
            "location": "Banashankari",
            "cuisines": "North Indian, Chinese",
            "rate": "4.1/5",
            "approx_cost(for two people)": "800",
        }
        r = normalize_row(row, mapping, settings)
        assert r is not None
        assert r.name == "Jalsa"
        assert r.location_normalized == "Bangalore"
        assert "North Indian" in r.cuisines
        assert r.rating == 4.1
        assert r.cost_estimate == 800.0

    def test_missing_name_skipped(self, mapping, settings):
        row = {
            "name": "",
            "address": "Bangalore",
            "location": "X",
            "cuisines": "Italian",
            "rate": "4.0/5",
            "approx_cost(for two people)": "500",
        }
        assert normalize_row(row, mapping, settings) is None


class TestDedupe:
    def test_keeps_higher_rating(self):
        a = Restaurant(
            id="1",
            name="Cafe",
            location="Area",
            location_normalized="Bangalore",
            cuisines=["Italian"],
            rating=3.5,
            cost_estimate=500,
            budget_tier=BudgetTier.MEDIUM,
        )
        b = a.model_copy(update={"id": "2", "rating": 4.5, "location": "Area"})
        c = a.model_copy(update={"id": "3", "location": "Other Area", "rating": 3.0})
        result = dedupe_restaurants([a, b, c])
        assert len(result) == 2
        assert max(r.rating for r in result if r.location == "Area") == 4.5


class TestBudgetTiers:
    def test_assign_tiers(self, settings):
        restaurants = [
            Restaurant(
                id=str(i),
                name=f"R{i}",
                location="X",
                location_normalized="Bangalore",
                cuisines=["Indian"],
                rating=4.0,
                cost_estimate=float(c),
                budget_tier=BudgetTier.MEDIUM,
            )
            for i, c in enumerate([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
        ]
        tiered = assign_budget_tiers(restaurants, settings)
        tiers = {r.budget_tier for r in tiered}
        assert BudgetTier.LOW in tiers
        assert BudgetTier.HIGH in tiers


class TestValidateIngestRatio:
    def test_passes_above_threshold(self):
        stats = {
            "total_rows": 100,
            "eligible_rows": 80,
            "skipped_invalid_rating": 10,
            "parsed_before_dedupe": 63,
            "normalized": 50,
        }
        validate_ingest_ratio(stats, 0.9)

    def test_fails_below_threshold(self):
        stats = {
            "total_rows": 100,
            "eligible_rows": 80,
            "skipped_invalid_rating": 10,
            "parsed_before_dedupe": 50,
            "normalized": 40,
        }
        with pytest.raises(ValueError):
            validate_ingest_ratio(stats, 0.9)


class TestExtractCity:
    def test_bangalore_alias(self, mapping):
        city = extract_city("2nd Stage, Banashankari, Bengaluru", mapping["city_aliases"])
        assert city == "Bangalore"
