"""Load raw Zomato dataset from Hugging Face."""

from __future__ import annotations

import logging
from typing import Any, Iterator

from datasets import load_dataset

from config.settings import get_settings

logger = logging.getLogger(__name__)


class DatasetLoadError(Exception):
    """Raised when the Hugging Face dataset cannot be loaded (EC-DATA-01)."""


def load_raw_dataset(
    dataset_name: str | None = None,
    split: str = "train",
) -> list[dict[str, Any]]:
    """
    Load the full dataset into memory as a list of row dicts.

    Raises DatasetLoadError on network or hub failures.
    """
    name = dataset_name or get_settings().dataset_name
    try:
        ds = load_dataset(name, split=split)
    except Exception as exc:
        logger.exception("Failed to load dataset %s", name)
        raise DatasetLoadError(
            f"Could not load dataset '{name}': {exc}"
        ) from exc

    if len(ds) == 0:
        raise DatasetLoadError(f"Dataset '{name}' split '{split}' is empty (EC-DATA-03)")

    logger.info("Loaded %d rows from %s", len(ds), name)
    return [dict(row) for row in ds]


def iter_raw_batches(
    rows: list[dict[str, Any]], batch_size: int = 1000
) -> Iterator[list[dict[str, Any]]]:
    for i in range(0, len(rows), batch_size):
        yield rows[i : i + batch_size]
