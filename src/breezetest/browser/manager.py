"""Browser lifecycle manager using Playwright async API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from playwright.async_api import async_playwright

from breezetest.browser.config import BrowserConfig

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page


class BrowserManager:
    def __init__(self, config: BrowserConfig | None = None) -> None:
        self.config = config or BrowserConfig()
        self._playwright = None
        self._browser: Browser | None = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        browser_type = self.config.browser_type
        launcher = getattr(self._playwright, browser_type)
        launch_opts: dict = {"headless": self.config.headless}
        if self.config.slow_mo:
            launch_opts["slow_mo"] = self.config.slow_mo
        if self.config.args:
            launch_opts["args"] = self.config.args
        self._browser = await launcher.launch(**launch_opts)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def new_page(self) -> Page:
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")
        ctx_opts: dict = {}
        if self.config.viewport:
            ctx_opts["viewport"] = {
                "width": self.config.viewport.width,
                "height": self.config.viewport.height,
            }
        context = await self._browser.new_context(**ctx_opts)
        page = await context.new_page()
        return page

    async def __aenter__(self) -> BrowserManager:
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.stop()
