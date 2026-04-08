from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
import re
import shutil
import unicodedata
import warnings

from langchain_core.documents import Document
from langchain_core._api.deprecation import LangChainDeprecationWarning

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever

try:
    from app.config import (
        DEFAULT_CHUNK_OVERLAP,
        DEFAULT_CHUNK_SIZE,
        DEFAULT_TOP_K,
        EMBEDDING_MODEL_NAME,
        INDEX_DIR,
        OLLAMA_BASE_URL,
        OLLAMA_MODEL,
        RAW_DIR,
    )
    from app.document_loader import load_documents
except ModuleNotFoundError:
    from config import (
        DEFAULT_CHUNK_OVERLAP,
        DEFAULT_CHUNK_SIZE,
        DEFAULT_TOP_K,
        EMBEDDING_MODEL_NAME,
        INDEX_DIR,
        OLLAMA_BASE_URL,
        OLLAMA_MODEL,
        RAW_DIR,
    )
    from document_loader import load_documents


FALLBACK_MODELS = ("qwen2.5:1.5b", "qwen2.5:0.5b")
SCORING_MAX_DOCS = 8
SCORING_EXCERPT_CHARS = 320
SCORING_CONTEXT_MAX_CHARS = 3200


@dataclass
class RagResult:
    answer: str
    sources: list[dict[str, Any]]
    mode: str = "llm"
    model_used: str = OLLAMA_MODEL
    is_fallback: bool = False
    confidence: str = "N/A"


@dataclass
class IngestResult:
    file_path: Path
    raw_docs_count: int
    chunks_count: int
    chunks: list[Document]


@dataclass
class IndexBuildResult:
    index_name: str
    index_dir: Path
    chunks_count: int


def _sanitize_name(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    safe = re.sub(r"[^a-zA-Z0-9.-]", "_", name)
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_") or "document"


def save_uploaded_file(uploaded_file: Any, target_dir: Path = RAW_DIR) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / uploaded_file.name
    file_path.write_bytes(uploaded_file.getbuffer())
    return file_path


def _file_type_from_path(file_path: Path) -> str:
    return file_path.suffix.lower().lstrip(".") or "unknown"


def _upload_time_from_path(file_path: Path) -> str:
    try:
        return datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(timespec="seconds")
    except Exception:
        return datetime.now().isoformat(timespec="seconds")


def _enrich_chunks_metadata(chunks: list[Document], file_path: Path) -> list[Document]:
    source = str(file_path)
    file_name = file_path.name
    file_type = _file_type_from_path(file_path)
    upload_time = _upload_time_from_path(file_path)
    upload_date = upload_time[:10]

    for doc in chunks:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("source", source)
        metadata["file_name"] = metadata.get("file_name") or _source_name_from_path(str(metadata.get("source", source))) or file_name
        metadata["file_type"] = metadata.get("file_type") or file_type
        metadata["upload_time"] = metadata.get("upload_time") or upload_time
        metadata["upload_date"] = metadata.get("upload_date") or upload_date
        doc.metadata = metadata

    return chunks


def ingest_document(
    file_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> IngestResult:
    path_obj = Path(file_path)
    raw_docs = load_documents(path_obj)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(raw_docs)
    chunks = _enrich_chunks_metadata(chunks, path_obj)

    return IngestResult(
        file_path=path_obj,
        raw_docs_count=len(raw_docs),
        chunks_count=len(chunks),
        chunks=chunks,
    )


def ingest_uploaded_file(
    uploaded_file: Any,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> IngestResult:
    file_path = save_uploaded_file(uploaded_file)
    return ingest_document(
        file_path=file_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def ingest_multiple_uploaded_files(
    uploaded_files: list[Any],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> IngestResult:
    all_chunks: list[Document] = []
    total_raw_docs = 0
    file_paths: list[Path] = []

    for uploaded_file in uploaded_files:
        file_path = save_uploaded_file(uploaded_file)
        file_paths.append(file_path)
        result = ingest_document(file_path, chunk_size, chunk_overlap)
        total_raw_docs += result.raw_docs_count
        all_chunks.extend(result.chunks)

    return IngestResult(
        file_path=file_paths[0] if file_paths else Path("."),
        raw_docs_count=total_raw_docs,
        chunks_count=len(all_chunks),
        chunks=all_chunks,
    )


@lru_cache(maxsize=1)
def _build_embedder() -> HuggingFaceEmbeddings:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )


def build_and_save_faiss_index(
    chunks: list[Document],
    source_name: str,
    index_root: Path = INDEX_DIR,
) -> IndexBuildResult:
    if not chunks:
        raise ValueError("No chunks available to build index.")

    index_root.mkdir(parents=True, exist_ok=True)
    index_name = _sanitize_name(Path(source_name).stem)
    index_dir = index_root / index_name
    index_dir.mkdir(parents=True, exist_ok=True)

    embedder = _build_embedder()
    vector_store = FAISS.from_documents(chunks, embedder)
    vector_store.save_local(str(index_dir))

    return IndexBuildResult(
        index_name=index_name,
        index_dir=index_dir,
        chunks_count=len(chunks),
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

    return {
        "index_deleted": index_deleted,
        "raw_deleted": raw_deleted,
    }


def evaluate_chunk_strategies(
    file_paths: list[str | Path],
    query: str,
    strategies: list[tuple[int, int]],
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    evaluations: list[dict[str, Any]] = []
    if not file_paths:
        return evaluations

    embedder = _build_embedder()

    for chunk_size, chunk_overlap in strategies:
        all_chunks: list[Document] = []
        for file_path in file_paths:
            try:
                ingest_result = ingest_document(
                    file_path=file_path,
                    chunk_size=int(chunk_size),
                    chunk_overlap=int(chunk_overlap),
                )
                all_chunks.extend(ingest_result.chunks)
            except Exception:
                continue

        if not all_chunks:
            evaluations.append(
                {
                    "chunk_size": int(chunk_size),
                    "chunk_overlap": int(chunk_overlap),
                    "chunks": 0,
                    "avg_chunk_chars": 0,
                    "relevance_proxy": 0.0,
                }
            )
            continue

        chunk_lengths = [len((doc.page_content or "").strip()) for doc in all_chunks]
        avg_chars = int(sum(chunk_lengths) / len(chunk_lengths)) if chunk_lengths else 0

        relevance_proxy = 0.0
        try:
            vector_store = FAISS.from_documents(all_chunks, embedder)
            docs = vector_store.similarity_search(query, k=min(top_k, len(all_chunks)))
            if docs:
                relevance_proxy = sum(_keyword_overlap_score(query, doc.page_content or "") for doc in docs) / len(docs)
        except Exception:
            relevance_proxy = 0.0

        evaluations.append(
            {
                "chunk_size": int(chunk_size),
                "chunk_overlap": int(chunk_overlap),
                "chunks": len(all_chunks),
                "avg_chunk_chars": avg_chars,
                "relevance_proxy": round(float(relevance_proxy), 3),
            }
        )

    return evaluations


def load_faiss_index(index_dir: str | Path) -> FAISS:
    embedder = _build_embedder()
    return FAISS.load_local(
        str(index_dir),
        embedder,
        allow_dangerous_deserialization=True,
    )


def _strip_accents(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")


def _normalize_for_match(text: str) -> str:
    normalized = _strip_accents(text).lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _normalize_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def _keyword_overlap_score(query: str, text: str) -> float:
    query_tokens = _normalize_tokens(query)
    if not query_tokens:
        return 0.0
    text_tokens = _normalize_tokens(text)
    if not text_tokens:
        return 0.0
    overlap = query_tokens.intersection(text_tokens)
    return len(overlap) / len(query_tokens)


def _looks_like_toc(text: str) -> bool:
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


def _is_toc_intent(query: str) -> bool:
    q = query.lower()
    return any(
        key in q
        for key in [
            "muc luc",
            "mục lục",
            "contents",
            "table of contents",
            "danh sach bai",
            "danh sách bài",
        ]
    )


def _deduplicate_docs(docs: list[Document]) -> list[Document]:
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


def _source_name_from_path(path_value: str) -> str:
    return Path(path_value).name if path_value else ""


def _source_name_core(path_value: str) -> str:
    stem = Path(path_value).stem
    stem = _normalize_for_match(stem)
    stem = re.sub(r"^(bai\s*tap|bai|thuc\s*hanh|lab|exercise|chapter)\s*\d*\s*", "", stem).strip()
    return stem


def _sources_from_docs(docs: list[Document]) -> list[str]:
    source_names = {
        _source_name_from_path(str(doc.metadata.get("source", "")))
        for doc in docs
        if (doc.metadata or {}).get("source")
    }
    return sorted(name for name in source_names if name)


def _detect_sources_mentioned_in_query(query: str, available_sources: list[str]) -> list[str]:
    return list(_detect_sources_mentioned_in_query_cached(_normalize_for_match(query), tuple(sorted(available_sources))))


@lru_cache(maxsize=256)
def _detect_sources_mentioned_in_query_cached(query_normalized: str, available_sources: tuple[str, ...]) -> tuple[str, ...]:
    query_norm = f" {query_normalized} "
    query_tokens = {token for token in query_normalized.split() if len(token) >= 2 and not token.isdigit()}
    stop_tokens = {
        "bai",
        "tap",
        "thuc",
        "hanh",
        "exercise",
        "chapter",
        "file",
        "pdf",
        "docx",
    }
    mentioned: list[str] = []

    for source_name in available_sources:
        candidates = [
            _normalize_for_match(Path(source_name).stem),
            _source_name_core(source_name),
        ]
        candidates = [cand for cand in candidates if len(cand) >= 3]
        if not candidates:
            continue

        matched = False
        for candidate in candidates:
            if f" {candidate} " in query_norm:
                matched = True
                break

            candidate_tokens = {
                token
                for token in candidate.split()
                if len(token) >= 2 and not token.isdigit() and token not in stop_tokens
            }
            if not candidate_tokens:
                continue

            overlapped = candidate_tokens.intersection(query_tokens)
            overlap_ratio = len(overlapped) / len(candidate_tokens)
            if len(overlapped) >= 2 and overlap_ratio >= 0.5:
                matched = True
                break

        if matched:
            mentioned.append(source_name)

    return tuple(sorted(set(mentioned)))


def _source_matches_filter(doc_source: str, source_filter: list[str] | None) -> bool:
    if not source_filter:
        return True

    doc_name = _source_name_from_path(doc_source)
    doc_norm = _normalize_for_match(doc_name)

    for selected in source_filter:
        selected_name = _source_name_from_path(selected)
        selected_norm = _normalize_for_match(selected_name)
        if not selected_norm:
            continue
        if selected_norm == doc_norm:
            return True
        if selected_norm in _normalize_for_match(doc_source):
            return True

    return False


def _metadata_matches_filters(
    metadata: dict[str, Any],
    source_filter: list[str] | None,
    file_type_filter: list[str] | None,
    upload_date_filter: list[str] | None,
) -> bool:
    source_value = str(metadata.get("source", ""))
    if source_filter and not _source_matches_filter(source_value, source_filter):
        return False

    if file_type_filter:
        allowed_types = {value.lower().lstrip(".") for value in file_type_filter}
        doc_type = str(metadata.get("file_type", "")).lower().lstrip(".")
        if doc_type not in allowed_types:
            return False

    if upload_date_filter:
        allowed_dates = {value.strip() for value in upload_date_filter if value and value.strip()}
        doc_date = str(metadata.get("upload_date", "")).strip()
        if doc_date not in allowed_dates:
            return False

    return True


def _resolve_effective_source_filter(
    query: str,
    source_filter: list[str] | None,
    all_docs: list[Document],
) -> list[str] | None:
    available_sources = _sources_from_docs(all_docs)
    mentioned_sources = _detect_sources_mentioned_in_query(query, available_sources)
    if mentioned_sources:
        return mentioned_sources
    return source_filter if source_filter else None


@lru_cache(maxsize=1)
def _get_cross_encoder():
    try:
        from sentence_transformers import CrossEncoder

        return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    except ImportError:
        return None


def _rerank_docs(query: str, docs: list[Document], top_k: int) -> list[Document]:
    if not docs:
        return []

    candidate_limit = max(top_k * 8, 24)
    docs = docs[:candidate_limit]

    toc_intent = _is_toc_intent(query)
    cross_encoder = _get_cross_encoder()

    scored: list[tuple[float, Document]] = []

    if cross_encoder:
        try:
            pairs = [[query, doc.page_content] for doc in docs]
            scores = cross_encoder.predict(pairs)
            for score, doc in zip(scores, docs):
                text = doc.page_content or ""
                toc_penalty = 3.0 if (_looks_like_toc(text) and not toc_intent) else 0.0
                short_penalty = 1.0 if len(text.strip()) < 120 else 0.0
                final_score = float(score) - toc_penalty - short_penalty
                scored.append((final_score, doc))
        except Exception as error:
            print(f"Cross-encoder error: {error}, falling back to keyword overlap.")
            cross_encoder = None

    if not cross_encoder:
        for doc in docs:
            text = doc.page_content or ""
            overlap = _keyword_overlap_score(query, text)
            toc_penalty = 0.18 if (_looks_like_toc(text) and not toc_intent) else 0.0
            short_penalty = 0.05 if len(text.strip()) < 120 else 0.0
            score = overlap - toc_penalty - short_penalty
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


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
    effective_filter = _resolve_effective_source_filter(query=query, source_filter=source_filter, all_docs=all_docs)

    fetch_k = max(20, top_k * 6)
    candidates: list[Document] = []

    filter_kwargs: dict[str, Any] = {}
    if effective_filter or file_type_filter or upload_date_filter:

        def match_source(metadata: dict[str, Any]) -> bool:
            return _metadata_matches_filters(
                metadata=metadata,
                source_filter=effective_filter,
                file_type_filter=file_type_filter,
                upload_date_filter=upload_date_filter,
            )

        filter_kwargs["filter"] = match_source

    try:
        mmr_docs = vector_store.max_marginal_relevance_search(
            query,
            k=max(top_k * 3, 10),
            fetch_k=fetch_k,
            lambda_mult=0.35,
            **filter_kwargs,
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
                doc
                for doc in all_docs
                if _metadata_matches_filters(
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

    unique_docs = _deduplicate_docs(candidates)
    if not use_rerank:
        return unique_docs[:top_k]
    return _rerank_docs(query=query, docs=unique_docs, top_k=top_k)


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
    effective_filter = _resolve_effective_source_filter(query=query, source_filter=source_filter, all_docs=all_docs)

    filter_kwargs: dict[str, Any] = {}
    if effective_filter or file_type_filter or upload_date_filter:

        def match_metadata(metadata: dict[str, Any]) -> bool:
            return _metadata_matches_filters(
                metadata=metadata,
                source_filter=effective_filter,
                file_type_filter=file_type_filter,
                upload_date_filter=upload_date_filter,
            )

        filter_kwargs["filter"] = match_metadata

    candidates: list[Document] = []
    try:
        docs = vector_store.similarity_search(query, k=max(top_k * 4, 12), **filter_kwargs)
        candidates.extend(docs)
    except Exception:
        pass

    unique_docs = _deduplicate_docs(candidates)
    return _rerank_docs(query=query, docs=unique_docs, top_k=top_k)


def _format_sources(docs: list[Document]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for idx, doc in enumerate(docs, start=1):
        metadata = doc.metadata or {}
        source_path = str(metadata.get("source", "unknown"))
        sources.append(
            {
                "id": f"S{idx}",
                "source": source_path,
                "file_name": _source_name_from_path(source_path) or "unknown",
                "page": metadata.get("page", metadata.get("page_number", "n/a")),
                "file_type": metadata.get("file_type", "n/a"),
                "upload_date": metadata.get("upload_date", "n/a"),
                "excerpt": doc.page_content[:500],
                "context": doc.page_content[:1800],
            }
        )
    return sources


def _detect_vietnamese(text: str) -> bool:
    vietnamese_chars = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    text_lower = text.lower()
    return any(char in text_lower for char in vietnamese_chars)


def _answer_without_footer(answer_text: str) -> str:
    return answer_text.split("---", 1)[0].strip()


def _build_chat_history_context(chat_history: list[dict] | None, max_turns: int = 4) -> str:
    if not chat_history:
        return ""

    turns = list(reversed(chat_history[:max_turns]))
    lines: list[str] = []
    for turn in turns:
        question = str(turn.get("question", "")).strip()
        answer = _answer_without_footer(str(turn.get("answer", ""))).strip()
        if not question and not answer:
            continue
        if question:
            lines.append(f"- User: {question[:220]}")
        if answer:
            lines.append(f"- Assistant: {answer[:260]}")

    return "\n".join(lines)


def _is_follow_up_query(query: str) -> bool:
    q = _normalize_for_match(query)
    if not q:
        return False

    # If question already looks explicit/standalone, do not force follow-up rewrite.
    standalone_markers = [
        "noi dung",
        "chi tiet",
        "de bai",
        "la gi",
        "bao nhieu",
        "liet ke",
        "danh sach",
        "bai tap",
        "exercise",
        "chapter",
        "chuong",
    ]
    if any(marker in q for marker in standalone_markers) and len(q.split()) >= 6:
        return False

    followup_prefixes = (
        "con ",
        "vay con",
        "the con",
        "tiep theo",
        "what about",
        "and ",
        "then ",
    )
    if q.startswith(followup_prefixes):
        return True

    tokens = q.split()
    referential_tokens = {"no", "do", "vay", "it", "that", "this", "those", "them"}
    if len(tokens) <= 6 and any(token in referential_tokens for token in tokens):
        return True

    return False


def _rewrite_query_with_history(
    query: str,
    chat_history: list[dict] | None,
    model_name: str,
) -> tuple[str, bool]:
    # Do not rewrite queries that are already explicit deterministic intents.
    if _is_exercise_content_query(query) or _is_exercise_count_query(query) or _is_architecture_style_count_query(query):
        return query, False

    if not chat_history:
        return query, False

    history_context = _build_chat_history_context(chat_history)
    if not history_context:
        return query, False

    if not _is_follow_up_query(query):
        return query, False

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


def _extract_retrieval_keywords(text: str, max_terms: int = 4) -> list[str]:
    stop_words = {
        "the",
        "and",
        "that",
        "this",
        "from",
        "with",
        "about",
        "what",
        "which",
        "where",
        "how",
        "cua",
        "cho",
        "voi",
        "nhung",
        "trong",
        "theo",
        "la",
        "cac",
        "mot",
        "tai",
        "lieu",
        "bai",
        "tap",
    }
    tokens = re.findall(r"[a-zA-Z0-9_]+", _strip_accents(text).lower())
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


def _multi_hop_retrieve(
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

    combined = _deduplicate_docs(hop1_docs + hop2_docs)
    return _rerank_docs(query=query, docs=combined, top_k=top_k)


def _build_prompt(query: str, docs: list[Document], chat_history: list[dict] | None = None) -> str:
    context_blocks: list[str] = []
    for idx, doc in enumerate(docs, start=1):
        metadata = doc.metadata or {}
        source = metadata.get("source", "unknown")
        page = metadata.get("page", metadata.get("page_number", "n/a"))
        context_blocks.append(f"[S{idx}] source={source}, page={page}\n{doc.page_content[:1800]}")

    context_text = "\n\n".join(context_blocks)
    history_context = _build_chat_history_context(chat_history)
    history_text = f"Lịch sử hội thoại liên quan:\n{history_context}\n\n" if history_context else ""

    if _detect_vietnamese(query):
        return (
            "Sử dụng ngữ cảnh sau đây để trả lời câu hỏi.\n"
            "Nếu không đủ thông tin, hãy nói rõ là không tìm thấy thông tin trong tài liệu.\n"
            "Trả lời ngắn gọn (3-4 câu) bằng tiếng Việt.\n"
            "Nếu có thông tin trích dẫn thì kèm [Sx] ngay sau câu liên quan.\n\n"
            "KHONG duoc bo sung thong tin ngoai context, khong duoc tu them danh sach bai tap neu context khong noi den.\n\n"
            f"{history_text}"
            f"Ngữ cảnh tài liệu:\n{context_text}\n\n"
            f"Câu hỏi: {query}\n\n"
            "Trả lời:"
        )

    return (
        "Use the following context to answer the question.\n"
        "If you don't know the answer, say you don't know.\n"
        "Keep answer concise (3-4 sentences).\n"
        "If citing information, include [Sx] after the relevant sentence.\n\n"
        "Do not add facts outside the context and do not invent exercise lists unless explicitly present in context.\n\n"
        f"{history_text}"
        f"Document Context:\n{context_text}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )


def _is_architecture_style_count_query(query: str) -> bool:
    q = _normalize_for_match(query)
    has_target = (
        "phong cach kien truc" in q
        or "kieu kien truc" in q
        or "architecture style" in q
        or "architectural style" in q
    )
    has_intent = any(
        key in q
        for key in [
            "bao nhieu",
            "tong",
            "liet ke",
            "danh sach",
            "how many",
            "number of",
            "list",
        ]
    )
    return has_target and has_intent


def _extract_architecture_styles_from_text(text: str) -> list[str]:
    style_patterns = [
        (r"client\s*/\s*server|client\s*server", "Client/Server"),
        (r"component\s*[- ]?based", "Component-Based"),
        (r"domain\s*driven\s*design", "Domain-Driven Design"),
        (r"layered\s*architecture|kien\s*truc\s*phan\s*lop", "Layered Architecture"),
        (r"message\s*bus", "Message Bus"),
        (r"n\s*[- ]?tier|3\s*[- ]?tier", "N-Tier / 3-Tier"),
        (r"object\s*[- ]?oriented", "Object-Oriented"),
        (r"\bsoa\b|service\s*oriented\s*architecture", "SOA"),
    ]

    normalized_text = _normalize_for_match(text)
    found: list[str] = []
    for pattern, style_name in style_patterns:
        if re.search(pattern, normalized_text, flags=re.IGNORECASE):
            found.append(style_name)

    return sorted(set(found), key=_natural_sort_key)


def _deterministic_architecture_style_map(
    all_docs: list[Document],
    source_filter: list[str] | None,
) -> dict[str, list[str]]:
    source_paths = {
        str(doc.metadata.get("source", ""))
        for doc in all_docs
        if (doc.metadata or {}).get("source")
    }

    result: dict[str, list[str]] = {}
    for source_path in sorted(source_paths):
        if source_filter and not _source_matches_filter(source_path, source_filter):
            continue

        source_name = _source_name_from_path(source_path)
        full_text = _read_full_text_from_source(source_path)
        if not full_text:
            continue

        styles = _extract_architecture_styles_from_text(full_text)
        if styles:
            result[source_name] = styles

    return result


def _is_exercise_count_query(query: str) -> bool:
    q = _normalize_for_match(query)
    intent_keywords = [
        "bao nhieu",
        "tong",
        "liet ke",
        "danh sach",
        "so bai",
        "may bai",
        "how many",
        "number of",
        "list all",
    ]
    has_intent = any(keyword in q for keyword in intent_keywords)
    has_target = bool(re.search(r"\bbai\b", q)) or ("exercise" in q) or ("question" in q)
    return has_intent and has_target


def _extract_chapter_number(query: str) -> int | None:
    match = re.search(r"(?:chuong|chương|chapter)\s*(\d+)", query, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _slice_text_by_chapter(text: str, chapter_number: int | None) -> str:
    if chapter_number is None:
        return text

    start_pattern = re.compile(
        rf"(?:^|\n)\s*(?:chuong|chương|chapter)\s*[:\-.]?\s*{chapter_number}\b",
        flags=re.IGNORECASE,
    )
    end_pattern = re.compile(
        rf"(?:^|\n)\s*(?:chuong|chương|chapter)\s*[:\-.]?\s*{chapter_number + 1}\b",
        flags=re.IGNORECASE,
    )

    start_match = start_pattern.search(text)
    if not start_match:
        return ""

    end_match = end_pattern.search(text, start_match.end())
    end_index = end_match.start() if end_match else len(text)
    return text[start_match.start() : end_index]


def _natural_sort_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def _extract_vi_exercises(text: str) -> list[str]:
    pattern = re.compile(
        r"(?im)^\s*((?:bài|bai)\s*(?:tập|tap|thực\s*hành|thuc\s*hanh)?\s*[:\-]?\s*\d{1,3}\b[^\n]*)"
    )
    return sorted({match.strip()[:180] for match in pattern.findall(text) if match.strip()}, key=_natural_sort_key)


def _extract_en_numbered_exercises(text: str) -> list[str]:
    pattern = re.compile(r"(?im)^\s*(\d{1,3})\.\s+([^\n]{2,})")
    results: set[str] = set()

    for number, content in pattern.findall(text):
        cleaned = content.strip()
        if len(cleaned) < 3:
            continue
        if re.fullmatch(r"[\d\W]+", cleaned):
            continue
        results.add(f"Bài {number}: {cleaned[:170]}")

    return sorted(results, key=_natural_sort_key)


@lru_cache(maxsize=128)
def _read_full_text_from_source(source_path: str) -> str:
    path = Path(source_path)
    if not path.exists():
        candidate = RAW_DIR / path.name
        if candidate.exists():
            path = candidate
        else:
            return ""

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        try:
            import pdfplumber

            pages_text: list[str] = []
            with pdfplumber.open(str(path)) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    pages_text.append(f"\n[PAGE {idx}]\n{page_text}")
            return "\n".join(pages_text)
        except Exception:
            return ""

    if suffix == ".docx":
        try:
            from docx import Document as DocxDocument

            doc = DocxDocument(str(path))
            paragraphs = [paragraph.text.strip() for paragraph in doc.paragraphs if paragraph.text and paragraph.text.strip()]
            return "\n".join(paragraphs)
        except Exception:
            return ""

    try:
        return path.read_text("utf-8")
    except Exception:
        return ""


def _extract_exercises_from_text(text: str) -> list[str]:
    vi_exercises = _extract_vi_exercises(text)
    if vi_exercises:
        return vi_exercises
    return _extract_en_numbered_exercises(text)


def _deterministic_exercise_map(
    all_docs: list[Document],
    query: str,
    source_filter: list[str] | None,
) -> dict[str, list[str]]:
    chapter_number = _extract_chapter_number(query)
    source_paths = {
        str(doc.metadata.get("source", ""))
        for doc in all_docs
        if (doc.metadata or {}).get("source")
    }

    result: dict[str, list[str]] = {}
    for source_path in sorted(source_paths):
        if source_filter and not _source_matches_filter(source_path, source_filter):
            continue

        source_name = _source_name_from_path(source_path)
        full_text = _read_full_text_from_source(source_path)
        if not full_text:
            continue

        target_text = _slice_text_by_chapter(full_text, chapter_number)
        if chapter_number is not None and not target_text:
            continue
        if chapter_number is None:
            target_text = full_text

        exercises = _extract_exercises_from_text(target_text)
        if exercises:
            result[source_name] = exercises

    return result


def _is_exercise_content_query(query: str) -> str | None:
    q_norm = _normalize_for_match(query)
    match = re.search(
        r"(?:noi dung|chi tiet|de bai).{0,80}?(?:bai(?:\s*tap)?|exercise|task)\s*(\d{1,3})",
        q_norm,
    )
    if match:
        return match.group(1)
    match = re.search(
        r"(?:bai(?:\s*tap)?|exercise|task)\s*(\d{1,3}).{0,120}?(?:noi dung|chi tiet|de bai|la gi|content|about)",
        q_norm,
    )
    if match:
        return match.group(1)
    return None


def _extract_exercise_content_from_docs(
    all_docs: list[Document],
    exercise_number: str,
    source_filter: list[str] | None,
) -> list[str]:
    source_chunks: dict[str, list[tuple[int, str]]] = {}
    for doc in all_docs:
        metadata = doc.metadata or {}
        source_path = str(metadata.get("source", ""))
        if source_filter and not _source_matches_filter(source_path, source_filter):
            continue

        source_name = _source_name_from_path(source_path) or "unknown"
        raw_page = metadata.get("page", metadata.get("page_number", 0))
        try:
            page = int(raw_page or 0)
        except (TypeError, ValueError):
            page = 0
        source_chunks.setdefault(source_name, []).append((page, doc.page_content or ""))

    numbered_pattern = re.compile(r"((?:bài|bai)\s*(?:tập|tap|thực\s*hành|thuc\s*hanh)?\s*[:\-]?\s*)(\d{1,3})", re.IGNORECASE)
    details: list[str] = []

    for source_name in sorted(source_chunks.keys()):
        chunks = source_chunks[source_name]
        chunks.sort(key=lambda item: item[0])
        full_text = "\n\n".join(chunk_text for _, chunk_text in chunks)

        matches = list(numbered_pattern.finditer(full_text))
        start_idx = -1
        end_idx = -1

        for i, match in enumerate(matches):
            if match.group(2) == str(exercise_number):
                start_idx = match.start()
                end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
                break

        if start_idx == -1:
            continue

        content = full_text[start_idx:end_idx].strip()
        if len(content) > 1500:
            content = content[:1500] + "...\n(Noi dung da duoc cat bot cho gon)"
        details.append(f"### {source_name}\n\n```text\n{content}\n```")

    return details


def _build_context_for_scoring(docs: list[Document]) -> str:
    context_blocks: list[str] = []
    current_len = 0
    for idx, doc in enumerate(docs[:SCORING_MAX_DOCS], start=1):
        metadata = doc.metadata or {}
        source_name = _source_name_from_path(str(metadata.get("source", "unknown"))) or "unknown"
        page = metadata.get("page", metadata.get("page_number", "n/a"))
        excerpt = (doc.page_content or "").strip()[:SCORING_EXCERPT_CHARS]
        block = f"[S{idx}] file={source_name}, page={page}\n{excerpt}"
        if current_len + len(block) > SCORING_CONTEXT_MAX_CHARS:
            break
        context_blocks.append(block)
        current_len += len(block)

    return "\n\n".join(context_blocks)


def _self_rag_confidence_score(
    llm: OllamaLLM,
    query: str,
    answer: str,
    docs: list[Document],
) -> int:
    context_text = _build_context_for_scoring(docs)
    scoring_prompt = (
        "Ban la bo phan kiem chung chat luong RAG.\n"
        "Duoc cho cau hoi, context truy xuat va cau tra loi cua model.\n"
        "Hay danh gia do tin cay cua cau tra loi so voi context theo thang 1-10.\n"
        "Chi tra ve DUY NHAT mot so nguyen tu 1 den 10.\n\n"
        f"Cau hoi: {query}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Cau tra loi: {answer}\n\n"
        "Diem (1-10):"
    )

    try:
        score_raw = str(llm.invoke(scoring_prompt)).strip()
        matched = re.search(r"\d+", score_raw)
        if not matched:
            return 6
        value = int(matched.group())
        return max(1, min(10, value))
    except Exception:
        return 6


def _is_retryable_llm_error(error: Exception) -> bool:
    error_text = str(error).lower()
    memory_keywords = [
        "out of memory",
        "requires more system memory",
        "insufficient memory",
        "cuda out of memory",
    ]
    connection_keywords = [
        "connection refused",
        "failed to connect",
        "connecterror",
        "read timed out",
        "timed out",
        "max retries exceeded",
        "llama runner process has terminated",
        "status code: 500",
        "service unavailable",
        "temporary failure",
    ]
    return any(keyword in error_text for keyword in (memory_keywords + connection_keywords))


def _append_standard_footer(answer_body: str, mode_label: str, model_used: str, confidence: str) -> str:
    return (
        f"{answer_body.strip()}\n\n"
        "---\n"
        "**Thông tin xử lý**\n"
        f"- 🤖 Chế độ: {mode_label}\n"
        f"- 🤖 Model: {model_used}\n"
        f"- 🤖 [Self-RAG] Độ tin cậy: {confidence}"
    )


def _build_result(
    answer_body: str,
    sources: list[dict[str, Any]],
    mode: str,
    model_used: str,
    confidence: str,
    is_fallback: bool = False,
) -> RagResult:
    final_answer = _append_standard_footer(
        answer_body=answer_body,
        mode_label=mode,
        model_used=model_used,
        confidence=confidence,
    )
    return RagResult(
        answer=final_answer,
        sources=sources,
        mode=mode,
        model_used=model_used,
        is_fallback=is_fallback,
        confidence=confidence,
    )


def answer_question(
    index_dir: str | Path,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    model_name: str = OLLAMA_MODEL,
    chat_history: list[dict] | None = None,
    source_filter: list[str] | None = None,
    file_type_filter: list[str] | None = None,
    upload_date_filter: list[str] | None = None,
) -> RagResult:
    vector_store = load_faiss_index(index_dir)
    all_docs = list(vector_store.docstore._dict.values())
    effective_filter = _resolve_effective_source_filter(query=query, source_filter=source_filter, all_docs=all_docs)
    filtered_all_docs = [
        doc
        for doc in all_docs
        if _metadata_matches_filters(
            metadata=(doc.metadata or {}),
            source_filter=effective_filter,
            file_type_filter=file_type_filter,
            upload_date_filter=upload_date_filter,
        )
    ]
    rewritten_query, used_rewrite = _rewrite_query_with_history(
        query=query,
        chat_history=chat_history,
        model_name=model_name,
    )

    effective_top_k = top_k
    if effective_filter and len(effective_filter) > 0:
        effective_top_k = top_k * len(effective_filter)

    docs = _multi_hop_retrieve(
        index_dir=index_dir,
        query=rewritten_query,
        top_k=effective_top_k,
        source_filter=effective_filter,
        file_type_filter=file_type_filter,
        upload_date_filter=upload_date_filter,
    )
    sources = _format_sources(docs)

    has_deterministic_intent = bool(
        _is_exercise_count_query(query)
        or _is_exercise_content_query(query)
        or _is_architecture_style_count_query(query)
    )

    if not docs and not has_deterministic_intent:
        return _build_result(
            answer_body="Không tìm thấy nội dung liên quan trong tài liệu đã index.",
            sources=[],
            mode="Không tìm thấy ngữ cảnh",
            model_used="rule-based",
            confidence="N/A",
        )

    if _is_exercise_count_query(query):
        source_exercises = _deterministic_exercise_map(
            all_docs=filtered_all_docs,
            query=query,
            source_filter=effective_filter,
        )
        total_exercises = sum(len(items) for items in source_exercises.values())

        if total_exercises > 0:
            detail_lines: list[str] = []
            for source_name in sorted(source_exercises.keys(), key=_natural_sort_key):
                exercises = source_exercises[source_name]
                detail_lines.append(f"- {source_name}: ({len(exercises)} bài)")
                for exercise in exercises:
                    detail_lines.append(f"  + {exercise}")

            deterministic_answer = (
                f"Tổng cộng có {total_exercises} bài tập trong các tài liệu khớp với câu hỏi.\n\n"
                "Danh sách chi tiết:\n"
                f"{'\n'.join(detail_lines)}\n\n"
                "[Deterministic Extraction] Trích xuất bằng Regex trên toàn văn bản tài liệu, không để model tự đếm."
            )
            return _build_result(
                answer_body=deterministic_answer,
                sources=sources,
                mode="Deterministic Extraction",
                model_used="rule-based",
                confidence="N/A",
            )

        return _build_result(
            answer_body=(
                "Không tìm thấy bài tập nào thỏa mãn yêu cầu trong phạm vi tài liệu/chương đã lọc.\n"
                "[Deterministic Extraction] Đã quét Regex trên toàn bộ văn bản tài liệu."
            ),
            sources=[],
            mode="Deterministic Extraction",
            model_used="rule-based",
            confidence="N/A",
        )

    exercise_number = _is_exercise_content_query(query)
    if exercise_number:
        details = _extract_exercise_content_from_docs(
            all_docs=filtered_all_docs,
            exercise_number=exercise_number,
            source_filter=effective_filter,
        )
        if details:
            return _build_result(
                answer_body=(
                    f"Dưới đây là nội dung chi tiết của Bài tập {exercise_number} được trích xuất trực tiếp từ tài liệu gốc:\n\n"
                    f"{'\n\n'.join(details)}"
                ),
                sources=sources,
                mode="Deterministic Extraction",
                model_used="rule-based",
                confidence="N/A",
            )

        return _build_result(
            answer_body=(
                f"Không tìm thấy nội dung của Bài tập {exercise_number} trong các tài liệu đã lọc.\n"
                "Vui lòng kiểm tra lại số thứ tự bài tập hoặc bộ lọc tài liệu."
            ),
            sources=[],
            mode="Deterministic Extraction",
            model_used="rule-based",
            confidence="N/A",
        )

    if _is_architecture_style_count_query(query):
        style_map = _deterministic_architecture_style_map(
            all_docs=filtered_all_docs,
            source_filter=effective_filter,
        )
        merged_styles = sorted({style for values in style_map.values() for style in values}, key=_natural_sort_key)

        if merged_styles:
            detail_lines = [f"- {idx}. {style}" for idx, style in enumerate(merged_styles, start=1)]
            deterministic_answer = (
                f"Tổng cộng có {len(merged_styles)} phong cách kiến trúc được đề cập trong tài liệu đã lọc.\n\n"
                "Danh sách phong cách:\n"
                f"{'\n'.join(detail_lines)}\n\n"
                "[Deterministic Extraction] Được trích xuất bằng Regex từ toàn văn bản, không để model tự suy luận."
            )
            return _build_result(
                answer_body=deterministic_answer,
                sources=sources,
                mode="Deterministic Extraction",
                model_used="rule-based",
                confidence="N/A",
            )

        return _build_result(
            answer_body=(
                "Không tìm thấy danh sách phong cách kiến trúc trong tài liệu đã lọc.\n"
                "[Deterministic Extraction] Đã quét toàn bộ văn bản của tài liệu."
            ),
            sources=sources,
            mode="Deterministic Extraction",
            model_used="rule-based",
            confidence="N/A",
        )

    prompt = _build_prompt(query=rewritten_query, docs=docs, chat_history=chat_history)

    def _invoke_with_model(active_model: str) -> tuple[str, int]:
        llm = OllamaLLM(model=active_model, base_url=OLLAMA_BASE_URL, temperature=0.2)
        raw_answer = str(llm.invoke(prompt)).strip()
        confidence = _self_rag_confidence_score(llm=llm, query=query, answer=raw_answer, docs=docs)
        return raw_answer, confidence

    try:
        answer_body, confidence = _invoke_with_model(model_name)
        if used_rewrite and rewritten_query.strip() and rewritten_query.strip().lower() != query.strip().lower():
            answer_body = (
                f"[Conversational RAG] Truy vấn đã được viết lại để xử lý follow-up: `{rewritten_query}`\n\n"
                f"{answer_body}"
            )
        return _build_result(
            answer_body=answer_body,
            sources=sources,
            mode="Conversational Multi-hop RAG + Self-RAG",
            model_used=model_name,
            confidence=f"{confidence}/10",
            is_fallback=False,
        )
    except Exception as error:
        if _is_retryable_llm_error(error):
            for fallback_model in FALLBACK_MODELS:
                if fallback_model == model_name:
                    continue
                try:
                    fallback_answer_body, confidence = _invoke_with_model(fallback_model)
                    return _build_result(
                        answer_body=fallback_answer_body,
                        sources=sources,
                        mode="Conversational Multi-hop RAG + Self-RAG (Fallback)",
                        model_used=fallback_model,
                        confidence=f"{confidence}/10",
                        is_fallback=True,
                    )
                except Exception:
                    continue

        return _build_result(
            answer_body=(
                "Không thể kết nối tới Ollama để sinh câu trả lời. "
                "Hệ thống đã thử fallback model nhưng không thành công.\n"
                f"Chi tiết lỗi: {error}"
            ),
            sources=sources,
            mode="Lỗi hệ thống",
            model_used="N/A",
            confidence="N/A",
        )
