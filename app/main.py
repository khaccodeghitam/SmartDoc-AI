from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import streamlit as st

import sys
for mod in list(sys.modules.keys()):
    if 'rag_pipeline' in mod or 'app.rag_pipeline' in mod:
        del sys.modules[mod]

try:
    from app.config import APP_TITLE, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_TOP_K, CHAT_HISTORY_DIR
    from app.rag_pipeline import answer_question, build_and_save_faiss_index, ingest_uploaded_file, search_similar_chunks, ingest_multiple_uploaded_files
    from app.ui import (
        apply_styles,
        render_chip_row,
        render_hero,
        render_sidebar_header,
        render_sidebar_help,
        render_sidebar_notes,
    )
except ModuleNotFoundError:
    from config import APP_TITLE, DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, DEFAULT_TOP_K, CHAT_HISTORY_DIR
    from rag_pipeline import answer_question, build_and_save_faiss_index, ingest_uploaded_file, search_similar_chunks, ingest_multiple_uploaded_files
    from ui import (
        apply_styles,
        render_chip_row,
        render_hero,
        render_sidebar_header,
        render_sidebar_help,
        render_sidebar_notes,
    )


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
    st.session_state.setdefault("last_query", "")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = _load_persistent_history()
    st.session_state.setdefault("confirm_clear_status", False)
    st.session_state.setdefault("confirm_clear_history", False)


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


def _render_sources(sources: list[dict]) -> None:
    st.markdown("#### Citation / Source tracking")
    if not sources:
        st.info("Chưa có nguồn trích dẫn.")
        return

    for source in sources:
        with st.expander(f"{source['id']} - {source['source']} (page: {source['page']})", expanded=False):
            st.caption(f"Loại file: {source['file_type']}")
            st.write(source["excerpt"])


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
    apply_styles()
    render_hero()

    with st.sidebar:
        render_sidebar_header()
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

        st.markdown("---")
        render_sidebar_notes()

        if not st.session_state["confirm_clear_status"]:
            if st.button("Xóa trạng thái hiện tại"):
                st.session_state["confirm_clear_status"] = True
                st.rerun()
        else:
            st.warning("Bạn có chắc chắn muốn xóa trạng thái và vector store trên memory?")
            col_yes, col_no = st.columns(2)
            if col_yes.button("Đồng ý xóa", key="yes_clear_status"):
                st.session_state["last_index_dir"] = ""
                st.session_state["last_index_name"] = ""
                st.session_state["last_uploaded_file"] = ""
                st.session_state["retrieval_history"] = []
                st.session_state["last_chunks"] = []
                st.session_state["last_query"] = ""
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
                    with st.spinner(f"Đang ingest {len(uploaded_files)} file, tạo embedding và build FAISS index..."):
                        # Use the new multi-file function
                        ingest_result = ingest_multiple_uploaded_files(
                            uploaded_files=uploaded_files,
                            chunk_size=int(chunk_size),
                            chunk_overlap=int(chunk_overlap),
                        )
                        # Name the index based on first file or "multi_doc_index"
                        idx_name = f"{len(uploaded_files)}_docs_" + uploaded_files[0].name if len(uploaded_files) > 1 else uploaded_files[0].name
                        index_result = build_and_save_faiss_index(
                            chunks=ingest_result.chunks,
                            source_name=idx_name,
                        )

                    st.session_state["last_index_dir"] = str(index_result.index_dir)
                    st.session_state["last_index_name"] = index_result.index_name
                    st.session_state["last_uploaded_file"] = file_names
                    st.session_state["last_chunks"] = ingest_result.chunks
                    st.session_state["last_query"] = ""
                    
                    # Store available sources for metadata filtering
                    sources = list(set(chunk.metadata.get("source", "unknown") for chunk in ingest_result.chunks))
                    # Extract just the filename for cleaner UI
                    st.session_state["available_sources"] = list(set(Path(s).name for s in sources))

                    _append_history(
                        "index",
                        f"Multi docs ({len(uploaded_files)}) -> {ingest_result.chunks_count} chunks -> {index_result.index_name}",
                    )

                    st.success("Ingest hoàn tất")
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric("Document thô", ingest_result.raw_docs_count)
                    metric_col2.metric("Chunks", ingest_result.chunks_count)
                    metric_col3.metric("Index", index_result.index_name)
                    st.caption(f"Index đã lưu tại: {index_result.index_dir}")

                    with st.expander("Preview chunk đầu tiên", expanded=False):
                        st.write(ingest_result.chunks[0].page_content[:1500])
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
                
                # Multi-document metadata filter
                available_sources = st.session_state.get("available_sources", [])
                source_filter = None
                if available_sources:
                    source_filter = st.multiselect("Lọc theo tài liệu (Metadata Filter)", options=available_sources)
                
                if st.button("Tìm chunks liên quan", key="retrieve_button", disabled=not query.strip()):
                    with st.spinner("Đang search bằng Hybrid Search (FAISS + BM25)..."):
                        docs = search_similar_chunks(last_index_dir, query=query, top_k=int(top_k), source_filter=source_filter)
                    st.session_state["last_query"] = query
                    st.session_state["last_chunks"] = docs
                    _append_history("query", query)
                    st.success(f"Tìm thấy {len(docs)} chunks")
                    if docs:
                        st.markdown("#### Tóm tắt nhanh")
                        st.write(docs[0].page_content[:900])
            else:
                st.warning("Chưa có index trong session. Hãy upload và tạo FAISS index trước.")
            _card_end()

        with right:
            _card_start("Kết quả truy xuất", "Hiển thị top-k chunks, metadata và preview để người dùng dễ kiểm tra.")
            if st.session_state.get("last_chunks"):
                for idx, doc in enumerate(st.session_state["last_chunks"], start=1):
                    _render_result_card(idx, doc)
            else:
                st.info("Chưa có kết quả truy xuất. Hãy chạy tìm kiếm ở khung bên trái.")
            _card_end()

    with tab_qa:
        left, right = st.columns([1.0, 1.0], gap="large")

        with left:
            _card_start("Bước 3: Hỏi đáp với LLM", "Retrieval Hybrid kết hợp cùng Qwen2.5:7b.")
            last_index_dir = st.session_state.get("last_index_dir")
            if last_index_dir:
                qa_query = st.text_area(
                    "Nhập câu hỏi",
                    placeholder="Ví dụ: Tài liệu yêu cầu gì về giao diện người dùng?",
                    height=120,
                    key="qa_query",
                )
                
                # Multi-document metadata filter (QA)
                available_sources = st.session_state.get("available_sources", [])
                qa_source_filter = None
                if available_sources:
                    qa_source_filter = st.multiselect("Lọc tài liệu để trả lời", options=available_sources, key="qa_source_filter")
                
                if st.button("Trả lời bằng LLM", type="primary", key="qa_button"):
                    if not qa_query.strip():
                        st.warning("Vui lòng nhập câu hỏi trước khi gửi.")
                    else:
                        with st.spinner("Đang truy xuất nguồn (Hybrid Search) và sinh câu trả lời..."):
                            rag_result = answer_question(
                                index_dir=last_index_dir,
                                query=qa_query.strip(),
                                top_k=int(top_k),
                                chat_history=st.session_state.get("chat_history", []),
                                source_filter=qa_source_filter,
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
                        _render_sources(rag_result.sources)
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
    st.caption("Đã có Q&A với LLM, citation/source tracking và lịch sử chat. Bước tiếp theo: thêm multi-document và metadata filtering.")


if __name__ == "__main__":
    main()
