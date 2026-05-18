"""Script actions: evaluate JavaScript."""

from __future__ import annotations

from typing import TYPE_CHECKING

from breezetest.actions.registry import register

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

    from breezetest.core.context import TestContext
    from breezetest.core.models import Step


@register("evaluate")
async def action_evaluate(page: Page, locator: None, step: Step, ctx: TestContext) -> None:
    expression = ctx.resolve_variables(step.value)
    result = await page.evaluate(expression)
    variable = step.options.get("variable")
    if variable:
        ctx.set_variable(variable, result)
