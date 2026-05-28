#!/usr/bin/env python3
"""Ingest Zomato dataset from Hugging Face into local parquet."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.ingest.loader import DatasetLoadError, load_raw_dataset
from src.ingest.normalize import (
    normalize_dataset,
    persist_restaurants,
    validate_ingest_ratio,
    _percentile_thresholds,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_ingest")


def _log_budget_thresholds(restaurants: list, settings) -> None:
    costs = sorted(r.cost_estimate for r in restaurants if r.cost_estimate is not None)
    if costs:
        low, high = _percentile_thresholds(
            costs,
            settings.budget_low_percentile,
            settings.budget_medium_percentile,
        )
        logger.info(
            "Global budget thresholds: low <= %.0f, medium <= %.0f, high > %.0f",
            low,
            high,
            high,
        )


def main() -> int:
    settings = get_settings()
    logger.info("Starting ingest at %s", datetime.now(timezone.utc).isoformat())
    logger.info("Dataset: %s", settings.dataset_name)
    logger.info("Output: %s", settings.data_path)

    try:
        rows = load_raw_dataset(settings.dataset_name)
    except DatasetLoadError as exc:
        logger.error("%s", exc)
        return 1

    restaurants, stats = normalize_dataset(rows, settings)
    logger.info("Ingest stats: %s", stats)

    try:
        validate_ingest_ratio(stats, settings.ingest_valid_threshold)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    _log_budget_thresholds(restaurants, settings)
    path = persist_restaurants(restaurants, settings.data_path)
    logger.info("Ingest complete: %d restaurants -> %s", len(restaurants), path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
