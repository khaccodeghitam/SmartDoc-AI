"""Basic RAG Chain Manager. Thuần chủng LLM 1 shot."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from src.application.prompt_engineering import build_rag_prompt
from src.data_layer.faiss_vector_store import load_faiss_index, search_similar_chunks
from src.model_layer.ollama_inference_engine import OllamaInferenceEngine
from src.utils import normalize_for_match, source_name_from_path


def _extract_vi_exercises(text: str) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines()]
    exercises: list[str] = []
    current_section = ""

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if _is_section_heading_line(line):
            current_section = line
            continue

        match = re.match(r"^b[àa]i\s*t[ậa]p\s*(\d+)\s*[:.-]?\s*(.*)$", line, flags=re.IGNORECASE)
        if not match:
            continue

        number = match.group(1)
        content = match.group(2).strip()
        prefix = f"{current_section} - " if current_section else ""
        if content:
            exercises.append(f"{prefix}Bài {number}: {content}")
        else:
            exercises.append(f"{prefix}Bài {number}")

    return exercises


def _extract_en_numbered_exercises(text: str) -> list[str]:
    exercises: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = re.match(r"^(\d+)\.\s+(.+)$", line)
        if match:
            exercises.append(f"Bài {match.group(1)}: {match.group(2).strip()}")
    return exercises


def _slice_text_by_chapter(text: str, chapter_number: int) -> str:
    if chapter_number < 1:
        return ""

    lines = text.splitlines()
    start = None
    chapter_start_pattern = re.compile(
        rf"^\s*(chapter|chuong)\s*{chapter_number}\b", flags=re.IGNORECASE
    )
    chapter_any_pattern = re.compile(r"^\s*(chapter|chuong)\s*\d+\b", flags=re.IGNORECASE)

    for idx, line in enumerate(lines):
        if chapter_start_pattern.search(line):
            start = idx
            break

    if start is None:
        return ""

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if chapter_any_pattern.search(lines[idx]):
            end = idx
            break

    return "\n".join(lines[start:end]).strip()


def _extract_chapter_title_keyword(query: str) -> str | None:
    normalized = normalize_for_match(query)
    if not normalized:
        return None

    marker = ""
    if "chuong " in normalized:
        marker = "chuong "
    elif "chapter " in normalized:
        marker = "chapter "

    if not marker:
        return None

    tail = normalized.split(marker, 1)[1].strip()
    if not tail:
        return None

    stop_tokens = {
        "co", "bao", "nhieu", "la", "gi", "trong", "tren", "duoi",
        "bai", "tap", "exercise", "so", "luong",
    }
    title_tokens: list[str] = []
    for token in tail.split():
        if token in stop_tokens and title_tokens:
            break
        if token in stop_tokens:
            continue
        if token.isdigit() and not title_tokens:
            continue
        title_tokens.append(token)

    return " ".join(title_tokens).strip() or None


def _slice_text_by_chapter_title(text: str, chapter_keyword: str) -> str:
    keyword = normalize_for_match(chapter_keyword)
    if not keyword:
        return ""

    lines = text.splitlines()
    start = None
    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue
        if keyword in normalize_for_match(line) and _is_section_heading_line(line):
            start = idx
            break

    if start is None:
        return ""

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        line = lines[idx].strip()
        if not line:
            continue
        if _is_section_heading_line(line):
            end = idx
            break

    return "\n".join(lines[start:end]).strip()


def _is_exercise_count_query(query: str) -> bool:
    q = normalize_for_match(query)
    if not q:
        return False
    has_exercise_signal = "bai tap" in q or "exercise" in q
    has_count_signal = "bao nhieu" in q or "so luong" in q or "dem" in q
    return has_exercise_signal and has_count_signal


def _is_exercise_content_query(query: str) -> str:
    q = normalize_for_match(query)
    match = re.search(r"\b(?:bai tap|exercise)\s*(\d+)\b", q)
    return match.group(1) if match else ""


def _is_architecture_style_count_query(query: str) -> bool:
    q = normalize_for_match(query)
    if not q:
        return False
    style_signal = "phong cach kien truc" in q or "architecture style" in q
    count_signal = "bao nhieu" in q or "so luong" in q or "count" in q
    return style_signal and count_signal


def _extract_architecture_styles_from_text(text: str) -> list[str]:
    styles: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("-•*")
        if not line:
            continue

        words = line.split()
        if len(words) > 6:
            continue
        if not re.search(r"[A-Za-z]", line):
            continue
        if line.lower().startswith(("chapter ", "chuong ", "bai tap ")):
            continue

        styles.append(line)

    return styles


def _is_beginner_recommendation_query(query: str) -> bool:
    q = normalize_for_match(query)
    return ("nguoi moi" in q) and ("tai lieu nao" in q or "hoc truoc" in q)


def _is_technology_suggestion_query(query: str) -> bool:
    q = normalize_for_match(query)
    has_topic = "cong nghe" in q or "thu vien" in q or "technology" in q
    has_ask = "goi y" in q or "dang chu y" in q or "de xuat" in q
    return has_topic and has_ask


def _is_section_heading_line(line: str) -> bool:
    candidate = line.strip()
    if not candidate:
        return False
    if candidate.startswith("[") and candidate.endswith("]"):
        return False

    normalized = normalize_for_match(candidate)
    if normalized.startswith("page "):
        return False
    if re.search(r"\b(bai tap|exercise|chapter|chuong)\b", normalized):
        return False
    if re.search(r"^\d+[.)]", normalized):
        return False
    if len(candidate) > 80:
        return False

    words = [word for word in re.split(r"\s+", candidate) if word]
    if not words:
        return False

    # Heuristic: chapter-like headings in this dataset are usually all caps.
    if candidate.upper() == candidate and re.search(r"[A-Za-zÀ-ỹ]", candidate):
        return True

    return False

@dataclass
class RAGAnswer:
    answer: str
    context_chunks: list[str]
    prompt: str
    confidence_score: int
    raw_docs: list[Any]


class RAGChainManager:
    """Application layer orchestration for retrieval and generation (Basic RAG)."""

    def __init__(self, index_dir: str, model_engine: OllamaInferenceEngine) -> None:
        self.vector_store_idx = index_dir
        self.model_engine = model_engine
        self._faiss_store = None

    def _get_faiss(self):
        if self._faiss_store is None:
            self._faiss_store = load_faiss_index(self.vector_store_idx)
        return self._faiss_store

    @staticmethod
    def _format_context_chunks(documents: list[Any]) -> list[str]:
        contexts: list[str] = []
        for idx, doc in enumerate(documents, start=1):
            content = (getattr(doc, "page_content", "") or "").strip()
            if not content:
                continue

            metadata = dict(getattr(doc, "metadata", {}) or {})
            source = str(metadata.get("source", ""))
            file_name = source_name_from_path(source) or "unknown"
            page = metadata.get("page", metadata.get("page_number", "n/a"))

            header = f"[Đoạn trích từ file: {file_name} | Trang: {page}]"
            contexts.append(f"{header}\n{content}".strip())

        return contexts

    def ask(
        self,
        question: str,
        top_k: int = 4,
        retrieval_query: str | None = None,
        chat_history: list[dict] | None = None,
        include_history: bool = False,
    ) -> RAGAnswer:
        question_text = question.strip()
        if not question_text:
            raise ValueError("Hãy nhập nội dung câu hỏi.")
        if top_k < 1:
            raise ValueError("top_k phải >= 1")
        retrieval_text = (retrieval_query or question_text).strip()
        if not retrieval_text:
            retrieval_text = question_text

        retrieved = search_similar_chunks(self.vector_store_idx, retrieval_text, top_k=top_k)
        contexts = self._format_context_chunks(retrieved)
        
        if not contexts:
            return RAGAnswer(
                answer="Không tìm thấy ngữ cảnh phù hợp trong tài liệu.",
                context_chunks=[],
                prompt="",
                confidence_score=0,
                raw_docs=[],
            )

        prompt = build_rag_prompt(
            question=question_text,
            contexts=contexts,
            chat_history=chat_history if include_history else None,
        )
        answer = self.model_engine.generate(prompt=prompt, question=question_text)
        
        confidence = self.model_engine.self_rag_confidence_score(
            query=question_text, answer=answer, docs=retrieved
        )

        return RAGAnswer(
            answer=answer, 
            context_chunks=contexts, 
            prompt=prompt, 
            confidence_score=confidence,
            raw_docs=retrieved
        )
