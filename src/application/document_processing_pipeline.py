"""Document processing pipeline: ingest, chunk, and metadata enrichment."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, DEFAULT_TOP_K
from src.models import IngestResult
from src.utils import keyword_overlap_score
from src.data_layer.pdf_document_storage import (
    load_documents,
    save_uploaded_file,
    enrich_chunks_metadata,
)
from src.data_layer.multilingual_mpnet_embeddings import build_embedder
from langchain_community.vectorstores import FAISS


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

def ingest_document(
    file_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    use_advanced_pdf: bool = False,
) -> IngestResult:
    """
    Ingest and process a single document.
    
    Args:
        file_path: Path to the document
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        use_advanced_pdf: Use PyMuPDF with block detection for PDFs (better for multi-column)
    
    Returns:
        IngestResult with processed chunks
    """
    path_obj = Path(file_path)
    raw_docs = load_documents(path_obj, use_advanced_pdf=use_advanced_pdf)

    # We use RecursiveCharacterTextSplitter but with smart separators
    # to avoid splitting too early on small paragraphs.
    # We want chunks to be as close to chunk_size as possible.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Re-ordering and adding more punctuation to allow overlap to catch context
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        length_function=len,
    )
        
    chunks = splitter.split_documents(raw_docs)
    chunks = enrich_chunks_metadata(chunks, path_obj)

    return IngestResult(
        file_path=path_obj,
        raw_docs_count=len(raw_docs),
        chunks_count=len(chunks),
        chunks=chunks,
    )


def ingest_multiple_uploaded_files(
    uploaded_files: list[Any],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    use_advanced_pdf: bool = False,
) -> IngestResult:
    """
    Ingest and process multiple uploaded files.
    
    Args:
        uploaded_files: List of uploaded file objects
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        use_advanced_pdf: Use PyMuPDF with block detection for PDFs
    
    Returns:
        IngestResult with all chunks combined
    """
    all_chunks: list[Document] = []
    total_raw_docs = 0
    file_paths: list[Path] = []

    for uploaded_file in uploaded_files:
        file_path = save_uploaded_file(uploaded_file)
        file_paths.append(file_path)
        result = ingest_document(file_path, chunk_size, chunk_overlap, use_advanced_pdf=use_advanced_pdf)
        total_raw_docs += result.raw_docs_count
        all_chunks.extend(result.chunks)

    return IngestResult(
        file_path=file_paths[0] if file_paths else Path("."),
        raw_docs_count=total_raw_docs,
        chunks_count=len(all_chunks),
        chunks=all_chunks,
    )


# ---------------------------------------------------------------------------
# Chunk strategy evaluation (Câu 4)
# ---------------------------------------------------------------------------

def evaluate_chunk_strategies(
    file_paths: list[str | Path],
    query: str,
    strategies: list[tuple[int, int]],
    top_k: int = DEFAULT_TOP_K,
    use_advanced_pdf: bool = False,
) -> list[dict[str, Any]]:
    """
    Evaluate different chunk strategies for document processing.
    
    Args:
        file_paths: List of document paths
        query: Query to evaluate relevance
        strategies: List of (chunk_size, chunk_overlap) tuples to test
        top_k: Number of top results to consider
        use_advanced_pdf: Use PyMuPDF with block detection for PDFs
    
    Returns:
        List of evaluation results for each strategy
    """
    evaluations: list[dict[str, Any]] = []
    if not file_paths:
        return evaluations

    embedder = build_embedder()

    for chunk_size, chunk_overlap in strategies:
        all_chunks: list[Document] = []
        for file_path in file_paths:
            try:
                ingest_result = ingest_document(
                    file_path=file_path,
                    chunk_size=int(chunk_size),
                    chunk_overlap=int(chunk_overlap),
                    use_advanced_pdf=use_advanced_pdf,
                )
                all_chunks.extend(ingest_result.chunks)
            except Exception:
                continue

        if not all_chunks:
            evaluations.append({
                "chunk_size": int(chunk_size),
                "chunk_overlap": int(chunk_overlap),
                "chunks": 0,
                "avg_chunk_chars": 0,
                "relevance_proxy": 0.0,
            })
            continue

        chunk_lengths = [len((doc.page_content or "").strip()) for doc in all_chunks]
        avg_chars = int(sum(chunk_lengths) / len(chunk_lengths)) if chunk_lengths else 0

        relevance_proxy = 0.0
        try:
            vector_store = FAISS.from_documents(all_chunks, embedder)
            docs = vector_store.similarity_search(query, k=min(top_k, len(all_chunks)))
            if docs:
                relevance_proxy = sum(keyword_overlap_score(query, doc.page_content or "") for doc in docs) / len(docs)
        except Exception:
            relevance_proxy = 0.0

        evaluations.append({
            "chunk_size": int(chunk_size),
            "chunk_overlap": int(chunk_overlap),
            "chunks": len(all_chunks),
            "avg_chunk_chars": avg_chars,
            "relevance_proxy": round(float(relevance_proxy), 3),
        })

    return evaluations
