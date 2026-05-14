'''
@create_time: 2026/4/28 上午12:16
@Author: GeChao
@File: rag_tools.py
'''

from langchain_core.tools import tool

from app.rag.formatter import format_docs
from app.tools.runtime import (
    get_knowledge_tool_call_this_turn,
    increase_knowledge_tool_calls_this_turn,
    set_last_rag_context)


@tool("search_knowledge_base")
def search_knowledge_base(query: str) -> str:
    """知识库检索."""
    calls_this_turn = get_knowledge_tool_call_this_turn()
    if calls_this_turn >= 1:
        return (
            "本轮已经调用过知识库了 "
            "请基于已有结果直接回答"
        )

    increase_knowledge_tool_calls_this_turn()

    from app.rag import run_rag_graph

    rag_result = run_rag_graph(query)

    docs = rag_result.get("docs", []) if isinstance(rag_result, dict) else []
    rag_trace = rag_result.get("rag_trace", {}) if isinstance(rag_result, dict) else {}
    if rag_trace:
        set_last_rag_context({"rag_trace": rag_trace})

    if not docs:
        return "没有找到相关文档"

    formatted = format_docs(docs)
    return "检索块:\n" + "\n\n---\n\n".join(formatted)
