"""
Document parsing and chunking for uploaded RAG files.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
)


class DocumentLoader:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        # Prefer paragraph/newline/punctuation boundaries before falling back to length-based splits.
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
            separators=["\n\n", "\n", "。", "，", "；", "：", "、", " ", ""],
        )

    @staticmethod
    def _build_chunk_id(filename: str, page_number: int, index: int) -> str:
        return f"{filename}::p{page_number}::{index}"

    @staticmethod
    def _build_parent_chunk_id(filename: str, page_number: int) -> str:
        return f"{filename}::p{page_number}::parent"

    def _load_legacy_doc(self, file_path: str, filename: str) -> list[dict]:
        """Extract text from old .doc (OLE2) files."""
        import olefile
        import re

        ole = olefile.OleFileIO(file_path)
        try:
            try:
                stream = ole.openstream("WordDocument")
                raw = stream.read()
            except Exception:
                # Fallback for some old Word documents that store content in a different stream.
                stream = ole.openstream("1Table")
                raw = stream.read()
        except Exception as exc:
            raise Exception("Unable to parse .doc file. Convert it to .docx and try again.") from exc
        finally:
            ole.close()

        # Best-effort extraction of readable text from binary Word content.
        text = ""
        for byte in raw:
            ch = chr(byte) if 32 <= byte < 127 or byte in (10, 13) else " "
            text += ch

        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        page_text = text.strip()

        if not page_text:
            raise Exception("No readable text could be extracted from the .doc file.")

        return self._build_documents(filename, file_path, "Word", {0: page_text})

    def _build_documents(
        self, filename: str, file_path: str, doc_type: str, pages: dict
    ) -> list[dict]:
        """Turn page/unit text into leaf chunks with parent chunk metadata."""
        documents = []
        for page_number, page_text in pages.items():
            page_text = page_text.strip()
            if not page_text:
                continue

            parent_chunk_id = self._build_parent_chunk_id(filename, page_number)
            # Split each page/unit into leaf chunks but keep a shared parent id for later auto-merge.
            texts = self._splitter.split_text(page_text)
            for chunk_idx, text in enumerate(texts):
                if not text.strip():
                    continue
                documents.append(
                    {
                        "text": text.strip(),
                        "filename": filename,
                        "file_path": file_path,
                        "file_type": doc_type,
                        "page_number": page_number,
                        "chunk_id": self._build_chunk_id(filename, page_number, chunk_idx),
                        "parent_chunk_id": parent_chunk_id,
                        "root_chunk_id": parent_chunk_id,
                        "chunk_idx": chunk_idx,
                        # Store the original page/unit text so retrieval can expand back to the parent block.
                        "parent_text": page_text,
                        "chunk_level": 3,
                    }
                )
        return documents

    def load_document(self, file_path: str, filename: str) -> list[dict]:
        file_lower = filename.lower()

        # Parse each file type into text units first, then apply one shared chunking strategy.
        if file_lower.endswith(".pdf"):
            doc_type = "PDF"
            loader = PyPDFLoader(file_path)
        elif file_lower.endswith(".docx"):
            doc_type = "Word"
            loader = Docx2txtLoader(file_path)
        elif file_lower.endswith(".doc"):
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
            raise ValueError(f"Unsupported file type: {filename}")

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
                    documents.append(
                        {
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
                        }
                    )
            return documents
        except Exception as exc:
            raise Exception(f"Failed to process document: {exc}") from exc


document_loader = DocumentLoader()
