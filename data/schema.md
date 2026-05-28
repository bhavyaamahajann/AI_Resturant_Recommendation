# Dataset Schema

> Auto-generated: 2026-05-17T09:41:49.125321+00:00
> Source: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)

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

- Total rows: 51717
- Rows with parseable rating: 41665
- Rows with invalid/NEW rating (skipped): 10052
- City distribution (from address): {'Bangalore': 49843}

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
| `budget_tier` | low/medium/high | Per-city percentiles (33.0% / 66.0%), global fallback if city &lt; 10 rows |
| `raw_attributes` | object | Extra source fields |

## Ingest validation

- `INGEST_VALID_THRESHOLD` (default 0.9): `normalized / rated_eligible` must meet threshold
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
