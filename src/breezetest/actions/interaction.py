"""Interaction actions: click, fill, select, check, hover, press_key, drag_to, scroll_to."""

from __future__ import annotations

from typing import TYPE_CHECKING

from breezetest.actions.registry import register

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

    from breezetest.core.context import TestContext
    from breezetest.core.models import Step


@register("click")
async def action_click(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    opts = step.options
    if opts.get("double_click"):
        await locator.dblclick(
            button=opts.get("button", "left"),
            force=opts.get("force", False),
            timeout=opts.get("timeout", ctx.config.timeout),
        )
    else:
        await locator.click(
            button=opts.get("button", "left"),
            force=opts.get("force", False),
            timeout=opts.get("timeout", ctx.config.timeout),
        )


@register("fill")
async def action_fill(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    value = ctx.resolve_variables(step.value)
    if step.options.get("clear", True):
        await locator.fill("")
    await locator.fill(
        value,
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("type")
async def action_type(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    value = ctx.resolve_variables(step.value)
    await locator.type(
        value,
        delay=step.options.get("delay", 0),
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("select")
async def action_select(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    value = ctx.resolve_variables(step.value)
    await locator.select_option(
        value,
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("check")
async def action_check(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    await locator.check(
        force=step.options.get("force", False),
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("uncheck")
async def action_uncheck(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    await locator.uncheck(
        force=step.options.get("force", False),
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("hover")
async def action_hover(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    await locator.hover(
        force=step.options.get("force", False),
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("press_key")
async def action_press_key(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    key = ctx.resolve_variables(step.value)
    if step.selector:
        await locator.press(key, timeout=step.options.get("timeout", ctx.config.timeout))
    else:
        await page.keyboard.press(key)


@register("drag_to")
async def action_drag_to(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    target_selector = ctx.resolve_variables(step.value)
    target = page.locator(target_selector)
    await locator.drag_to(
        target,
        timeout=step.options.get("timeout", ctx.config.timeout),
    )


@register("scroll_to")
async def action_scroll_to(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    await locator.scroll_into_view_if_needed(
        timeout=step.options.get("timeout", ctx.config.timeout),
    )
