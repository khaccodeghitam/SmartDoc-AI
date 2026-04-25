"""Basic RAG Chain Manager. Thuần chủng LLM 1 shot."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.application.prompt_engineering import build_rag_prompt
from src.data_layer.faiss_vector_store import load_faiss_index, search_similar_chunks
from src.model_layer.ollama_inference_engine import OllamaInferenceEngine
from src.utils import clean_generated_answer, source_name_from_path


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
    def _notify_progress(progress_callback: Callable[[str], None] | None, message: str) -> None:
        if not progress_callback:
            return
        try:
            progress_callback(message)
        except Exception:
            # Never break QA flow if UI progress callback fails.
            pass

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
        source_filter: list[str] | None = None,
        chat_history: list[dict] | None = None,
        include_history: bool = False,
        progress_callback: Callable[[str], None] | None = None,
    ) -> RAGAnswer:
        question_text = question.strip()
        if not question_text:
            raise ValueError("Hãy nhập nội dung câu hỏi.")
        if top_k < 1:
            raise ValueError("top_k phải >= 1")
        retrieval_text = (retrieval_query or question_text).strip()
        if not retrieval_text:
            retrieval_text = question_text

        self._notify_progress(progress_callback, "Đang phân tích ngữ cảnh và truy xuất tài liệu liên quan...")
        retrieved = search_similar_chunks(
            self.vector_store_idx,
            retrieval_text,
            top_k=top_k,
            source_filter=source_filter,
        )
        contexts = self._format_context_chunks(retrieved)

        if not contexts:
            self._notify_progress(progress_callback, "Không tìm thấy ngữ cảnh phù hợp trong tài liệu.")
            return RAGAnswer(
                answer="Không tìm thấy ngữ cảnh phù hợp trong tài liệu.",
                context_chunks=[],
                prompt="",
                confidence_score=0,
                raw_docs=[],
            )

        self._notify_progress(progress_callback, "Đang xây dựng prompt từ ngữ cảnh truy xuất...")
        prompt = build_rag_prompt(
            question=question_text,
            contexts=contexts,
            chat_history=chat_history if include_history else None,
        )
        self._notify_progress(progress_callback, "Đang tìm câu trả lời bằng mô hình ngôn ngữ...")
        answer = clean_generated_answer(self.model_engine.generate(prompt=prompt, question=question_text))

        self._notify_progress(progress_callback, "Đang tóm tắt và chấm độ tự tin câu trả lời...")
        confidence = self.model_engine.self_rag_confidence_score(
            query=question_text, answer=answer, docs=retrieved
        )
        self._notify_progress(progress_callback, "Đã hoàn tất.")

        return RAGAnswer(
            answer=answer,
            context_chunks=contexts,
            prompt=prompt,
            confidence_score=confidence,
            raw_docs=retrieved
        )
