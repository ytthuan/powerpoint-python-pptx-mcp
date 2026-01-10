"""Asynchronous utilities for MCP server."""

import asyncio
from typing import Any, Callable, TypeVar

T = TypeVar("T")


async def run_in_thread(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a blocking function in a separate thread to avoid blocking the event loop.

    This is a wrapper around asyncio.to_thread for compatibility and ease of use.
    """
    return await asyncio.to_thread(func, *args, **kwargs)
