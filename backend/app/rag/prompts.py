GRADE_PROMPT = (
    "你是一个文档相关性评估器。请判断检索到的文档与用户问题是否相关。\n"
    "检索到的文档：\n\n{context}\n\n"
    "用户问题：{question}\n"
    "如果文档包含与问题相关的关键词、实体、事实或语义内容，就判定为相关。\n"
    "只返回 JSON，对象中只包含一个字段 binary_score，取值只能是 yes 或 no。\n"
    "只要文档内容与问题主题存在明显关联，就倾向返回 yes。"
)


REWRITE_STRATEGY_PROMPT = """
你是一个 RAG 查询扩展策略选择器。

请根据用户问题选择最合适的查询扩展策略：

- step_back：问题包含具体名词、代号、日期、术语等细节，需要先抽象成更通用的问题
- hyde：问题较模糊、概念性较强，适合先生成一段假设性答案文档辅助检索
- complex：问题较复杂，需要综合 step_back 和 hyde

用户问题：
{question}

只返回 JSON：
{{
  "strategy": "step_back" | "hyde" | "complex"
}}
"""
