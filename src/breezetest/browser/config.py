"""Browser configuration model."""

from __future__ import annotations

from pydantic import BaseModel

from breezetest.core.models import ViewportConfig


class BrowserConfig(BaseModel):
    browser_type: str = "chromium"
    headless: bool = True
    viewport: ViewportConfig | None = None
    slow_mo: int = 0
    args: list[str] | None = None

    @classmethod
    def from_breeze_config(cls, config: "BreezeConfig") -> "BrowserConfig":
        return cls(
            browser_type=config.browser,
            headless=config.headless,
            viewport=config.viewport,
        )
