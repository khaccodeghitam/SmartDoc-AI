"""CoRAG – Chain-of-Retrieval Augmented Generation.

Thuộc Application Layer — điều phối vòng lặp truy xuất đa bước.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from src.application.prompt_engineering import (
    build_corag_final_prompt,
    build_corag_sufficiency_check_prompt,
)
from src.data_layer.faiss_vector_store import (
    filter_low_quality_chunks,
    load_faiss_index,
    search_similar_chunks,
)
from src.model_layer.ollama_inference_engine import OllamaInferenceEngine
from src.utils import clean_generated_answer, source_name_from_path

_SUFFICIENT_SIGNAL = "SUFFICIENT"


@dataclass
class CoRAGIteration:
    """Kết quả một vòng truy xuất trong chuỗi CoRAG."""
    round_num: int
    sub_query: str
    retrieved_chunks: list[str] = field(default_factory=list)
    llm_assessment: str = ""


@dataclass
class CoRAGAnswer:
    """Kết quả trả về từ CoRAGChainManager."""
    answer: str
    context_chunks: list[str]
    iterations: list[CoRAGIteration]
    final_prompt: str
    total_rounds: int
    confidence_score: int


class CoRAGChainManager:
    """Application layer orchestration cho Chain-of-Retrieval Augmented Generation."""

    def __init__(
        self,
        index_dir: str,
        model_engine: OllamaInferenceEngine,
        max_rounds: int = 3,
        top_k: int = 4,
    ) -> None:
        self.vector_store_idx = index_dir
        self.model_engine = model_engine
        self.max_rounds = max_rounds
        self.top_k = top_k
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
    def _is_explicit_sufficient_signal(assessment: str) -> bool:
        """Accept only explicit SUFFICIENT responses to avoid false positives like INSUFFICIENT."""
        normalized = (assessment or "").strip().upper()
        if not normalized:
            return False

        first_line = normalized.splitlines()[0].strip()
        if not first_line:
            return False

        first_word = first_line.split()[0].strip(".,:;!?()[]{}\"'`")
        return first_word == _SUFFICIENT_SIGNAL

    def _retrieve_and_format_chunks(
        self,
        query: str,
        source_filter: list[str] | None = None,
    ) -> tuple[list[str], list[Any]]:
        retrieved = search_similar_chunks(
            self.vector_store_idx,
            query,
            top_k=self.top_k,
            aggressive_rerank=False,
            source_filter=source_filter,
        )
        # Keep shorter chunks too, because exercise headings like "BÀI TẬP 2..."
        # are often concise but critical for counting questions.
        quality_filtered = filter_low_quality_chunks(retrieved, query=query, min_length=20)
        chunks: list[str] = []
        for idx, doc in enumerate(quality_filtered, start=1):
            content = (getattr(doc, "page_content", "") or "").strip()
            if not content:
                continue

            metadata = dict(getattr(doc, "metadata", {}) or {})
            source = str(metadata.get("source", ""))
            file_name = source_name_from_path(source) or "unknown"
            page = metadata.get("page", metadata.get("page_number", "n/a"))

            header = f"[Đoạn trích từ file: {file_name} | Trang: {page}]"
            chunks.append(f"{header}\n{content}".strip())

        return chunks, quality_filtered

    @staticmethod
    def _deduplicate_chunks(existing: list[str], new_chunks: list[str]) -> list[str]:
        seen = set(existing)
        result = list(existing)
        for chunk in new_chunks:
            if chunk not in seen:
                result.append(chunk)
                seen.add(chunk)
        return result

    def _assess_sufficiency(self, question: str, accumulated_context: list[str]) -> str:
        prompt = build_corag_sufficiency_check_prompt(question=question, contexts=accumulated_context)
        return self.model_engine.generate(prompt=prompt, question=question).strip()

    @staticmethod
    def _is_cancelled(stop_signal: Any | None) -> bool:
        if stop_signal is None:
            return False
        checker = getattr(stop_signal, "is_set", None)
        if callable(checker):
            try:
                return bool(checker())
            except Exception:
                return False
        return False

    def ask(
        self,
        question: str,
        retrieval_query: str | None = None,
        source_filter: list[str] | None = None,
        chat_history: list[dict] | None = None,
        include_history: bool = False,
        stop_signal: Any | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> CoRAGAnswer:
        question_text = question.strip()
        if not question_text:
            raise ValueError("Hãy nhập nội dung câu hỏi.")
        retrieval_text = (retrieval_query or question_text).strip()
        if not retrieval_text:
            retrieval_text = question_text

        self._notify_progress(progress_callback, "Đang khởi tạo Co-RAG và kiểm tra dữ liệu truy xuất...")
        store = self._get_faiss()
        all_docs = list(store.docstore._dict.values())
        if not all_docs:
            raise ValueError("Vector store chưa có dữ liệu.")

        iterations: list[CoRAGIteration] = []
        accumulated_context: list[str] = []
        all_raw_retrieved_docs: list[Any] = []

        # Vòng 1
        if self._is_cancelled(stop_signal):
            raise RuntimeError("Co-RAG cancelled by user.")
        self._notify_progress(progress_callback, "Vòng 1: đang truy xuất ngữ cảnh ban đầu...")
        initial_chunks, raw_docs = self._retrieve_and_format_chunks(
            retrieval_text,
            source_filter=source_filter,
        )
        all_raw_retrieved_docs.extend(raw_docs)

        accumulated_context = self._deduplicate_chunks(accumulated_context, initial_chunks)
        iterations.append(
            CoRAGIteration(
                round_num=1,
                sub_query=retrieval_text,
                retrieved_chunks=list(initial_chunks),
                llm_assessment="",
            )
        )

        # Vòng 2..max_rounds
        for round_num in range(2, self.max_rounds + 1):
            if self._is_cancelled(stop_signal):
                raise RuntimeError("Co-RAG cancelled by user.")
            self._notify_progress(
                progress_callback,
                f"Vòng {round_num - 1}: đang đánh giá mức độ đủ thông tin...",
            )
            assessment = self._assess_sufficiency(
                question=question_text,
                accumulated_context=accumulated_context,
            )

            prev = iterations[-1]
            iterations[-1] = CoRAGIteration(
                round_num=prev.round_num,
                sub_query=prev.sub_query,
                retrieved_chunks=prev.retrieved_chunks,
                llm_assessment=assessment,
            )

            if self._is_explicit_sufficient_signal(assessment):
                self._notify_progress(progress_callback, "Ngữ cảnh đã đủ, chuyển sang bước tổng hợp câu trả lời Co-RAG...")
                break

            sub_query = _extract_subquery(assessment, fallback=retrieval_text)
            # Keep retrieval anchored to the original question to reduce topic drift.
            anchored_query = f"{question_text}\n{sub_query}".strip()
            self._notify_progress(
                progress_callback,
                f"Vòng {round_num}: đang mở rộng truy xuất với sub-query mới...",
            )
            new_chunks, new_raw_docs = self._retrieve_and_format_chunks(
                anchored_query,
                source_filter=source_filter,
            )
            accumulated_context = self._deduplicate_chunks(accumulated_context, new_chunks)
            all_raw_retrieved_docs.extend(new_raw_docs)

            iterations.append(
                CoRAGIteration(
                    round_num=round_num,
                    sub_query=sub_query,
                    retrieved_chunks=list(new_chunks),
                    llm_assessment="",
                )
            )

        # Trả lời vòng cuối
        if self._is_cancelled(stop_signal):
            raise RuntimeError("Co-RAG cancelled by user.")
        self._notify_progress(progress_callback, "Đang tổng hợp và tóm tắt câu trả lời cuối...")
        final_prompt = build_corag_final_prompt(
            question=question_text,
            contexts=accumulated_context,
            document_overview="",
            chat_history=chat_history if include_history else None,
        )
        answer = clean_generated_answer(self.model_engine.generate(prompt=final_prompt, question=question_text))
        
        # Self-RAG score
        self._notify_progress(progress_callback, "Đang chấm độ tự tin kết quả...")
        confidence = self.model_engine.self_rag_confidence_score(
            query=question_text, answer=answer, docs=all_raw_retrieved_docs
        )
        self._notify_progress(progress_callback, "Đã hoàn tất.")

        return CoRAGAnswer(
            answer=answer,
            context_chunks=accumulated_context,
            iterations=iterations,
            final_prompt=final_prompt,
            total_rounds=len(iterations),
            confidence_score=confidence,
        )


def _extract_subquery(llm_response: str, fallback: str) -> str:
    lower = llm_response.lower()
    for prefix in ("sub_query:", "sub-query:", "query:", "search for:", "retrieve:"):
        idx = lower.find(prefix)
        if idx != -1:
            candidate = llm_response[idx + len(prefix):].strip().split("\n")[0].strip()
            if candidate:
                return candidate
    # If the assessment does not provide an explicit sub-query field,
    # fall back to the original retrieval query to avoid drifting to
    # noisy phrases like "CHƯA ĐỦ: TRẢ LỜI BỔ SUNG".
    return fallback
