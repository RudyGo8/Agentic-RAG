import json
import re

from app.utils.log import get_logger
logger = get_logger(__name__)
from app.rag.llm import _get_default_model


def step_back_expand(query: str) -> dict:
    try:
        model = _get_default_model()
        prompt = f"""请根据用户问题生成一个更通用的退步问题（Step-back），以及对应的通用答案。
用户问题：{query}

请按以下 JSON 格式输出，只输出 JSON：
{{
  "step_back_question": "更通用的退步问题",
  "step_back_answer": "通用答案",
  "expanded_query": "可用于检索的扩展查询"
}}"""

        response = model.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            result = json.loads(match.group())
            return {
                "step_back_question": result.get("step_back_question", query),
                "step_back_answer": result.get("step_back_answer", ""),
                "expanded_query": result.get("expanded_query", query),
            }
    except Exception as exc:
        logger.warning("step_back_expand_failed error=%s", exc)

    return {
        "step_back_question": query,
        "step_back_answer": "",
        "expanded_query": query,
    }


def generate_hypothetical_document(query: str) -> str:
    try:
        model = _get_default_model()
        prompt = (
            "请生成一段用于 HyDE 检索的假设性文档内容。"
            f"这段文档应该回答以下问题：{query}。"
            "请直接输出文档内容，不要添加解释。"
        )
        response = model.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.warning("hyde_generate_failed error=%s", exc)
        return query
