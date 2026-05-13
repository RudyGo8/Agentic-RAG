import asyncio
import json
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from app.agent.context import prepare_messages
from app.agent.factory import get_recursion_limit, create_agent_instance
from app.agent.prompt import build_turn_prompt
from app.agent.trace import collect_rag_trace, extract_usage_from_message
from app.config import logger
from app.mcp import mcp_client_manager
from app.mcp.trace import reset_mcp_trace
from app.services.conversation_service import conversation_service as storage
from app.tools.runtime import get_last_rag_context, reset_tool_call_guards, set_rag_step_queue
from app.tools.registry import TOOL_REGISTRY


def _extract_tool_name(chunk) -> str | None:
    if isinstance(chunk, dict):
        name = chunk.get("name")
        return str(name).strip() if name else None
    name = getattr(chunk, "name", None)
    return str(name).strip() if name else None


def _backfill_trace(rag_trace: dict, called_tools: set[str], mcp_tool_names: set[str], rag_step_count: int) -> dict:
    if not isinstance(rag_trace, dict):
        rag_trace = {}

    if "tool_used" not in rag_trace:
        rag_trace["tool_used"] = bool(called_tools or rag_step_count > 0)
    if not rag_trace.get("tool_name"):
        if "search_knowledge_base" in called_tools:
            rag_trace["tool_name"] = "search_knowledge_base"
        elif called_tools:
            rag_trace["tool_name"] = sorted(called_tools)[0]
        elif rag_step_count > 0:
            rag_trace["tool_name"] = "search_knowledge_base"

    if "mcp_used" not in rag_trace:
        rag_trace["mcp_used"] = any(name in mcp_tool_names for name in called_tools)
    return rag_trace


async def chat_with_agent_stream(user_text: str, user_id: str = "default_user", session_id: str = "default_session"):
    # 清空上一次RAG检索缓存
    get_last_rag_context(clear=True)
    reset_tool_call_guards()
    reset_mcp_trace()
    # 从mysql数据库和redis加载该用户的历史消息
    messages = storage.load(user_id, session_id)
    messages = prepare_messages(messages)


    # Agent 的工具集合 = 本地工具 + 可选 MCP 工具。
    # mcp先不维护
    local_tools = [spec.tool for spec in TOOL_REGISTRY.values()]
    mcp_tools = await mcp_client_manager.get_agent_tools()
    mcp_tool_names = {
        str(getattr(tool, "name", "")).strip()
        for tool in mcp_tools
        if getattr(tool, "name", None)
    }
    candidate_tools = local_tools + mcp_tools



    agent, _ = create_agent_instance(tools=candidate_tools)

    # 异步队列
    output_queue = asyncio.Queue()
    trace_state = {
        "rag_step_count": 0,
        "called_tools": set(),
    }

    # 代理对象
    class _RagStepProxy:
        # RAG 节点里 emit 的步骤事件，通过这个代理转成前端 SSE 事件。
        def put_nowait(self, step):
            trace_state["rag_step_count"] += 1
            output_queue.put_nowait({"type": "rag_step", "step": step})

    set_rag_step_queue(_RagStepProxy())

    agent_messages = [*messages, HumanMessage(content=user_text.strip())]

    full_response = ""
    stream_usage = None

    async def _agent_worker():
        nonlocal full_response, stream_usage
        try:
            # LangChain 会持续产出 AIMessageChunk；这里拆成前端能消费的内容片段。
            async for msg, _metadata in agent.astream(
                    {"messages": agent_messages},
                    stream_mode="messages",
                    config={"recursion_limit": get_recursion_limit()},
            ):
                if not isinstance(msg, AIMessageChunk):
                    continue

                usage = extract_usage_from_message(msg)
                if usage:
                    stream_usage = usage

                tool_call_chunks = getattr(msg, "tool_call_chunks", None)
                if tool_call_chunks:
                    # 工具调用块不直出给用户，只用于记录本轮到底调了哪些工具。
                    for chunk in tool_call_chunks:
                        tool_name = _extract_tool_name(chunk)
                        if tool_name:
                            trace_state["called_tools"].add(tool_name)
                    continue

                content = ""
                if isinstance(msg.content, str):
                    content = msg.content
                elif isinstance(msg.content, list):
                    for block in msg.content:
                        if isinstance(block, str):
                            content += block
                        elif isinstance(block, dict) and block.get("type") == "text":
                            content += block.get("text", "")

                if content:
                    full_response += content
                    await output_queue.put({"type": "content", "content": content})
        except Exception as e:
            await output_queue.put({"type": "error", "content": str(e)})
        finally:
            await output_queue.put(None)

    agent_task = asyncio.create_task(_agent_worker())

    try:
        while True:
            event = await output_queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"
    except GeneratorExit:
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass
        raise
    finally:
        set_rag_step_queue(None)
        if not agent_task.done():
            agent_task.cancel()

    rag_trace = collect_rag_trace(stream_usage)
    # 某些模型返回的工具元数据不完整，这里用本地统计兜底补全 trace。
    rag_trace = _backfill_trace(
        rag_trace,
        called_tools=trace_state["called_tools"],
        mcp_tool_names=mcp_tool_names,
        rag_step_count=trace_state["rag_step_count"],
    )

    tool_used = bool(rag_trace.get("tool_used")) if isinstance(rag_trace, dict) else False
    tool_name = rag_trace.get("tool_name") if isinstance(rag_trace, dict) else None

    logger.info(
        "stream_chat_trace user_id=%s session_id=%s tool_used=%s tool_name=%s",
        user_id,
        session_id,
        tool_used,
        tool_name or "none",
    )

    if rag_trace:
        yield f"data: {json.dumps({'type': 'trace', 'rag_trace': rag_trace})}\n\n"

    yield "data: [DONE]\n\n"

    # 最终只持久化“用户原始问题 + AI 整体回答”，trace 挂在最后一条 AI 消息上。
    persisted_messages = [*messages, HumanMessage(content=user_text), AIMessage(content=full_response)]
    extra_message_data = [None] * (len(persisted_messages) - 1) + [{"rag_trace": rag_trace}]
    storage.save(user_id, session_id, persisted_messages, extra_message_data=extra_message_data)
