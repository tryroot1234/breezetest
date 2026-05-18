"""YAML/JSON test suite parser with variable resolution and data-driven expansion."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml

from breezetest.core.models import (
    BreezeConfig,
    Step,
    TestCase,
    TestSuite,
)


class ParseError(Exception):
    pass


def parse_suite_file(path: str | Path) -> TestSuite:
    path = Path(path)
    if not path.exists():
        raise ParseError(f"File not found: {path}")
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ParseError(f"Expected a YAML mapping, got {type(data).__name__}")
    suite = _parse_suite_data(data)
    suite.source_file = path
    return suite


def parse_suite(data: dict[str, Any]) -> TestSuite:
    return _parse_suite_data(data)


def _parse_suite_data(data: dict[str, Any]) -> TestSuite:
    config = _parse_config(data.get("config", {}))
    tests = []
    for i, test_data in enumerate(data.get("tests", [])):
        if not isinstance(test_data, dict):
            raise ParseError(f"Test #{i}: expected a mapping, got {type(test_data).__name__}")
        tests.append(_parse_test(test_data))
    return TestSuite(config=config, tests=tests)


def _parse_config(data: dict[str, Any]) -> BreezeConfig:
    if not data:
        return BreezeConfig()
    return BreezeConfig(**data)


def _parse_test(data: dict[str, Any]) -> TestCase:
    name = data.get("name")
    if not name:
        raise ParseError("Each test must have a 'name' field")

    steps = []
    for i, step_data in enumerate(data.get("steps", [])):
        if not isinstance(step_data, dict):
            raise ParseError(f"Test '{name}' step #{i}: expected a mapping")
        steps.append(_parse_step(step_data))

    data_field = data.get("data")
    return TestCase(
        name=name,
        description=data.get("description"),
        tags=data.get("tags", []),
        skip=data.get("skip", False),
        retry=data.get("retry"),
        steps=steps,
        data=data_field,
    )


def _parse_step(data: dict[str, Any]) -> Step:
    action = data.get("action")
    if not action:
        raise ParseError("Each step must have an 'action' field")
    return Step(
        action=action,
        selector=data.get("selector"),
        value=data.get("value"),
        options=data.get("options", {}),
        description=data.get("description"),
        on_failure=data.get("on_failure", "fail"),
    )


def expand_parameterized(test: TestCase, base_dir: Path | None = None) -> list[TestCase]:
    if test.data is None:
        return [test]

    rows = _load_data(test.data, base_dir)
    if not rows:
        return [test]

    expanded = []
    for i, row in enumerate(rows):
        suffix = _format_params(row)
        expanded.append(
            TestCase(
                name=f"{test.name} [{suffix}]",
                description=test.description,
                tags=test.tags.copy(),
                skip=test.skip,
                retry=test.retry,
                steps=[step.model_copy(deep=True) for step in test.steps],
                data=None,
            )
        )
    return expanded


def _load_data(
    data: list[dict[str, Any]] | str,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data

    if isinstance(data, str):
        csv_path = Path(data)
        if base_dir and not csv_path.is_absolute():
            csv_path = base_dir / csv_path
        if not csv_path.exists():
            raise ParseError(f"Data file not found: {csv_path}")
        return _load_csv(csv_path)

    raise ParseError(f"Invalid data type: {type(data)}")


def _load_csv(path: Path) -> list[dict[str, Any]]:
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _format_params(params: dict[str, Any]) -> str:
    parts = []
    for k, v in params.items():
        val = str(v)
        if len(val) > 30:
            val = val[:27] + "..."
        parts.append(f"{k}={val}")
    return ", ".join(parts)


def resolve_variables(value: Any, variables: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value
    for key, val in variables.items():
        value = value.replace(f"{{{{{key}}}}}", str(val))
    return value


def parse_comparison(value: str) -> tuple[str, str]:
    patterns = [
        (r"^>=\s*(.+)$", "gte"),
        (r"^<=\s*(.+)$", "lte"),
        (r"^>\s*(.+)$", "gt"),
        (r"^<\s*(.+)$", "lt"),
        (r"^!=\s*(.+)$", "ne"),
        (r"^between:\s*(.+),\s*(.+)$", "between"),
    ]
    for pattern, op in patterns:
        match = re.match(pattern, value.strip())
        if match:
            return op, ",".join(match.groups())
    return "eq", value
