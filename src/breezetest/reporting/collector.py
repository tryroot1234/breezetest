"""Result collector - aggregates test results during execution."""

from __future__ import annotations

from breezetest.core.models import SuiteResult, TestResult


class ResultCollector:
    def __init__(self) -> None:
        self._results: list[TestResult] = []

    def add(self, result: TestResult) -> None:
        self._results.append(result)

    @property
    def results(self) -> list[TestResult]:
        return list(self._results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self._results if r.status == "passed")

    @property
    def failed(self) -> int:
        return sum(1 for r in self._results if r.status == "failed")

    @property
    def skipped(self) -> int:
        return sum(1 for r in self._results if r.status == "skipped")

    @property
    def error(self) -> int:
        return sum(1 for r in self._results if r.status == "error")

    def clear(self) -> None:
        self._results.clear()
