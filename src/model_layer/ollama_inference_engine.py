"""Ollama LLM inference engine: invoke, fallback, Self-RAG scoring."""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field

from langchain_ollama import OllamaLLM
from langchain_core.documents import Document
import streamlit as st

from src.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    FALLBACK_MODELS,
    SCORING_MAX_DOCS,
    SCORING_EXCERPT_CHARS,
    SCORING_CONTEXT_MAX_CHARS,
)
from src.utils import keyword_overlap_score, normalize_for_match, source_name_from_path

logger = logging.getLogger(__name__)


def is_retryable_llm_error(error: Exception) -> bool:
    """Check if an LLM error is retryable (OOM, connection issues)."""
    error_text = str(error).lower()
    memory_keywords = [
        "out of memory", "requires more system memory", "insufficient memory", "cuda out of memory",
    ]
    connection_keywords = [
        "connection refused", "failed to connect", "connecterror", "read timed out",
        "timed out", "max retries exceeded", "llama runner process has terminated",
        "status code: 500", "service unavailable", "temporary failure",
    ]
    return any(keyword in error_text for keyword in (memory_keywords + connection_keywords))


def _build_context_for_scoring(docs: list[Document]) -> str:
    context_blocks: list[str] = []
    current_len = 0
    for idx, doc in enumerate(docs[:SCORING_MAX_DOCS], start=1):
        metadata = doc.metadata or {}
        source_name = source_name_from_path(str(metadata.get("source", "unknown"))) or "unknown"
        page = metadata.get("page", metadata.get("page_number", "n/a"))
        excerpt = (doc.page_content or "").strip()[:SCORING_EXCERPT_CHARS]
        block = f"[S{idx}] file={source_name}, page={page}\n{excerpt}"
        if current_len + len(block) > SCORING_CONTEXT_MAX_CHARS:
            break
        context_blocks.append(block)
        current_len += len(block)

    return "\n\n".join(context_blocks)


def _heuristic_confidence_score(query: str, answer: str, context_text: str) -> int:
    answer_text = (answer or "").strip()
    if not answer_text:
        return 1

    query_alignment = keyword_overlap_score(query, answer_text)
    context_alignment = keyword_overlap_score(context_text, answer_text)
    answer_length = len(normalize_for_match(answer_text))

    length_score = 0.0
    if answer_length >= 200:
        length_score = 1.0
    elif answer_length >= 120:
        length_score = 0.7
    elif answer_length >= 60:
        length_score = 0.4
    else:
        length_score = 0.1

    blended = (query_alignment * 3.5) + (context_alignment * 4.0) + (length_score * 2.5)
    return max(1, min(10, int(round(blended))))


class OllamaInferenceEngine:
    """Class encapsulate LLM invocation with fallback logic."""

    def __init__(self, model_name: str = OLLAMA_MODEL, temperature: float = 0.2):
        self.model_name = model_name
        self.temperature = temperature
        
        # Determine the actual model to use based on sticky fallbacks
        self.active_model = self.model_name
        if "sticky_fallbacks" in st.session_state and self.model_name in st.session_state["sticky_fallbacks"]:
            for fallback in FALLBACK_MODELS:
                if fallback not in st.session_state.get("sticky_fallbacks", []):
                    self.active_model = fallback
                    break

        self._llm = OllamaLLM(
            model=self.active_model,
            base_url=OLLAMA_BASE_URL,
            temperature=self.temperature,
            num_gpu=99,
            num_thread=8,
            num_ctx=3000,
        )

    def _get_llm(self, model: str) -> OllamaLLM:
        return OllamaLLM(
            model=model,
            base_url=OLLAMA_BASE_URL,
            temperature=self.temperature,
            num_gpu=99,
            num_thread=8,
            num_ctx=3000,
        )

    def generate(self, prompt: str, question: str = "", document_name: str = "") -> str:
        """Thực thi câu truy vấn tới LLM, có mechanism fallback nếu lỗi model."""
        try:
            return str(self._llm.invoke(prompt)).strip()
        except Exception as e:
            if is_retryable_llm_error(e):
                logger.warning(f"Error accessing model {self.active_model}: {e}. Trying fallbacks...")
                
                # Mark current model as failed for this session
                if "sticky_fallbacks" not in st.session_state:
                    st.session_state["sticky_fallbacks"] = []
                if self.active_model not in st.session_state["sticky_fallbacks"]:
                    st.session_state["sticky_fallbacks"].append(self.active_model)
                
                for fallback in FALLBACK_MODELS:
                    if fallback in st.session_state.get("sticky_fallbacks", []):
                        continue
                    try:
                        fallback_llm = self._get_llm(fallback)
                        result = str(fallback_llm.invoke(prompt)).strip()
                        # Update current engine to use this successful fallback next time
                        self.active_model = fallback
                        self._llm = fallback_llm
                        return result
                    except Exception as fb_err:
                        logger.warning(f"Fallback {fallback} failed: {fb_err}")
            raise

    def self_rag_confidence_score(self, query: str, answer: str, docs: list[Document]) -> int:
        """Let the LLM evaluate its own answer against the retrieved context (1-10)."""
        context_text = _build_context_for_scoring(docs)
        scoring_prompt = (
            "Ban la bo phan cham diem do tin cay.\n"
            "Dua tren cau hoi, context truyen vao va cau tra loi.\n"
            "Chiem diem theo thang 1-10, trong do: 1-3 = sai/rat yeu, 4-6 = tam on, 7-8 = tot, 9-10 = rat chac chan va bam sat context.\n"
            "Chi tra ve DUY NHAT mot so nguyen tu 1 den 10.\n\n"
            f"Cau hoi: {query}\n\n"
            f"Context:\n{context_text}\n\n"
            f"Cau tra loi: {answer}\n\n"
            "Diem (1-10):"
        )
        try:
            score_raw = str(self._llm.invoke(scoring_prompt)).strip()
            matched = re.search(r"\d+", score_raw)
            model_score = int(matched.group()) if matched else 6
            model_score = max(1, min(10, model_score))
            heuristic_score = _heuristic_confidence_score(query=query, answer=answer, context_text=context_text)
            blended_score = round((model_score * 0.55) + (heuristic_score * 0.45))
            return max(1, min(10, blended_score))
        except Exception:
            return _heuristic_confidence_score(query=query, answer=answer, context_text=context_text)
