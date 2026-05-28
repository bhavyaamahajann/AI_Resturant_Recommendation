#!/usr/bin/env python3
"""Print dataset schema and write data/schema.md."""

from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.ingest.loader import load_raw_dataset
from src.ingest.normalize import parse_cost, parse_rating, extract_city, load_field_mapping


def main() -> None:
    settings = get_settings()
    mapping = load_field_mapping()
    cols = mapping["source_columns"]

    rows = load_raw_dataset(settings.dataset_name)
    print(f"Rows: {len(rows)}")
    print(f"Columns: {list(rows[0].keys())}")

    city_counts: Counter = Counter()
    invalid_rating = 0
    for row in rows:
        addr = str(row.get(cols["address"]) or "")
        city = extract_city(addr, mapping.get("city_aliases", {}))
        if city:
            city_counts[city] += 1
        if parse_rating(row.get(cols["rating"])) is None:
            invalid_rating += 1

    schema_path = PROJECT_ROOT / "data" / "schema.md"
    schema_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# Dataset Schema

> Auto-generated: {datetime.now(timezone.utc).isoformat()}
> Source: [{settings.dataset_name}](https://huggingface.co/datasets/{settings.dataset_name})

## Raw columns

| Column | Maps to |
|--------|---------|
| `name` | `name` |
| `address` | city extraction + `raw_attributes.address` |
| `location` | `location` (area/neighborhood) |
| `cuisines` | `cuisines[]` |
| `rate` | `rating` (parsed from e.g. `4.1/5`; `NEW` skipped) |
| `approx_cost(for two people)` | `cost_estimate` |
| `rest_type`, `online_order`, etc. | `raw_attributes` |

## Row statistics

- Total rows: {len(rows)}
- Rows with parseable rating: {len(rows) - invalid_rating}
- Rows with invalid/NEW rating (skipped): {invalid_rating}
- City distribution (from address): {dict(city_counts.most_common(10))}

## Canonical `Restaurant` model

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | SHA256 prefix of name+location+address |
| `name` | string | Required |
| `location` | string | Area/neighborhood display |
| `location_normalized` | string | City (e.g. Bangalore) |
| `cuisines` | list[string] | Split on comma |
| `rating` | float | 0–5 |
| `cost_estimate` | float? | Parsed numeric; null → budget tier default medium |
| `budget_tier` | low/medium/high | Per-city percentiles ({settings.budget_low_percentile}% / {settings.budget_medium_percentile}%), global fallback if city &lt; {settings.min_city_rows_for_percentiles} rows |
| `raw_attributes` | object | Extra source fields |

## Ingest validation

- `INGEST_VALID_THRESHOLD` (default {settings.ingest_valid_threshold}): `normalized / rated_eligible` must meet threshold
- `rated_eligible` = rows with name+location minus invalid ratings

## Edge cases handled

- EC-DATA-06: skip missing name
- EC-DATA-07: skip missing address and area
- EC-DATA-08: skip NEW/invalid ratings
- EC-DATA-09: null cost → `budget_tier=medium`
- EC-DATA-10: cost ranges → midpoint
- EC-DATA-11: multi-cuisine split
- EC-DATA-12: dedupe by (name, location_normalized), keep highest rating
- EC-DATA-15/16: per-city percentiles with global fallback
"""
    schema_path.write_text(content, encoding="utf-8")
    print(f"Wrote {schema_path}")


if __name__ == "__main__":
    main()
