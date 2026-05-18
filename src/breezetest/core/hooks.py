"""Hook/plugin system for lifecycle events."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable


class HookManager:
    VALID_EVENTS = frozenset({
        "before_suite",
        "after_suite",
        "before_test",
        "after_test",
        "before_step",
        "after_step",
        "on_browser_launch",
        "on_context_create",
        "register_actions",
    })

    def __init__(self) -> None:
        self._hooks: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def register(self, event: str, handler: Callable[..., Any]) -> None:
        if event not in self.VALID_EVENTS:
            raise ValueError(f"Unknown hook event: '{event}'. Valid: {sorted(self.VALID_EVENTS)}")
        self._hooks[event].append(handler)

    async def trigger(self, event: str, **kwargs: Any) -> None:
        for handler in self._hooks.get(event, []):
            if asyncio.iscoroutinefunction(handler):
                await handler(**kwargs)
            else:
                handler(**kwargs)

    def has_hooks(self, event: str) -> bool:
        return bool(self._hooks.get(event))
