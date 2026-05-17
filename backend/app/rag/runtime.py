'''
@create_time: 2026/4/28 上午12:24
@Author: GeChao
@File: runtime.py
'''

import threading
from typing import Any, Optional

_STATE_LOCK = threading.RLock()
_LAST_RAG_CONTEXT: Optional[dict] = None
_KNOWLEDGE_TOOL_CALLS_THIS_TURN: int = 0
_RAG_STEP_QUEUE: Optional[Any] = None
_RAG_STEP_LOOP: Optional[Any] = None


def set_last_rag_context(context: dict):
    global _LAST_RAG_CONTEXT
    with _STATE_LOCK:
        _LAST_RAG_CONTEXT = context

# 上一轮rag对话的短期记忆管理
def get_last_rag_context(clear: bool = True) -> Optional[dict]:
    global _LAST_RAG_CONTEXT
    # 线程安全：确保在多线程环境中的读写操作是原子性的
    with _STATE_LOCK:
        context = _LAST_RAG_CONTEXT
        if clear:
            _LAST_RAG_CONTEXT = None
        return context

# 知识库调用计数+1
def increase_knowledge_tool_calls_this_turn():
    global _KNOWLEDGE_TOOL_CALLS_THIS_TURN
    with _STATE_LOCK:
        _KNOWLEDGE_TOOL_CALLS_THIS_TURN += 1

# 知识库调用次数
def get_knowledge_tool_call_this_turn() -> int:
    with _STATE_LOCK:
        return _KNOWLEDGE_TOOL_CALLS_THIS_TURN

# 重置工具调用
def reset_tool_call_guards():
    global _KNOWLEDGE_TOOL_CALLS_THIS_TURN
    with _STATE_LOCK:
        _KNOWLEDGE_TOOL_CALLS_THIS_TURN = 0

# 设置队列步骤
def set_rag_step_queue(queue):
    global _RAG_STEP_QUEUE, _RAG_STEP_LOOP
    with _STATE_LOCK:
        _RAG_STEP_QUEUE = queue
    if queue:
        import asyncio
        try:
            # 优先尝试获取当前正在运行的 asyncio 事件循环
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                # 默认事件循环
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None
        with _STATE_LOCK:
            # 获取到的事件循环保存到全局变量中
            _RAG_STEP_LOOP = loop
    else:
        with _STATE_LOCK:
            _RAG_STEP_LOOP = None


# 异步进度上报
def emit_rag_step(icon: str, label: str, detail: str = ""):
    with _STATE_LOCK:
        queue = _RAG_STEP_QUEUE
        loop = _RAG_STEP_LOOP
    if queue is not None and loop is not None:
        # 异步安全投递到队列
        step = {"icon": icon, "label": label, "detail": detail}
        try:
            if not loop.is_closed():
                loop.call_soon_threadsafe(queue.put_nowait, step)
        except Exception:
            pass
