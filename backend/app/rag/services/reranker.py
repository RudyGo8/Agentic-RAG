import os

import requests
from dotenv import load_dotenv

from app.config import logger

load_dotenv()


def rerank_documents(query: str, docs: list[dict], max_docs: int = 10):
    rerank_api_key = os.getenv("RERANK_API_KEY")
    rerank_model_name = os.getenv("RERANK_MODEL")
    rerank_host = os.getenv("RERANK_BINDING_HOST")

    results = docs or []
    meta = {
        "rerank_enabled": False,
        "rerank_applied": False,
        "rerank_model": None,
        "rerank_endpoint": None,
        "rerank_error": None,
    }

    if not (rerank_api_key and rerank_model_name and rerank_host and results):
        return results, meta

    meta["rerank_enabled"] = True
    try:
        rerank_limit = min(max_docs, len(results))
        rerank_docs = [item.get("text", "")[:1000] for item in results[:rerank_limit]]
        response = requests.post(
            rerank_host,
            headers={
                "Authorization": f"Bearer {rerank_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": rerank_model_name,
                "query": query,
                "documents": rerank_docs,
            },
            timeout=30,
        )
        response.raise_for_status()
        reranked = response.json().get("results", [])

        if reranked:
            scores = {item["index"]: item["relevance_score"] for item in reranked}
            for idx, item in enumerate(results[:rerank_limit]):
                item["rerank_score"] = scores.get(idx, 0.0)

            reranked_head = sorted(
                results[:rerank_limit],
                key=lambda item: item.get("rerank_score", 0.0),
                reverse=True,
            )
            results = reranked_head + results[rerank_limit:]
            meta["rerank_applied"] = True
            meta["rerank_model"] = rerank_model_name
            meta["rerank_endpoint"] = rerank_host
    except Exception as exc:
        meta["rerank_error"] = str(exc)
        logger.warning("rerank_failed error=%s", exc)

    return results, meta
