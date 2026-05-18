"""Assertion actions: assert_visible, assert_text, assert_count, etc."""

from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.async_api import expect

from breezetest.actions.registry import register
from breezetest.core.parser import parse_comparison

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

    from breezetest.core.context import TestContext
    from breezetest.core.models import Step


@register("assert_visible")
async def action_assert_visible(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    await expect(locator).to_be_visible(timeout=step.options.get("timeout", ctx.config.timeout))


@register("assert_hidden")
async def action_assert_hidden(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    await expect(locator).to_be_hidden(timeout=step.options.get("timeout", ctx.config.timeout))


@register("assert_text")
async def action_assert_text(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    expected = ctx.resolve_variables(step.value)
    timeout = step.options.get("timeout", ctx.config.timeout)
    if step.options.get("exact", False):
        await expect(locator).to_have_text(expected, timeout=timeout)
    else:
        await expect(locator).to_contain_text(expected, timeout=timeout)


@register("assert_value")
async def action_assert_value(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    expected = ctx.resolve_variables(step.value)
    await expect(locator).to_have_value(
        expected, timeout=step.options.get("timeout", ctx.config.timeout)
    )


@register("assert_attribute")
async def action_assert_attribute(
    page: Page, locator: Locator, step: Step, ctx: TestContext
) -> None:
    attr = step.options.get("attribute", "href")
    expected = ctx.resolve_variables(step.value)
    await expect(locator).to_have_attribute(
        attr, expected, timeout=step.options.get("timeout", ctx.config.timeout)
    )


@register("assert_count")
async def action_assert_count(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    raw = str(step.value)
    op, val = parse_comparison(raw)
    count = int(val)
    timeout = step.options.get("timeout", ctx.config.timeout)

    if op == "eq":
        await expect(locator).to_have_count(count, timeout=timeout)
    elif op == "gte":
        await expect(locator).to_have_count(
            lambda n, c=count: n >= c, timeout=timeout
        )
    elif op == "lte":
        await expect(locator).to_have_count(
            lambda n, c=count: n <= c, timeout=timeout
        )
    elif op == "gt":
        await expect(locator).to_have_count(
            lambda n, c=count: n > c, timeout=timeout
        )
    elif op == "lt":
        await expect(locator).to_have_count(
            lambda n, c=count: n < c, timeout=timeout
        )
    elif op == "ne":
        await expect(locator).to_have_count(
            lambda n, c=count: n != c, timeout=timeout
        )


@register("assert_url")
async def action_assert_url(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    expected = ctx.resolve_variables(step.value)
    if step.options.get("exact", False):
        await expect(page).to_have_url(expected, timeout=step.options.get("timeout", ctx.config.timeout))
    else:
        await expect(page).to_have_url(
            f"*{expected}*",
            timeout=step.options.get("timeout", ctx.config.timeout),
        )


@register("assert_title")
async def action_assert_title(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    expected = ctx.resolve_variables(step.value)
    await expect(page).to_have_title(
        expected, timeout=step.options.get("timeout", ctx.config.timeout)
    )


@register("assert_enabled")
async def action_assert_enabled(page: Page, locator: Locator, step: Step, ctx: TestContext) -> None:
    await expect(locator).to_be_enabled(timeout=step.options.get("timeout", ctx.config.timeout))


@register("assert_disabled")
async def action_assert_disabled(
    page: Page, locator: Locator, step: Step, ctx: TestContext
) -> None:
    await expect(locator).to_be_disabled(timeout=step.options.get("timeout", ctx.config.timeout))


@register("assert_checked")
async def action_assert_checked(
    page: Page, locator: Locator, step: Step, ctx: TestContext
) -> None:
    await expect(locator).to_be_checked(timeout=step.options.get("timeout", ctx.config.timeout))
