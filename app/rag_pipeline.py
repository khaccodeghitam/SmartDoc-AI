from __future__ import annotations
# Triggering reload

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
import re
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


@dataclass
class RagResult:
    answer: str
    sources: list[dict[str, Any]]


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
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return safe.strip("_") or "document"


def save_uploaded_file(uploaded_file: Any, target_dir: Path = RAW_DIR) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / uploaded_file.name
    file_path.write_bytes(uploaded_file.getbuffer())
    return file_path


def ingest_document(
    file_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> IngestResult:
    raw_docs = load_documents(file_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(raw_docs)

    return IngestResult(
        file_path=Path(file_path),
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
    all_chunks = []
    total_raw_docs = 0
    file_paths = []
    
    for uf in uploaded_files:
        file_path = save_uploaded_file(uf)
        file_paths.append(file_path)
        res = ingest_document(file_path, chunk_size, chunk_overlap)
        total_raw_docs += res.raw_docs_count
        all_chunks.extend(res.chunks)
        
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


def load_faiss_index(index_dir: str | Path) -> FAISS:
    embedder = _build_embedder()
    return FAISS.load_local(
        str(index_dir),
        embedder,
        allow_dangerous_deserialization=True,
    )


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


@lru_cache(maxsize=1)
def _get_cross_encoder():
    try:
        from sentence_transformers import CrossEncoder
        # Using a small, fast cross-encoder model
        return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    except ImportError:
        return None


def _rerank_docs(query: str, docs: list[Document], top_k: int) -> list[Document]:
    if not docs:
        return []

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
        except Exception as e:
            print(f"Cross-encoder error: {e}, falling back to keyword overlap.")
            cross_encoder = None

    if not cross_encoder:
        # Fallback to keyword overlap
        for doc in docs:
            text = doc.page_content or ""
            overlap = _keyword_overlap_score(query, text)
            toc_penalty = 0.18 if (_looks_like_toc(text) and not toc_intent) else 0.0
            short_penalty = 0.05 if len(text.strip()) < 120 else 0.0
            score = overlap - toc_penalty - short_penalty
            scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def search_similar_chunks(index_dir: str | Path, query: str, top_k: int = 3, source_filter: list[str] = None) -> list[Document]:
    vector_store = load_faiss_index(index_dir)
    fetch_k = max(20, top_k * 6)
    candidates: list[Document] = []
    
    filter_kwargs = {}
    if source_filter:
        def match_source(md):
            src = md.get("source")
            if not src:
                return False
            # Check if any part of the path matches
            return any(s in src for s in source_filter) or any(Path(src).name == s for s in source_filter)
        filter_kwargs["filter"] = match_source

    # 1. FAISS Search (MMR + Similarity)
    try:
        mmr_docs = vector_store.max_marginal_relevance_search(
            query,
            k=max(top_k * 3, 10),
            fetch_k=fetch_k,
            lambda_mult=0.35,
            **filter_kwargs
        )
        candidates.extend(mmr_docs)
    except Exception:
        pass

    try:
        sim_docs = vector_store.similarity_search(query, k=fetch_k, **filter_kwargs)
        candidates.extend(sim_docs)
    except Exception:
        pass

    # 2. BM25 Hybrid Search Support
    try:
        all_docs = list(vector_store.docstore._dict.values())
        if source_filter:
            def matches(doc_src):
                if not doc_src: return False
                return any(s in doc_src for s in source_filter) or any(Path(doc_src).name == s for s in source_filter)
            all_docs = [doc for doc in all_docs if matches(doc.metadata.get("source"))]
            
        if all_docs:
            bm25_retriever = BM25Retriever.from_documents(all_docs)
            bm25_retriever.k = max(top_k * 3, 10)
            bm25_docs = bm25_retriever.invoke(query)
            candidates.extend(bm25_docs)
    except Exception as e:
        print(f"BM25 Retrieval error: {e}")
        pass

    unique_docs = _deduplicate_docs(candidates)
    return _rerank_docs(query=query, docs=unique_docs, top_k=top_k)


def _format_sources(docs: list[Document]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for idx, doc in enumerate(docs, start=1):
        metadata = doc.metadata or {}
        sources.append(
            {
                "id": f"S{idx}",
                "source": metadata.get("source", "unknown"),
                "page": metadata.get("page", metadata.get("page_number", "n/a")),
                "file_type": metadata.get("file_type", "n/a"),
                "excerpt": doc.page_content[:500],
            }
        )
    return sources


def _detect_vietnamese(text: str) -> bool:
    """Detect if text contains Vietnamese characters."""
    vietnamese_chars = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    text_lower = text.lower()
    return any(char in text_lower for char in vietnamese_chars)


def _build_prompt(query: str, docs: list[Document], chat_history: list[dict] = None) -> str:
    context_blocks: list[str] = []
    for idx, doc in enumerate(docs, start=1):
        metadata = doc.metadata or {}
        source = metadata.get("source", "unknown")
        page = metadata.get("page", metadata.get("page_number", "n/a"))
        context_blocks.append(
            f"[S{idx}] source={source}, page={page}\n{doc.page_content[:1800]}"
        )

    context_text = "\n\n".join(context_blocks)

    history_text = ""
    if chat_history:
        history_blocks = []
        for item in reversed(chat_history[:3]):  # Take last 3 exchanges, reverse to chronological order
            history_blocks.append(f"User: {item['question']}\nBot: {item['answer']}")
        if history_blocks:
            history_text = "Lịch sử hội thoại trước đó (Context):\n" + "\n".join(history_blocks) + "\n\n"

    is_vietnamese = _detect_vietnamese(query)

    if is_vietnamese:
        return (
            "Sử dụng ngữ cảnh sau đây để trả lời câu hỏi.\n"
            "Nếu không đủ thông tin, hãy nói rõ là không tìm thấy thông tin trong tài liệu.\n"
            "Trả lời ngắn gọn (3-4 câu) BẰNG TIẾNG VIỆT.\n"
            "Nếu có thông tin trích dẫn thì kèm [Sx] ngay sau câu liên quan.\n\n"
            f"{history_text}"
            f"Ngữ cảnh tài liệu:\n{context_text}\n\n"
            f"Câu hỏi: {query}\n\n"
            "Trả lời:"
        )
    else:
        return (
            "Use the following context to answer the question.\n"
            "If you don't know the answer, just say you don't know.\n"
            "Keep answer concise (3-4 sentences).\n"
            "If citing information, include [Sx] after the relevant sentence.\n\n"
            f"{history_text}"
            f"Document Context:\n{context_text}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )


def answer_question(
    index_dir: str | Path,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    model_name: str = OLLAMA_MODEL,
    chat_history: list[dict] = None,
    source_filter: list[str] = None,
) -> RagResult:
    docs = search_similar_chunks(index_dir=index_dir, query=query, top_k=top_k, source_filter=source_filter)
    sources = _format_sources(docs)

    if not docs:
        return RagResult(
            answer="Khong tim thay noi dung lien quan trong tai lieu da index.",
            sources=[],
        )

    prompt = _build_prompt(query=query, docs=docs, chat_history=chat_history)
    llm = OllamaLLM(model=model_name, base_url=OLLAMA_BASE_URL, temperature=0.2)
    try:
        answer = llm.invoke(prompt)
        
        # Self-RAG (Q10): Verification & Confidence Scoring
        verification_prompt = (
            "Dựa vào câu hỏi và câu trả lời dưới đây, hãy đánh giá độ tin cậy của câu trả lời liên quan tới ngữ cảnh từ 1 đến 10.\n"
            "Chỉ trả về một con số duy nhất từ 1 đến 10, không giải thích gì thêm.\n\n"
            f"Câu hỏi: {query}\n"
            f"Câu trả lời: {answer}\n"
            "Điểm số (1-10):"
        )
        try:
            score_str = llm.invoke(verification_prompt).strip()
            match = re.search(r'\d+', score_str)
            if match:
                score = min(int(match.group()), 10)
                answer += f"\n\n**🤖 [Self-RAG] Độ tin cậy (Confidence Score): {score}/10**"
        except Exception:
            pass
            
    except Exception as exc:
        return RagResult(
            answer=(
                "Khong the ket noi toi Ollama de sinh cau tra loi. "
                "Hay kiem tra Ollama dang chay va model da tai xong.\n"
                f"Chi tiet loi: {exc}"
            ),
            sources=sources,
        )

    return RagResult(
        answer=str(answer).strip(),
        sources=sources,
    )
