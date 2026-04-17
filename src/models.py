from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path




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
