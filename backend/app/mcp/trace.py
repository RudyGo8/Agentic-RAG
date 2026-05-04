from datetime import datetime, timezone
import threading
from typing import Any

_TRACE_LOCK = threading.RLock()
_MCP_CALLS: list[dict[str, Any]] = []


def reset_mcp_trace() -> None:
    global _MCP_CALLS
    with _TRACE_LOCK:
        _MCP_CALLS = []


def append_mcp_trace(call: dict[str, Any]) -> None:
    with _TRACE_LOCK:
        _MCP_CALLS.append(call)


def get_mcp_trace(clear: bool = True) -> list[dict[str, Any]]:
    global _MCP_CALLS
    with _TRACE_LOCK:
        items = list(_MCP_CALLS)
        if clear:
            _MCP_CALLS = []
        return items


def new_mcp_call(
    *,
    server_name: str,
    tool_name: str,
    query: str,
    success: bool,
    duration_ms: int,
    result_summary: str,
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "source_type": "mcp",
        "server_name": server_name,
        "tool_name": tool_name,
        "query": query,
        "success": success,
        "duration_ms": duration_ms,
        "result_summary": result_summary,
        "error": error,
    }
