"""Plugin base class and registration interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from breezetest.actions.registry import ActionHandler
    from breezetest.core.hooks import HookManager


class BreezePlugin(Protocol):
    """Protocol for BreezeTest plugins."""

    def register(self, hooks: HookManager, register_action: "callable") -> None:
        """Register hooks and custom actions."""
        ...


def register_plugin(hooks: HookManager, plugin: BreezePlugin) -> None:
    from breezetest.actions.registry import register as action_register
    plugin.register(hooks, action_register)
