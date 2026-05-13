from collections import Counter

from app.config import AUTO_MERGE_ENABLED, AUTO_MERGE_THRESHOLD, LEAF_RETRIEVE_LEVEL, logger


def _parse_bool(value) -> bool:
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


AUTO_MERGE_ENABLED_VALUE = _parse_bool(AUTO_MERGE_ENABLED)
AUTO_MERGE_THRESHOLD_VALUE = int(AUTO_MERGE_THRESHOLD) if AUTO_MERGE_THRESHOLD else 2
LEAF_RETRIEVE_LEVEL_VALUE = int(LEAF_RETRIEVE_LEVEL) if LEAF_RETRIEVE_LEVEL else 3


def auto_merge_chunks(results: list[dict], top_k: int = 5):
    auto_merge_applied = False
    auto_merge_replaced_chunks = 0
    auto_merge_steps = 0

    if AUTO_MERGE_ENABLED_VALUE and results:
        try:
            from app.utils.parent_chunk_store import parent_chunk_store

            parent_counts = Counter(
                item.get("parent_chunk_id", "") for item in results if item.get("parent_chunk_id")
            )
            merged_results = []
            used_indices = set()

            for i, item in enumerate(results):
                if i in used_indices:
                    continue

                parent_id = item.get("parent_chunk_id", "")
                should_merge = (
                    parent_id
                    and parent_counts.get(parent_id, 0) >= AUTO_MERGE_THRESHOLD_VALUE
                )

                if should_merge:
                    parent_doc = parent_chunk_store.get_chunk(parent_id)
                    if parent_doc:
                        item["text"] = parent_doc.get("text", item.get("text", ""))
                        item["parent_retrieved"] = True
                        for j in range(i + 1, len(results)):
                            if results[j].get("parent_chunk_id") == parent_id:
                                used_indices.add(j)
                        auto_merge_applied = True
                        auto_merge_replaced_chunks += 1
                        auto_merge_steps = 1

                merged_results.append(item)

            results = merged_results
        except Exception as exc:
            logger.warning("auto_merge_failed error=%s", exc)

    results = results[:top_k]
    for index, item in enumerate(results):
        item["final_rank"] = index + 1

    meta = {
        "leaf_retrieve_level": LEAF_RETRIEVE_LEVEL_VALUE,
        "auto_merge_enabled": AUTO_MERGE_ENABLED_VALUE,
        "auto_merge_applied": auto_merge_applied,
        "auto_merge_threshold": AUTO_MERGE_THRESHOLD_VALUE,
        "auto_merge_replaced_chunks": auto_merge_replaced_chunks,
        "auto_merge_steps": auto_merge_steps,
    }
    return results, meta
