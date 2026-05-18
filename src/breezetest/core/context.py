"""Test execution context - mutable state during a single test run."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Page

    from breezetest.core.models import BreezeConfig, TestCase


class TestContext:
    def __init__(
        self,
        config: BreezeConfig,
        test: TestCase,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.config = config
        self.test = test
        self.parameters = parameters or {}
        self.variables: dict[str, Any] = {
            **config.variables,
            **self.parameters,
        }
        self.screenshots: list[str] = []
        self.page: Page | None = None
        self._start_time: float = 0.0

    def start_timer(self) -> None:
        self._start_time = time.monotonic()

    def elapsed_ms(self) -> float:
        return (time.monotonic() - self._start_time) * 1000

    def resolve_variables(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        for key, val in self.variables.items():
            value = value.replace(f"{{{{{key}}}}}", str(val))
        return value

    def set_variable(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)
