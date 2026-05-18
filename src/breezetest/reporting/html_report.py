"""Self-contained HTML report generator."""

from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader

if TYPE_CHECKING:
    from breezetest.core.models import SuiteResult


class HtmlReportGenerator:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._env = Environment(
            loader=PackageLoader("breezetest", "reporting/templates"),
            autoescape=True,
        )

    def generate(self, suite_result: SuiteResult) -> Path:
        template = self._env.get_template("report.html")

        # Prepare screenshot data
        for test in suite_result.tests:
            for step in test.steps:
                step_data = step
                if step.screenshot_path:
                    try:
                        with open(step.screenshot_path, "rb") as f:
                            step_data._b64_screenshot = base64.b64encode(f.read()).decode()
                    except (FileNotFoundError, OSError):
                        step_data._b64_screenshot = None

        html = template.render(
            suite=suite_result,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        output_path = self.output_dir / "report.html"
        output_path.write_text(html, encoding="utf-8")
        return output_path
