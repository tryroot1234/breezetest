"""Data providers for data-driven testing."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class DataProviderError(Exception):
    pass


def load_data(data: list[dict[str, Any]] | str, base_dir: Path | None = None) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, str):
        path = Path(data)
        if base_dir and not path.is_absolute():
            path = base_dir / path
        if not path.exists():
            raise DataProviderError(f"Data file not found: {path}")
        if path.suffix == ".csv":
            return load_csv(path)
        elif path.suffix == ".json":
            return load_json(path)
        else:
            raise DataProviderError(f"Unsupported data file format: {path.suffix}")
    raise DataProviderError(f"Invalid data type: {type(data)}")


def load_csv(path: Path) -> list[dict[str, Any]]:
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def load_json(path: Path) -> list[dict[str, Any]]:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    raise DataProviderError(f"JSON data must be a list or have a 'data' key")
