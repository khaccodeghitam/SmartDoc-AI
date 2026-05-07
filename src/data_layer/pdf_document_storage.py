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
    """Load PDF with layout analysis for multi-column documents (pdfplumber)."""
    docs = []
    
    try:
        import pdfplumber
        
        with pdfplumber.open(str(path)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # layout=True: Auto-detect multi-column layout
                text = page.extract_text(layout=True)
                
                if text and text.strip():
                    docs.append(Document(
                        page_content=text,
                        metadata={
                            "source": str(path),
                            "page": page_num,
                            "file_type": "pdf",
                            "extraction_method": "pdfplumber_layout"
                        }
                    ))
        
        return docs if docs else []
    
    except Exception as e:
        # Fallback to PDFPlumberLoader if pdfplumber fails
        print(f"⚠️ Warning: PDF layout extraction failed ({e}), using fallback")
        loader = PDFPlumberLoader(str(path))
        return loader.load()


def load_pdf_advanced(path: str | Path) -> List[Document]:
    """
    Load PDF with advanced block detection (PyMuPDF).
    
    Best for multi-column documents with complex layouts.
    Automatically sorts text blocks by position (top-bottom, left-right).
    
    Returns:
        List[Document]: List of documents with preserved text order.
    """
    try:
        import fitz  # PyMuPDF
        docs = []
        
        with fitz.open(str(path)) as pdf:
            for page_num, page in enumerate(pdf, 1):
                # Get text blocks with position information
                blocks = page.get_text("blocks")
                
                # Sort blocks by Y-coordinate (top to bottom), then X-coordinate (left to right)
                # This preserves reading order for multi-column layouts
                # Round Y to nearest 10 to group lines on same row
                sorted_blocks = sorted(
                    blocks, 
                    key=lambda b: (round(b[1], -1), b[0])
                )
                
                text_parts = []
                for block in sorted_blocks:
                    if block[6] == 0:  # Text block (not image)
                        text = block[4].strip()
                        if text:
                            text_parts.append(text)
                
                # Join text parts with proper spacing
                full_text = "\n".join(text_parts)
                
                if full_text.strip():
                    docs.append(Document(
                        page_content=full_text,
                        metadata={
                            "source": str(path),
                            "page": page_num,
                            "file_type": "pdf",
                            "extraction_method": "pymupdf_blocks"
                        }
                    ))
        
        return docs if docs else []
    
    except ImportError:
        # Fallback to pdfplumber if pymupdf not installed
        print("⚠️ Warning: pymupdf not installed, falling back to pdfplumber")
        return load_pdf(path)
    except Exception as e:
        # Fallback to pdfplumber if pymupdf fails
        print(f"⚠️ Warning: PyMuPDF extraction failed ({e}), using fallback")
        return load_pdf(path)


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


def load_documents(
    path: str | Path, 
    use_advanced_pdf: bool = False
) -> List[Document]:
    """
    Load documents from PDF or DOCX files.
    
    Args:
        path: Path to the document file
        use_advanced_pdf: If True, use PyMuPDF with block detection for PDFs.
                         Better for multi-column layouts.
    
    Returns:
        List[Document]: List of loaded documents
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        if use_advanced_pdf:
            return load_pdf_advanced(file_path)
        else:
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
