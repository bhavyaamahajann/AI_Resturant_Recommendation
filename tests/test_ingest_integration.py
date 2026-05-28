"""Integration checks when local parquet exists (post run_ingest)."""

from pathlib import Path

import pytest

from config.settings import get_settings
from src.data.store import RestaurantStore

PARQUET = get_settings().data_path


@pytest.mark.skipif(not PARQUET.exists(), reason="Run scripts/run_ingest.py first")
class TestIngestedStore:
    def test_has_restaurants(self):
        store = RestaurantStore.from_parquet()
        assert len(store) > 0

    def test_bangalore_has_results(self):
        store = RestaurantStore.from_parquet()
        assert len(store.filter_by_location("Bangalore")) > 0

    def test_second_location_has_results(self):
        """Dataset is Bangalore-centric; Banashankari is a major area."""
        store = RestaurantStore.from_parquet()
        assert len(store.filter_by_location("Banashankari")) > 0

    def test_required_fields_present(self):
        store = RestaurantStore.from_parquet()
        r = store.get_all()[0]
        assert r.name
        assert r.location_normalized
        assert r.cuisines
        assert r.rating is not None
        assert r.budget_tier
