"""Wait actions: wait_for_selector, wait_for_url, wait_for_text, wait_for_timeout, wait_for_load."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from breezetest.actions.registry import register

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

    from breezetest.core.context import TestContext
    from breezetest.core.models import Step


@register("wait_for_selector")
async def action_wait_for_selector(
    page: Page, locator: None, step: Step, ctx: TestContext
) -> None:
    selector = ctx.resolve_variables(step.selector)
    await page.wait_for_selector(
        selector,
        state=step.options.get("state", "visible"),
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("wait_for_url")
async def action_wait_for_url(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    url = ctx.resolve_variables(step.value)
    await page.wait_for_url(
        f"*{url}*",
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("wait_for_text")
async def action_wait_for_text(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    text = ctx.resolve_variables(step.value)
    timeout = step.options.get("timeout", ctx.config.timeout)
    await locator.wait_for(
        state="visible",
        timeout=timeout,
    )
    await page.wait_for_function(
        f"el => el.textContent && el.textContent.includes('{text}')",
        locator,
        timeout=timeout,
    )


@register("wait_for_timeout")
async def action_wait_for_timeout(
    page: Page, locator: None, step: Step, ctx: TestContext
) -> None:
    ms = int(step.value)
    await asyncio.sleep(ms / 1000)


@register("wait_for_load")
async def action_wait_for_load(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    state = step.options.get("state", "load")
    await page.wait_for_load_state(state, timeout=step.options.get("timeout", ctx.config.timeout))
