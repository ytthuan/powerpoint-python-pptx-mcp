"""Tool registry for decorator-based tool registration and dispatch.

This module provides a registry pattern for managing MCP tools, replacing
the large if/elif chain with a cleaner, more maintainable approach.
"""

import logging
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for MCP tools with decorator-based registration.

    This class provides a clean way to register and dispatch tool handlers
    without maintaining a large if/elif chain.

    Example:
        registry = ToolRegistry()

        @registry.register("read_notes")
        async def handle_read_notes(arguments: dict) -> dict:
            return {"content": "..."}

        # Dispatch a tool call
        result = await registry.dispatch("read_notes", {"path": "..."})
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {}

    def register(self, tool_name: str) -> Callable[
        [Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]],
        Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
    ]:
        """Decorator to register a tool handler.

        Args:
            tool_name: Name of the tool to register

        Returns:
            Decorator function

        Example:
            @registry.register("my_tool")
            async def handle_my_tool(arguments: dict) -> dict:
                return {"result": "success"}
        """

        def decorator(
            handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        ) -> Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]:
            if tool_name in self._handlers:
                logger.warning(f"Tool '{tool_name}' is already registered. Overwriting.")
            self._handlers[tool_name] = handler
            logger.debug(f"Registered tool: {tool_name}")
            return handler

        return decorator

    def register_handler(
        self, tool_name: str, handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> None:
        """Register a tool handler directly (non-decorator style).

        Args:
            tool_name: Name of the tool
            handler: Handler function for the tool

        Example:
            registry.register_handler("my_tool", handle_my_tool)
        """
        if tool_name in self._handlers:
            logger.warning(f"Tool '{tool_name}' is already registered. Overwriting.")
        self._handlers[tool_name] = handler
        logger.debug(f"Registered tool: {tool_name}")

    async def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a tool call to the appropriate handler.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Result from the tool handler

        Raises:
            ValueError: If the tool is not registered
        """
        handler = self._handlers.get(tool_name)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        logger.debug(f"Dispatching tool: {tool_name}")
        return await handler(arguments)

    def is_registered(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if the tool is registered, False otherwise
        """
        return tool_name in self._handlers

    def get_registered_tools(self) -> list[str]:
        """Get a list of all registered tool names.

        Returns:
            List of registered tool names
        """
        return list(self._handlers.keys())

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool.

        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self._handlers:
            del self._handlers[tool_name]
            logger.debug(f"Unregistered tool: {tool_name}")
        else:
            logger.warning(f"Attempted to unregister non-existent tool: {tool_name}")

    def clear(self) -> None:
        """Clear all registered tools."""
        self._handlers.clear()
        logger.debug("Cleared all registered tools")


# Global tool registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance.

    Returns:
        The global tool registry instance
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def reset_tool_registry() -> None:
    """Reset the global tool registry (useful for testing)."""
    global _tool_registry
    _tool_registry = None


def register_tool(tool_name: str):
    """Decorator to register a tool with the global registry.

    Args:
        tool_name: Name of the tool to register

    Returns:
        Decorator function

    Example:
        @register_tool("my_tool")
        async def handle_my_tool(arguments: dict) -> dict:
            return {"result": "success"}
    """
    registry = get_tool_registry()
    return registry.register(tool_name)
