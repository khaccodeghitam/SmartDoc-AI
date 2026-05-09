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
            f"Câu hỏi gồm {len(question_parts)} ý. Hãy trả lời đầy đủ từng ý một cách rõ ràng.\n"
            "Mỗi ý trả lời 2-4 gạch đầu dòng hoặc đoạn văn ngắn gọn.\n"
            "KHÔNG tự suy diễn mốc thời gian/sự kiện ngoài ngữ cảnh đã cho.\n"
        )

    doc_overview_text = f"Tổng quan tài liệu:\n{document_overview}\n\n" if document_overview else ""

    if detect_vietnamese(question) or not is_probably_english_query(question):
        return (
            "⚠️ BẮT BUỘC: TRẢ LỜI HOÀN TOÀN BẰNG TIẾNG VIỆT. Không được phép trả lời tiếng Anh, tiếng Trung, hay ngôn ngữ khác.\n\n"
            "Dựa vào ngữ cảnh được cung cấp để trả lời câu hỏi. Hãy nỗ lực tìm kiếm và tổng hợp thông tin liên quan dù là một phần.\n"
            "QUY TẮC TƯ DUY:\n"
            "1. Kiểm tra kỹ các con số khi so sánh (ví dụ: 150 nhỏ hơn 160).\n"
            "2. Xác định đúng vai trò: FAISS = Vector/Ngữ nghĩa, BM25 = Từ khóa/Văn bản.\n"
            "3. Chỉ khi hoàn toàn không có bất kỳ dữ kiện nào liên quan, hãy trả lời là không tìm thấy.\n"
            "Kèm tên file gốc khi trích dẫn [file.pdf]. Không tự bịa thông tin ngoài context.\n\n"
            f"{multi_part_hint}"
            f"{doc_overview_text}"
            f"{history_text}"
            f"Ngữ cảnh tài liệu:\n{context_text}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Trả lời logic và chính xác:"
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
        "Bạn là giám định viên thông tin. Hãy kiểm tra xem ngữ cảnh dưới đây có chứa nội dung để trả lời cho câu hỏi không.\n"
        "⚠️ ALWAYS RESPOND IN VIETNAMESE ONLY, regardless of context language.\n\n"
        f"CÂU HỎI: {question}\n\n"
        f"NGỮ CẢNH HIỆN TẠI:\n{context_text}\n\n"
        "QUY TẮC:\n"
        "- Nếu ngữ cảnh ĐÃ CÓ thông tin chính (ví dụ: đã thấy tên chương, định nghĩa hoặc nội dung cốt lõi): Trả lời duy nhất từ 'SUFFICIENT'.\n"
        "- Chỉ khi hoàn toàn không có thông tin hoặc thông tin quá sơ sài: Trả lời 'SUB_QUERY: <câu hỏi tìm kiếm bổ sung>'.\n"
        "Ưu tiên trả lời SUFFICIENT để tiết kiệm thời gian."
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
            "⚠️ QUAN TRỌNG: TRẢ LỜI PHẢI BẰNG TIẾNG VIỆT. Nếu context có tiếng Anh, hãy dịch/tóm tắt sang tiếng Việt.\n\n"
            "Dựa hoàn toàn vào ngữ cảnh để trả lời câu hỏi. Ưu tiên giữ nguyên các thuật ngữ chuyên môn và tiêu đề từ ngữ cảnh.\n"
            "TUYỆT ĐỐI KHÔNG lặp lại nội dung và KHÔNG tự bịa ra từ ngữ mới. Trình bày trung thực, chính xác.\n\n"
            f"{doc_overview_text}"
            f"{history_text}"
            f"NGỮ CẢNH TÀI LIỆU:\n{context_text}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "CÂU TRẢ LỜI (TRÍCH XUẤT CHÍNH XÁC, TIẾNG VIỆT):"
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
