"""Streamlit application entry point - Presentation Layer."""
from __future__ import annotations

from datetime import datetime
from concurrent.futures import Future, ThreadPoolExecutor
import html
import inspect
import re
from pathlib import Path
from threading import Event
import uuid

import streamlit as st

from src.config import APP_TITLE, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_TOP_K, OLLAMA_MODEL
from src.data_layer.conversation_store import (
    save_persistent_history, load_persistent_history,
    save_app_session, load_app_session,
)
from src.data_layer.faiss_vector_store import (
    clear_vector_store_data,
    search_similar_chunks,
    search_vector_only_chunks,
)
from src.application.document_processing_pipeline import (
    ingest_multiple_uploaded_files,
    evaluate_chunk_strategies,
)
from src.application.query_rewriter import rewrite_query_with_history, should_include_history_in_prompt
from src.data_layer.faiss_vector_store import build_and_save_faiss_index, update_faiss_index
from src.application.rag_chain_manager import RAGChainManager, RAGAnswer
from src.application.corag_chain_manager import CoRAGChainManager, CoRAGAnswer
from src.model_layer.ollama_inference_engine import OllamaInferenceEngine
from src.presentation.ui_config import (
    apply_styles,
    render_chip_row,
    render_hero,
    render_model_badge,
    render_sidebar_header,
)

_CORAG_EXECUTOR = ThreadPoolExecutor(max_workers=2)
_CORAG_JOBS: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def _init_state() -> None:
    # Restore persisted index session on fresh load (after F5)
    if "last_index_dir" not in st.session_state:
        saved = load_app_session()
        st.session_state["last_index_dir"] = saved.get("last_index_dir", "")
        st.session_state["last_index_name"] = saved.get("last_index_name", "")
        st.session_state["last_uploaded_file"] = saved.get("last_uploaded_file", "")
        st.session_state["available_sources"] = saved.get("available_sources", [])
        st.session_state["available_file_types"] = saved.get("available_file_types", [])
        st.session_state["available_upload_dates"] = saved.get("available_upload_dates", [])
    st.session_state.setdefault("last_index_dir", "")
    st.session_state.setdefault("last_index_name", "")
    st.session_state.setdefault("last_uploaded_file", "")
    st.session_state.setdefault("retrieval_history", [])
    st.session_state.setdefault("last_chunks", [])
    st.session_state.setdefault("last_bi_encoder_chunks", [])
    st.session_state.setdefault("last_vector_only_chunks", [])
    st.session_state.setdefault("last_query", "")
    if "chat_sessions" not in st.session_state:
        st.session_state["chat_sessions"] = load_persistent_history()
    st.session_state.setdefault("active_session_id", None)
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("confirm_clear_status", False)

    st.session_state.setdefault("sidebar_source_filter", [])
    st.session_state.setdefault("sidebar_file_type_filter", [])
    st.session_state.setdefault("sidebar_upload_date_filter", [])
    st.session_state.setdefault("active_model", OLLAMA_MODEL)
    st.session_state.setdefault("is_fallback_model", False)
    st.session_state.setdefault("ingest_notice", "")
    st.session_state.setdefault("available_sources", [])
    st.session_state.setdefault("available_file_types", [])
    st.session_state.setdefault("available_upload_dates", [])
    st.session_state.setdefault("last_ingested_paths", [])
    st.session_state.setdefault("chunk_benchmark_rows", [])
    st.session_state.setdefault("pending_sidebar_filter_reset", False)
    st.session_state.setdefault("sticky_fallbacks", [])
    st.session_state.setdefault("pending_qa", None)
    st.session_state.setdefault("clear_qa_query_pending", False)
    st.session_state.setdefault("qa_generation_in_progress", False)
    st.session_state.setdefault("qa_requires_pause", False)
    st.session_state.setdefault("qa_submit_requested", False)


def _clear_pending_qa_state() -> None:
    st.session_state["pending_qa"] = None


def _request_clear_qa_query() -> None:
    st.session_state["clear_qa_query_pending"] = True


def _request_qa_generation() -> None:
    st.session_state["qa_submit_requested"] = True
    st.session_state["qa_generation_in_progress"] = True


def _extract_pending_qa_from_history(chat_history: list[dict] | None) -> dict | None:
    if not chat_history:
        return None

    for item in chat_history:
        if not bool(item.get("is_pending_selection", False)):
            continue
        if str(item.get("selected_source", "")).strip():
            continue

        return {
            "turn_id": str(item.get("turn_id", "")).strip(),
            "question": str(item.get("question", "")).strip(),
            "rewritten_query": str(item.get("rewritten_query", "")).strip(),
            "include_history": bool(item.get("include_history", False)),
            "used_rewrite": bool(item.get("used_rewrite", False)),
            "corag_state": str(item.get("corag_state", "pending")),
            "rag": {
                "answer": str(item.get("rag_answer", "")),
                "confidence": item.get("rag_confidence"),
                "contexts": list(item.get("rag_contexts", [])),
                "error": str(item.get("rag_error", "")),
            },
            "corag": {
                "answer": str(item.get("corag_answer", "")),
                "confidence": item.get("corag_confidence"),
                "total_rounds": int(item.get("corag_total_rounds", 0) or 0),
                "iterations": list(item.get("corag_iterations", [])),
                "error": str(item.get("corag_error", "")),
            },
        }

    return None


def _refresh_pending_qa_from_current_history() -> None:
    st.session_state["pending_qa"] = _extract_pending_qa_from_history(st.session_state.get("chat_history", []))


def _cancel_corag_job(turn_id: str) -> None:
    job = _CORAG_JOBS.get(turn_id)
    if not job:
        return
    cancel_event = job.get("cancel_event")
    if cancel_event:
        cancel_event.set()
    future = job.get("future")
    if isinstance(future, Future):
        future.cancel()
    _CORAG_JOBS.pop(turn_id, None)


def _start_corag_background_job(
    turn_id: str,
    question: str,
    rewritten_query: str,
    include_history: bool,
    history_for_corag: list[dict],
    last_index_dir: str,
    top_k: int,
    active_model: str,
) -> None:
    cancel_event = Event()

    def _job() -> dict:
        model_engine = OllamaInferenceEngine(model_name=active_model)
        co_manager = CoRAGChainManager(index_dir=last_index_dir, model_engine=model_engine, top_k=top_k)
        try:
            corag_ans = co_manager.ask(
                question=question,
                retrieval_query=rewritten_query,
                chat_history=history_for_corag,
                include_history=include_history,
                stop_signal=cancel_event,
            )
            return {
                "answer": corag_ans.answer,
                "confidence": corag_ans.confidence_score,
                "total_rounds": corag_ans.total_rounds,
                "iterations": [
                    {
                        "llm_assessment": iteration.llm_assessment,
                        "sub_query": iteration.sub_query,
                        "retrieved_chunks_count": len(iteration.retrieved_chunks),
                    }
                    for iteration in corag_ans.iterations
                ],
                "error": "",
            }
        except Exception as exc:
            return {
                "answer": "",
                "confidence": None,
                "total_rounds": 0,
                "iterations": [],
                "error": str(exc),
            }

    future = _CORAG_EXECUTOR.submit(_job)
    _CORAG_JOBS[turn_id] = {"future": future, "cancel_event": cancel_event}


def _collect_corag_result_if_ready(pending: dict | None) -> dict | None:
    if not pending:
        return None

    turn_id = str(pending.get("turn_id", "")).strip()
    if not turn_id:
        return pending

    job = _CORAG_JOBS.get(turn_id)
    if not job:
        return pending

    future = job.get("future")
    if not isinstance(future, Future) or not future.done():
        return pending

    try:
        result = future.result()
    except Exception as exc:
        result = {
            "answer": "",
            "confidence": None,
            "total_rounds": 0,
            "iterations": [],
            "error": str(exc),
        }

    _CORAG_JOBS.pop(turn_id, None)
    updated = _update_pending_turn_with_corag(turn_id=turn_id, corag_data=result)
    if updated:
        st.session_state["pending_qa"] = updated
        return updated
    return pending


def _get_or_create_active_session(title_seed: str) -> tuple[list[dict], dict]:
    sessions = st.session_state.get("chat_sessions", [])
    active_id = st.session_state.get("active_session_id")

    current_session = None
    if active_id:
        for session in sessions:
            if session.get("session_id") == active_id:
                current_session = session
                break

    if not current_session:
        current_session = {
            "session_id": str(uuid.uuid4()),
            "title": title_seed[:45] + ("..." if len(title_seed) > 45 else ""),
            "timestamp": datetime.now().strftime("%d/%m/%Y - %H:%M"),
            "history": [],
            "rag_state": {
                "last_index_dir": st.session_state.get("last_index_dir", ""),
                "last_index_name": st.session_state.get("last_index_name", ""),
                "last_uploaded_file": st.session_state.get("last_uploaded_file", ""),
                "available_sources": st.session_state.get("available_sources", []),
                "available_file_types": st.session_state.get("available_file_types", []),
                "available_upload_dates": st.session_state.get("available_upload_dates", []),
            }
        }
        sessions.insert(0, current_session)
        st.session_state["active_session_id"] = current_session["session_id"]
        st.session_state["chat_sessions"] = sessions

    return sessions, current_session


def _sync_current_session_history(sessions: list[dict], current_session: dict) -> None:
    history_arr = current_session.setdefault("history", [])
    st.session_state["chat_history"] = history_arr[:50]
    save_persistent_history(sessions)
    _refresh_pending_qa_from_current_history()


def _append_pending_dual_chat(
    question: str,
    rewritten_query: str,
    include_history: bool,
    used_rewrite: bool,
    rag_data: dict,
    corag_data: dict,
    corag_state: str = "pending",
) -> dict | None:
    rag_answer = str(rag_data.get("answer", "")).strip()
    corag_answer = str(corag_data.get("answer", "")).strip()
    if not rag_answer and not corag_answer:
        return None

    sessions, current_session = _get_or_create_active_session(question)
    history_arr = current_session.setdefault("history", [])
    turn_id = str(uuid.uuid4())

    history_arr.insert(0, {
        "turn_id": turn_id,
        "time": datetime.now().strftime("%H:%M:%S"),
        "question": question,
        "answer": "",
        "sources": [],
        "is_pending_selection": True,
        "selected_source": "",
        "rewritten_query": rewritten_query,
        "include_history": include_history,
        "used_rewrite": used_rewrite,
        "corag_state": corag_state,
        "rag_answer": rag_answer,
        "rag_confidence": rag_data.get("confidence"),
        "rag_contexts": rag_data.get("contexts", []),
        "rag_error": rag_data.get("error", ""),
        "corag_answer": corag_answer,
        "corag_confidence": corag_data.get("confidence"),
        "corag_total_rounds": corag_data.get("total_rounds", 0),
        "corag_iterations": corag_data.get("iterations", []),
        "corag_error": corag_data.get("error", ""),
    })

    _sync_current_session_history(sessions, current_session)
    return _extract_pending_qa_from_history(st.session_state.get("chat_history", []))


def _update_pending_turn_with_corag(turn_id: str, corag_data: dict) -> dict | None:
    if not turn_id.strip():
        return None

    sessions = st.session_state.get("chat_sessions", [])
    active_id = st.session_state.get("active_session_id")
    current_session = None
    if active_id:
        for session in sessions:
            if session.get("session_id") == active_id:
                current_session = session
                break

    if not current_session:
        return None

    history_arr = current_session.setdefault("history", [])
    for item in history_arr:
        if str(item.get("turn_id", "")).strip() != turn_id:
            continue
        if not bool(item.get("is_pending_selection", False)):
            return None

        item["corag_answer"] = str(corag_data.get("answer", ""))
        item["corag_confidence"] = corag_data.get("confidence")
        item["corag_total_rounds"] = corag_data.get("total_rounds", 0)
        item["corag_iterations"] = list(corag_data.get("iterations", []))
        item["corag_error"] = str(corag_data.get("error", ""))
        item["corag_state"] = "done"
        _sync_current_session_history(sessions, current_session)
        return _extract_pending_qa_from_history(st.session_state.get("chat_history", []))

    return None


def _finalize_pending_turn(turn_id: str, selected_source: str) -> bool:
    if not turn_id.strip():
        return False

    sessions = st.session_state.get("chat_sessions", [])
    active_id = st.session_state.get("active_session_id")
    current_session = None
    if active_id:
        for session in sessions:
            if session.get("session_id") == active_id:
                current_session = session
                break

    if not current_session:
        return False

    history_arr = current_session.setdefault("history", [])
    for item in history_arr:
        if str(item.get("turn_id", "")) != turn_id:
            continue
        if not bool(item.get("is_pending_selection", False)):
            return False

        rag_answer = str(item.get("rag_answer", "")).strip()
        corag_answer = str(item.get("corag_answer", "")).strip()
        if selected_source == "rag":
            answer = rag_answer
        elif selected_source == "corag":
            answer = corag_answer
        elif selected_source == "pause":
            answer = corag_answer or rag_answer or "Dừng trả lời"
        else:
            return False

        item["answer"] = answer
        item["selected_source"] = selected_source
        item["is_pending_selection"] = False
        item["finalized_at"] = datetime.now().strftime("%H:%M:%S")
        _sync_current_session_history(sessions, current_session)
        return True

    return False


def _save_selected_answer_from_pending(source: str) -> bool:
    pending = st.session_state.get("pending_qa") or {}
    turn_id = str(pending.get("turn_id", "")).strip()
    question = str(pending.get("question", "")).strip()
    if not question:
        return False

    rag_data = pending.get("rag") or {}
    corag_data = pending.get("corag") or {}

    if source == "rag":
        answer = str(rag_data.get("answer", "")).strip()
        if not answer:
            return False
    elif source == "corag":
        answer = str(corag_data.get("answer", "")).strip()
        if not answer:
            return False
    else:
        return False

    if turn_id:
        if source == "rag":
            _cancel_corag_job(turn_id)
        if not _finalize_pending_turn(turn_id=turn_id, selected_source=source):
            return False
    else:
        _append_chat(question=question, answer=answer, sources=[])

    _append_history("save", f"Đã lưu câu trả lời {source.upper()} cho câu hỏi: {question[:90]}")
    _clear_pending_qa_state()
    st.session_state["qa_requires_pause"] = False
    _request_clear_qa_query()
    return True


def _pause_and_store_current_question(current_input: str) -> bool:
    pending = st.session_state.get("pending_qa")
    if pending:
        turn_id = str(pending.get("turn_id", "")).strip()
        question = str(pending.get("question", "")).strip()
        rag_answer = str((pending.get("rag") or {}).get("answer", "")).strip()
        corag_answer = str((pending.get("corag") or {}).get("answer", "")).strip()

        if corag_answer:
            answer = corag_answer
        elif rag_answer:
            answer = rag_answer
        else:
            answer = "Dừng trả lời"

        if not question:
            return False

        if turn_id:
            _cancel_corag_job(turn_id)
            if not _finalize_pending_turn(turn_id=turn_id, selected_source="pause"):
                return False
        else:
            _append_chat(question=question, answer=answer, sources=[])

        _append_history("pause", f"Pause tại câu hỏi: {question[:90]}")
        _clear_pending_qa_state()
        _request_clear_qa_query()
        return True

    question = current_input.strip()
    if not question:
        return False

    _append_chat(question=question, answer="Dừng trả lời", sources=[])
    _append_history("pause", f"Pause trước khi sinh câu trả lời: {question[:90]}")
    _request_clear_qa_query()
    return True


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _card_start(title: str, subtitle: str | None = None) -> None:
    st.markdown('<div class="smartdoc-card">', unsafe_allow_html=True)
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f"<div class='smartdoc-muted'>{subtitle}</div>", unsafe_allow_html=True)


def _card_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def _render_index_state() -> None:
    index_name = st.session_state.get("last_index_name") or "Chưa có index"
    index_dir = st.session_state.get("last_index_dir") or "Chưa lưu"
    uploaded = st.session_state.get("last_uploaded_file") or "Chưa upload"

    st.markdown("### Trạng thái hiện tại")
    render_chip_row([
        f"File: {uploaded}",
        f"Index: {index_name}",
        f"Thư mục: {Path(index_dir).name if index_dir != 'Chưa lưu' else index_dir}",
    ])


def _append_history(kind: str, detail: str) -> None:
    history = st.session_state.setdefault("retrieval_history", [])
    history.insert(0, {"kind": kind, "detail": detail})
    st.session_state["retrieval_history"] = history[:10]


def _append_chat(question: str, answer: str, sources: list[dict]) -> None:
    sessions, current_session = _get_or_create_active_session(question)
    history_arr = current_session.setdefault("history", [])
    history_arr.insert(0, {
        "turn_id": str(uuid.uuid4()),
        "time": datetime.now().strftime("%H:%M:%S"),
        "question": question,
        "answer": answer,
        "sources": sources,
        "is_pending_selection": False,
        "selected_source": "single",
    })
    _sync_current_session_history(sessions, current_session)


def _highlight_context_snippet(text: str, query: str) -> tuple[str, int]:
    safe_text = html.escape(text or "")
    tokens = [token for token in re.findall(r"[\wÀ-ỹ]+", query, flags=re.UNICODE) if len(token) >= 3]
    seen: set[str] = set()
    unique_tokens: list[str] = []
    for token in tokens:
        lowered = token.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_tokens.append(token)
        if len(unique_tokens) >= 8:
            break

    highlighted = safe_text
    total_matches = 0
    for token in unique_tokens:
        pattern = re.compile(re.escape(html.escape(token)), flags=re.IGNORECASE)
        highlighted, matches = pattern.subn(lambda m: f"<mark>{m.group(0)}</mark>", highlighted)
        total_matches += matches

    return highlighted.replace("\n", "<br>"), total_matches


def _to_user_error_message(exc: Exception, stage: str) -> str:
    raw = str(exc).strip()
    text = raw.lower()

    if "paging file is too small" in text or "os error 1455" in text:
        return (
            "Máy đang thiếu bộ nhớ ảo khi nạp model embedding. "
            "Hãy đóng bớt ứng dụng nặng hoặc tăng Virtual Memory (Paging File) của Windows, rồi ingest lại."
        )
    if "unsupported file type" in text:
        return "Định dạng file không được hỗ trợ. Vui lòng dùng PDF hoặc DOCX."
    if "no chunks available" in text or "empty" in text:
        return "Không trích xuất được nội dung từ tài liệu. Hãy kiểm tra lại file đầu vào."
    if "permission" in text or "denied" in text:
        return "Không đủ quyền truy cập file/thư mục dữ liệu. Vui lòng kiểm tra quyền ghi đọc."
    if "ollama" in text or "connection refused" in text or "failed to connect" in text:
        return "Không kết nối được Ollama. Hãy kiểm tra Ollama đang chạy và model đã sẵn sàng."
    if "faiss" in text or "index" in text:
        return "Có lỗi khi đọc/tạo FAISS index. Vui lòng ingest lại tài liệu."

    stage_map = {"ingest": "xử lý tài liệu", "retrieve": "truy xuất dữ liệu", "qa": "hỏi đáp với mô hình"}
    stage_text = stage_map.get(stage, "xử lý yêu cầu")
    return f"Đã xảy ra lỗi khi {stage_text}. Chi tiết: {raw or type(exc).__name__}"


def _call_with_supported_kwargs(func, **kwargs):
    try:
        sig = inspect.signature(func)
        allowed = {key: value for key, value in kwargs.items() if key in sig.parameters}
    except Exception:
        allowed = kwargs
    return func(**allowed)


def _render_result_card(index: int, doc) -> None:
    st.markdown(
        f"""
        <div class="smartdoc-card" style="margin-bottom: 0.9rem;">
            <div class="smartdoc-section-title">Chunk #{index}</div>
            <div class="smartdoc-muted" style="margin-bottom: 0.5rem;">
                Nguồn: {doc.metadata.get('source', 'unknown')} | Loại: {doc.metadata.get('file_type', 'n/a')}
            </div>
            <div>{doc.page_content[:1100]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sources(sources: list[dict], query: str) -> None:
    st.markdown("#### Citation / Source tracking")
    if not sources:
        st.info("Chưa có nguồn trích dẫn.")
        return

    for source in sources:
        source_identity = f"{source.get('id', 'S')}::{source.get('source', 'unknown')}::{source.get('page', 'n/a')}"
        source_key_suffix = re.sub(r"[^a-zA-Z0-9_]+", "_", source_identity).strip("_")[:140] or "source"
        context_key = f"ctx_visible_{source_key_suffix}"
        button_key = f"btn_{source_key_suffix}"
        st.session_state.setdefault(context_key, False)

        with st.expander(
            f"{source['id']} | {source.get('file_name', source['source'])} | page: {source['page']}",
            expanded=bool(st.session_state.get(context_key, False)),
        ):
            st.caption(f"ID nguồn: {source['id']}")
            st.caption(f"Tên file: {source.get('file_name', source['source'])}")
            st.caption(f"Đường dẫn nguồn: {source['source']}")
            st.caption(f"Loại file: {source['file_type']}")
            st.caption(f"Ngày upload: {source.get('upload_date', 'n/a')}")
            st.caption("Excerpt:")
            st.write(source["excerpt"])

            label = "Ẩn ngữ cảnh highlight" if st.session_state.get(context_key) else "Xem ngữ cảnh gốc + highlight"
            if st.button(label, key=button_key, use_container_width=True):
                st.session_state[context_key] = not st.session_state.get(context_key, False)
                st.rerun()

            if st.session_state.get(context_key):
                context_text = source.get("context", source.get("excerpt", ""))
                highlighted, match_count = _highlight_context_snippet(context_text, query)
                if match_count == 0:
                    st.caption("Không tìm thấy từ khóa khớp trực tiếp trong đoạn này, đang hiển thị toàn bộ ngữ cảnh gốc.")
                st.markdown(
                    f"""
                    <div class="smartdoc-card" style="margin-top:0.55rem; background: rgba(20, 34, 67, 0.82);">
                        <div class="smartdoc-muted" style="margin-bottom: 0.4rem;">Ngữ cảnh gốc (đã highlight theo từ khóa câu hỏi)</div>
                        <div style="line-height:1.65; font-size:0.93rem;">{highlighted}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _render_chat_sidebar() -> None:
    st.markdown("### Lịch sử cuộc trò chuyện")
    
    if st.button("➕ Cuộc trò chuyện mới", type="primary", use_container_width=True, key="btn_new_session"):
        current_pending = st.session_state.get("pending_qa") or {}
        _cancel_corag_job(str(current_pending.get("turn_id", "")))
        st.session_state["qa_requires_pause"] = False
        st.session_state["active_session_id"] = None
        st.session_state["chat_history"] = []
        _clear_pending_qa_state()
        
        # Reset hoàn toàn trạng thái RAG để bắt đầu phiên mới sạch sẽ
        st.session_state["last_index_dir"] = ""
        st.session_state["last_index_name"] = ""
        st.session_state["last_uploaded_file"] = ""
        st.session_state["available_sources"] = []
        st.session_state["available_file_types"] = []
        st.session_state["available_upload_dates"] = []
        st.session_state["sidebar_source_filter"] = []
        st.session_state["sidebar_file_type_filter"] = []
        
        # Cập nhật cả "hộp đen" F5 persistence về trạng thái trống
        from src.data_layer.conversation_store import save_app_session
        save_app_session(
            index_dir="", index_name="", uploaded_file="",
            sources=[], file_types=[], upload_dates=[]
        )
        
        st.rerun()
        
    sessions = st.session_state.get("chat_sessions", [])
    if not sessions:
        st.caption("Chưa có đoạn chat nào.")
        return

    st.markdown("---")
    
    # Render interactive chat sessions list
    for session in sessions:
        col1, col2 = st.columns([4, 1])
        is_active = session.get("session_id") == st.session_state.get("active_session_id")
        button_type = "primary" if is_active else "secondary"
        
        with col1:
            if st.button(f"💬 {session['title']}\n\n{session['timestamp']}", key=f"sess_{session['session_id']}", use_container_width=True, type=button_type):
                current_pending = st.session_state.get("pending_qa") or {}
                _cancel_corag_job(str(current_pending.get("turn_id", "")))
                st.session_state["qa_requires_pause"] = False
                st.session_state["active_session_id"] = session["session_id"]
                st.session_state["chat_history"] = session.get("history", [])
                _refresh_pending_qa_from_current_history()
                
                # Khôi phục trạng thái RAG của riêng đoạn chat này
                rs = session.get("rag_state", {})
                if rs:
                    st.session_state["last_index_dir"] = rs.get("last_index_dir", "")
                    st.session_state["last_index_name"] = rs.get("last_index_name", "")
                    st.session_state["last_uploaded_file"] = rs.get("last_uploaded_file", "")
                    st.session_state["available_sources"] = rs.get("available_sources", [])
                    st.session_state["available_file_types"] = rs.get("available_file_types", [])
                    st.session_state["available_upload_dates"] = rs.get("available_upload_dates", [])
                    
                    # Cập nhật cả "hộp đen" F5 persistence để khớp với đoạn chat đang chọn
                    from src.data_layer.conversation_store import save_app_session
                    save_app_session(
                        index_dir=st.session_state["last_index_dir"],
                        index_name=st.session_state["last_index_name"],
                        uploaded_file=st.session_state["last_uploaded_file"],
                        sources=st.session_state["available_sources"],
                        file_types=st.session_state["available_file_types"],
                        upload_dates=st.session_state["available_upload_dates"],
                    )
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{session['session_id']}", help="Xóa lịch sử trò chuyện này", type="tertiary"):
                sessions.remove(session)
                if is_active:
                    current_pending = st.session_state.get("pending_qa") or {}
                    _cancel_corag_job(str(current_pending.get("turn_id", "")))
                    st.session_state["qa_requires_pause"] = False
                    st.session_state["active_session_id"] = None
                    st.session_state["chat_history"] = []
                    _clear_pending_qa_state()
                st.session_state["chat_sessions"] = sessions
                save_persistent_history(sessions)
                st.rerun()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📄", layout="wide")
    _init_state()

    # Safety fallback: avoid sticky lock if previous run crashed mid-generation.
    if st.session_state.get("qa_generation_in_progress", False) and not st.session_state.get("pending_qa"):
        st.session_state["qa_generation_in_progress"] = False

    if st.session_state.get("pending_sidebar_filter_reset", False):
        st.session_state["sidebar_source_filter"] = []
        st.session_state["sidebar_file_type_filter"] = []
        st.session_state["sidebar_upload_date_filter"] = []
        st.session_state["pending_sidebar_filter_reset"] = False

    apply_styles()
    render_hero()

    with st.sidebar:
        render_sidebar_header()
        
        # Move chat history to the top to avoid StreamlitAPIException when resetting filters
        _render_chat_sidebar()
        
        st.markdown("---")
        
        model_badge_slot = st.empty()
        render_model_badge(
            model_name=st.session_state.get("active_model", OLLAMA_MODEL),
            is_fallback=st.session_state.get("is_fallback_model", False),
            target=model_badge_slot,
        )

        st.markdown("### Cấu hình ingest")
        uploaded_files = st.file_uploader("Upload tài liệu PDF/DOCX (Có thể chọn nhiều file)", type=["pdf", "docx"], accept_multiple_files=True)
        chunk_size = st.number_input("Chunk size", min_value=200, max_value=4000, value=DEFAULT_CHUNK_SIZE, step=100)
        chunk_overlap = st.number_input("Chunk overlap", min_value=0, max_value=1000, value=DEFAULT_CHUNK_OVERLAP, step=20)
        top_k = st.number_input("Top-k search", min_value=1, max_value=10, value=DEFAULT_TOP_K, step=1)

        available_sources_sidebar = st.session_state.get("available_sources", [])
        available_file_types_sidebar = st.session_state.get("available_file_types", [])
        available_upload_dates_sidebar = st.session_state.get("available_upload_dates", [])
        sidebar_source_filter = None
        sidebar_file_type_filter = None
        sidebar_upload_date_filter = None
        if available_sources_sidebar:
            sidebar_source_filter = st.multiselect("Filter tài liệu mặc định", options=available_sources_sidebar, key="sidebar_source_filter")
        if available_file_types_sidebar:
            sidebar_file_type_filter = st.multiselect("Filter loại file", options=available_file_types_sidebar, key="sidebar_file_type_filter")
        if available_upload_dates_sidebar:
            sidebar_upload_date_filter = st.multiselect("Filter ngày upload", options=available_upload_dates_sidebar, key="sidebar_upload_date_filter")

        st.markdown("---")

        # Clear vector store
        if not st.session_state["confirm_clear_status"]:
            if st.button("Clear Vector Store + trạng thái"):
                st.session_state["confirm_clear_status"] = True
                st.rerun()
        else:
            st.warning("Bạn có chắc chắn muốn xóa toàn bộ file đã upload và FAISS index trong data/raw + data/index?")
            col_yes, col_no = st.columns(2)
            if col_yes.button("Đồng ý xóa", key="yes_clear_status"):
                clear_result = clear_vector_store_data()
                st.session_state["last_index_dir"] = ""
                st.session_state["last_index_name"] = ""
                st.session_state["last_uploaded_file"] = ""
                st.session_state["retrieval_history"] = []
                st.session_state["last_chunks"] = []
                st.session_state["last_bi_encoder_chunks"] = []
                st.session_state["last_vector_only_chunks"] = []
                st.session_state["last_query"] = ""
                st.session_state["available_sources"] = []
                st.session_state["available_file_types"] = []
                st.session_state["available_upload_dates"] = []
                st.session_state["pending_sidebar_filter_reset"] = True
                st.session_state["last_ingested_paths"] = []
                st.session_state["chunk_benchmark_rows"] = []
                st.session_state["ingest_notice"] = (
                    "Đã xóa dữ liệu tạm: "
                    f"{clear_result.get('raw_deleted', 0)} mục trong raw, "
                    f"{clear_result.get('index_deleted', 0)} mục trong index."
                )
                st.session_state["confirm_clear_status"] = False
                st.rerun()
            if col_no.button("Hủy", key="no_clear_status"):
                st.session_state["confirm_clear_status"] = False
                st.rerun()



        st.markdown("---")
        # _render_chat_sidebar() moved to top

    render_chip_row(["Streamlit UI", "Streamlit + CSS", "FAISS", "Ollama", "PDF/DOCX"])

    st.markdown('<div class="smartdoc-card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tài liệu", "PDF/DOCX")
    col2.metric("Vector store", "FAISS")
    col3.metric("UI layer", "Streamlit")
    st.markdown('</div>', unsafe_allow_html=True)

    tab_upload, tab_retrieve, tab_qa, tab_history = st.tabs([
        "1. Upload & Index", "2. Retrieval Demo", "3. Q&A với LLM", "4. Lịch sử & Ghi chú",
    ])

    with tab_upload:
        left, right = st.columns([1.25, 0.9], gap="large")

        with left:
            _card_start("Bước 1: Nạp tài liệu", "Tải file lên, sau đó chunking và build FAISS index thật.")
            if st.session_state.get("ingest_notice"):
                st.success(st.session_state["ingest_notice"])
                st.session_state["ingest_notice"] = ""

            if uploaded_files:
                file_names = ", ".join([f.name for f in uploaded_files])
                st.success(f"Đã chọn {len(uploaded_files)} file: {file_names}")
                st.markdown(
                    """
                    <div class="smartdoc-muted">
                        Hệ thống sẽ lưu file vào <b>data/raw</b>, tách chunk bằng RecursiveCharacterTextSplitter
                        và lưu chung vào một FAISS index tại <b>data/index</b>.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("Ingest và tạo FAISS index", type="primary"):
                    try:
                        with st.spinner(f"Đang ingest {len(uploaded_files)} file..."):
                            ingest_result = ingest_multiple_uploaded_files(
                                uploaded_files=uploaded_files,
                                chunk_size=int(chunk_size),
                                chunk_overlap=int(chunk_overlap),
                            )
                            
                            existing_index = st.session_state.get("last_index_dir")
                            if existing_index and Path(existing_index).exists():
                                # Incrementally update existing index
                                index_result = update_faiss_index(
                                    new_chunks=ingest_result.chunks,
                                    index_dir=existing_index,
                                )
                                is_incremental = True
                            else:
                                # Build fresh index
                                idx_name = f"{len(uploaded_files)}_docs_" + uploaded_files[0].name if len(uploaded_files) > 1 else uploaded_files[0].name
                                index_result = build_and_save_faiss_index(
                                    chunks=ingest_result.chunks,
                                    source_name=idx_name,
                                )
                                is_incremental = False
                            
                    except Exception as exc:
                        st.error(_to_user_error_message(exc, stage="ingest"))
                        _append_history("error", f"Ingest failed: {type(exc).__name__}")
                    else:
                        st.session_state["last_index_dir"] = str(index_result.index_dir)
                        st.session_state["last_index_name"] = index_result.index_name
                        
                        # Update cumulative file list
                        new_file_names = ", ".join([f.name for f in uploaded_files])
                        if is_incremental:
                            st.session_state["last_uploaded_file"] = f"{st.session_state.get('last_uploaded_file', '')}, {new_file_names}"
                        else:
                            st.session_state["last_uploaded_file"] = new_file_names
                            
                        st.session_state["last_chunks"] = ingest_result.chunks
                        st.session_state["last_bi_encoder_chunks"] = []
                        st.session_state["last_vector_only_chunks"] = []
                        st.session_state["last_query"] = ""

                        # Extract metadata from NEW chunks
                        new_sources = {
                            Path(str(chunk.metadata.get("source", "unknown"))).name
                            for chunk in ingest_result.chunks if chunk.metadata
                        }
                        new_file_types = {
                            str(chunk.metadata.get("file_type", "")).lower().lstrip(".")
                            for chunk in ingest_result.chunks if chunk.metadata and chunk.metadata.get("file_type")
                        }
                        new_upload_dates = {
                            str(chunk.metadata.get("upload_date", "")).strip()
                            for chunk in ingest_result.chunks if chunk.metadata and chunk.metadata.get("upload_date")
                        }
                        new_ingested_paths = {
                            str(chunk.metadata.get("source", ""))
                            for chunk in ingest_result.chunks if chunk.metadata and chunk.metadata.get("source")
                        }

                        # Merge with EXISTING session state metadata
                        st.session_state["available_sources"] = sorted(list(set(st.session_state.get("available_sources", [])) | set(new_sources)))
                        st.session_state["available_file_types"] = sorted(list(set(st.session_state.get("available_file_types", [])) | set(new_file_types)))
                        st.session_state["available_upload_dates"] = sorted(list(set(st.session_state.get("available_upload_dates", [])) | set(new_upload_dates)), reverse=True)
                        st.session_state["last_ingested_paths"] = sorted(list(set(st.session_state.get("last_ingested_paths", [])) | set(new_ingested_paths)))
                        
                        st.session_state["pending_sidebar_filter_reset"] = True
                        st.session_state["chunk_benchmark_rows"] = []

                        # Lưu trạng thái index xuống file "hộp đen" F5 persistence
                        save_app_session(
                            index_dir=st.session_state["last_index_dir"],
                            index_name=st.session_state["last_index_name"],
                            uploaded_file=st.session_state["last_uploaded_file"],
                            sources=st.session_state["available_sources"],
                            file_types=st.session_state["available_file_types"],
                            upload_dates=st.session_state["available_upload_dates"],
                        )
                        
                        # Cập nhật thông tin bổ sung vào Session hiện tại (nếu có)
                        active_id = st.session_state.get("active_session_id")
                        if active_id:
                            for sess in st.session_state.get("chat_sessions", []):
                                if sess.get("session_id") == active_id:
                                    sess["rag_state"] = {
                                        "last_index_dir": st.session_state["last_index_dir"],
                                        "last_index_name": st.session_state["last_index_name"],
                                        "last_uploaded_file": st.session_state["last_uploaded_file"],
                                        "available_sources": st.session_state["available_sources"],
                                        "available_file_types": st.session_state["available_file_types"],
                                        "available_upload_dates": st.session_state["available_upload_dates"],
                                    }
                                    save_persistent_history(st.session_state["chat_sessions"])
                                    break

                        # Ghi log lịch sử hệ thống
                        _append_history("index", f"{'Nạp thêm' if is_incremental else 'Nạp mới'}: {len(uploaded_files)} file -> {index_result.index_name}")

                        st.session_state["ingest_notice"] = (
                            f"Đã {'nạp thêm' if is_incremental else 'tạo mới'} {ingest_result.raw_docs_count} docs. "
                            f"Tổng số file đang khả dụng: {len(st.session_state['available_sources'])}"
                        )
                        st.rerun()

                        _append_history("index", f"Multi docs ({len(uploaded_files)}) -> {ingest_result.chunks_count} chunks -> {index_result.index_name}")
                        st.session_state["ingest_notice"] = (
                            f"Ingest hoàn tất: {ingest_result.raw_docs_count} docs, "
                            f"{ingest_result.chunks_count} chunks, index {index_result.index_name}"
                        )
                        st.rerun()
            else:
                st.info("Chưa chọn tài liệu. Hãy upload PDF hoặc DOCX để bắt đầu.")
            _card_end()

        with right:
            _card_start("Bước 1.1: Checklist giao diện", "Đây là những phần UI bám sát yêu cầu assignment.")
            st.markdown(
                """
                <div class="smartdoc-step">
                    <div class="smartdoc-step-title">File uploader</div>
                    <div class="smartdoc-step-desc">Nhận tài liệu PDF/DOCX từ người dùng.</div>
                </div>
                <div class="smartdoc-step">
                    <div class="smartdoc-step-title">Processing state</div>
                    <div class="smartdoc-step-desc">Hiển thị spinner và thông báo trong lúc xử lý.</div>
                </div>
                <div class="smartdoc-step">
                    <div class="smartdoc-step-title">Result display</div>
                    <div class="smartdoc-step-desc">Trình bày chunk, metadata và trạng thái index.</div>
                </div>
                <div class="smartdoc-step">
                    <div class="smartdoc-step-title">Error handling</div>
                    <div class="smartdoc-step-desc">Thông báo rõ ràng nếu file sai định dạng hoặc lỗi xử lý.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            _render_index_state()
            _card_end()

            _card_start("Bước 1.2: So sánh chunk strategy", "Đánh giá nhanh các cấu hình chunk_size/chunk_overlap trên cùng truy vấn.")
            eval_query = st.text_input(
                "Câu truy vấn để benchmark",
                value=st.session_state.get("last_query", ""),
                key="chunk_eval_query",
                placeholder="Ví dụ: yêu cầu giao diện người dùng trong tài liệu",
            )
            if st.button("So sánh 3 cấu hình chunk", key="chunk_benchmark_btn"):
                ingested_paths = st.session_state.get("last_ingested_paths", [])
                if not ingested_paths:
                    st.warning("Chưa có dữ liệu để benchmark. Hãy ingest tài liệu trước.")
                elif not eval_query.strip():
                    st.warning("Vui lòng nhập truy vấn benchmark trước khi chạy.")
                else:
                    base_size = int(chunk_size)
                    base_overlap = int(chunk_overlap)
                    candidates = [
                        (max(250, int(base_size * 0.7)), max(0, int(base_overlap * 0.6))),
                        (base_size, base_overlap),
                        (min(4000, int(base_size * 1.3)), min(1000, int(base_overlap * 1.4))),
                    ]
                    strategies: list[tuple[int, int]] = []
                    seen: set[tuple[int, int]] = set()
                    for strategy in candidates:
                        if strategy in seen:
                            continue
                        seen.add(strategy)
                        strategies.append(strategy)

                    with st.spinner("Đang benchmark chunk strategy..."):
                        rows = evaluate_chunk_strategies(
                            file_paths=ingested_paths, query=eval_query.strip(),
                            strategies=strategies, top_k=int(top_k),
                        )
                    st.session_state["chunk_benchmark_rows"] = rows

            benchmark_rows = st.session_state.get("chunk_benchmark_rows", [])
            if benchmark_rows:
                st.dataframe(benchmark_rows, use_container_width=True)
                st.caption("relevance_proxy là chỉ số gần đúng dựa trên overlap truy vấn với top-k chunk được truy xuất.")
            _card_end()

    with tab_retrieve:
        left, right = st.columns([1.0, 1.0], gap="large")

        with left:
            _card_start("Bước 2: Truy vấn top-k chunks", "Chạy FAISS (Vector) + BM25 (Keyword) Hybrid Search.")
            last_index_dir = st.session_state.get("last_index_dir")
            if last_index_dir:
                query = st.text_area(
                    "Nhập câu hỏi để test retrieval",
                    placeholder="Ví dụ: FAISS là gì? hoặc Tài liệu này nói gì về giao diện?",
                    height=120, key="retrieval_query",
                )

                if st.button("Tìm chunks liên quan", key="retrieve_button", disabled=not query.strip()):
                    try:
                        with st.spinner("Đang search bằng Hybrid Search (FAISS + BM25)..."):
                            effective_filter = sidebar_source_filter if sidebar_source_filter else None
                            effective_type_filter = sidebar_file_type_filter if sidebar_file_type_filter else None
                            effective_date_filter = sidebar_upload_date_filter if sidebar_upload_date_filter else None
                            effective_top_k = int(top_k)
                            if effective_filter and len(effective_filter) > 0:
                                effective_top_k = int(top_k) * len(effective_filter)
                            docs = _call_with_supported_kwargs(
                                search_similar_chunks, index_dir=last_index_dir, query=query,
                                top_k=effective_top_k, source_filter=effective_filter,
                                file_type_filter=effective_type_filter, upload_date_filter=effective_date_filter,
                            )
                            bi_encoder_docs = _call_with_supported_kwargs(
                                search_similar_chunks, index_dir=last_index_dir, query=query,
                                top_k=effective_top_k, source_filter=effective_filter,
                                file_type_filter=effective_type_filter, upload_date_filter=effective_date_filter,
                                use_rerank=False,
                            )
                            vector_only_docs = _call_with_supported_kwargs(
                                search_vector_only_chunks, index_dir=last_index_dir, query=query,
                                top_k=effective_top_k, source_filter=effective_filter,
                                file_type_filter=effective_type_filter, upload_date_filter=effective_date_filter,
                            )
                    except Exception as exc:
                        st.error(_to_user_error_message(exc, stage="retrieve"))
                        _append_history("error", f"Retrieve failed: {type(exc).__name__}")
                    else:
                        st.session_state["last_query"] = query
                        st.session_state["last_chunks"] = docs
                        st.session_state["last_bi_encoder_chunks"] = bi_encoder_docs
                        st.session_state["last_vector_only_chunks"] = vector_only_docs
                        _append_history("query", query)
                        st.success(f"Tìm thấy {len(docs)} chunks")
                        st.caption(
                            "Hybrid+CrossEncoder: "
                            f"{len(docs)} | Hybrid Bi-encoder: {len(bi_encoder_docs)} | Vector-only: {len(vector_only_docs)}"
                        )
                        if docs:
                            st.markdown("#### Tóm tắt nhanh")
                            st.write(docs[0].page_content[:900])
            else:
                st.warning("Chưa có index trong session. Hãy upload và tạo FAISS index trước.")
            _card_end()

        with right:
            _card_start("Kết quả truy xuất", "Hiển thị top-k chunks, metadata và preview để người dùng dễ kiểm tra.")
            hybrid_chunks = st.session_state.get("last_chunks", [])
            bi_encoder_chunks = st.session_state.get("last_bi_encoder_chunks", [])
            vector_chunks = st.session_state.get("last_vector_only_chunks", [])
            if hybrid_chunks or bi_encoder_chunks or vector_chunks:
                tab_hybrid, tab_bi, tab_vector = st.tabs(["Hybrid + CrossEncoder", "Hybrid Bi-encoder", "Vector-only Baseline"])
                with tab_hybrid:
                    if hybrid_chunks:
                        for idx, doc in enumerate(hybrid_chunks, start=1):
                            _render_result_card(idx, doc)
                    else:
                        st.info("Hybrid search chưa trả về chunk nào.")
                with tab_bi:
                    if bi_encoder_chunks:
                        for idx, doc in enumerate(bi_encoder_chunks, start=1):
                            _render_result_card(idx, doc)
                    else:
                        st.info("Hybrid bi-encoder chưa trả về chunk nào.")
                with tab_vector:
                    if vector_chunks:
                        for idx, doc in enumerate(vector_chunks, start=1):
                            _render_result_card(idx, doc)
                    else:
                        st.info("Vector-only chưa trả về chunk nào.")
            else:
                st.info("Chưa có kết quả truy xuất. Hãy chạy tìm kiếm ở khung bên trái.")
            _card_end()

    with tab_qa:
        _card_start("Bước 3: Giao diện so sánh - Basic RAG vs Co-RAG", "Hiển thị cách LLM lấy thông tin và tự suy luận đa bước.")
        last_index_dir = st.session_state.get("last_index_dir")
        
        # Luon hien thi lich su trao doi cua phien chat dang chon (ngay ca khi chua co index)
        current_history = st.session_state.get("chat_history", [])
        if current_history:
            st.markdown("##### Lich su trao doi")
            for item in reversed(current_history):
                if bool(item.get("is_pending_selection", False)) and not str(item.get("selected_source", "")).strip():
                    continue
                with st.chat_message("user"):
                    st.write(item["question"])
                with st.chat_message("assistant"):
                    st.markdown(item.get("answer", ""))
            st.markdown("---")

        if not last_index_dir:
            if not current_history:
                st.warning("Chưa có index trong session. Hãy upload và tạo FAISS index trước.")
            _card_end()
        else:
            if st.session_state.get("clear_qa_query_pending", False):
                st.session_state.pop("qa_query", None)
                st.session_state["clear_qa_query_pending"] = False
            qa_query = st.text_area(
                "Nhập câu hỏi", placeholder="Ví dụ: Có bao nhiêu bài tập trong tài liệu này?",
                height=80, key="qa_query",
            )
            pending_qa = st.session_state.get("pending_qa")
            action_col_ask, action_col_pause = st.columns([4, 1])
            action_col_ask.button(
                "Tranh luận / So sánh AI",
                type="primary",
                key="qa_button",
                disabled=(
                    bool(pending_qa)
                    or bool(st.session_state.get("qa_generation_in_progress", False))
                    or bool(st.session_state.get("qa_requires_pause", False))
                ),
                on_click=_request_qa_generation,
            )
            pause_clicked = action_col_pause.button("⏸", key="qa_pause_button", help="Pause câu hỏi hiện tại")

            if st.session_state.get("qa_submit_requested", False):
                if st.session_state.get("pending_qa"):
                    st.warning("Bạn cần Lưu một câu trả lời hoặc bấm Pause trước khi hỏi câu mới.")
                    st.session_state["qa_submit_requested"] = False
                    st.session_state["qa_generation_in_progress"] = False
                elif not qa_query.strip():
                    st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
                    st.session_state["qa_submit_requested"] = False
                    st.session_state["qa_generation_in_progress"] = False
                else:
                    st.session_state["qa_requires_pause"] = True
                    original_query = qa_query.strip()
                    history_for_rewrite = list(st.session_state.get("chat_history", []))
                    rewritten_query, used_rewrite = rewrite_query_with_history(
                        query=original_query,
                        chat_history=history_for_rewrite,
                        model_name=st.session_state.get("active_model", OLLAMA_MODEL),
                    )
                    include_history = should_include_history_in_prompt(
                        query=original_query,
                        used_rewrite=used_rewrite,
                    )

                    # Khởi tạo model engine dùng chung
                    model_engine = OllamaInferenceEngine(model_name=st.session_state.get("active_model", OLLAMA_MODEL))
                    manager = RAGChainManager(index_dir=last_index_dir, model_engine=model_engine)
                    co_manager = CoRAGChainManager(index_dir=last_index_dir, model_engine=model_engine, top_k=int(top_k))

                    rag_ans, rag_err = None, None
                    corag_ans, corag_err = None, None

                    status_col_rag, status_col_corag = st.columns(2)
                    with status_col_rag:
                        st.caption("🤖 Basic RAG")
                        rag_status_slot = st.empty()
                        rag_live_answer_slot = st.empty()
                        rag_status_slot.info("Đang chạy RAG...")
                    with status_col_corag:
                        st.caption("🧠 Co-RAG")
                        corag_status_slot = st.empty()
                        corag_status_slot.info("Đang chạy Co-RAG...")

                    try:
                        rag_ans = manager.ask(
                            question=original_query,
                            top_k=int(top_k),
                            retrieval_query=rewritten_query,
                            chat_history=history_for_rewrite,
                            include_history=include_history,
                        )
                    except Exception as e:
                        rag_err = e
                    finally:
                        if rag_err:
                            rag_status_slot.error(f"RAG lỗi: {rag_err}")
                            corag_status_slot.warning("Co-RAG đang chờ sau RAG...")
                        else:
                            rag_status_slot.success("RAG đã hoàn tất")
                            rag_live_answer_slot.markdown("**Câu trả lời RAG (hiển thị ngay):**")
                            rag_live_answer_slot.markdown(rag_ans.answer)
                            corag_status_slot.info("Co-RAG đang tiếp tục xử lý...")

                    if not rag_err:
                        try:
                            corag_ans = co_manager.ask(
                                question=original_query,
                                retrieval_query=rewritten_query,
                                chat_history=history_for_rewrite,
                                include_history=include_history,
                            )
                        except Exception as e:
                            corag_err = e

                    if corag_err:
                        corag_status_slot.error(f"Co-RAG lỗi: {corag_err}")
                    elif corag_ans:
                        corag_status_slot.success("Co-RAG đã hoàn tất")
                    elif rag_err:
                        corag_status_slot.warning("Không chạy Co-RAG vì RAG lỗi.")
                    else:
                        corag_status_slot.warning("Co-RAG không trả về kết quả.")

                    # Once Co-RAG is done, remove the temporary live RAG preview
                    # to avoid duplicated RAG rendering above and below.
                    rag_live_answer_slot.empty()

                    pending_payload = {
                        "question": original_query,
                        "rewritten_query": rewritten_query,
                        "include_history": include_history,
                        "used_rewrite": used_rewrite,
                        "corag_state": "done" if (corag_ans or corag_err) else "idle",
                        "rag": {
                            "answer": rag_ans.answer if rag_ans else "",
                            "confidence": rag_ans.confidence_score if rag_ans else None,
                            "contexts": rag_ans.context_chunks if rag_ans else [],
                            "error": str(rag_err) if rag_err else "",
                        },
                        "corag": {
                            "answer": corag_ans.answer if corag_ans else "",
                            "confidence": corag_ans.confidence_score if corag_ans else None,
                            "total_rounds": corag_ans.total_rounds if corag_ans else 0,
                            "iterations": [
                                {
                                    "llm_assessment": iteration.llm_assessment,
                                    "sub_query": iteration.sub_query,
                                    "retrieved_chunks_count": len(iteration.retrieved_chunks),
                                }
                                for iteration in (corag_ans.iterations if corag_ans else [])
                            ],
                            "error": str(corag_err) if corag_err else "",
                        },
                    }

                    persisted_pending = _append_pending_dual_chat(
                        question=original_query,
                        rewritten_query=rewritten_query,
                        include_history=include_history,
                        used_rewrite=used_rewrite,
                        rag_data=pending_payload["rag"],
                        corag_data=pending_payload["corag"],
                        corag_state="done" if (corag_ans or corag_err) else "idle",
                    )
                    if persisted_pending:
                        st.session_state["pending_qa"] = persisted_pending
                    else:
                        st.session_state["pending_qa"] = None

                    _append_history("qa", original_query)
                    _append_history(
                        "rewrite",
                        (
                            f"original='{original_query[:120]}' | "
                            f"rewritten='{rewritten_query[:120]}' | "
                            f"include_history={include_history}"
                        ),
                    )
                    st.session_state["qa_submit_requested"] = False
                    st.session_state["qa_generation_in_progress"] = False

            if pause_clicked:
                if _pause_and_store_current_question(qa_query):
                    st.session_state["qa_requires_pause"] = False
                    st.success("Đã pause và lưu lịch sử theo trạng thái hiện tại.")
                    st.rerun()
                else:
                    st.warning("Không có câu hỏi để pause. Hãy nhập câu hỏi hoặc tạo một lượt hỏi trước.")

            pending_qa = st.session_state.get("pending_qa")
            if pending_qa:
                col_rag, col_corag = st.columns(2)
                rag_data = pending_qa.get("rag") or {}
                corag_data = pending_qa.get("corag") or {}
                corag_state = str(pending_qa.get("corag_state", "pending"))
                rag_answer_ready = bool(str(rag_data.get("answer", "")).strip())
                corag_done = corag_state == "done" or bool(str(corag_data.get("answer", "")).strip()) or bool(str(corag_data.get("error", "")).strip())
                ready_to_select = rag_answer_ready and corag_done

                if ready_to_select:
                    st.info("Đang chờ chọn câu trả lời để lưu. Bạn phải Lưu hoặc Pause trước khi hỏi câu mới.")
                else:
                    st.info("Đang sinh câu trả lời. Nút chọn lưu sẽ hiện khi cả RAG và Co-RAG hoàn tất.")

                st.caption(
                    "Query sử dụng retrieval: "
                    f"{pending_qa.get('rewritten_query', '')} | include_history={pending_qa.get('include_history', False)}"
                )

                with col_rag:
                    st.markdown("### 🤖 Basic RAG")
                    st.caption("Sinh câu trả lời với 1 shot context duy nhất.")
                    rag_error = str(rag_data.get("error", "")).strip()
                    rag_answer = str(rag_data.get("answer", "")).strip()
                    if rag_error:
                        st.error(f"Lỗi RAG: {rag_error}")
                    elif rag_answer:
                        st.success("Hoàn tất Basic RAG")
                        st.markdown(f"**Câu trả lời:**\n\n{rag_answer}")
                        if rag_data.get("confidence") is not None:
                            st.caption(f"Độ tự tin: {rag_data.get('confidence')}/10")
                        with st.expander("Ngữ cảnh đã dùng"):
                            st.write("\n\n---\n\n".join(rag_data.get("contexts", [])))
                    else:
                        st.warning("RAG chưa sinh được câu trả lời.")

                    if ready_to_select and st.button("Lưu đoạn RAG này", key="btn_save_rag", use_container_width=True, disabled=not bool(rag_answer)):
                        if _save_selected_answer_from_pending("rag"):
                            st.success("Đã lưu câu trả lời RAG và bỏ qua câu còn lại.")
                            st.rerun()

                with col_corag:
                    st.markdown("### 🧠 Co-RAG (Advanced)")
                    st.caption("Hiển thị so sánh với Basic RAG sau khi xử lý hoàn tất.")
                    corag_error = str(corag_data.get("error", "")).strip()
                    corag_answer = str(corag_data.get("answer", "")).strip()
                    if corag_error:
                        st.error(f"Lỗi Co-RAG: {corag_error}")
                    elif corag_answer:
                        st.success(f"Hoàn tất (Trải qua {int(corag_data.get('total_rounds', 0))} vòng)")
                        st.markdown(f"**Câu trả lời:**\n\n{corag_answer}")
                        if corag_data.get("confidence") is not None:
                            st.caption(f"Độ tự tin: {corag_data.get('confidence')}/10")

                        for it_idx, iteration in enumerate(corag_data.get("iterations", []), start=1):
                            with st.expander(f"Vòng {it_idx} | Đánh giá & Sub-query"):
                                st.markdown(f"**Ý kiến LLM:** {iteration.get('llm_assessment') or 'Không có (Vòng đánh giá/Cuối)'}")
                                st.markdown(f"**Sub-query tạo ra:** `{iteration.get('sub_query', '')}`")
                                st.markdown(f"**Chunks kéo về:** {int(iteration.get('retrieved_chunks_count', 0))} chunks")
                    else:
                        st.warning("Co-RAG chưa sinh được câu trả lời.")

                    if ready_to_select and st.button("Lưu đoạn Co-RAG này", key="btn_save_corag", use_container_width=True, disabled=not bool(corag_answer)):
                        if _save_selected_answer_from_pending("corag"):
                            st.success("Đã lưu câu trả lời Co-RAG và bỏ qua câu còn lại.")
                            st.rerun()
            _card_end()

    with tab_history:
        _card_start("Lịch sử thao tác", "Những hành động gần nhất của người dùng trong phiên hiện tại.")
        history = st.session_state.get("retrieval_history", [])
        if history:
            for item in history:
                st.markdown(f"- **{item['kind']}**: {item['detail']}")
        else:
            st.write("Chưa có lịch sử nào.")
        _card_end()

    st.markdown('<hr class="smartdoc-divider" />', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
