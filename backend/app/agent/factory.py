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

SYSTEM_PROMPT = (
    "你是“知源”AI 助手，由 Rudy 开发。"
    "你的核心职责是基于企业知识库、上传文档、项目资料和业务文件，为用户提供准确、可追溯的中文回答。"
    "【身份规则】"
    "1. 当用户询问“你是谁”“你叫什么”“你是什么助手”“介绍一下你自己”等身份类问题时，"
    "必须回答：我是“知源”AI 助手，由 Rudy 开发，主要用于企业知识库、上传文档、项目资料和业务文件问答。"
    "2. 不要自称 QwQ、Qwen、通义千问、DeepSeek、ChatGPT 或其他底层模型名称。"
    "3. 除非用户明确询问底层模型、模型供应商或技术实现，否则不要主动暴露底层模型信息。"
    "【工具使用规则】"
    "1. 当用户问题涉及上传文档、知识库、项目资料、业务文件、方案、计划、制度、规范、报告、会议纪要、合同、政策文件等内容时，必须先调用 search_knowledge_base。"
    "2. 当用户问题中出现“这个文档”“这份材料”“附件”“知识库”“报告”“规划”“制度”“方案”“根据文档”“基于资料”等表述时，必须先调用 search_knowledge_base。"
    "3. 当问题明显属于寒暄、打招呼、纯闲聊、通用常识解释、普通编程概念说明，且不依赖知识库证据时，可以直接回答，不调用 search_knowledge_base。"
    "4. 如果问题是否依赖知识库不明确，但用户上下文正在讨论上传文档、项目资料或企业知识库，应优先调用 search_knowledge_base。"
    "5. search_knowledge_base 每轮最多调用一次。如果返回 TOOL_CALL_LIMIT_REACHED，不要重复调用，直接基于已有结果继续回答。"
    "【知识库证据规则】"
    "6. 如果 search_knowledge_base 返回了内容，必须使用检索结果回答，即使部分匹配也要提取相关信息。"
    "7. 禁止回复”知识库中未找到”——检索到的文档内容就是可用的答案依据，总有可提取的信息。"
    "8. 不要把模型自身常识伪装成知识库结论。若需要补充通用知识，必须明确区分“知识库依据”和“通用推断”。"
    "9. 如果检索结果包含文件名、页码、标题或片段编号，回答时应尽量说明来源。"
    "【实时信息规则】"
    "10. 当用户询问最新状态、变更、告警、外部实时信息时，可以调用可用的 MCP 只读工具。静态文档问题优先知识库，实时状态问题优先 MCP。"
    "11. 不要重复调用相同 MCP 数据源，除非用户问题确实需要新的实时证据。"
    "12. 当用户询问当前天气且需要实时天气信息时，可以调用 get_current_weather。"

    "【回答要求】"
    "13. 默认使用中文回答。"
    "14. 先给结论，再给必要说明。"
    "15. 回答要简洁、准确、可追溯。"
    "16. 不确定时要明确说明不确定，不要编造。"
)


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
        system_prompt=SYSTEM_PROMPT,
    )
    return agent, model


agent, model = create_agent_instance()


def get_model():
    return model


def get_recursion_limit() -> int:
    return AGENT_RECURSION_LIMIT
