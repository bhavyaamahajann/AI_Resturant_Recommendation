"""In-memory restaurant store backed by parquet."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from config.settings import get_settings
from src.data.models import BudgetTier, Restaurant

logger = logging.getLogger(__name__)
_PINCODE_RE = re.compile(r"\b\d{5,6}\b")


class DataStoreError(Exception):
    """Raised when the restaurant data file is missing or corrupt (EC-DATA-18)."""


class RestaurantStore:
    def __init__(self, restaurants: list[Restaurant] | None = None) -> None:
        self._restaurants: list[Restaurant] = restaurants or []
        self._by_id: dict[str, Restaurant] = {}
        self._by_location: dict[str, list[Restaurant]] = {}
        self._cuisine_index: dict[str, set[str]] = {}
        if self._restaurants:
            self._build_indexes()

    @classmethod
    def from_parquet(cls, path: Path | None = None) -> "RestaurantStore":
        path = path or get_settings().data_path
        if not path.exists():
            raise DataStoreError(
                f"Restaurant data not found at {path}. Run scripts/run_ingest.py first."
            )
        try:
            df = pd.read_parquet(path)
        except Exception as exc:
            raise DataStoreError(f"Failed to read parquet at {path}: {exc}") from exc

        restaurants: list[Restaurant] = []
        for _, row in df.iterrows():
            cuisines = row["cuisines"]
            if isinstance(cuisines, str):
                cuisines = json.loads(cuisines)
            raw_attrs = row.get("raw_attributes", {})
            if isinstance(raw_attrs, str):
                raw_attrs = json.loads(raw_attrs)

            restaurants.append(
                Restaurant(
                    id=str(row["id"]),
                    name=str(row["name"]),
                    location=str(row["location"]),
                    location_normalized=str(row["location_normalized"]),
                    cuisines=list(cuisines),
                    rating=float(row["rating"]),
                    cost_estimate=(
                        float(row["cost_estimate"])
                        if pd.notna(row.get("cost_estimate"))
                        else None
                    ),
                    budget_tier=BudgetTier(str(row["budget_tier"])),
                    raw_attributes=dict(raw_attrs) if raw_attrs else {},
                )
            )

        logger.info("Loaded %d restaurants from %s", len(restaurants), path)
        return cls(restaurants)

    def _build_indexes(self) -> None:
        self._by_id = {r.id: r for r in self._restaurants}
        self._by_location = {}
        self._cuisine_index = {}
        for r in self._restaurants:
            loc_key = r.location_normalized.lower()
            self._by_location.setdefault(loc_key, []).append(r)
            area_key = r.location.lower()
            if area_key != loc_key:
                self._by_location.setdefault(area_key, []).append(r)

            for cuisine in r.cuisines:
                c_key = cuisine.lower()
                self._cuisine_index.setdefault(c_key, set()).add(r.id)

    def get_all(self) -> list[Restaurant]:
        return list(self._restaurants)

    def get_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        return self._by_id.get(restaurant_id)

    def get_by_ids(self, restaurant_ids: list[str]) -> list[Restaurant]:
        return [self._by_id[rid] for rid in restaurant_ids if rid in self._by_id]

    def filter_by_location(self, location: str) -> list[Restaurant]:
        """Case-insensitive match on city or area (EC-INPUT-04, EC-INPUT-05)."""
        if not location or not location.strip():
            return []
        key = location.strip().lower()
        direct = self._by_location.get(key, [])
        if direct:
            return list(direct)

        return [
            r
            for r in self._restaurants
            if key in r.location_normalized.lower() or key in r.location.lower()
        ]

    def filter_by_cuisine(self, cuisine: str) -> list[Restaurant]:
        key = cuisine.strip().lower()
        ids = self._cuisine_index.get(key, set())
        if ids:
            return [self._by_id[i] for i in ids]

        return [
            r
            for r in self._restaurants
            if any(key in c.lower() for c in r.cuisines)
        ]

    def known_locations(self, limit: int = 50) -> list[str]:
        counts: dict[str, int] = {}
        for r in self._restaurants:
            counts[r.location_normalized] = counts.get(r.location_normalized, 0) + 1
        sorted_locs = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        return [loc for loc, _ in sorted_locs[:limit]]

    def known_cuisines(self, limit: int = 200) -> list[str]:
        """Return distinct cuisines sorted by restaurant count."""
        counts: dict[str, int] = {}
        for r in self._restaurants:
            for c in r.cuisines:
                cuisine = str(c).strip()
                if not cuisine:
                    continue
                counts[cuisine] = counts.get(cuisine, 0) + 1
        sorted_items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        return [c for c, _ in sorted_items[:limit]]

    def known_areas(self, limit: int = 200) -> list[str]:
        """Return distinct area/neighborhood names sorted by restaurant count.

        Unlike ``known_locations`` which returns city-level
        ``location_normalized`` values (e.g. 'Bangalore'), this method
        returns the finer-grained ``location`` field (e.g. 'Indiranagar',
        'Bellandur', 'Koramangala').
        """
        counts: dict[str, int] = {}
        for r in self._restaurants:
            area = self._best_area_name(r)
            if area:
                counts[area] = counts.get(area, 0) + 1
        sorted_areas = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        return [area for area, _ in sorted_areas[:limit]]

    def _best_area_name(self, r: Restaurant) -> str:
        """
        Best-effort area extraction for UI dropdowns.

        Some datasets store only the city in the `location` field. In that
        case we try to derive a neighborhood/locality from the address.
        """
        raw = (r.location or "").strip()
        city = (r.location_normalized or "").strip()

        # If the location already looks like a locality (not equal to city), keep it.
        if raw and (not city or raw.casefold() != city.casefold()):
            return raw

        address = ""
        if r.raw_attributes:
            address = str(r.raw_attributes.get("address") or "").strip()
        if not address:
            return raw

        parts = [p.strip() for p in address.split(",") if p and p.strip()]
        if not parts:
            return raw

        # Remove known "noise" parts: city name, pincodes.
        filtered = []
        for p in parts:
            if city and p.casefold() == city.casefold():
                continue
            if _PINCODE_RE.search(p):
                continue
            filtered.append(p)

        # Heuristic: the last meaningful part is often the area/locality.
        if filtered:
            candidate = filtered[-1]
            # If still equals city, try the previous token.
            if city and candidate.casefold() == city.casefold() and len(filtered) >= 2:
                candidate = filtered[-2]
            return candidate.strip() or raw

        return raw

    def __len__(self) -> int:
        return len(self._restaurants)
