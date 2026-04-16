"""Prompt engineering: language detection, prompt building, chat history context."""
from __future__ import annotations

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

    doc_overview_text = f"Tổng quan tài liệu:\n{document_overview}\n\n" if document_overview else ""

    if detect_vietnamese(question) or not is_probably_english_query(question):
        return (
            "Dựa théo các ngữ cảnh sau đây để trả lời câu hỏi.\n"
            "Nếu không đủ thông tin, hãy nói rõ là không tìm thấy thông tin trong tài liệu.\n"
            "Trả lời ngắn gọn, đúng trọng tâm bằng tiếng Việt.\n"
            "Nếu có thông tin trích dẫn thì hãy kèm tham chiếu nguồn bằng tên file gốc (Ví dụ: [file.pdf]).\n"
            "KHÔNG gọi chung chung là 'Tài liệu 1', 'Tài liệu 2', hãy nêu rõ tên tài liệu.\n\n"
            "KHONG duoc bo sung thong tin ngoai context, khong tu tien the hien danh sach bai tap neu context khong co.\n\n"
            f"{doc_overview_text}"
            f"{history_text}"
            f"Ngữ cảnh tài liệu:\n{context_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Trả lời:"
        )

    return (
        "Use the following context to answer the question.\n"
        "If you don't know the answer, say you don't know.\n"
        "Keep answer concise and to the point.\n"
        "If citing information, include source references.\n\n"
        "Do not add facts outside the context.\n\n"
        f"{doc_overview_text}"
        f"{history_text}"
        f"Document Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )


# ---------------------------------------------------------------------------
# Co-RAG Prompt Building
# ---------------------------------------------------------------------------

def build_corag_sufficiency_check_prompt(question: str, contexts: list[str]) -> str:
    context_text = "\n\n".join(contexts) if contexts else "(Chưa có ngữ cảnh)"
    return (
        "Bạn là một trợ lý thông minh đóng vai trò Đánh Giá Context (Sufficiency Assessor).\n"
        "Mục tiêu là xác định xem các đoạn ngữ cảnh hiện tại đã ĐỦ thông tin để trả lời câu hỏi hay chưa.\n\n"
        f"Câu hỏi: {question}\n\n"
        f"Ngữ cảnh hiện tại:\n{context_text}\n\n"
        "Nhiệm vụ:\n"
        "1. Nếu NGỮ CẢNH HIỆN TẠI ĐÃ ĐỦ ĐỂ TRẢ LỜI CÂU HỎI MỘT CÁCH TRỌN VẸN: Hãy phản hồi đúng một chữ 'SUFFICIENT'.\n"
        "2. Nếu NGỮ CẢNH CHƯA ĐỦ (thiếu thông tin quan trọng): Hãy sinh ra MỘT câu truy vấn tìm kiếm MỚI (sub-query) "
        "bổ sung từ khóa để hệ thống có thể kéo thêm thông tin cần thiết từ vector store.\n"
        "  - Định dạng sub-query bắt buộc phải bắt đầu bằng 'SUB_QUERY:' (ví dụ: SUB_QUERY: so luong bai tap chuong 2).\n"
        "  - KHÔNG giải thích dài dòng."
    )


def build_corag_final_prompt(
    question: str, 
    contexts: list[str], 
    document_overview: str = ""
) -> str:
    context_text = "\n\n".join(contexts)
    doc_overview_text = f"Tổng quan tài liệu:\n{document_overview}\n\n" if document_overview else ""

    if detect_vietnamese(question) or not is_probably_english_query(question):
        return (
            "Dựa théo các ngữ cảnh sau đây để trả lời câu hỏi.\n"
            "Hãy trả lời ở mức độ chi tiết và có giải thích. Dùng gạch đầu dòng nếu cần thiết.\n"
            "Tham chiếu nguồn bằng tên file gốc (Ví dụ: [file.pdf]). KHÔNG gọi chung chung là 'Tài liệu 1', 'Tài liệu 2'.\n\n"
            f"{doc_overview_text}"
            f"Ngữ cảnh tài liệu tích lũy được:\n{context_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Câu trả lời:"
        )

    return (
        "Use the following detailed context to answer the question.\n"
        "Provide a VERY DETAILED, COMPREHENSIVE, AND IN-DEPTH answer.\n"
        "Do not be brief. Explain the rationale and use bullet points where necessary.\n\n"
        f"{doc_overview_text}"
        f"Accumulated Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Detailed Answer:"
    )
