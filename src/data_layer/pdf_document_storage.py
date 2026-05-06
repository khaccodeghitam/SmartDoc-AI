"""PDF/DOCX document loading, saving, and raw text extraction."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, List

from docx import Document as DocxDocument
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.documents import Document

from src.config import RAW_DIR
from src.utils import sanitize_name, source_name_from_path


# ---------------------------------------------------------------------------
# Document loading (from old document_loader.py)
# ---------------------------------------------------------------------------

def load_pdf(path: str | Path) -> List[Document]:
    loader = PDFPlumberLoader(str(path))
    return loader.load()


def load_docx(path: str | Path) -> List[Document]:
    doc = DocxDocument(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    full_text = "\n".join(paragraphs).strip()

    if not full_text:
        return []

    return [
        Document(
            page_content=full_text,
            metadata={
                "source": str(path),
                "file_type": "docx",
            },
        )
    ]


def load_documents(path: str | Path) -> List[Document]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(file_path)
    if suffix == ".docx":
        return load_docx(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")


# ---------------------------------------------------------------------------
# File saving and metadata
# ---------------------------------------------------------------------------

def save_uploaded_file(uploaded_file: Any, target_dir: Path = RAW_DIR) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / uploaded_file.name
    file_path.write_bytes(uploaded_file.getbuffer())
    return file_path


def file_type_from_path(file_path: Path) -> str:
    return file_path.suffix.lower().lstrip(".") or "unknown"


def upload_time_from_path(file_path: Path) -> str:
    try:
        return datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(timespec="seconds")
    except Exception:
        return datetime.now().isoformat(timespec="seconds")


def enrich_chunks_metadata(chunks: list[Document], file_path: Path) -> list[Document]:
    source = str(file_path)
    file_name = file_path.name
    file_type = file_type_from_path(file_path)
    upload_time = upload_time_from_path(file_path)
    upload_date = upload_time[:10]

    for doc in chunks:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("source", source)
        metadata["file_name"] = metadata.get("file_name") or source_name_from_path(str(metadata.get("source", source))) or file_name
        metadata["file_type"] = metadata.get("file_type") or file_type
        metadata["upload_time"] = metadata.get("upload_time") or upload_time
        metadata["upload_date"] = metadata.get("upload_date") or upload_date
        doc.metadata = metadata

    return chunks
