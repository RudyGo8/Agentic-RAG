'''
@create_time: 2026/1/27 下午3:58
@Author: GeChao
@File: graph.py
'''
from langgraph.graph import StateGraph, END
from app.rag.nodes.grade_node import grade_documents_node
from app.rag.nodes.retrieve_node import retrieve_initial, retrieve_expanded
from app.rag.nodes.rewrite_node import rewrite_question_node
from app.rag.state import RAGState

# RAG 工作流
def build_rag_graph():
    # 状态流定义
    graph = StateGraph(RAGState)
    # 节点
    graph.add_node("retrieve_initial", retrieve_initial)
    graph.add_node("grade_documents", grade_documents_node)
    graph.add_node("rewrite_question", rewrite_question_node)
    graph.add_node("retrieve_expanded", retrieve_expanded)
    # 入口节点
    graph.set_entry_point("retrieve_initial")
    # 边
    graph.add_edge("retrieve_initial", "grade_documents")
    graph.add_conditional_edges(
        "grade_documents",
        lambda state: state.get("route"),
        {
            "generate_answer": END,
            "rewrite_question": "rewrite_question",
        },
    )
    graph.add_edge("rewrite_question", "retrieve_expanded")
    graph.add_edge("retrieve_expanded", END)
    # 流程图编译成可运行对象
    return graph.compile()


rag_graph = build_rag_graph()


def run_rag_graph(question: str) -> dict:
    # 状态
    return rag_graph.invoke({
        "question": question,
        "query": question,
        "context": "",
        "docs": [],
        "route": None,
        "expansion_type": None,
        "expanded_query": None,
        "step_back_question": None,
        "step_back_answer": None,
        "hypothetical_doc": None,
        "rag_trace": None,
    })
