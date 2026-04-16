from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from src.config import OLLAMA_MODEL


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
