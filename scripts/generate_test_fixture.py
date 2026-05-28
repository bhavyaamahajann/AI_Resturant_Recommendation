#!/usr/bin/env python3
"""Generate tests/fixtures/restaurants_small.parquet for filter tests."""

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ROWS = [
    {
        "id": "r01",
        "name": "Italian Place",
        "location": "Koramangala",
        "location_normalized": "Bangalore",
        "cuisines": ["Italian", "Pizza"],
        "rating": 4.5,
        "cost_estimate": 800.0,
        "budget_tier": "medium",
        "raw_attributes": "{}",
    },
    {
        "id": "r02",
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
        "id": "r03",
        "name": "Banashankari Bites",
        "location": "Banashankari",
        "location_normalized": "Bangalore",
        "cuisines": ["Chinese"],
        "rating": 4.0,
        "cost_estimate": 400.0,
        "budget_tier": "low",
        "raw_attributes": "{}",
    },
    {
        "id": "r04",
        "name": "Bangalore Italian 2",
        "location": "Indiranagar",
        "location_normalized": "Bangalore",
        "cuisines": ["Italian"],
        "rating": 4.8,
        "cost_estimate": 1200.0,
        "budget_tier": "high",
        "raw_attributes": "{}",
    },
    {
        "id": "r05",
        "name": "Bangalore Italian 3",
        "location": "HSR",
        "location_normalized": "Bangalore",
        "cuisines": ["Italian"],
        "rating": 4.6,
        "cost_estimate": 700.0,
        "budget_tier": "medium",
        "raw_attributes": "{}",
    },
    {
        "id": "r06",
        "name": "Cheap Chinese",
        "location": "BTM",
        "location_normalized": "Bangalore",
        "cuisines": ["Chinese"],
        "rating": 3.5,
        "cost_estimate": 250.0,
        "budget_tier": "low",
        "raw_attributes": "{}",
    },
    {
        "id": "r07",
        "name": "Thai Garden",
        "location": "Koramangala",
        "location_normalized": "Bangalore",
        "cuisines": ["Thai"],
        "rating": 4.3,
        "cost_estimate": 550.0,
        "budget_tier": "medium",
        "raw_attributes": "{}",
    },
    {
        "id": "r08",
        "name": "False Italian Test",
        "location": "Jayanagar",
        "location_normalized": "Bangalore",
        "cuisines": ["North Indian"],
        "rating": 4.0,
        "cost_estimate": 500.0,
        "budget_tier": "medium",
        "raw_attributes": "{}",
    },
    {
        "id": "r09",
        "name": "Strict Rating Only",
        "location": "Whitefield",
        "location_normalized": "Bangalore",
        "cuisines": ["Italian"],
        "rating": 4.95,
        "cost_estimate": 900.0,
        "budget_tier": "high",
        "raw_attributes": "{}",
    },
    {
        "id": "r10",
        "name": "Medium Budget Indian",
        "location": "Marathahalli",
        "location_normalized": "Bangalore",
        "cuisines": ["North Indian"],
        "rating": 4.1,
        "cost_estimate": 450.0,
        "budget_tier": "medium",
        "raw_attributes": "{}",
    },
]

if __name__ == "__main__":
    out = PROJECT_ROOT / "tests" / "fixtures" / "restaurants_small.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    for row in ROWS:
        row["cuisines"] = json.dumps(row["cuisines"])
    pd.DataFrame(ROWS).to_parquet(out, index=False)
    print(f"Wrote {out} ({len(ROWS)} rows)")
