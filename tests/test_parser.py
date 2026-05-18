"""Tests for the YAML parser."""

import pytest

from breezetest.core.models import BreezeConfig, Step, TestCase, TestSuite
from breezetest.core.parser import (
    expand_parameterized,
    parse_comparison,
    parse_suite,
    resolve_variables,
)


class TestParseSuite:
    def test_minimal_suite(self):
        data = {
            "tests": [
                {"name": "test1", "steps": [{"action": "goto", "value": "/"}]}
            ]
        }
        suite = parse_suite(data)
        assert len(suite.tests) == 1
        assert suite.tests[0].name == "test1"

    def test_suite_with_config(self):
        data = {
            "config": {
                "base_url": "https://example.com",
                "browser": "firefox",
                "headless": False,
            },
            "tests": [],
        }
        suite = parse_suite(data)
        assert suite.config.base_url == "https://example.com"
        assert suite.config.browser == "firefox"
        assert suite.config.headless is False

    def test_default_config(self):
        data = {"tests": []}
        suite = parse_suite(data)
        assert suite.config.browser == "chromium"
        assert suite.config.headless is True
        assert suite.config.timeout == 30000

    def test_missing_test_name_raises(self):
        data = {"tests": [{"steps": []}]}
        with pytest.raises(Exception):
            parse_suite(data)

    def test_missing_action_raises(self):
        data = {"tests": [{"name": "t", "steps": [{"value": "/"}]}]}
        with pytest.raises(Exception):
            parse_suite(data)

    def test_multiple_tests(self):
        data = {
            "tests": [
                {"name": "t1", "steps": [{"action": "goto", "value": "/"}]},
                {"name": "t2", "steps": [{"action": "click", "selector": "btn"}]},
            ]
        }
        suite = parse_suite(data)
        assert len(suite.tests) == 2
        assert suite.tests[0].name == "t1"
        assert suite.tests[1].name == "t2"

    def test_step_with_options(self):
        data = {
            "tests": [
                {
                    "name": "t",
                    "steps": [
                        {
                            "action": "click",
                            "selector": "btn",
                            "options": {"force": True, "timeout": 5000},
                        }
                    ],
                }
            ]
        }
        suite = parse_suite(data)
        step = suite.tests[0].steps[0]
        assert step.options["force"] is True
        assert step.options["timeout"] == 5000

    def test_tags(self):
        data = {
            "tests": [
                {
                    "name": "t",
                    "tags": ["smoke", "auth"],
                    "steps": [{"action": "goto", "value": "/"}],
                }
            ]
        }
        suite = parse_suite(data)
        assert suite.tests[0].tags == ["smoke", "auth"]

    def test_skip(self):
        data = {
            "tests": [
                {"name": "t", "skip": True, "steps": []}
            ]
        }
        suite = parse_suite(data)
        assert suite.tests[0].skip is True

    def test_data_driven_inline(self):
        data = {
            "tests": [
                {
                    "name": "search",
                    "data": [
                        {"query": "python"},
                        {"query": "testing"},
                    ],
                    "steps": [{"action": "goto", "value": "/search?q={{query}}"}],
                }
            ]
        }
        suite = parse_suite(data)
        test = suite.tests[0]
        assert test.data is not None
        assert len(test.data) == 2


class TestExpandParameterized:
    def test_no_data_returns_original(self):
        test = TestCase(name="t", steps=[Step(action="goto", value="/")])
        result = expand_parameterized(test)
        assert len(result) == 1
        assert result[0].name == "t"

    def test_inline_data_expands(self):
        test = TestCase(
            name="search",
            steps=[Step(action="goto", value="/")],
            data=[{"query": "a"}, {"query": "b"}],
        )
        result = expand_parameterized(test)
        assert len(result) == 2
        assert result[0].name == "search [query=a]"
        assert result[1].name == "search [query=b]"

    def test_expanded_tests_have_no_data(self):
        test = TestCase(
            name="t",
            steps=[],
            data=[{"x": "1"}],
        )
        result = expand_parameterized(test)
        assert result[0].data is None


class TestResolveVariables:
    def test_simple_replacement(self):
        assert resolve_variables("hello {{name}}", {"name": "world"}) == "hello world"

    def test_multiple_vars(self):
        result = resolve_variables("{{a}} and {{b}}", {"a": "1", "b": "2"})
        assert result == "1 and 2"

    def test_non_string_passthrough(self):
        assert resolve_variables(42, {}) == 42

    def test_missing_var_unchanged(self):
        assert resolve_variables("{{missing}}", {}) == "{{missing}}"


class TestParseComparison:
    def test_exact(self):
        op, val = parse_comparison("5")
        assert op == "eq"
        assert val == "5"

    def test_gte(self):
        op, val = parse_comparison(">=3")
        assert op == "gte"
        assert val == "3"

    def test_lt(self):
        op, val = parse_comparison("<10")
        assert op == "lt"
        assert val == "10"

    def test_ne(self):
        op, val = parse_comparison("!=0")
        assert op == "ne"
        assert val == "0"

    def test_gt(self):
        op, val = parse_comparison(">5")
        assert op == "gt"
        assert val == "5"
