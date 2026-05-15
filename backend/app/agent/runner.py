import asyncio
import json
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from app.agent.context import prepare_messages
from app.agent.factory import get_recursion_limit, create_agent_instance
from app.agent.trace import collect_rag_trace, extract_usage_from_message
import structlog
logger = structlog.get_logger(__name__)
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


# 补全trace
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

    # 完整消息
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
                # 工具调用块不直出给用户，只用于记录本轮到底调了哪些工具。
                if tool_call_chunks:
                    for chunk in tool_call_chunks:
                        tool_name = _extract_tool_name(chunk)
                        if tool_name:
                            trace_state["called_tools"].add(tool_name)
                    continue

                # 提取内容
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
                    # 推送到队列
                    full_response += content
                    await output_queue.put({"type": "content", "content": content})
        except Exception as e:
            await output_queue.put({"type": "error", "content": str(e)})
        finally:
            await output_queue.put(None)

    # 立即创建后台任务
    agent_task = asyncio.create_task(_agent_worker())

    try:
        while True:
            # 持续从生产者的输出队列中异步获取事件
            event = await output_queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    # 断开连接情况
    except GeneratorExit:
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass
        raise
    finally:
        # 清除rag步骤队列
        set_rag_step_queue(None)
        if not agent_task.done():
            agent_task.cancel()

    rag_trace = collect_rag_trace(stream_usage)
    # 用本地统计兜底补全 trace。
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

    # 标准 SSE 结束标记：前端通过监听[DONE]来判断流式响应
    yield "data: [DONE]\n\n"

    # 消息列表：历史会话+本轮用户问题+本轮AI回答
    persisted_messages = [*messages, HumanMessage(content=user_text), AIMessage(content=full_response)]
    # 最后一条AI回答附带trace
    extra_message_data = [None] * (len(persisted_messages) - 1) + [{"rag_trace": rag_trace}]
    storage.save(user_id, session_id, persisted_messages, extra_message_data=extra_message_data)
