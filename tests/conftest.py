from pathlib import Path

import pytest

from src.data.store import RestaurantStore

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "restaurants_small.parquet"


@pytest.fixture
def small_store() -> RestaurantStore:
    if not FIXTURE_PATH.exists():
        pytest.skip("Run: python scripts/generate_test_fixture.py")
    return RestaurantStore.from_parquet(FIXTURE_PATH)
