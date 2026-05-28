"""Normalize raw dataset rows into Restaurant records."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml

from config.settings import PROJECT_ROOT, Settings, get_settings
from src.data.models import BudgetTier, Restaurant

logger = logging.getLogger(__name__)

_MAPPING_PATH = PROJECT_ROOT / "config" / "field_mapping.yaml"
_COST_RANGE_RE = re.compile(r"(\d[\d,]*)\s*[-–to]+\s*(\d[\d,]*)", re.IGNORECASE)
_RATING_RE = re.compile(r"([\d.]+)\s*/\s*5")


def load_field_mapping(path: Path | None = None) -> dict[str, Any]:
    mapping_path = path or _MAPPING_PATH
    if not mapping_path.exists():
        raise FileNotFoundError(f"Field mapping not found: {mapping_path}")
    with open(mapping_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len]


def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


def parse_rating(raw: Any) -> Optional[float]:
    """EC-DATA-08: coerce rating; NEW/invalid -> None."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.upper() in ("NEW", "-", "NAN", "NONE"):
        return None
    m = _RATING_RE.search(s)
    if m:
        value = float(m.group(1))
        if value > 5:
            value = value / 2.0
        if 0 <= value <= 5:
            return round(value, 2)
    try:
        value = float(s)
        if value > 5:
            value = value / 2.0
        if 0 <= value <= 5:
            return round(value, 2)
    except ValueError:
        pass
    return None


def parse_cost(raw: Any) -> Optional[float]:
    """EC-DATA-09, EC-DATA-10: parse cost; ranges use midpoint."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s in ("-", "?"):
        return None

    range_m = _COST_RANGE_RE.search(s.replace(",", ""))
    if range_m:
        low = float(range_m.group(1).replace(",", ""))
        high = float(range_m.group(2).replace(",", ""))
        return (low + high) / 2.0

    digits = re.sub(r"[^\d.]", "", s.replace(",", ""))
    if not digits:
        return None
    try:
        return float(digits)
    except ValueError:
        return None


def split_cuisines(raw: Any) -> list[str]:
    """EC-DATA-11: split multi-cuisine strings."""
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    parts = re.split(r"[,;/]", s)
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        c = _normalize_unicode(part)
        if not c:
            continue
        key = c.lower()
        if key not in seen:
            seen.add(key)
            result.append(c)
    return result


def extract_city(address: str, city_aliases: dict[str, list[str]]) -> Optional[str]:
    """Extract canonical city from address using alias map."""
    addr_lower = address.lower()
    for city, aliases in city_aliases.items():
        for alias in aliases:
            if alias in addr_lower:
                return city
    return None


def normalize_location_text(text: str) -> str:
    return _normalize_unicode(text).title()


def make_restaurant_id(name: str, location: str, address: str) -> str:
    key = f"{name}|{location}|{address}".lower().encode("utf-8")
    return hashlib.sha256(key).hexdigest()[:16]


def normalize_row(
    row: dict[str, Any],
    mapping: dict[str, Any],
    settings: Settings,
) -> Optional[Restaurant]:
    cols = mapping["source_columns"]
    city_aliases = mapping.get("city_aliases", {})

    name = _normalize_unicode(str(row.get(cols["name"]) or ""))
    if not name:
        return None

    address = _normalize_unicode(str(row.get(cols["address"]) or ""))
    area = _normalize_unicode(str(row.get(cols.get("area", "location") or "")))

    city = extract_city(address, city_aliases)
    if not city and area:
        city = area

    if not city and not area and not address:
        return None

    location_display = area or city or address.split(",")[-1].strip()
    location_normalized = normalize_location_text(city or location_display)

    cuisines = split_cuisines(row.get(cols["cuisines"]))
    rating = parse_rating(row.get(cols["rating"]))
    if rating is None:
        return None

    cost = parse_cost(row.get(cols["cost"]))

    raw_attributes = {
        k: row.get(v)
        for k, v in cols.items()
        if k not in ("name", "address", "area", "cuisines", "rating", "cost")
        and v in row
    }
    if address:
        raw_attributes["address"] = _truncate(address, settings.max_field_length)

    restaurant_id = make_restaurant_id(name, location_display, address)

    return Restaurant(
        id=restaurant_id,
        name=_truncate(name, settings.max_field_length),
        location=_truncate(location_display, settings.max_field_length),
        location_normalized=location_normalized,
        cuisines=cuisines,
        rating=rating,
        cost_estimate=cost,
        budget_tier=BudgetTier.MEDIUM,
        raw_attributes=raw_attributes,
    )


def assign_budget_tiers(
    restaurants: list[Restaurant],
    settings: Settings,
) -> list[Restaurant]:
    """
    EC-DATA-15, EC-DATA-16: per-city percentiles with global fallback.
    Restaurants without cost get MEDIUM (EC-DATA-09).
    """
    by_city: dict[str, list[Restaurant]] = {}
    for r in restaurants:
        by_city.setdefault(r.location_normalized, []).append(r)

    global_costs = sorted(
        r.cost_estimate for r in restaurants if r.cost_estimate is not None
    )
    global_low, global_high = _percentile_thresholds(
        global_costs,
        settings.budget_low_percentile,
        settings.budget_medium_percentile,
    )

    updated: list[Restaurant] = []
    for r in restaurants:
        if r.cost_estimate is None:
            updated.append(r.model_copy(update={"budget_tier": BudgetTier.MEDIUM}))
            continue

        city_rows = by_city.get(r.location_normalized, [])
        city_costs = sorted(
            x.cost_estimate for x in city_rows if x.cost_estimate is not None
        )

        if len(city_costs) >= settings.min_city_rows_for_percentiles:
            low_cut, high_cut = _percentile_thresholds(
                city_costs,
                settings.budget_low_percentile,
                settings.budget_medium_percentile,
            )
        else:
            low_cut, high_cut = global_low, global_high

        tier = _tier_for_cost(r.cost_estimate, low_cut, high_cut)
        updated.append(r.model_copy(update={"budget_tier": tier}))

    return updated


def _percentile_thresholds(
    sorted_costs: list[float], low_pct: float, medium_pct: float
) -> tuple[float, float]:
    if not sorted_costs:
        return 0.0, 0.0
    low_cut = _percentile(sorted_costs, low_pct)
    high_cut = _percentile(sorted_costs, medium_pct)
    return low_cut, high_cut


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def _tier_for_cost(cost: float, low_cut: float, high_cut: float) -> BudgetTier:
    if cost <= low_cut:
        return BudgetTier.LOW
    if cost <= high_cut:
        return BudgetTier.MEDIUM
    return BudgetTier.HIGH


def dedupe_restaurants(restaurants: list[Restaurant]) -> list[Restaurant]:
    """EC-DATA-12: keep highest rating per (name, area/location), not city alone."""
    best: dict[tuple[str, str], Restaurant] = {}
    for r in restaurants:
        key = (r.name.lower(), r.location.lower())
        existing = best.get(key)
        if existing is None or r.rating > existing.rating:
            best[key] = r
    return list(best.values())


def normalize_dataset(
    rows: list[dict[str, Any]],
    settings: Settings | None = None,
) -> tuple[list[Restaurant], dict[str, int]]:
    settings = settings or get_settings()
    mapping = load_field_mapping()

    stats = {
        "total_rows": len(rows),
        "skipped_missing_name": 0,
        "skipped_missing_location": 0,
        "skipped_invalid_rating": 0,
        "eligible_rows": 0,
        "normalized": 0,
        "duplicates_removed": 0,
    }

    normalized: list[Restaurant] = []
    for row in rows:
        cols = mapping["source_columns"]
        name = str(row.get(cols["name"]) or "").strip()
        if not name:
            stats["skipped_missing_name"] += 1
            continue

        address = str(row.get(cols["address"]) or "").strip()
        area = str(row.get(cols.get("area", "location") or "")).strip()
        if not address and not area:
            stats["skipped_missing_location"] += 1
            continue

        stats["eligible_rows"] += 1

        if parse_rating(row.get(cols["rating"])) is None:
            stats["skipped_invalid_rating"] += 1
            continue

        restaurant = normalize_row(row, mapping, settings)
        if restaurant is None:
            stats["skipped_missing_location"] += 1
            stats["eligible_rows"] -= 1
            continue
        normalized.append(restaurant)

    stats["parsed_before_dedupe"] = len(normalized)
    before_dedupe = len(normalized)
    normalized = dedupe_restaurants(normalized)
    stats["duplicates_removed"] = before_dedupe - len(normalized)
    stats["normalized"] = len(normalized)

    normalized = assign_budget_tiers(normalized, settings)
    return normalized, stats


def persist_restaurants(
    restaurants: list[Restaurant],
    path: Path | None = None,
) -> Path:
    path = path or get_settings().data_path
    path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for r in restaurants:
        rec = r.model_dump()
        rec["cuisines"] = list(rec["cuisines"])
        rec["budget_tier"] = rec["budget_tier"].value
        rec["raw_attributes"] = json.dumps(rec["raw_attributes"], ensure_ascii=False)
        records.append(rec)

    df = pd.DataFrame(records)
    df.to_parquet(path, index=False)
    logger.info("Wrote %d restaurants to %s", len(df), path)
    return path


def validate_ingest_ratio(stats: dict[str, int], threshold: float) -> None:
    total = stats["total_rows"]
    if total == 0:
        raise ValueError("No rows to ingest (EC-DATA-03)")

    rated_eligible = stats["eligible_rows"] - stats["skipped_invalid_rating"]
    if rated_eligible == 0:
        raise ValueError("No rows with parseable ratings (EC-DATA-08)")

    parsed = stats.get("parsed_before_dedupe", stats["normalized"])
    valid_ratio = parsed / rated_eligible
    if valid_ratio < threshold:
        raise ValueError(
            f"Ingest valid ratio {valid_ratio:.2%} below threshold {threshold:.2%} "
            f"(parsed={parsed}, rated_eligible={rated_eligible})"
        )
