from __future__ import annotations

from datetime import datetime
import html
import inspect
import json
from pathlib import Path
import re

import streamlit as st

try:
    from app.config import APP_TITLE, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_TOP_K, CHAT_HISTORY_DIR, OLLAMA_MODEL
    from app import rag_pipeline as _rag_pipeline
    from app.ui import (
        apply_styles,
        render_chip_row,
        render_hero,
        render_model_badge,
        render_sidebar_header,
        render_sidebar_help,
        render_sidebar_notes,
    )
except (ModuleNotFoundError, ImportError):
    from config import APP_TITLE, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_TOP_K, CHAT_HISTORY_DIR, OLLAMA_MODEL
    import rag_pipeline as _rag_pipeline
    from ui import (
        apply_styles,
        render_chip_row,
        render_hero,
        render_model_badge,
        render_sidebar_header,
        render_sidebar_help,
        render_sidebar_notes,
    )


answer_question = _rag_pipeline.answer_question
build_and_save_faiss_index = _rag_pipeline.build_and_save_faiss_index
ingest_uploaded_file = _rag_pipeline.ingest_uploaded_file
search_similar_chunks = _rag_pipeline.search_similar_chunks
ingest_multiple_uploaded_files = _rag_pipeline.ingest_multiple_uploaded_files
search_vector_only_chunks = getattr(_rag_pipeline, "search_vector_only_chunks", _rag_pipeline.search_similar_chunks)


def _clear_vector_store_fallback(*_args, **_kwargs) -> dict[str, int]:
    return {"index_deleted": 0, "raw_deleted": 0}


def _chunk_eval_fallback(*_args, **_kwargs) -> list[dict]:
    return []


clear_vector_store_data = getattr(_rag_pipeline, "clear_vector_store_data", _clear_vector_store_fallback)
evaluate_chunk_strategies = getattr(_rag_pipeline, "evaluate_chunk_strategies", _chunk_eval_fallback)
HAS_CLEAR_VECTOR_STORE = hasattr(_rag_pipeline, "clear_vector_store_data")
HAS_CHUNK_EVAL = hasattr(_rag_pipeline, "evaluate_chunk_strategies")


def _save_persistent_history(history: list) -> None:
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    history_file = CHAT_HISTORY_DIR / "history.json"
    try:
        history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), "utf-8")
    except Exception as e:
        print(f"Error saving chat history: {e}")


def _load_persistent_history() -> list:
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    history_file = CHAT_HISTORY_DIR / "history.json"
    if history_file.exists():
        try:
            return json.loads(history_file.read_text("utf-8"))
        except Exception:
            return []
    return []


def _init_state() -> None:
    st.session_state.setdefault("last_index_dir", "")
    st.session_state.setdefault("last_index_name", "")
    st.session_state.setdefault("last_uploaded_file", "")
    st.session_state.setdefault("retrieval_history", [])
    st.session_state.setdefault("last_chunks", [])
    st.session_state.setdefault("last_bi_encoder_chunks", [])
    st.session_state.setdefault("last_vector_only_chunks", [])
    st.session_state.setdefault("last_query", "")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = _load_persistent_history()
    st.session_state.setdefault("confirm_clear_status", False)
    st.session_state.setdefault("confirm_clear_history", False)
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
    render_chip_row(
        [
            f"File: {uploaded}",
            f"Index: {index_name}",
            f"Thư mục: {Path(index_dir).name if index_dir != 'Chưa lưu' else index_dir}",
        ]
    )


def _append_history(kind: str, detail: str) -> None:
    history = st.session_state.setdefault("retrieval_history", [])
    history.insert(0, {"kind": kind, "detail": detail})
    st.session_state["retrieval_history"] = history[:10]


def _append_chat(question: str, answer: str, sources: list[dict]) -> None:
    chat_history = st.session_state.get("chat_history", [])
    chat_history.insert(
        0,
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "question": question,
            "answer": answer,
            "sources": sources,
        },
    )
    st.session_state["chat_history"] = chat_history[:20]
    _save_persistent_history(st.session_state["chat_history"])


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

    stage_map = {
        "ingest": "xử lý tài liệu",
        "retrieve": "truy xuất dữ liệu",
        "qa": "hỏi đáp với mô hình",
    }
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
    st.sidebar.markdown("### Lịch sử chat")
    chat_history = st.session_state.get("chat_history", [])
    if not chat_history:
        st.sidebar.caption("Chưa có hội thoại nào.")
        return

    for item in chat_history[:8]:
        st.sidebar.markdown(f"- **{item['time']}**: {item['question'][:45]}")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📄", layout="wide")
    _init_state()

    # Streamlit does not allow changing widget-bound session keys after widget creation.
    # Defer sidebar filter resets to the next run and apply them before sidebar widgets render.
    if st.session_state.get("pending_sidebar_filter_reset", False):
        st.session_state["sidebar_source_filter"] = []
        st.session_state["sidebar_file_type_filter"] = []
        st.session_state["sidebar_upload_date_filter"] = []
        st.session_state["pending_sidebar_filter_reset"] = False

    apply_styles()
    if not HAS_CLEAR_VECTOR_STORE or not HAS_CHUNK_EVAL:
        st.warning(
            "Đang chạy ở chế độ tương thích do module rag_pipeline chưa nạp đủ symbol mới. "
            "Hãy restart app để kích hoạt đầy đủ tính năng mới."
        )
    render_hero()

    with st.sidebar:
        render_sidebar_header()
        model_badge_slot = st.empty()
        render_model_badge(
            model_name=st.session_state.get("active_model", OLLAMA_MODEL),
            is_fallback=st.session_state.get("is_fallback_model", False),
            target=model_badge_slot,
        )
        render_sidebar_help()

        st.markdown("### Cấu hình ingest")
        uploaded_files = st.file_uploader("Upload tài liệu PDF/DOCX (Có thể chọn nhiều file)", type=["pdf", "docx"], accept_multiple_files=True)
        chunk_size = st.number_input(
            "Chunk size",
            min_value=200,
            max_value=4000,
            value=DEFAULT_CHUNK_SIZE,
            step=100,
        )
        chunk_overlap = st.number_input(
            "Chunk overlap",
            min_value=0,
            max_value=1000,
            value=DEFAULT_CHUNK_OVERLAP,
            step=20,
        )
        top_k = st.number_input(
            "Top-k search",
            min_value=1,
            max_value=10,
            value=DEFAULT_TOP_K,
            step=1,
        )

        available_sources_sidebar = st.session_state.get("available_sources", [])
        available_file_types_sidebar = st.session_state.get("available_file_types", [])
        available_upload_dates_sidebar = st.session_state.get("available_upload_dates", [])
        sidebar_source_filter = None
        sidebar_file_type_filter = None
        sidebar_upload_date_filter = None
        if available_sources_sidebar:
            sidebar_source_filter = st.multiselect(
                "Filter tài liệu mặc định",
                options=available_sources_sidebar,
                key="sidebar_source_filter",
            )
        if available_file_types_sidebar:
            sidebar_file_type_filter = st.multiselect(
                "Filter loại file",
                options=available_file_types_sidebar,
                key="sidebar_file_type_filter",
            )
        if available_upload_dates_sidebar:
            sidebar_upload_date_filter = st.multiselect(
                "Filter ngày upload",
                options=available_upload_dates_sidebar,
                key="sidebar_upload_date_filter",
            )

        st.markdown("---")
        render_sidebar_notes()

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

        if not st.session_state["confirm_clear_history"]:
            if st.button("Xóa lịch sử chat"):
                st.session_state["confirm_clear_history"] = True
                st.rerun()
        else:
            st.warning("Bạn chắn chắn muốn xóa toàn bộ lịch sử chat?")
            col_y_chat, col_n_chat = st.columns(2)
            if col_y_chat.button("Đồng ý xóa", key="yes_clear_chat"):
                st.session_state["chat_history"] = []
                _save_persistent_history([])
                st.session_state["confirm_clear_history"] = False
                st.rerun()
            if col_n_chat.button("Hủy", key="no_clear_chat"):
                st.session_state["confirm_clear_history"] = False
                st.rerun()

        st.markdown("---")
        _render_chat_sidebar()

    render_chip_row(["Streamlit UI", "Streamlit + CSS", "FAISS", "Ollama", "PDF/DOCX"])

    st.markdown('<div class="smartdoc-card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tài liệu", "PDF/DOCX")
    col2.metric("Vector store", "FAISS")
    col3.metric("UI layer", "Streamlit")
    st.markdown('</div>', unsafe_allow_html=True)

    tab_upload, tab_retrieve, tab_qa, tab_history = st.tabs(
        [
            "1. Upload & Index",
            "2. Retrieval Demo",
            "3. Q&A với LLM",
            "4. Lịch sử & Ghi chú",
        ]
    )

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
                        with st.spinner(f"Đang ingest {len(uploaded_files)} file, tạo embedding và build FAISS index..."):
                            ingest_result = ingest_multiple_uploaded_files(
                                uploaded_files=uploaded_files,
                                chunk_size=int(chunk_size),
                                chunk_overlap=int(chunk_overlap),
                            )
                            idx_name = f"{len(uploaded_files)}_docs_" + uploaded_files[0].name if len(uploaded_files) > 1 else uploaded_files[0].name
                            index_result = build_and_save_faiss_index(
                                chunks=ingest_result.chunks,
                                source_name=idx_name,
                            )
                    except Exception as exc:
                        st.error(_to_user_error_message(exc, stage="ingest"))
                        _append_history("error", f"Ingest failed: {type(exc).__name__}")
                    else:
                        st.session_state["last_index_dir"] = str(index_result.index_dir)
                        st.session_state["last_index_name"] = index_result.index_name
                        st.session_state["last_uploaded_file"] = file_names
                        st.session_state["last_chunks"] = ingest_result.chunks
                        st.session_state["last_bi_encoder_chunks"] = []
                        st.session_state["last_vector_only_chunks"] = []
                        st.session_state["last_query"] = ""

                        sources = sorted(
                            {
                                Path(str(chunk.metadata.get("source", "unknown"))).name
                                for chunk in ingest_result.chunks
                                if chunk.metadata
                            }
                        )
                        file_types = sorted(
                            {
                                str(chunk.metadata.get("file_type", "")).lower().lstrip(".")
                                for chunk in ingest_result.chunks
                                if chunk.metadata and chunk.metadata.get("file_type")
                            }
                        )
                        upload_dates = sorted(
                            {
                                str(chunk.metadata.get("upload_date", "")).strip()
                                for chunk in ingest_result.chunks
                                if chunk.metadata and chunk.metadata.get("upload_date")
                            },
                            reverse=True,
                        )
                        ingested_paths = sorted(
                            {
                                str(chunk.metadata.get("source", ""))
                                for chunk in ingest_result.chunks
                                if chunk.metadata and chunk.metadata.get("source")
                            }
                        )

                        st.session_state["available_sources"] = sources
                        st.session_state["available_file_types"] = file_types
                        st.session_state["available_upload_dates"] = upload_dates
                        st.session_state["last_ingested_paths"] = ingested_paths
                        st.session_state["pending_sidebar_filter_reset"] = True
                        st.session_state["chunk_benchmark_rows"] = []

                        _append_history(
                            "index",
                            f"Multi docs ({len(uploaded_files)}) -> {ingest_result.chunks_count} chunks -> {index_result.index_name}",
                        )
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
                            file_paths=ingested_paths,
                            query=eval_query.strip(),
                            strategies=strategies,
                            top_k=int(top_k),
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
                    height=120,
                    key="retrieval_query",
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
                                search_similar_chunks,
                                index_dir=last_index_dir,
                                query=query,
                                top_k=effective_top_k,
                                source_filter=effective_filter,
                                file_type_filter=effective_type_filter,
                                upload_date_filter=effective_date_filter,
                            )
                            bi_encoder_docs = _call_with_supported_kwargs(
                                search_similar_chunks,
                                index_dir=last_index_dir,
                                query=query,
                                top_k=effective_top_k,
                                source_filter=effective_filter,
                                file_type_filter=effective_type_filter,
                                upload_date_filter=effective_date_filter,
                                use_rerank=False,
                            )
                            vector_only_docs = _call_with_supported_kwargs(
                                search_vector_only_chunks,
                                index_dir=last_index_dir,
                                query=query,
                                top_k=effective_top_k,
                                source_filter=effective_filter,
                                file_type_filter=effective_type_filter,
                                upload_date_filter=effective_date_filter,
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
                tab_hybrid, tab_bi, tab_vector = st.tabs(
                    ["Hybrid + CrossEncoder", "Hybrid Bi-encoder", "Vector-only Baseline"]
                )
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
        left, right = st.columns([1.0, 1.0], gap="large")

        with left:
            _card_start("Bước 3: Hỏi đáp với LLM", "Retrieval Hybrid kết hợp cùng Qwen2.5 (ưu tiên model nhẹ theo RAM máy).")
            last_index_dir = st.session_state.get("last_index_dir")
            if last_index_dir:
                qa_query = st.text_area(
                    "Nhập câu hỏi",
                    placeholder="Ví dụ: Tài liệu yêu cầu gì về giao diện người dùng?",
                    height=120,
                    key="qa_query",
                )
                
                if st.button("Trả lời bằng LLM", type="primary", key="qa_button"):
                    if not qa_query.strip():
                        st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
                    else:
                        try:
                            with st.spinner("Đang truy xuất nguồn (Hybrid Search) và sinh câu trả lời..."):
                                effective_filter = sidebar_source_filter if sidebar_source_filter else None
                                effective_type_filter = sidebar_file_type_filter if sidebar_file_type_filter else None
                                effective_date_filter = sidebar_upload_date_filter if sidebar_upload_date_filter else None
                                rag_result = _call_with_supported_kwargs(
                                    answer_question,
                                    index_dir=last_index_dir,
                                    query=qa_query.strip(),
                                    top_k=int(top_k),
                                    chat_history=st.session_state.get("chat_history", []),
                                    source_filter=effective_filter,
                                    file_type_filter=effective_type_filter,
                                    upload_date_filter=effective_date_filter,
                                )
                        except Exception as exc:
                            st.error(_to_user_error_message(exc, stage="qa"))
                            _append_history("error", f"QA failed: {type(exc).__name__}")
                        else:
                            st.session_state["active_model"] = rag_result.model_used
                            st.session_state["is_fallback_model"] = rag_result.is_fallback
                            model_badge_slot.empty()
                            render_model_badge(
                                model_name=st.session_state.get("active_model", OLLAMA_MODEL),
                                is_fallback=st.session_state.get("is_fallback_model", False),
                                target=model_badge_slot,
                            )

                            st.session_state["last_query"] = qa_query.strip()
                            _append_history("qa", qa_query.strip())
                            _append_chat(
                                question=qa_query.strip(),
                                answer=rag_result.answer,
                                sources=rag_result.sources,
                            )

                            st.success("Đã sinh câu trả lời")
                            st.markdown("#### Câu trả lời")
                            st.write(rag_result.answer)
                            _render_sources(rag_result.sources, qa_query.strip())
            else:
                st.warning("Chưa có index trong session. Hãy upload và tạo FAISS index trước.")
            _card_end()

        with right:
            _card_start("Lịch sử hội thoại gần đây", "Hiển thị câu hỏi, câu trả lời và nguồn đã dùng.")
            chat_history = st.session_state.get("chat_history", [])
            if not chat_history:
                st.info("Chưa có hội thoại nào. Hãy gửi câu hỏi ở khung bên trái.")
            else:
                for idx, item in enumerate(chat_history[:5], start=1):
                    st.markdown(f"#### #{idx} - {item['time']}")
                    st.markdown(f"**Q:** {item['question']}")
                    st.markdown(f"**A:** {item['answer']}")
                    if item.get("sources"):
                        st.caption("Nguồn: " + ", ".join(s["id"] for s in item["sources"]))
                    st.markdown("---")
            _card_end()

    with tab_history:
        left, right = st.columns([0.95, 1.05], gap="large")

        with left:
            _card_start("Lịch sử thao tác", "Những hành động gần nhất của người dùng trong phiên hiện tại.")
            history = st.session_state.get("retrieval_history", [])
            if history:
                for item in history:
                    st.markdown(f"- **{item['kind']}**: {item['detail']}")
            else:
                st.write("Chưa có lịch sử nào.")
            _card_end()

        with right:
            _card_start("Ghi chú triển khai giao diện", "Những điểm đang bám sát assignment và chỗ có thể mở rộng.")
            st.markdown(
                """
                - **Streamlit** là lớp frontend chính theo định hướng assignment.
                - **HTML/CSS** được dùng như lớp bổ sung để làm đẹp giao diện.
                - Có thể mở rộng thêm citation, chat history, clear history và preview nguồn.
                - Khi triển khai Q&A đầy đủ, khung UI hiện tại đã sẵn sàng cho câu hỏi và câu trả lời.
                """
            )
            _card_end()

    st.markdown('<hr class="smartdoc-divider" />', unsafe_allow_html=True)
    st.caption("Đã bật đầy đủ: DOCX, history, clear data, chunk benchmark, citation click-highlight, conversational multi-hop RAG, hybrid vs vector-only, metadata filtering, rerank và self-rag confidence.")


if __name__ == "__main__":
    main()
