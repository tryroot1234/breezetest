"""Action registry - maps YAML action names to handler functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

    from breezetest.core.context import TestContext
    from breezetest.core.models import Step

ActionHandler = Callable[["Page", "Locator | None", "Step", "TestContext"], Any]

_REGISTRY: dict[str, ActionHandler] = {}


class UnknownActionError(Exception):
    pass


def register(name: str) -> Callable[[ActionHandler], ActionHandler]:
    def decorator(fn: ActionHandler) -> ActionHandler:
        _REGISTRY[name] = fn
        return fn
    return decorator


def get_action(name: str) -> ActionHandler:
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise UnknownActionError(
            f"Unknown action: '{name}'. Available: {available}"
        )
    return _REGISTRY[name]


def list_actions() -> list[str]:
    return sorted(_REGISTRY.keys())
