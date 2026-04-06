from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RagResult:
    answer: str
    sources: list[Any]


def ingest_document(*args, **kwargs):
    raise NotImplementedError("Ingest pipeline will be implemented in the next step.")


def answer_question(*args, **kwargs):
    raise NotImplementedError("Question answering pipeline will be implemented in the next step.")
