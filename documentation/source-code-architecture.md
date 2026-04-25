# SmartDoc AI — Tài liệu kiến trúc mã nguồn (`src/`)

> Tài liệu này mô tả cấu trúc thư mục, chức năng từng file và từng hàm trong toàn bộ thư mục `src/`.
> Nội dung đã được cập nhật theo code hiện tại sau refactor: ingest, retrieval, Co-RAG, persistence và UI state.

---

## Sơ đồ tổng quan

```
src/
├── config.py                  ← Hằng số cấu hình toàn cục
├── models.py                  ← Các dataclass dùng chung
├── utils.py                   ← Thư viện tiện ích dùng chung
│
├── application/               ← Tầng xử lý nghiệp vụ (Application Layer)
│   ├── corag_chain_manager.py ← Pipeline Co-RAG (đa vòng truy xuất)
│   ├── document_processing_pipeline.py ← Ingest + chunking tài liệu
│   ├── prompt_engineering.py  ← Xây dựng prompt, phát hiện ngôn ngữ
│   ├── query_rewriter.py      ← Viết lại query, phát hiện follow-up, multi-hop
│   └── rag_chain_manager.py   ← Pipeline RAG cơ bản (1-shot)
│
├── data_layer/                ← Tầng lưu trữ và truy xuất dữ liệu
│   ├── conversation_store.py  ← Lưu/tải lịch sử hội thoại (JSON)
│   ├── faiss_vector_store.py  ← FAISS index + Hybrid Search + Re-ranking
│   ├── multilingual_mpnet_embeddings.py ← Mô hình embedding đa ngôn ngữ
│   └── pdf_document_storage.py ← Load PDF/DOCX, lưu file, chuẩn hóa metadata
│
├── model_layer/               ← Tầng tương tác trực tiếp với LLM
│   └── ollama_inference_engine.py ← Gọi Ollama, fallback model, Self-RAG scoring
│
└── presentation/              ← Tầng giao diện người dùng
    ├── streamlit_app.py       ← Main UI, routing, state management
    └── ui_config.py           ← CSS, theme, component helpers
```

---

## `src/config.py`

**Mục đích:** Định nghĩa hằng số cấu hình trung tâm cho toàn bộ ứng dụng.

| Hằng số                     | Giá trị                                                       | Mô tả                           |
| --------------------------- | ------------------------------------------------------------- | ------------------------------- |
| `BASE_DIR`                  | (root project)                                                | Đường dẫn gốc dự án             |
| `DATA_DIR`                  | `data/`                                                       | Thư mục chứa dữ liệu runtime    |
| `RAW_DIR`                   | `data/raw/`                                                   | Nơi lưu file gốc sau khi upload |
| `INDEX_DIR`                 | `data/index/`                                                 | Nơi lưu FAISS index             |
| `CHAT_HISTORY_DIR`          | `data/chat_history/`                                          | Nơi lưu lịch sử hội thoại       |
| `APP_TITLE`                 | `SmartDoc AI`                                                 | Tiêu đề ứng dụng Streamlit      |
| `DEFAULT_CHUNK_SIZE`        | `1000`                                                        | Kích thước chunk mặc định       |
| `DEFAULT_CHUNK_OVERLAP`     | `100`                                                         | Overlap giữa các chunk          |
| `DEFAULT_TOP_K`             | `5`                                                           | Số chunk truy xuất mặc định     |
| `EMBEDDING_MODEL_NAME`      | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Model embedding                 |
| `OLLAMA_BASE_URL`           | `http://localhost:11434`                                      | Endpoint Ollama                 |
| `OLLAMA_MODEL`              | `qwen2.5:7b`                                                  | Model LLM chính                 |
| `FALLBACK_MODELS`           | `(qwen2.5:1.5b, qwen2.5:0.5b)`                                | Model dự phòng khi lỗi/OOM      |
| `SCORING_MAX_DOCS`          | `8`                                                           | Số doc tối đa khi chấm tự tin   |
| `SCORING_EXCERPT_CHARS`     | `180`                                                         | Độ dài trích đoạn cho scoring   |
| `SCORING_CONTEXT_MAX_CHARS` | `1200`                                                        | Giới hạn độ dài context scoring |

---

## `src/models.py`

**Mục đích:** Khai báo các dataclass dùng chung giữa các tầng.

| Class              | Mô tả                                                                     |
| ------------------ | ------------------------------------------------------------------------- |
| `IngestResult`     | Kết quả ingest tài liệu: `file_path`, số raw docs, số chunks, list chunks |
| `IndexBuildResult` | Kết quả build/update FAISS: tên index, đường dẫn index, số chunks         |

---

## `src/utils.py`

**Mục đích:** Tiện ích dùng chung cho text normalization, path helpers và metadata/source filtering.

| Hàm                                                               | Mô tả                                                                     | Trạng thái                                        |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------- |
| `sanitize_name(name)`                                             | Chuyển tên file có dấu thành tên folder ASCII an toàn                     | ✅ Dùng                                           |
| `strip_accents(text)`                                             | Xóa dấu tiếng Việt khỏi text                                              | ✅ Dùng                                           |
| `normalize_for_match(text)`                                       | Normalize text để so khớp: lowercase, xóa dấu, chuẩn hóa khoảng trắng     | ✅ Dùng                                           |
| `normalize_tokens(text)`                                          | Tách text thành tập token lowercase                                       | ✅ Dùng (bởi `keyword_overlap_score`)             |
| `keyword_overlap_score(query, text)`                              | Tính tỉ lệ token trùng nhau giữa query và text                            | ✅ Dùng                                           |
| `clean_generated_answer(answer)`                                  | Làm sạch câu trả lời sinh ra khỏi phần echo context/footer                | ✅ Dùng                                           |
| `source_name_from_path(path)`                                     | Lấy tên file từ đường dẫn đầy đủ                                          | ✅ Dùng                                           |
| `source_name_core(path)`                                          | Lấy tên file đã normalize và bỏ tiền tố phổ biến như `bai tap`, `chapter` | ✅ Dùng (bởi `detect_sources_mentioned_in_query`) |
| `source_matches_filter(doc_source, source_filter)`                | Kiểm tra doc có thuộc danh sách lọc nguồn không                           | ✅ Dùng                                           |
| `metadata_matches_filters(metadata, ...)`                         | Kiểm tra doc có khớp source/file type/upload date không                   | ✅ Dùng                                           |
| `sources_from_docs(docs)`                                         | Trích xuất danh sách tên file từ list `Document`                          | ✅ Dùng                                           |
| `_detect_sources_mentioned_in_query_cached(...)`                  | Cache nội bộ cho phát hiện source trong query                             | ✅ Dùng                                           |
| `detect_sources_mentioned_in_query(query, available_sources)`     | Phát hiện tên file nào được đề cập trong câu hỏi                          | ✅ Dùng                                           |
| `extract_explicit_source_reference(query)`                        | Trích xuất tham chiếu kiểu `file X` / `tài liệu Y` / `document Z`         | ✅ Dùng                                           |
| `resolve_effective_source_filter(query, source_filter, all_docs)` | Quyết định bộ lọc nguồn hiệu quả dựa trên query và filter hiện có         | ✅ Dùng                                           |
| `detect_source_filter_conflict(query, source_filter, all_docs)`   | Phát hiện xung đột giữa filter đang chọn và file được hỏi                 | ✅ Dùng                                           |
| `detect_unknown_source_reference(query, all_docs)`                | Phát hiện câu hỏi về file không tồn tại trong index                       | ✅ Dùng                                           |

---

## `src/application/`

### `rag_chain_manager.py`

**Mục đích:** Pipeline RAG cơ bản: truy xuất top-k chunks một lần rồi sinh câu trả lời.

| Hàm / Class                                    | Mô tả                                                                           | Trạng thái |
| ---------------------------------------------- | ------------------------------------------------------------------------------- | ---------- |
| `RAGAnswer` (dataclass)                        | Kết quả trả về: answer, context chunks, confidence, raw docs, prompt            | ✅ Dùng    |
| `RAGChainManager.__init__`                     | Khởi tạo với `index_dir` và model engine                                        | ✅ Dùng    |
| `RAGChainManager._get_faiss()`                 | Lazy-load FAISS index                                                           | ✅ Dùng    |
| `RAGChainManager._format_context_chunks(docs)` | Format list `Document` thành list string có header nguồn                        | ✅ Dùng    |
| `RAGChainManager.ask(question, ...)`           | Entry point chính: retrieve → format → prompt → generate → clean answer → score | ✅ Dùng    |

---

### `corag_chain_manager.py`

**Mục đích:** Pipeline Co-RAG (Chain-of-Retrieval) với nhiều vòng truy xuất và đánh giá đủ/chưa đủ.

| Hàm / Class                              | Mô tả                                                                    | Trạng thái |
| ---------------------------------------- | ------------------------------------------------------------------------ | ---------- |
| `CoRAGIteration` (dataclass)             | Kết quả một vòng: round_num, sub_query, retrieved_chunks, llm_assessment | ✅ Dùng    |
| `CoRAGAnswer` (dataclass)                | Kết quả cuối: answer, iterations, total_rounds, confidence               | ✅ Dùng    |
| `CoRAGChainManager.__init__`             | Khởi tạo với `index_dir`, model, `max_rounds`, `top_k`                   | ✅ Dùng    |
| `_get_faiss()`                           | Lazy-load FAISS index                                                    | ✅ Dùng    |
| `_retrieve_and_format_chunks(query)`     | Truy xuất và format chunks cho một vòng                                  | ✅ Dùng    |
| `_deduplicate_chunks(existing, new)`     | Loại bỏ chunks trùng lặp khi gộp ngữ cảnh qua các vòng                   | ✅ Dùng    |
| `_assess_sufficiency(question, context)` | Hỏi LLM xem ngữ cảnh đã đủ chưa (`SUFFICIENT` / `SUB_QUERY:`)            | ✅ Dùng    |
| `_is_cancelled(stop_signal)`             | Kiểm tra tín hiệu hủy từ người dùng                                      | ✅ Dùng    |
| `ask(question, ...)`                     | Vòng lặp retrieve-assess cho đến `SUFFICIENT` hoặc `max_rounds`          | ✅ Dùng    |
| `_extract_subquery(response, fallback)`  | Trích xuất sub-query từ phản hồi LLM                                     | ✅ Dùng    |

---

### `document_processing_pipeline.py`

**Mục đích:** Xử lý ingest tài liệu: load, chunking, metadata enrichment, benchmark chunk strategy.

| Hàm                                                             | Mô tả                                                              | Trạng thái |
| --------------------------------------------------------------- | ------------------------------------------------------------------ | ---------- |
| `ingest_document(file_path, ...)`                               | Load file → split chunks → enrich metadata → trả về `IngestResult` | ✅ Dùng    |
| `ingest_multiple_uploaded_files(uploaded_files, ...)`           | Lưu từng file upload, ingest nhiều file một lần và gộp chunks      | ✅ Dùng    |
| `evaluate_chunk_strategies(file_paths, query, strategies, ...)` | So sánh nhiều chiến lược chunk bằng relevance proxy score          | ✅ Dùng    |

---

### `prompt_engineering.py`

**Mục đích:** Xây dựng prompt gửi cho LLM, phát hiện ngôn ngữ và format lịch sử hội thoại.

| Hàm                                                        | Mô tả                                             | Trạng thái |
| ---------------------------------------------------------- | ------------------------------------------------- | ---------- |
| `detect_vietnamese(text)`                                  | Phát hiện text có chứa ký tự tiếng Việt hay không | ✅ Dùng    |
| `is_probably_english_query(text)`                          | Phát hiện câu hỏi viết bằng tiếng Anh             | ✅ Dùng    |
| `answer_without_footer(answer_text)`                       | Cắt bỏ phần `---` footer khỏi câu trả lời         | ✅ Dùng    |
| `build_chat_history_context(chat_history, max_turns)`      | Format lịch sử hội thoại thành chuỗi cho prompt   | ✅ Dùng    |
| `build_rag_prompt(question, contexts, ...)`                | Xây dựng prompt cho Basic RAG                     | ✅ Dùng    |
| `build_corag_sufficiency_check_prompt(question, contexts)` | Prompt hỏi LLM đánh giá ngữ cảnh đủ/chưa đủ       | ✅ Dùng    |
| `build_corag_final_prompt(question, contexts, ...)`        | Prompt tổng hợp câu trả lời cuối cho Co-RAG       | ✅ Dùng    |

---

### `query_rewriter.py`

**Mục đích:** Phát hiện follow-up query, viết lại query độc lập hơn và hỗ trợ multi-hop retrieval.

| Hàm                                                                | Mô tả                                                                 | Trạng thái                                |
| ------------------------------------------------------------------ | --------------------------------------------------------------------- | ----------------------------------------- |
| `is_follow_up_query(query)`                                        | Phát hiện câu hỏi phụ thuộc ngữ cảnh trước                            | ✅ Dùng                                   |
| `should_include_history_in_prompt(query, used_rewrite)`            | Quyết định có đưa lịch sử vào prompt không                            | ✅ Dùng                                   |
| `rewrite_query_with_history(query, chat_history, model_name, ...)` | Dùng LLM hoặc heuristic để viết lại query follow-up thành câu độc lập | ✅ Dùng                                   |
| `_extract_retrieval_keywords(text, max_terms)`                     | Trích xuất từ khóa quan trọng từ text retrieved                       | ✅ Dùng (bởi `_build_second_hop_queries`) |
| `_build_second_hop_queries(query, docs)`                           | Tạo query mở rộng cho vòng retrieval thứ 2                            | ✅ Dùng (bởi `multi_hop_retrieve`)        |
| `multi_hop_retrieve(index_dir, query, ...)`                        | 2 vòng retrieval: hop1 → keywords → hop2 → rerank                     | ✅ Dùng                                   |

---

## `src/data_layer/`

### `faiss_vector_store.py`

**Mục đích:** Quản lý FAISS index, Hybrid Search, lọc metadata và reranking.

| Hàm                                                    | Mô tả                                                          | Trạng thái |
| ------------------------------------------------------ | -------------------------------------------------------------- | ---------- |
| `build_and_save_faiss_index(chunks, source_name, ...)` | Tạo FAISS index mới từ danh sách chunks                        | ✅ Dùng    |
| `update_faiss_index(new_chunks, index_dir)`            | Thêm chunks mới vào index có sẵn (incremental ingestion)       | ✅ Dùng    |
| `load_faiss_index(index_dir)`                          | Nạp FAISS index từ disk                                        | ✅ Dùng    |
| `clear_vector_store_data(index_root, raw_root)`        | Xóa toàn bộ index và file raw                                  | ✅ Dùng    |
| `looks_like_toc(text)`                                 | Phát hiện chunk giống mục lục                                  | ✅ Dùng    |
| `is_toc_intent(query)`                                 | Phát hiện user đang chủ động hỏi về mục lục                    | ✅ Dùng    |
| `filter_low_quality_chunks(docs, query, min_length)`   | Loại chunk chất lượng thấp/TOC/trùng lặp sớm                   | ✅ Dùng    |
| `deduplicate_docs(docs)`                               | Loại bỏ `Document` trùng lặp dựa trên source+page+content      | ✅ Dùng    |
| `_get_cross_encoder()`                                 | Lazy-load Cross-Encoder (cached bởi Streamlit)                 | ✅ Dùng    |
| `rerank_docs(query, docs, top_k, aggressive)`          | Chấm lại mức liên quan bằng Cross-Encoder hoặc keyword overlap | ✅ Dùng    |
| `_balance_docs_by_source(docs, top_k)`                 | Cân bằng top-k giữa các source                                 | ✅ Dùng    |
| `search_similar_chunks(index_dir, query, ...)`         | Hybrid Search: FAISS MMR + similarity + BM25 → dedup → rerank  | ✅ Dùng    |
| `search_vector_only_chunks(index_dir, query, ...)`     | Chỉ dùng vector search thuần để so sánh với Hybrid             | ✅ Dùng    |

---

### `multilingual_mpnet_embeddings.py`

**Mục đích:** Khởi tạo và cache mô hình embedding đa ngôn ngữ.

| Hàm                                     | Mô tả                                                                     | Trạng thái |
| --------------------------------------- | ------------------------------------------------------------------------- | ---------- |
| `_is_memory_related_error(exc)`         | Phát hiện lỗi do thiếu RAM khi load model                                 | ✅ Dùng    |
| `_build_embedder_for_model(model_name)` | Khởi tạo HuggingFaceEmbeddings cho một model cụ thể                       | ✅ Dùng    |
| `build_embedder()`                      | Entry point: thử load từ model chính, fallback sang model nhẹ hơn nếu OOM | ✅ Dùng    |

---

### `conversation_store.py`

**Mục đích:** Lưu trữ và tải lịch sử hội thoại và trạng thái phiên làm việc dưới dạng JSON.

| Hàm                                                                                         | Mô tả                                                        | Trạng thái |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ---------- |
| `save_persistent_history(history)`                                                          | Lưu toàn bộ lịch sử hội thoại vào `history.json`             | ✅ Dùng    |
| `load_persistent_history()`                                                                 | Tải lịch sử hội thoại, tự động migrate format cũ             | ✅ Dùng    |
| `save_app_session(index_dir, index_name, uploaded_file, sources, file_types, upload_dates)` | Lưu trạng thái index (F5 persistence) vào `app_session.json` | ✅ Dùng    |
| `load_app_session()`                                                                        | Tải trạng thái index đã lưu                                  | ✅ Dùng    |

---

### `pdf_document_storage.py`

**Mục đích:** Load tài liệu PDF/DOCX, lưu file upload, chuẩn hóa metadata chunk.

| Hàm                                             | Mô tả                                                                                              | Trạng thái |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------- |
| `load_pdf(path)`                                | Load file PDF bằng PDFPlumber                                                                      | ✅ Dùng    |
| `load_docx(path)`                               | Load file DOCX bằng python-docx                                                                    | ✅ Dùng    |
| `load_documents(path)`                          | Dispatcher: tự động chọn loader theo đuôi file                                                     | ✅ Dùng    |
| `save_uploaded_file(uploaded_file, target_dir)` | Lưu file upload từ Streamlit vào disk                                                              | ✅ Dùng    |
| `file_type_from_path(file_path)`                | Lấy đuôi file (`pdf`, `docx`, ...)                                                                 | ✅ Dùng    |
| `upload_time_from_path(file_path)`              | Lấy thời gian chỉnh sửa file                                                                       | ✅ Dùng    |
| `enrich_chunks_metadata(chunks, file_path)`     | Bổ sung metadata (`source`, `file_name`, `file_type`, `upload_time`, `upload_date`) vào từng chunk | ✅ Dùng    |

---

## `src/model_layer/`

### `ollama_inference_engine.py`

**Mục đích:** Tương tác trực tiếp với Ollama, xử lý fallback model và Self-RAG scoring.

| Hàm / Class                                                            | Mô tả                                                             | Trạng thái |
| ---------------------------------------------------------------------- | ----------------------------------------------------------------- | ---------- |
| `is_retryable_llm_error(error)`                                        | Phát hiện lỗi có thể retry (OOM, timeout, terminated)             | ✅ Dùng    |
| `_build_context_for_scoring(docs)`                                     | Format docs thành text ngắn gọn cho scoring prompt                | ✅ Dùng    |
| `_heuristic_confidence_score(query, answer, context_text)`             | Tính điểm tin cậy heuristic khi LLM scoring lỗi                   | ✅ Dùng    |
| `OllamaInferenceEngine.__init__`                                       | Khởi tạo LLM, tự chọn model hoạt động dựa trên `sticky_fallbacks` | ✅ Dùng    |
| `OllamaInferenceEngine._get_llm(model)`                                | Tạo instance `OllamaLLM` cho model cụ thể                         | ✅ Dùng    |
| `OllamaInferenceEngine._get_scoring_llm()`                             | Tạo LLM nhẹ hơn cho bước chấm điểm                                | ✅ Dùng    |
| `OllamaInferenceEngine.generate(prompt, ...)`                          | Gọi LLM sinh câu trả lời, tự fallback nếu model lỗi               | ✅ Dùng    |
| `OllamaInferenceEngine.self_rag_confidence_score(query, answer, docs)` | Cho LLM tự chấm điểm câu trả lời (1–10) rồi blend với heuristic   | ✅ Dùng    |

---

## `src/presentation/`

### `streamlit_app.py`

**Mục đích:** Main UI, routing, state management, ingest/retrieval/QA flow.

| Nhóm hàm                                                                                                                                             | Mô tả                                                                      | Trạng thái |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------- |
| `_init_state()`                                                                                                                                      | Khởi tạo và khôi phục `st.session_state` từ session persistence            | ✅ Dùng    |
| `_clear_pending_qa_state()`, `_request_clear_qa_query()`, `_request_qa_generation()`                                                                 | Quản lý cờ trạng thái cho luồng Q&A                                        | ✅ Dùng    |
| `_is_pending_selection_item()`, `_prune_stale_pending_entries()`, `_extract_pending_qa_from_history()`, `_refresh_pending_qa_from_current_history()` | Xử lý pending QA trong lịch sử hội thoại                                   | ✅ Dùng    |
| `_cancel_corag_job()`, `_start_corag_background_job()`, `_collect_corag_result_if_ready()`                                                           | Quản lý job Co-RAG chạy nền                                                | ✅ Dùng    |
| `_get_or_create_active_session()`, `_sync_current_session_history()`                                                                                 | Tạo/đồng bộ phiên chat hiện tại                                            | ✅ Dùng    |
| `_append_pending_dual_chat()`, `_update_pending_turn_with_corag()`, `_finalize_pending_turn()`                                                       | Lưu và chốt một turn Basic RAG / Co-RAG                                    | ✅ Dùng    |
| `_save_selected_answer_from_pending()`, `_pause_and_store_current_question()`                                                                        | Lưu câu trả lời đã chọn hoặc pause turn hiện tại                           | ✅ Dùng    |
| `_card_start()`, `_card_end()`, `_render_index_state()`, `_append_history()`, `_append_chat()`                                                       | Các helper render UI và log lịch sử                                        | ✅ Dùng    |
| `_highlight_context_snippet()`, `_to_user_error_message()`, `_call_with_supported_kwargs()`, `_create_live_activity_stream()`                        | Helper hỗ trợ hiển thị, lỗi và callback tương thích                        | ✅ Dùng    |
| `_render_result_card()`, `_render_sources()`, `_render_chat_sidebar()`                                                                               | Render kết quả retrieval, citation và sidebar chat                         | ✅ Dùng    |
| `main()`                                                                                                                                             | Entry point UI: upload/index, retrieval demo, QA, clear/reset, persistence | ✅ Dùng    |

**Các state chính do UI quản lý:** `last_index_dir`, `last_index_name`, `last_uploaded_file`, `available_sources`, `available_file_types`, `available_upload_dates`, `last_ingested_paths`, `last_chunks`, `last_bi_encoder_chunks`, `last_vector_only_chunks`, `pending_qa`, `chat_sessions`, `chat_history`, `confirm_clear_status`, `confirm_clear_history_status`, `sidebar_*_filter`, `ingest_notice`.

### `ui_config.py`

**Mục đích:** CSS, theme, badge, chip và thành phần UI dùng chung.

| Hàm                       | Mô tả                          | Trạng thái |
| ------------------------- | ------------------------------ | ---------- |
| `apply_styles()`          | Inject CSS và theme cho app    | ✅ Dùng    |
| `render_chip_row(...)`    | Hiển thị hàng chip trạng thái  | ✅ Dùng    |
| `render_hero()`           | Hiển thị hero/header chính     | ✅ Dùng    |
| `render_model_badge(...)` | Hiển thị badge model đang chạy | ✅ Dùng    |
| `render_sidebar_header()` | Render tiêu đề sidebar         | ✅ Dùng    |

---

## Ghi chú về dead code

Trong bản đối chiếu hiện tại, các mục dead code cũ như `RagResult`, `ingest_uploaded_file()` và `read_full_text_from_source()` đã không còn xuất hiện trong code đã kiểm tra, nên không còn giữ lại trong tài liệu này. Nếu bạn muốn, có thể làm tiếp một vòng rà soát dead code riêng bằng cách quét toàn bộ `src/` theo reference thực tế.
