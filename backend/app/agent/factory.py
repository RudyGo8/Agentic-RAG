import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from app.tools.rag_tools import search_knowledge_base
from app.tools.weather_tools import get_current_weather

load_dotenv()

API_KEY = os.getenv("ARK_API_KEY")
MODEL = os.getenv("MODEL")
BASE_URL = os.getenv("BASE_URL")
AGENT_RECURSION_LIMIT = max(8, int(os.getenv("AGENT_RECURSION_LIMIT", "16")))


def create_agent_instance(tools: list | None = None):
    model = init_chat_model(
        model=MODEL,
        model_provider="openai",
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0.3,
        stream_usage=True,
    )

    selected_tools = tools if tools is not None else [
        get_current_weather,
        search_knowledge_base,
    ]

    agent = create_agent(
        model=model,
        tools=selected_tools,
        system_prompt=(
            "你是一个名为「知源」的 AI 助手，由 Rudy 开发。"
            "你的核心能力是基于企业知识库、上传文档和项目资料进行可溯源问答。"
            "当用户的问题涉及上传文档、项目知识、内部知识库、业务资料，"
            "或者需要基于证据回答时，必须优先调用 search_knowledge_base 工具。"
            "当用户只是打招呼、闲聊、简单推理、通用编程知识、概念解释，"
            "且不依赖知识库证据时，可以直接回答，不需要调用 search_knowledge_base。"
            "如果 search_knowledge_base 返回 TOOL_CALL_LIMIT_REACHED，"
            "或者没有检索到相关文档，不要重复调用该工具，"
            "应基于已有信息回答，并明确说明知识库中没有找到充分证据。"
            "当用户询问最新状态、变更、告警、外部实时信息时，"
            "可以调用可用的 MCP 只读工具获取信息。"
            "不要重复调用相同的 MCP 数据源，除非确实需要新的证据。"
            "当用户询问当前天气时，如果需要实时天气信息，可以调用 get_current_weather 工具。"
            "如果证据不足、知识库没有相关内容，或者工具返回结果有限，"
            "请用中文简要说明，只回答核心结论；如果证据不足，直接说明证据不足，不要编造。"
        ),
    )
    return agent, model


agent, model = create_agent_instance()


def get_agent(tools: list | None = None, extra_tools: list | None = None):
    agent, _ = create_agent_instance(tools=tools, extra_tools=extra_tools)
    return agent


def get_model():
    return model


def get_recursion_limit() -> int:
    return AGENT_RECURSION_LIMIT
