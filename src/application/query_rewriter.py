"""Query rewriting, follow-up detection, and multi-hop retrieval (Câu 6 + 10)."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_ollama import OllamaLLM

from src.config import OLLAMA_BASE_URL, FALLBACK_MODELS
from src.utils import normalize_for_match, strip_accents
from src.application.prompt_engineering import build_chat_history_context
from src.data_layer.faiss_vector_store import (
    search_similar_chunks,
    deduplicate_docs,
    rerank_docs,
)


# ---------------------------------------------------------------------------
# Follow-up detection
# ---------------------------------------------------------------------------

def is_follow_up_query(query: str) -> bool:
    q = normalize_for_match(query)
    if not q:
        return False

    standalone_markers = [
        "noi dung", "chi tiet", "de bai", "la gi", "bao nhieu",
        "liet ke", "danh sach", "bai tap", "exercise", "chapter", "chuong",
    ]
    if any(marker in q for marker in standalone_markers) and len(q.split()) >= 6:
        return False

    followup_prefixes = (
        "con ", "vay con", "the con", "tiep theo", "what about", "and ", "then ",
    )
    if q.startswith(followup_prefixes):
        return True

    tokens = q.split()
    referential_tokens = {"no", "do", "vay", "it", "that", "this", "those", "them"}
    if len(tokens) <= 6 and any(token in referential_tokens for token in tokens):
        return True

    return False


def should_include_history_in_prompt(query: str, used_rewrite: bool) -> bool:
    if used_rewrite:
        return True
    return is_follow_up_query(query)


# ---------------------------------------------------------------------------
# Query rewriting (Câu 10: Query rewriting)
# ---------------------------------------------------------------------------

def rewrite_query_with_history(
    query: str,
    chat_history: list[dict] | None,
    model_name: str,
    is_deterministic_intent: bool = False,
) -> tuple[str, bool]:
    # Keep deterministic queries unchanged unless they are follow-up references.
    if is_deterministic_intent and not is_follow_up_query(query):
        return query, False

    if not chat_history:
        return query, False

    history_context = build_chat_history_context(chat_history)
    if not history_context:
        return query, False

    if not is_follow_up_query(query):
        return query, False

    if is_deterministic_intent:
        last_question = str(chat_history[0].get("question", "")).strip() if chat_history else ""
        if last_question and last_question.lower() != query.lower():
            heuristic = f"{query} (ngu canh cau truoc: {last_question})"
            return heuristic, True

    rewrite_prompt = (
        "Ban la bo phan viet lai truy van retrieval cho RAG.\n"
        "Viet lai cau hoi follow-up thanh mot cau hoi doc lap ro rang dua tren lich su hoi thoai.\n"
        "Khong duoc thay doi y dinh cau hoi.\n"
        "Tra ve DUY NHAT cau hoi moi.\n\n"
        f"Lich su hoi thoai:\n{history_context}\n\n"
        f"Follow-up hien tai: {query}\n\n"
        "Cau hoi viet lai:"
    )

    tried_models = [model_name, *FALLBACK_MODELS]
    seen_models: set[str] = set()

    for active_model in tried_models:
        if active_model in seen_models:
            continue
        seen_models.add(active_model)
        try:
            llm = OllamaLLM(model=active_model, base_url=OLLAMA_BASE_URL, temperature=0.0)
            rewritten = str(llm.invoke(rewrite_prompt)).strip().splitlines()[0].strip()
            rewritten = rewritten.strip('"').strip("'").strip()
            if rewritten and len(rewritten) >= 5:
                return rewritten, rewritten.lower() != query.lower()
        except Exception:
            continue

    last_question = str(chat_history[0].get("question", "")).strip() if chat_history else ""
    if last_question and last_question.lower() != query.lower():
        heuristic = f"{query} (ngữ cảnh liên quan: {last_question})"
        return heuristic, True

    return query, False


# ---------------------------------------------------------------------------
# Multi-hop retrieval (Câu 10: Multi-hop reasoning)
# ---------------------------------------------------------------------------

def _extract_retrieval_keywords(text: str, max_terms: int = 4) -> list[str]:
    stop_words = {
        "the", "and", "that", "this", "from", "with", "about", "what", "which", "where", "how",
        "cua", "cho", "voi", "nhung", "trong", "theo", "la", "cac", "mot", "tai", "lieu", "bai", "tap",
    }
    tokens = re.findall(r"[a-zA-Z0-9_]+", strip_accents(text).lower())
    filtered = [token for token in tokens if len(token) >= 4 and token not in stop_words and not token.isdigit()]
    if not filtered:
        return []
    return [term for term, _ in Counter(filtered).most_common(max_terms)]


def _build_second_hop_queries(query: str, docs: list[Document]) -> list[str]:
    if not docs:
        return []

    corpus = "\n".join((doc.page_content or "")[:500] for doc in docs[:4])
    keywords = _extract_retrieval_keywords(corpus, max_terms=4)
    if not keywords:
        return []

    expansion = f"{query} {' '.join(keywords[:3])}".strip()
    if expansion.lower() == query.lower():
        return []

    return [expansion]


def multi_hop_retrieve(
    index_dir: str | Path,
    query: str,
    top_k: int,
    source_filter: list[str] | None,
    file_type_filter: list[str] | None,
    upload_date_filter: list[str] | None,
) -> list[Document]:
    hop1_docs = search_similar_chunks(
        index_dir=index_dir,
        query=query,
        top_k=max(top_k, 3),
        source_filter=source_filter,
        file_type_filter=file_type_filter,
        upload_date_filter=upload_date_filter,
        use_rerank=False,
    )
    if not hop1_docs:
        return []

    hop2_queries = _build_second_hop_queries(query, hop1_docs)
    hop2_docs: list[Document] = []
    for hop_query in hop2_queries[:2]:
        try:
            retrieved = search_similar_chunks(
                index_dir=index_dir,
                query=hop_query,
                top_k=max(top_k, 3),
                source_filter=source_filter,
                file_type_filter=file_type_filter,
                upload_date_filter=upload_date_filter,
                use_rerank=False,
            )
            hop2_docs.extend(retrieved)
        except Exception:
            continue

    combined = deduplicate_docs(hop1_docs + hop2_docs)
    return rerank_docs(query=query, docs=combined, top_k=top_k)
