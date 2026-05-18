"""Navigation actions: goto, go_back, reload."""

from __future__ import annotations

from typing import TYPE_CHECKING

from breezetest.actions.registry import register

if TYPE_CHECKING:
    from playwright.async_api import Page

    from breezetest.core.context import TestContext
    from breezetest.core.models import Step


@register("goto")
async def action_goto(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    url = ctx.resolve_variables(step.value)
    if url and not url.startswith(("http://", "https://")):
        base = ctx.config.base_url or ""
        url = base.rstrip("/") + "/" + url.lstrip("/")
    await page.goto(
        url,
        wait_until=step.options.get("wait_until", "load"),
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("go_back")
async def action_go_back(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    await page.go_back(
        wait_until=step.options.get("wait_until", "load"),
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("reload")
async def action_reload(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    await page.reload(
        wait_until=step.options.get("wait_until", "load"),
        timeout=step.options.get("timeout", ctx.config.timeout),
    )
