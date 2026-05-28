# AI-Powered Restaurant Recommendation System

Zomato-inspired restaurant recommendations using structured data + LLM (phases 0–2 implemented).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Phase 1: Data ingest

Download and normalize the Hugging Face dataset into local parquet:

```bash
python scripts/run_ingest.py
```

Regenerate schema documentation:

```bash
python scripts/discover_schema.py
```

Output:

- `data/restaurants.parquet` (gitignored)
- `data/schema.md`

## Phase 2: Filter candidates

```python
from src.data.store import RestaurantStore
from src.data.preferences import UserPreferences
from src.data.models import BudgetTier
from src.services.filter import CandidateFilterService

store = RestaurantStore.from_parquet()
service = CandidateFilterService(store)

prefs = UserPreferences(
    location="Bangalore",
    budget=BudgetTier.MEDIUM,
    cuisine="Italian",
    min_rating=4.0,
)
result = service.get_candidates(prefs)
print(result.metadata)
for r in result.restaurants:
    print(r.name, r.rating, r.budget_tier)
```

Relaxation: if no strict matches, drops cuisine → budget → lowers `min_rating` by 0.5 (see `docs/edge-cases.md`).

## Use the restaurant store

```python
from src.data.store import RestaurantStore

store = RestaurantStore.from_parquet()
print(len(store))
print(store.filter_by_location("Bangalore")[:3])
print(store.filter_by_cuisine("Italian")[:3])
```

## Tests

```bash
pytest tests/ -v
```

## Project layout

```
config/           settings and field_mapping.yaml
src/ingest/       HF loader, normalization, budget tiers
src/data/         models, preferences, RestaurantStore
src/services/     CandidateFilterService
scripts/          run_ingest.py, discover_schema.py
tests/            unit tests + fixtures/restaurants_small.parquet
data/             generated parquet and schema.md
docs/             architecture and planning
```
