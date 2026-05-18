"""Tests for Pydantic models."""

from breezetest.core.models import (
    BreezeConfig,
    RunConfig,
    Step,
    StepResult,
    SuiteResult,
    TestCase,
    TestResult,
    TestSuite,
)


class TestBreezeConfig:
    def test_defaults(self):
        config = BreezeConfig()
        assert config.browser == "chromium"
        assert config.headless is True
        assert config.timeout == 30000
        assert config.retries == 0

    def test_custom_values(self):
        config = BreezeConfig(
            base_url="https://test.com",
            browser="firefox",
            headless=False,
            timeout=10000,
        )
        assert config.base_url == "https://test.com"
        assert config.browser == "firefox"
        assert config.headless is False
        assert config.timeout == 10000


class TestStep:
    def test_minimal(self):
        step = Step(action="click", selector="button")
        assert step.action == "click"
        assert step.selector == "button"
        assert step.on_failure == "fail"

    def test_with_options(self):
        step = Step(action="click", selector="btn", options={"force": True})
        assert step.options["force"] is True


class TestTestCase:
    def test_minimal(self):
        test = TestCase(name="test1")
        assert test.name == "test1"
        assert test.skip is False
        assert test.tags == []


class TestSuiteResult:
    def test_counts(self):
        result = SuiteResult(
            suite_name="test",
            tests=[
                TestResult(test_name="t1", status="passed"),
                TestResult(test_name="t2", status="failed"),
                TestResult(test_name="t3", status="skipped"),
            ],
            total=3,
            passed=1,
            failed=1,
            skipped=1,
        )
        assert result.total == 3
        assert result.passed == 1
        assert result.failed == 1
        assert result.skipped == 1


class TestRunConfig:
    def test_defaults(self):
        config = RunConfig()
        assert config.browser == "chromium"
        assert config.headless is True
        assert config.workers == 1
        assert config.html is True
        assert config.junit is True
