from app.utils.embedding_service import embedding_service
from app.utils.milvus_service import milvus_service
from app.utils.document_loader import document_loader
from app.utils.parent_chunk_store import parent_chunk_store
from app.utils.log import get_logger
logger = get_logger(__name__)


class MilvusWriter:
    def __init__(self):
        self.embedding_service = embedding_service
        self.milvus_service = milvus_service
        self.document_loader = document_loader

    def write_documents(self, file_path: str, filename: str) -> int:
        self.milvus_service.init_collection()

        # 解析文件并切成标准化 chunk 列表
        docs = self.document_loader.load_document(file_path, filename)
        if not docs:
            return 0

        # 父块单独保存，供检索阶段 auto-merge 回填完整上下文
        self._save_parent_chunks(docs)
        # 只对叶子块做向量化，Milvus 里存的是可检索的最小单元
        texts = [doc["text"] for doc in docs]
        dense_embeddings = self.embedding_service.get_embeddings(texts)
        sparse_embeddings = self.embedding_service.get_sparse_embeddings(texts)
        
        data = []
        for i, doc in enumerate(docs):
            data.append({
                # Milvus 的 text 字段上限是2000，这里做一次截断
                "text": doc["text"][:2000],
                "filename": doc["filename"],
                "file_type": doc["file_type"],
                "page_number": doc.get("page_number", 0),
                "chunk_id": doc.get("chunk_id", ""),
                "parent_chunk_id": doc.get("parent_chunk_id", ""),
                "chunk_level": doc.get("chunk_level", 3),
                "dense_embedding": dense_embeddings[i] if i < len(dense_embeddings) else [],
                "sparse_embedding": sparse_embeddings[i] if i < len(sparse_embeddings) else {},
            })

        # 叶子块+双向量一起写入 Milvus，供后续 hybrid search 使用
        self.milvus_service.insert(data)
        return len(docs)

    @staticmethod
    def _save_parent_chunks(docs: list[dict]) -> None:
        parent_payload: dict[str, dict] = {}
        for doc in docs:
            parent_id = (doc.get("parent_chunk_id") or "").strip()
            parent_text = (doc.get("parent_text") or "").strip()
            if not parent_id or not parent_text:
                continue
            if parent_id in parent_payload:
                continue

            # 同一页可能切出多个字块，这里只保留一份父块正文：“rag.pdf::p1::parent"
            parent_payload[parent_id] = {
                "text": parent_text,
                "metadata": {
                    "filename": doc.get("filename", ""),
                    "file_type": doc.get("file_type", ""),
                    "file_path": doc.get("file_path", ""),
                    "page_number": doc.get("page_number", 0),
                    "parent_chunk_id": "",
                    "root_chunk_id": parent_id,
                    "chunk_level": 1,
                    "chunk_idx": 0,
                },
            }

        for parent_id, payload in parent_payload.items():
            try:
                parent_chunk_store.save_chunk(parent_id, payload["text"], payload["metadata"])
            except Exception as exc:
                logger.warning("save_parent_chunk_failed chunk_id=%s err=%s", parent_id, exc)


milvus_writer = MilvusWriter()
