from app.rag.models import _get_router_model
from app.rag.prompts import REWRITE_STRATEGY_PROMPT
from app.rag.schema import RewriteStrategy
from app.rag.services import generate_hypothetical_document, step_back_expand
from app.rag.state import RAGState
from app.tools.runtime import emit_rag_step


def rewrite_question_node(state: RAGState) -> RAGState:
    question = state["question"]
    emit_rag_step("✍️", "正在重写查询...")
    router = _get_router_model()

    strategy = "step_back"
    if router:
        try:
            decision = router.with_structured_output(RewriteStrategy).invoke(
                [{"role": "user", "content": REWRITE_STRATEGY_PROMPT.format(question=question)}]
            )
            strategy = decision.strategy
        except Exception:
            strategy = "step_back"

    expanded_query = question
    step_back_question = ""
    step_back_answer = ""
    hypothetical_doc = ""

    if strategy in ("step_back", "complex"):
        emit_rag_step("🧭", f"使用策略: {strategy}", "生成退步问题")
        step_back = step_back_expand(question)
        step_back_question = step_back.get("step_back_question", "")
        step_back_answer = step_back.get("step_back_answer", "")
        expanded_query = step_back.get("expanded_query", question)

    if strategy in ("hyde", "complex"):
        emit_rag_step("📘", "HyDE 假设文档生成中...")
        hypothetical_doc = generate_hypothetical_document(question)

    rag_trace = state.get("rag_trace", {}) or {}
    rag_trace.update({
        "rewrite_strategy": strategy,
        "rewrite_query": expanded_query,
    })

    return {
        "expansion_type": strategy,
        "expanded_query": expanded_query,
        "step_back_question": step_back_question,
        "step_back_answer": step_back_answer,
        "hypothetical_doc": hypothetical_doc,
        "rag_trace": rag_trace,
    }
