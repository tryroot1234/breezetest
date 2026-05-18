"""Tests for reporting modules."""

import xml.etree.ElementTree as ET
from pathlib import Path

from breezetest.core.models import (
    Step,
    StepResult,
    SuiteResult,
    TestCase,
    TestResult,
)
from breezetest.reporting.junit_xml import JunitXmlReporter


class TestJunitXmlReporter:
    def test_generate_creates_file(self, tmp_path):
        result = SuiteResult(
            suite_name="test_suite",
            tests=[
                TestResult(
                    test_name="passing_test",
                    status="passed",
                    duration_ms=100,
                    steps=[],
                ),
                TestResult(
                    test_name="failing_test",
                    status="failed",
                    duration_ms=50,
                    error_message="Assertion failed",
                    steps=[
                        StepResult(
                            step=Step(action="click", selector="btn"),
                            status="failed",
                            duration_ms=50,
                            error_message="Element not found",
                        )
                    ],
                ),
            ],
            total=2,
            passed=1,
            failed=1,
            duration_ms=150,
        )

        reporter = JunitXmlReporter(tmp_path)
        path = reporter.generate(result)
        assert path.exists()

        tree = ET.parse(path)
        root = tree.getroot()
        assert root.tag == "testsuites"

        testsuite = root.find("testsuite")
        assert testsuite is not None
        assert testsuite.get("tests") == "2"
        assert testsuite.get("failures") == "1"

        testcases = testsuite.findall("testcase")
        assert len(testcases) == 2
        assert testcases[0].get("name") == "passing_test"
        assert testcases[1].get("name") == "failing_test"

        failure = testcases[1].find("failure")
        assert failure is not None

    def test_skipped_test(self, tmp_path):
        result = SuiteResult(
            suite_name="test",
            tests=[
                TestResult(test_name="skipped", status="skipped", duration_ms=0, steps=[])
            ],
            total=1,
            skipped=1,
        )
        reporter = JunitXmlReporter(tmp_path)
        path = reporter.generate(result)
        tree = ET.parse(path)
        skipped = tree.find(".//skipped")
        assert skipped is not None
