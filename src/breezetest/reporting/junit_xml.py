"""JUnit XML report generator for CI integration."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from breezetest.core.models import SuiteResult


class JunitXmlReporter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, suite_result: SuiteResult) -> Path:
        root = ET.Element("testsuites")
        testsuite = ET.SubElement(root, "testsuite")
        testsuite.set("name", suite_result.suite_name)
        testsuite.set("tests", str(suite_result.total))
        testsuite.set("failures", str(suite_result.failed))
        testsuite.set("errors", str(suite_result.error))
        testsuite.set("skipped", str(suite_result.skipped))
        testsuite.set("time", f"{suite_result.duration_ms / 1000:.3f}")

        if suite_result.base_url:
            properties = ET.SubElement(testsuite, "properties")
            prop = ET.SubElement(properties, "property")
            prop.set("name", "base_url")
            prop.set("value", suite_result.base_url)

        for test in suite_result.tests:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", test.test_name)
            classname = test.test_name.split(" [")[0].replace(" ", "_")
            testcase.set("classname", classname)
            testcase.set("time", f"{test.duration_ms / 1000:.3f}")

            if test.status == "failed":
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", test.error_message or "Test failed")
                if test.steps:
                    details = []
                    for step in test.steps:
                        if step.error_message:
                            details.append(
                                f"Step '{step.step.action}': {step.error_message}"
                            )
                    failure.text = "\n".join(details)
            elif test.status == "error":
                error = ET.SubElement(testcase, "error")
                error.set("message", test.error_message or "Test error")
            elif test.status == "skipped":
                ET.SubElement(testcase, "skipped")

            if test.steps:
                system_out = ET.SubElement(testcase, "system-out")
                lines = []
                for step in test.steps:
                    desc = step.step.description or step.step.action
                    lines.append(f"[{step.status}] {desc} ({step.duration_ms:.0f}ms)")
                    if step.error_message:
                        lines.append(f"  Error: {step.error_message}")
                system_out.text = "\n".join(lines)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        output_path = self.output_dir / "results.xml"
        tree.write(str(output_path), encoding="unicode", xml_declaration=True)
        return output_path
