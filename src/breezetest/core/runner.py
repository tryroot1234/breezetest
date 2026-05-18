"""Test suite runner - orchestrates execution of all test cases."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from breezetest.browser.config import BrowserConfig
from breezetest.browser.manager import BrowserManager
from breezetest.core.executor import TestExecutor
from breezetest.core.hooks import HookManager
from breezetest.core.models import (
    BreezeConfig,
    RunConfig,
    SuiteResult,
    TestCase,
    TestResult,
    TestSuite,
)
from breezetest.core.parser import expand_parameterized
from breezetest.reporting.collector import ResultCollector
from breezetest.reporting.console import ConsoleReporter
from breezetest.reporting.html_report import HtmlReportGenerator
from breezetest.reporting.junit_xml import JunitXmlReporter

# Import actions to trigger registration
import breezetest.actions.navigation  # noqa: F401
import breezetest.actions.interaction  # noqa: F401
import breezetest.actions.assertion  # noqa: F401
import breezetest.actions.wait  # noqa: F401
import breezetest.actions.capture  # noqa: F401
import breezetest.actions.script  # noqa: F401


class TestRunner:
    def __init__(self, run_config: RunConfig) -> None:
        self.run_config = run_config
        self.hook_manager = HookManager()
        self.collector = ResultCollector()

    async def run_suites(self, suites: list[TestSuite]) -> SuiteResult:
        all_results: list[TestResult] = []
        all_tests: list[tuple[TestCase, BreezeConfig]] = []

        for suite in suites:
            config = self._merge_config(suite.config)
            tests = self._filter_by_tags(suite.tests, self.run_config.tags)
            expanded = []
            for test in tests:
                expanded.extend(expand_parameterized(test, suite.source_file.parent if suite.source_file else None))
            for test in expanded:
                all_tests.append((test, config))

        if self.run_config.dry_run:
            console = ConsoleReporter(verbose=self.run_config.verbose)
            console.print_header(self.run_config, len(all_tests))
            result = self._build_dry_run_result(all_tests)
            for test_result in result.tests:
                console.print_test_result(test_result)
            console.print_summary(result)
            return result

        console = ConsoleReporter(verbose=self.run_config.verbose)
        console.print_header(self.run_config, len(all_tests))

        browser_config = BrowserConfig(
            browser_type=self.run_config.browser,
            headless=self.run_config.headless,
        )

        async with BrowserManager(browser_config) as browser_manager:
            executor = TestExecutor(
                browser_manager=browser_manager,
                hook_manager=self.hook_manager,
                screenshot_mode=self.run_config.screenshot_mode,
                report_dir=self.run_config.report_dir,
            )

            if self.run_config.workers > 1:
                all_results = await self._run_parallel(
                    all_tests, executor, console
                )
            else:
                all_results = await self._run_sequential(
                    all_tests, executor, console
                )

            # Retry failed tests
            if self.run_config.retries and self.run_config.retries > 0:
                all_results = await self._retry_failed(
                    all_results, all_tests, executor, console
                )

        suite_result = self._build_suite_result(suites, all_results)

        # Generate reports
        report_dir = Path(self.run_config.report_dir)
        if self.run_config.html:
            gen = HtmlReportGenerator(report_dir)
            html_path = gen.generate(suite_result)
            console.print_report_path(str(html_path))
        if self.run_config.junit:
            gen = JunitXmlReporter(report_dir)
            xml_path = gen.generate(suite_result)
            console.print_report_path(str(xml_path))

        console.print_summary(suite_result)
        return suite_result

    def _merge_config(self, suite_config: BreezeConfig) -> BreezeConfig:
        data = suite_config.model_dump()
        if self.run_config.base_url:
            data["base_url"] = self.run_config.base_url
        if self.run_config.timeout:
            data["timeout"] = self.run_config.timeout
        if self.run_config.env_vars:
            data["variables"] = {**data.get("variables", {}), **self.run_config.env_vars}
        return BreezeConfig(**data)

    def _filter_by_tags(self, tests: list[TestCase], tags: list[str]) -> list[TestCase]:
        if not tags:
            return [t for t in tests if not t.skip]
        tag_set = set(tags)
        return [t for t in tests if not t.skip and tag_set.intersection(t.tags)]

    async def _run_sequential(
        self,
        tests: list[tuple[TestCase, BreezeConfig]],
        executor: TestExecutor,
        console: ConsoleReporter,
    ) -> list[TestResult]:
        results = []
        for test, config in tests:
            result = await executor.execute(test, config)
            results.append(result)
            console.print_test_result(result)
            if self.run_config.fail_fast and result.status in ("failed", "error"):
                break
        return results

    async def _run_parallel(
        self,
        tests: list[tuple[TestCase, BreezeConfig]],
        executor: TestExecutor,
        console: ConsoleReporter,
    ) -> list[TestResult]:
        semaphore = asyncio.Semaphore(self.run_config.workers)
        results: list[TestResult | None] = [None] * len(tests)

        async def run_one(idx: int, test: TestCase, config: BreezeConfig) -> None:
            async with semaphore:
                result = await executor.execute(test, config)
                results[idx] = result
                console.print_test_result(result)

        tasks = [
            run_one(i, test, config)
            for i, (test, config) in enumerate(tests)
        ]
        await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def _retry_failed(
        self,
        results: list[TestResult],
        tests: list[tuple[TestCase, BreezeConfig]],
        executor: TestExecutor,
        console: ConsoleReporter,
    ) -> list[TestResult]:
        max_retries = self.run_config.retries or 0
        test_map = {t.name: (t, c) for t, c in tests}
        final = list(results)

        for attempt in range(max_retries):
            failed = [r for r in final if r.status in ("failed", "error")]
            if not failed:
                break

            console.print_retry_header(attempt + 1, len(failed))
            retry_results = []
            for old_result in failed:
                key = old_result.test_name.split(" [")[0]  # strip params
                if key not in test_map:
                    continue
                test, config = test_map[key]
                new_result = await executor.execute(test, config)
                new_result.retry_count = attempt + 1
                retry_results.append((old_result, new_result))
                console.print_test_result(new_result)

            for old, new in retry_results:
                idx = final.index(old)
                final[idx] = new

        return final

    def _build_suite_result(
        self, suites: list[TestSuite], results: list[TestResult]
    ) -> SuiteResult:
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        error = sum(1 for r in results if r.status == "error")
        total_ms = sum(r.duration_ms for r in results)

        suite_name = ", ".join(
            s.source_file.stem for s in suites if s.source_file
        ) or "unnamed"

        return SuiteResult(
            suite_name=suite_name,
            tests=results,
            total=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            error=error,
            duration_ms=total_ms,
            timestamp=datetime.now(),
            browser=self.run_config.browser,
        )

    def _build_dry_run_result(
        self, tests: list[tuple[TestCase, BreezeConfig]]
    ) -> SuiteResult:
        results = []
        for test, config in tests:
            results.append(TestResult(
                test_name=test.name,
                status="skipped",
                duration_ms=0,
                parameters=None,
            ))
        return SuiteResult(
            suite_name="dry-run",
            tests=results,
            total=len(results),
            skipped=len(results),
            timestamp=datetime.now(),
            browser=self.run_config.browser,
        )
