from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

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


def _build_embedder() -> HuggingFaceEmbeddings:
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


def search_similar_chunks(index_dir: str | Path, query: str, top_k: int = 3) -> list[Document]:
    vector_store = load_faiss_index(index_dir)
    return vector_store.similarity_search(query, k=top_k)


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


def _build_prompt(query: str, docs: list[Document]) -> str:
    context_blocks: list[str] = []
    for idx, doc in enumerate(docs, start=1):
        metadata = doc.metadata or {}
        source = metadata.get("source", "unknown")
        page = metadata.get("page", metadata.get("page_number", "n/a"))
        context_blocks.append(
            f"[S{idx}] source={source}, page={page}\n{doc.page_content[:1800]}"
        )

    context_text = "\n\n".join(context_blocks)

    return (
        "Ban la tro ly hoi dap tai lieu.\n"
        "Chi duoc su dung thong tin trong cac nguon [S1], [S2], ... ben duoi de tra loi.\n"
        "Neu khong du thong tin, hay noi ro la khong tim thay thong tin trong tai lieu.\n"
        "Tra loi ngan gon, ro rang, va neu co thong tin trich dan thi kem [Sx] ngay sau cau lien quan.\n\n"
        f"Cau hoi: {query}\n\n"
        f"Nguon tai lieu:\n{context_text}\n\n"
        "Tra loi:"
    )


def answer_question(
    index_dir: str | Path,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    model_name: str = OLLAMA_MODEL,
) -> RagResult:
    docs = search_similar_chunks(index_dir=index_dir, query=query, top_k=top_k)
    sources = _format_sources(docs)

    if not docs:
        return RagResult(
            answer="Khong tim thay noi dung lien quan trong tai lieu da index.",
            sources=[],
        )

    prompt = _build_prompt(query=query, docs=docs)
    llm = Ollama(model=model_name, base_url=OLLAMA_BASE_URL, temperature=0.2)
    answer = llm.invoke(prompt)

    return RagResult(
        answer=str(answer).strip(),
        sources=sources,
    )
