"""FAISS vector store operations: build, load, search (hybrid + reranking)."""
from __future__ import annotations

import re
import shutil
import streamlit as st
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from src.config import INDEX_DIR, RAW_DIR
from src.models import IndexBuildResult
from src.utils import (
    sanitize_name,
    keyword_overlap_score,
    metadata_matches_filters,
    resolve_effective_source_filter,
)
from src.data_layer.multilingual_mpnet_embeddings import build_embedder


# ---------------------------------------------------------------------------
# Build / Load / Clear
# ---------------------------------------------------------------------------

def build_and_save_faiss_index(
    chunks: list[Document],
    source_name: str,
    index_root: Path = INDEX_DIR,
) -> IndexBuildResult:
    if not chunks:
        raise ValueError("No chunks available to build index.")

    index_root.mkdir(parents=True, exist_ok=True)
    index_name = sanitize_name(Path(source_name).stem)
    index_dir = index_root / index_name
    index_dir.mkdir(parents=True, exist_ok=True)

    embedder = build_embedder()
    vector_store = FAISS.from_documents(chunks, embedder)
    vector_store.save_local(str(index_dir))

    return IndexBuildResult(
        index_name=index_name,
        index_dir=index_dir,
        chunks_count=len(chunks),
    )


def load_faiss_index(index_dir: str | Path) -> FAISS:
    embedder = build_embedder()
    return FAISS.load_local(
        str(index_dir),
        embedder,
        allow_dangerous_deserialization=True,
    )


def clear_vector_store_data(index_root: Path = INDEX_DIR, raw_root: Path = RAW_DIR) -> dict[str, int]:
    index_deleted = 0
    raw_deleted = 0

    if index_root.exists():
        for item in index_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                index_deleted += 1
            elif item.is_file():
                item.unlink(missing_ok=True)
                index_deleted += 1

    if raw_root.exists():
        for item in raw_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                raw_deleted += 1
            elif item.is_file():
                item.unlink(missing_ok=True)
                raw_deleted += 1

    return {"index_deleted": index_deleted, "raw_deleted": raw_deleted}


# ---------------------------------------------------------------------------
# TOC and chunk quality helpers
# ---------------------------------------------------------------------------

def looks_like_toc(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True

    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if not lines:
        return True

    dot_lines = 0
    page_num_lines = 0
    for line in lines:
        if "..." in line or "....." in line:
            dot_lines += 1
        if re.search(r"\b\d{1,3}\s*$", line):
            page_num_lines += 1

    dot_ratio = dot_lines / len(lines)
    page_num_ratio = page_num_lines / len(lines)
    return dot_ratio >= 0.35 and page_num_ratio >= 0.35


def is_toc_intent(query: str) -> bool:
    q = query.lower()
    return any(
        key in q
        for key in ["muc luc", "mục lục", "contents", "table of contents", "danh sach bai", "danh sách bài"]
    )


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate_docs(docs: list[Document]) -> list[Document]:
    seen: set[str] = set()
    unique_docs: list[Document] = []

    for doc in docs:
        metadata = doc.metadata or {}
        source = str(metadata.get("source", ""))
        page = str(metadata.get("page", metadata.get("page_number", "")))
        content_key = re.sub(r"\s+", " ", doc.page_content.strip().lower())[:300]
        key = f"{source}|{page}|{content_key}"
        if key in seen:
            continue
        seen.add(key)
        unique_docs.append(doc)

    return unique_docs


# ---------------------------------------------------------------------------
# Cross-encoder reranking (Câu 9)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def _get_cross_encoder():
    try:
        from sentence_transformers import CrossEncoder
        return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    except ImportError:
        return None


def rerank_docs(query: str, docs: list[Document], top_k: int) -> list[Document]:
    if not docs:
        return []

    candidate_limit = max(top_k * 8, 24)
    docs = docs[:candidate_limit]

    toc_intent = is_toc_intent(query)
    cross_encoder = _get_cross_encoder()

    scored: list[tuple[float, Document]] = []

    if cross_encoder:
        try:
            pairs = [[query, doc.page_content] for doc in docs]
            scores = cross_encoder.predict(pairs)
            for score, doc in zip(scores, docs):
                text = doc.page_content or ""
                toc_penalty = 3.0 if (looks_like_toc(text) and not toc_intent) else 0.0
                short_penalty = 1.0 if len(text.strip()) < 120 else 0.0
                final_score = float(score) - toc_penalty - short_penalty
                scored.append((final_score, doc))
        except Exception as error:
            print(f"Cross-encoder error: {error}, falling back to keyword overlap.")
            cross_encoder = None

    if not cross_encoder:
        for doc in docs:
            text = doc.page_content or ""
            overlap = keyword_overlap_score(query, text)
            toc_penalty = 0.18 if (looks_like_toc(text) and not toc_intent) else 0.0
            short_penalty = 0.05 if len(text.strip()) < 120 else 0.0
            score = overlap - toc_penalty - short_penalty
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


# ---------------------------------------------------------------------------
# Hybrid search (Câu 7): FAISS (similarity + MMR) + BM25
# ---------------------------------------------------------------------------

def search_similar_chunks(
    index_dir: str | Path,
    query: str,
    top_k: int = 3,
    source_filter: list[str] | None = None,
    file_type_filter: list[str] | None = None,
    upload_date_filter: list[str] | None = None,
    use_rerank: bool = True,
) -> list[Document]:
    vector_store = load_faiss_index(index_dir)
    all_docs = list(vector_store.docstore._dict.values())
    effective_filter = resolve_effective_source_filter(query=query, source_filter=source_filter, all_docs=all_docs)

    fetch_k = max(20, top_k * 6)
    candidates: list[Document] = []

    filter_kwargs: dict[str, Any] = {}
    if effective_filter or file_type_filter or upload_date_filter:
        def match_source(metadata: dict[str, Any]) -> bool:
            return metadata_matches_filters(
                metadata=metadata,
                source_filter=effective_filter,
                file_type_filter=file_type_filter,
                upload_date_filter=upload_date_filter,
            )
        filter_kwargs["filter"] = match_source

    try:
        mmr_docs = vector_store.max_marginal_relevance_search(
            query, k=max(top_k * 3, 10), fetch_k=fetch_k, lambda_mult=0.35, **filter_kwargs,
        )
        candidates.extend(mmr_docs)
    except Exception:
        pass

    try:
        sim_docs = vector_store.similarity_search(query, k=fetch_k, **filter_kwargs)
        candidates.extend(sim_docs)
    except Exception:
        pass

    try:
        bm25_docs_pool = all_docs
        if effective_filter or file_type_filter or upload_date_filter:
            bm25_docs_pool = [
                doc for doc in all_docs
                if metadata_matches_filters(
                    metadata=(doc.metadata or {}),
                    source_filter=effective_filter,
                    file_type_filter=file_type_filter,
                    upload_date_filter=upload_date_filter,
                )
            ]

        if bm25_docs_pool:
            bm25_retriever = BM25Retriever.from_documents(bm25_docs_pool)
            bm25_retriever.k = max(top_k * 3, 10)
            bm25_docs = bm25_retriever.invoke(query)
            candidates.extend(bm25_docs)
    except Exception as error:
        print(f"BM25 Retrieval error: {error}")

    unique_docs = deduplicate_docs(candidates)
    if not use_rerank:
        return unique_docs[:top_k]
    return rerank_docs(query=query, docs=unique_docs, top_k=top_k)


def search_vector_only_chunks(
    index_dir: str | Path,
    query: str,
    top_k: int = 3,
    source_filter: list[str] | None = None,
    file_type_filter: list[str] | None = None,
    upload_date_filter: list[str] | None = None,
) -> list[Document]:
    vector_store = load_faiss_index(index_dir)
    all_docs = list(vector_store.docstore._dict.values())
    effective_filter = resolve_effective_source_filter(query=query, source_filter=source_filter, all_docs=all_docs)

    filter_kwargs: dict[str, Any] = {}
    if effective_filter or file_type_filter or upload_date_filter:
        def match_metadata(metadata: dict[str, Any]) -> bool:
            return metadata_matches_filters(
                metadata=metadata, source_filter=effective_filter,
                file_type_filter=file_type_filter, upload_date_filter=upload_date_filter,
            )
        filter_kwargs["filter"] = match_metadata

    candidates: list[Document] = []
    try:
        docs = vector_store.similarity_search(query, k=max(top_k * 4, 12), **filter_kwargs)
        candidates.extend(docs)
    except Exception:
        pass

    unique_docs = deduplicate_docs(candidates)
    return rerank_docs(query=query, docs=unique_docs, top_k=top_k)
