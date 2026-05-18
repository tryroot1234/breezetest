"""Single test case executor - runs steps against a browser page."""

from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

from breezetest.actions.registry import get_action
from breezetest.core.context import TestContext
from breezetest.core.models import BreezeConfig, Step, StepResult, TestCase, TestResult

if TYPE_CHECKING:
    from playwright.async_api import Page

    from breezetest.browser.manager import BrowserManager
    from breezetest.core.hooks import HookManager


class TestExecutor:
    def __init__(
        self,
        browser_manager: BrowserManager,
        hook_manager: HookManager,
        screenshot_mode: str = "failure",
        report_dir: str = "./breezetest-reports",
    ) -> None:
        self.browser_manager = browser_manager
        self.hook_manager = hook_manager
        self.screenshot_mode = screenshot_mode
        self.report_dir = report_dir

    async def execute(
        self,
        test: TestCase,
        config: BreezeConfig,
        parameters: dict | None = None,
    ) -> TestResult:
        ctx = TestContext(config, test, parameters)
        step_results: list[StepResult] = []
        status = "passed"

        page = await self.browser_manager.new_page()
        ctx.page = page

        try:
            await self.hook_manager.trigger("before_test", test=test, context=ctx)
            ctx.start_timer()

            for step in test.steps:
                await self.hook_manager.trigger("before_step", step=step, context=ctx)
                result = await self._execute_step(page, step, ctx)
                step_results.append(result)
                await self.hook_manager.trigger("after_step", step=step, result=result, context=ctx)

                if result.status == "failed":
                    status = "failed"
                    if step.on_failure == "fail":
                        break
                    elif step.on_failure == "skip_next":
                        idx = test.steps.index(step)
                        for remaining in test.steps[idx + 1:]:
                            step_results.append(StepResult(
                                step=remaining,
                                status="skipped",
                                duration_ms=0,
                            ))
                        break
                elif result.status == "error":
                    status = "error"
                    break

        except Exception as e:
            status = "error"
            screenshot_path = await self._take_screenshot(page, ctx, f"error_{test.name}")
            step_results.append(StepResult(
                step=Step(action="error", value=str(e)),
                status="error",
                duration_ms=0,
                screenshot_path=screenshot_path,
                error_message=f"{e}\n{traceback.format_exc()}",
            ))
        finally:
            try:
                await self.hook_manager.trigger(
                    "after_test", test=test, context=ctx, status=status
                )
            except Exception:
                pass
            await page.close()

        total_ms = ctx.elapsed_ms()
        return TestResult(
            test_name=test.name,
            status=status,
            duration_ms=total_ms,
            steps=step_results,
            screenshots=ctx.screenshots,
            parameters=parameters,
        )

    async def _execute_step(self, page: Page, step: Step, ctx: TestContext) -> StepResult:
        start = time.monotonic()
        try:
            handler = get_action(step.action)
            locator = None
            if step.selector:
                selector = ctx.resolve_variables(step.selector)
                locator = page.locator(selector)

            await handler(page, locator, step, ctx)

            # Screenshot on success if mode is "always"
            screenshot_path = None
            if self.screenshot_mode == "always":
                screenshot_path = await self._take_screenshot(page, ctx, step.action)

            return StepResult(
                step=step,
                status="passed",
                duration_ms=(time.monotonic() - start) * 1000,
                screenshot_path=screenshot_path,
            )
        except Exception as e:
            screenshot_path = None
            if self.screenshot_mode in ("always", "failure"):
                screenshot_path = await self._take_screenshot(page, ctx, f"fail_{step.action}")

            return StepResult(
                step=step,
                status="failed",
                duration_ms=(time.monotonic() - start) * 1000,
                screenshot_path=screenshot_path,
                error_message=str(e),
            )

    async def _take_screenshot(self, page: Page, ctx: TestContext, name: str) -> str | None:
        try:
            screenshot_dir = Path(self.report_dir) / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
            path = screenshot_dir / f"{safe_name}_{int(time.time())}.png"
            await page.screenshot(path=str(path), full_page=False)
            ctx.screenshots.append(str(path))
            return str(path)
        except Exception:
            return None
