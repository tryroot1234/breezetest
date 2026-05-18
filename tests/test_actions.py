"""Tests for the action registry."""

import pytest

from breezetest.actions.registry import (
    UnknownActionError,
    get_action,
    list_actions,
    register,
)


class TestRegistry:
    def test_register_and_get(self):
        @register("_test_action")
        async def my_action(page, locator, step, ctx):
            pass

        handler = get_action("_test_action")
        assert handler is my_action

    def test_unknown_action_raises(self):
        with pytest.raises(UnknownActionError, match="Unknown action"):
            get_action("nonexistent_action_xyz")

    def test_list_actions(self):
        actions = list_actions()
        assert isinstance(actions, list)
        # Should have our built-in actions
        assert "goto" in actions
        assert "click" in actions
        assert "fill" in actions
        assert "assert_visible" in actions
        assert "screenshot" in actions
        assert "evaluate" in actions

    def test_navigation_actions_registered(self):
        actions = list_actions()
        for name in ["goto", "go_back", "reload"]:
            assert name in actions

    def test_interaction_actions_registered(self):
        actions = list_actions()
        for name in ["click", "fill", "type", "select", "check", "uncheck", "hover", "press_key"]:
            assert name in actions

    def test_assertion_actions_registered(self):
        actions = list_actions()
        for name in [
            "assert_visible", "assert_hidden", "assert_text",
            "assert_value", "assert_count", "assert_url",
            "assert_title", "assert_enabled", "assert_disabled",
        ]:
            assert name in actions

    def test_wait_actions_registered(self):
        actions = list_actions()
        for name in ["wait_for_selector", "wait_for_url", "wait_for_text", "wait_for_timeout"]:
            assert name in actions

    def test_capture_actions_registered(self):
        actions = list_actions()
        for name in ["screenshot", "capture_text", "capture_attribute"]:
            assert name in actions
