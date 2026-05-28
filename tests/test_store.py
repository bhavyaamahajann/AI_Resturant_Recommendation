import json
from pathlib import Path

import pandas as pd
import pytest

from src.data.models import BudgetTier, Restaurant
from src.data.store import DataStoreError, RestaurantStore


@pytest.fixture
def fixture_parquet(tmp_path: Path) -> Path:
    rows = [
        {
            "id": "aaa",
            "name": "Italian Place",
            "location": "Koramangala",
            "location_normalized": "Bangalore",
            "cuisines": ["Italian", "Pizza"],
            "rating": 4.5,
            "cost_estimate": 800.0,
            "budget_tier": "medium",
            "raw_attributes": json.dumps({"rest_type": "Casual Dining"}),
        },
        {
            "id": "bbb",
            "name": "Delhi Diner",
            "location": "Connaught Place",
            "location_normalized": "Delhi",
            "cuisines": ["North Indian"],
            "rating": 4.2,
            "cost_estimate": 600.0,
            "budget_tier": "low",
            "raw_attributes": "{}",
        },
        {
            "id": "ccc",
            "name": "Banashankari Bites",
            "location": "Banashankari",
            "location_normalized": "Bangalore",
            "cuisines": ["Chinese"],
            "rating": 4.0,
            "cost_estimate": 400.0,
            "budget_tier": "low",
            "raw_attributes": "{}",
        },
    ]
    path = tmp_path / "restaurants.parquet"
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def test_store_loads_parquet(fixture_parquet: Path):
    store = RestaurantStore.from_parquet(fixture_parquet)
    assert len(store) == 3


def test_filter_by_location_city(fixture_parquet: Path):
    store = RestaurantStore.from_parquet(fixture_parquet)
    bangalore = store.filter_by_location("Bangalore")
    assert len(bangalore) == 2
    delhi = store.filter_by_location("Delhi")
    assert len(delhi) == 1
    assert delhi[0].name == "Delhi Diner"


def test_filter_by_location_area(fixture_parquet: Path):
    store = RestaurantStore.from_parquet(fixture_parquet)
    area = store.filter_by_location("Banashankari")
    assert len(area) >= 1


def test_filter_by_cuisine(fixture_parquet: Path):
    store = RestaurantStore.from_parquet(fixture_parquet)
    italian = store.filter_by_cuisine("Italian")
    assert len(italian) == 1
    assert italian[0].name == "Italian Place"


def test_get_by_ids(fixture_parquet: Path):
    store = RestaurantStore.from_parquet(fixture_parquet)
    found = store.get_by_ids(["aaa", "missing"])
    assert len(found) == 1
    assert found[0].id == "aaa"


def test_missing_parquet_raises(tmp_path: Path):
    with pytest.raises(DataStoreError):
        RestaurantStore.from_parquet(tmp_path / "missing.parquet")


def test_in_memory_store():
    r = Restaurant(
        id="x",
        name="Test",
        location="Area",
        location_normalized="Bangalore",
        cuisines=["Thai"],
        rating=4.0,
        cost_estimate=300,
        budget_tier=BudgetTier.LOW,
    )
    store = RestaurantStore([r])
    assert store.get_by_id("x") == r
    assert len(store.filter_by_location("bangalore")) == 1
