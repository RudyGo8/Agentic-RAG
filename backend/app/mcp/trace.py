import threading
from typing import Any

_TRACE_LOCK = threading.RLock()
_MCP_CALLS: list[dict[str, Any]] = []


def reset_mcp_trace() -> None:
    global _MCP_CALLS
    with _TRACE_LOCK:
        _MCP_CALLS = []


def get_mcp_trace(clear: bool = True) -> list[dict[str, Any]]:
    global _MCP_CALLS
    with _TRACE_LOCK:
        items = list(_MCP_CALLS)
        if clear:
            _MCP_CALLS = []
        return items
