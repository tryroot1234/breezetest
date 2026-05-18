"""Capture actions: screenshot, capture_text, capture_attribute."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from breezetest.actions.registry import register

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

    from breezetest.core.context import TestContext
    from breezetest.core.models import Step


@register("screenshot")
async def action_screenshot(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    name = ctx.resolve_variables(step.value) or "screenshot"
    report_dir = step.options.get("report_dir", "./breezetest-reports")
    screenshot_dir = Path(report_dir) / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / f"{name}.png"
    await page.screenshot(
        path=str(path),
        full_page=step.options.get("full_page", False),
    )
    ctx.screenshots.append(str(path))


@register("capture_text")
async def action_capture_text(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    variable = step.options.get("variable") or step.value
    text = await locator.text_content()
    ctx.set_variable(variable, text or "")


@register("capture_attribute")
async def action_capture_attribute(
    page: Page, locator: Locator, step: Step, ctx: TestContext
) -> None:
    variable = step.options.get("variable") or step.value
    attr = step.options.get("attribute", "href")
    value = await locator.get_attribute(attr)
    ctx.set_variable(variable, value or "")
