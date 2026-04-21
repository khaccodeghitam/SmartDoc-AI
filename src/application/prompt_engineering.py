"""Prompt engineering: language detection, prompt building, chat history context."""
from __future__ import annotations

import re
from typing import Iterable

from langchain_core.documents import Document

from src.utils import normalize_for_match


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def detect_vietnamese(text: str) -> bool:
    vietnamese_chars = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    text_lower = text.lower()
    return any(char in text_lower for char in vietnamese_chars)


def is_probably_english_query(text: str) -> bool:
    normalized = normalize_for_match(text)
    tokens = [token for token in normalized.split() if token]
    if not tokens:
        return False

    english_markers = {
        "what", "how", "why", "when", "where", "which", "who",
        "count", "many", "number", "list", "show", "chapter", "exercise",
    }
    marker_hits = sum(1 for token in tokens if token in english_markers)
    return marker_hits >= 1


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def answer_without_footer(answer_text: str) -> str:
    return answer_text.split("---", 1)[0].strip()


def build_chat_history_context(chat_history: list[dict] | None, max_turns: int = 4) -> str:
    if not chat_history:
        return ""

    turns = list(reversed(chat_history[:max_turns]))
    lines: list[str] = []
    for turn in turns:
        question = str(turn.get("question", "")).strip()
        answer = answer_without_footer(str(turn.get("answer", ""))).strip()
        if not question and not answer:
            continue
        if question:
            lines.append(f"- User: {question[:220]}")
        if answer:
            lines.append(f"- Assistant: {answer[:260]}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Basic RAG Prompt Building
# ---------------------------------------------------------------------------

def build_rag_prompt(
    question: str, 
    contexts: list[str], 
    document_overview: str = "",
    chat_history: list[dict] | None = None
) -> str:
    context_text = "\n\n".join(contexts)
    history_context = build_chat_history_context(chat_history)
    history_text = f"Lịch sử hội thoại liên quan:\n{history_context}\n\n" if history_context else ""
    question_parts = [part.strip() for part in re.split(r"[\n\?]+", question) if part.strip()]
    multi_part_hint = ""
    if len(question_parts) > 1:
        multi_part_hint = (
            f"Câu hỏi gồm {len(question_parts)} ý. BẮT BUỘC trả lời đủ từng ý theo thứ tự 1..{len(question_parts)}. "
            "Ý nào không thấy trong tài liệu thì ghi rõ: 'Không thấy thông tin trong tài liệu'.\n"
            "Mỗi ý trả lời tối đa 1-2 câu, không lan man.\n"
        )

    doc_overview_text = f"Tổng quan tài liệu:\n{document_overview}\n\n" if document_overview else ""

    if detect_vietnamese(question) or not is_probably_english_query(question):
        return (
            "Dựa vào ngữ cảnh trả lời câu hỏi. Trả lời ngắn gọn, chính xác.\n"
            "Nếu không có thông tin, nói rõ là không tìm thấy.\n"
            "Kèm tên file gốc khi trích dẫn [file.pdf], không gọi chung chung.\n"
            "Không thêm thông tin ngoài context. Không chép lại ngữ cảnh, không ghi 'Dữ liệu gốc' hay 'Ngữ cảnh đã dùng'.\n\n"
            f"{multi_part_hint}"
            f"{doc_overview_text}"
            f"{history_text}"
            f"Ngữ cảnh tài liệu:\n{context_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Trả lời:"
        )

    return (
        "Answer based on context provided. Be concise and accurate.\n"
        "If information not found, state it clearly.\n"
        "Include file name when citing [file.pdf].\n"
        "Do not add facts outside context. Do not repeat the raw context or echo headings like 'Context' or 'Document Context'.\n\n"
        f"{multi_part_hint}"
        f"{doc_overview_text}"
        f"{history_text}"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )


# ---------------------------------------------------------------------------
# Co-RAG Prompt Building
# ---------------------------------------------------------------------------

def build_corag_sufficiency_check_prompt(question: str, contexts: list[str]) -> str:
    context_text = "\n\n".join(contexts) if contexts else "(Chưa có ngữ cảnh)"
    return (
        "Đánh giá: ngữ cảnh hiện tại có đủ trả lời câu hỏi không?\n\n"
        f"Câu hỏi: {question}\n\n"
        f"Ngữ cảnh hiện tại:\n{context_text}\n\n"
        "Nếu ĐỦ: Trả lời 'SUFFICIENT'.\n"
        "Nếu CHƯA ĐỦ: Trả lời 'SUB_QUERY: <tìm kiếm bổ sung>' (không giải thích thêm)."
    )


def build_corag_final_prompt(
    question: str, 
    contexts: list[str], 
    document_overview: str = "",
    chat_history: list[dict] | None = None,
) -> str:
    context_text = "\n\n".join(contexts)
    history_context = build_chat_history_context(chat_history)
    history_text = f"Lịch sử hội thoại liên quan:\n{history_context}\n\n" if history_context else ""
    doc_overview_text = f"Tổng quan tài liệu:\n{document_overview}\n\n" if document_overview else ""

    if detect_vietnamese(question) or not is_probably_english_query(question):
        return (
            "Dựa vào ngữ cảnh trả lời chi tiết. Kèm tên file gốc [file.pdf].\n"
            "Không gọi chung chung 'Tài liệu 1', 'Tài liệu 2'. Không lặp lại nguyên văn ngữ cảnh hay thêm mục 'Dữ liệu gốc'.\n\n"
            f"{doc_overview_text}"
            f"{history_text}"
            f"Ngữ cảnh tài liệu tích lũy được:\n{context_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Câu trả lời:"
        )

    return (
        "Use the following detailed context to answer the question.\n"
        "Provide a VERY DETAILED, COMPREHENSIVE, AND IN-DEPTH answer.\n"
        "Do not be brief. Explain the rationale and use bullet points where necessary.\n\n"
        f"{doc_overview_text}"
        f"{history_text}"
        f"Accumulated Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Detailed Answer:"
    )
