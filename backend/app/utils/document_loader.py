'''
@create_time: 2026/02/09
@Author: GeChao
@File: document_loader.py
'''
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.documents import Document


class DocumentLoader:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", "。", "！", "？", "，", "、", " ", ""],
        )

    @staticmethod
    def _build_chunk_id(filename: str, page_number: int, index: int) -> str:
        return f"{filename}::p{page_number}::{index}"

    @staticmethod
    def _build_parent_chunk_id(filename: str, page_number: int) -> str:
        return f"{filename}::p{page_number}::parent"

    def _load_legacy_doc(self, file_path: str, filename: str) -> list[dict]:
        """Extract text from old .doc (OLE2) format using olefile."""
        import olefile
        ole = olefile.OleFileIO(file_path)
        try:
            stream = ole.openstream('WordDocument')
            raw = stream.read()
        except Exception:
            # Try reading the main text stream
            try:
                stream = ole.openstream('1Table')
                raw = stream.read()
            except Exception:
                ole.close()
                raise Exception("无法解析 .doc 文件，建议转为 .docx 格式后上传")
        ole.close()

        # Extract readable text from binary (crude but effective for most docs)
        text = ''
        for byte in raw:
            ch = chr(byte) if 32 <= byte < 127 or byte in (10, 13) else ' '
            text += ch
        # Clean up whitespace
        import re
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        page_text = text.strip()

        if not page_text:
            raise Exception("无法从 .doc 文件中提取文本，建议转为 .docx 格式后上传")

        return self._build_documents(filename, file_path, "Word", {0: page_text})

    def _build_documents(self, filename: str, file_path: str, doc_type: str, pages: dict) -> list[dict]:
        """Build chunk documents from page dict {page_num: text}."""
        documents = []
        for page_number, page_text in pages.items():
            page_text = page_text.strip()
            if not page_text:
                continue
            parent_chunk_id = self._build_parent_chunk_id(filename, page_number)
            texts = self._splitter.split_text(page_text)
            for chunk_idx, text in enumerate(texts):
                if not text.strip():
                    continue
                documents.append({
                    "text": text.strip(),
                    "filename": filename,
                    "file_path": file_path,
                    "file_type": doc_type,
                    "page_number": page_number,
                    "chunk_id": self._build_chunk_id(filename, page_number, chunk_idx),
                    "parent_chunk_id": parent_chunk_id,
                    "root_chunk_id": parent_chunk_id,
                    "chunk_idx": chunk_idx,
                    "parent_text": page_text,
                    "chunk_level": 3,
                })
        return documents

    def load_document(self, file_path: str, filename: str) -> list[dict]:
        file_lower = filename.lower()

        if file_lower.endswith(".pdf"):
            doc_type = "PDF"
            loader = PyPDFLoader(file_path)
        elif file_lower.endswith(".docx"):
            doc_type = "Word"
            loader = Docx2txtLoader(file_path)
        elif file_lower.endswith(".doc"):
            doc_type = "Word"
            return self._load_legacy_doc(file_path, filename)
        elif file_lower.endswith((".xlsx", ".xls")):
            doc_type = "Excel"
            loader = UnstructuredExcelLoader(file_path)
        elif file_lower.endswith((".txt", ".log", ".text")):
            doc_type = "Text"
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_lower.endswith((".md", ".markdown")):
            doc_type = "Markdown"
            loader = UnstructuredMarkdownLoader(file_path)
        elif file_lower.endswith(".csv"):
            doc_type = "CSV"
            loader = CSVLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"不支持的文件类型: {filename}")

        try:
            raw_docs = loader.load()
            documents = []
            for idx, doc in enumerate(raw_docs):
                page_text = (doc.page_content or "").strip()
                if not page_text:
                    continue
                page_number = doc.metadata.get("page", idx)
                try:
                    page_number = int(page_number)
                except (TypeError, ValueError):
                    page_number = idx
                parent_chunk_id = self._build_parent_chunk_id(filename, page_number)
                texts = self._splitter.split_text(page_text)
                for chunk_idx, text in enumerate(texts):
                    if not text.strip():
                        continue
                    documents.append({
                        "text": text.strip(),
                        "filename": filename,
                        "file_path": file_path,
                        "file_type": doc_type,
                        "page_number": page_number,
                        "chunk_id": self._build_chunk_id(filename, page_number, chunk_idx),
                        "parent_chunk_id": parent_chunk_id,
                        "root_chunk_id": parent_chunk_id,
                        "chunk_idx": chunk_idx,
                        "parent_text": page_text,
                        "chunk_level": 3,
                    })
            return documents
        except Exception as e:
            raise Exception(f"处理文档失败: {str(e)}")


document_loader = DocumentLoader()
