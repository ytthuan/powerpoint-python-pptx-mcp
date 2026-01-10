"""Tests for tool registry."""

import pytest
from mcp_server.tools.registry import (
    ToolRegistry,
    get_tool_registry,
    reset_tool_registry,
    register_tool,
)


@pytest.fixture
def registry():
    """Create a fresh tool registry for testing."""
    return ToolRegistry()


@pytest.fixture(autouse=True)
def cleanup_global_registry():
    """Clean up global registry after each test."""
    yield
    reset_tool_registry()


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    @pytest.mark.asyncio
    async def test_register_and_dispatch(self, registry):
        """Test basic tool registration and dispatch."""

        @registry.register("test_tool")
        async def handler(arguments):
            return {"result": "success", "args": arguments}

        result = await registry.dispatch("test_tool", {"key": "value"})
        assert result == {"result": "success", "args": {"key": "value"}}

    @pytest.mark.asyncio
    async def test_register_handler_method(self, registry):
        """Test registering handler with register_handler method."""

        async def handler(arguments):
            return {"result": "ok"}

        registry.register_handler("my_tool", handler)
        result = await registry.dispatch("my_tool", {})
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_dispatch_unknown_tool(self, registry):
        """Test dispatching to unknown tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool: nonexistent"):
            await registry.dispatch("nonexistent", {})

    def test_is_registered(self, registry):
        """Test checking if tool is registered."""

        @registry.register("test_tool")
        async def handler(arguments):
            return {}

        assert registry.is_registered("test_tool")
        assert not registry.is_registered("other_tool")

    def test_get_registered_tools(self, registry):
        """Test getting list of registered tools."""

        @registry.register("tool1")
        async def handler1(arguments):
            return {}

        @registry.register("tool2")
        async def handler2(arguments):
            return {}

        tools = registry.get_registered_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools

    def test_unregister(self, registry):
        """Test unregistering a tool."""

        @registry.register("test_tool")
        async def handler(arguments):
            return {}

        assert registry.is_registered("test_tool")

        registry.unregister("test_tool")
        assert not registry.is_registered("test_tool")

    def test_unregister_nonexistent(self, registry):
        """Test unregistering nonexistent tool doesn't raise error."""
        # Should not raise
        registry.unregister("nonexistent")

    def test_clear(self, registry):
        """Test clearing all registered tools."""

        @registry.register("tool1")
        async def handler1(arguments):
            return {}

        @registry.register("tool2")
        async def handler2(arguments):
            return {}

        assert len(registry.get_registered_tools()) == 2

        registry.clear()
        assert len(registry.get_registered_tools()) == 0

    def test_overwrite_warning(self, registry, caplog):
        """Test that overwriting a tool logs a warning."""

        @registry.register("test_tool")
        async def handler1(arguments):
            return {"version": 1}

        @registry.register("test_tool")
        async def handler2(arguments):
            return {"version": 2}

        assert "already registered" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_multiple_tools(self, registry):
        """Test registering and calling multiple tools."""

        @registry.register("add")
        async def add_handler(arguments):
            return {"result": arguments["a"] + arguments["b"]}

        @registry.register("multiply")
        async def multiply_handler(arguments):
            return {"result": arguments["a"] * arguments["b"]}

        result1 = await registry.dispatch("add", {"a": 2, "b": 3})
        assert result1 == {"result": 5}

        result2 = await registry.dispatch("multiply", {"a": 2, "b": 3})
        assert result2 == {"result": 6}


class TestGlobalRegistry:
    """Tests for global tool registry functions."""

    def test_get_tool_registry_singleton(self):
        """Test that get_tool_registry returns same instance."""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        assert registry1 is registry2

    def test_reset_tool_registry(self):
        """Test resetting global registry."""
        registry1 = get_tool_registry()
        reset_tool_registry()
        registry2 = get_tool_registry()
        assert registry1 is not registry2

    @pytest.mark.asyncio
    async def test_register_tool_decorator(self):
        """Test register_tool decorator with global registry."""

        @register_tool("global_test_tool")
        async def handler(arguments):
            return {"result": "from_global"}

        registry = get_tool_registry()
        assert registry.is_registered("global_test_tool")

        result = await registry.dispatch("global_test_tool", {})
        assert result == {"result": "from_global"}
