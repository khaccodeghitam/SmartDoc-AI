# SmartDoc AI — Tài liệu kiến trúc mã nguồn (`src/`)

> Tài liệu này mô tả cấu trúc thư mục, chức năng từng file và từng hàm trong toàn bộ thư mục `src/`.
> Bao gồm kết quả kiểm tra **dead code** (hàm không còn được gọi).

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

**Mục đích:** Định nghĩa tất cả hằng số cấu hình trung tâm cho toàn bộ ứng dụng.

| Hằng số | Giá trị | Mô tả |
|---|---|---|
| `BASE_DIR` | (root project) | Đường dẫn gốc dự án |
| `DATA_DIR` | `data/` | Thư mục chứa toàn bộ dữ liệu runtime |
| `RAW_DIR` | `data/raw/` | Nơi lưu file gốc sau khi upload |
| `INDEX_DIR` | `data/index/` | Nơi lưu FAISS index |
| `CHAT_HISTORY_DIR` | `data/chat_history/` | Nơi lưu lịch sử hội thoại |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Model LLM chính |
| `FALLBACK_MODELS` | `(qwen2.5:1.5b, qwen2.5:0.5b)` | Model dự phòng khi OOM |
| `EMBEDDING_MODEL_NAME` | `paraphrase-multilingual-MiniLM-L12-v2` | Model embedding |
| `DEFAULT_CHUNK_SIZE` | `1000` | Kích thước chunk mặc định |
| `DEFAULT_CHUNK_OVERLAP` | `100` | Overlap giữa các chunk |
| `DEFAULT_TOP_K` | `3` | Số chunk tìm kiếm mặc định |

---

## `src/models.py`

**Mục đích:** Khai báo các dataclass (cấu trúc dữ liệu) dùng chung giữa các tầng.

| Class | Mô tả |
|---|---|
| `IngestResult` | Kết quả sau khi ingest tài liệu: số raw docs, số chunks, danh sách chunks |
| `IndexBuildResult` | Kết quả sau khi build FAISS index: tên index, đường dẫn, số chunks |
| `RagResult` | ⚠️ **Dead code** — Không còn được dùng ở bất kỳ đâu trong pipeline. Đã bị thay thế bởi `RAGAnswer` trong `rag_chain_manager.py` |

---

## `src/utils.py`

**Mục đích:** Thư viện tiện ích dùng chung cho toàn bộ project (text normalization, path helpers, metadata filtering).

| Hàm | Mô tả | Trạng thái |
|---|---|---|
| `sanitize_name(name)` | Chuyển tên file có dấu thành tên folder ASCII an toàn | ✅ Dùng |
| `strip_accents(text)` | Xóa dấu tiếng Việt khỏi text | ✅ Dùng |
| `normalize_for_match(text)` | Normalize text để so khớp (lowercase + xóa dấu + xóa ký tự đặc biệt) | ✅ Dùng |
| `normalize_tokens(text)` | Tách text thành set token lowercase | ✅ Dùng (bởi `keyword_overlap_score`) |
| `keyword_overlap_score(query, text)` | Tính tỉ lệ token trùng nhau giữa query và text (0.0–1.0) | ✅ Dùng |
| `natural_sort_key(value)` | Tạo sort key theo thứ tự tự nhiên (1, 2, 10 thay vì 1, 10, 2) | ⚠️ **Dead code** — không được gọi ở đâu trong `src/` |
| `source_name_from_path(path)` | Lấy tên file từ đường dẫn đầy đủ | ✅ Dùng |
| `source_name_core(path)` | Lấy tên file, loại bỏ tiền tố "bai tap", số thứ tự | ✅ Dùng (bởi `detect_sources_mentioned_in_query`) |
| `source_matches_filter(doc_source, filter)` | Kiểm tra doc có thuộc danh sách lọc nguồn không | ✅ Dùng |
| `metadata_matches_filters(metadata, ...)` | Kiểm tra doc có khớp tất cả bộ lọc (source, type, date) | ✅ Dùng |
| `sources_from_docs(docs)` | Trích xuất danh sách tên file từ list Document | ✅ Dùng |
| `_detect_sources_mentioned_in_query_cached(...)` | Phiên bản cache nội bộ của hàm phát hiện source | ✅ Dùng |
| `detect_sources_mentioned_in_query(query, sources)` | Phát hiện tên file nào được đề cập trong câu hỏi | ✅ Dùng |
| `extract_explicit_source_reference(query)` | Trích xuất tham chiếu "file X" / "tài liệu Y" trong câu hỏi | ✅ Dùng |
| `resolve_effective_source_filter(query, filter, docs)` | Quyết định bộ lọc nguồn hiệu quả dựa trên query | ✅ Dùng |
| `detect_source_filter_conflict(query, filter, docs)` | Phát hiện xung đột giữa filter đang chọn và file được hỏi | ✅ Dùng |
| `detect_unknown_source_reference(query, docs)` | Phát hiện câu hỏi về file không tồn tại trong index | ✅ Dùng |

---

## `src/application/`

### `rag_chain_manager.py`
**Mục đích:** Pipeline RAG cơ bản — truy xuất top-k chunks một lần rồi sinh câu trả lời.

| Hàm / Class | Mô tả | Trạng thái |
|---|---|---|
| `RAGAnswer` (dataclass) | Kết quả trả về: answer, chunks, prompt, confidence, raw docs | ✅ Dùng |
| `RAGChainManager.__init__` | Khởi tạo với index_dir và model engine | ✅ Dùng |
| `RAGChainManager._get_faiss()` | Lazy-load FAISS index | ✅ Dùng |
| `RAGChainManager._format_context_chunks(docs)` | Format list Document thành list string có header nguồn | ✅ Dùng |
| `RAGChainManager.ask(question, ...)` | Entry point chính: retrieve → format → prompt → generate → score | ✅ Dùng |

---

### `corag_chain_manager.py`
**Mục đích:** Pipeline Co-RAG (Chain-of-Retrieval) — đa vòng truy xuất, LLM tự đánh giá ngữ cảnh đủ/thiếu.

| Hàm / Class | Mô tả | Trạng thái |
|---|---|---|
| `CoRAGIteration` (dataclass) | Kết quả một vòng: round_num, sub_query, chunks, assessment | ✅ Dùng |
| `CoRAGAnswer` (dataclass) | Kết quả cuối: answer, iterations, total_rounds, confidence | ✅ Dùng |
| `CoRAGChainManager.__init__` | Khởi tạo với index_dir, model, max_rounds, top_k | ✅ Dùng |
| `_get_faiss()` | Lazy-load FAISS index | ✅ Dùng |
| `_retrieve_and_format_chunks(query)` | Truy xuất và format chunks cho một vòng | ✅ Dùng |
| `_deduplicate_chunks(existing, new)` | Loại bỏ chunks trùng lặp khi gộp ngữ cảnh qua các vòng | ✅ Dùng |
| `_assess_sufficiency(question, context)` | Hỏi LLM xem ngữ cảnh đã đủ chưa (SUFFICIENT / SUB_QUERY:...) | ✅ Dùng |
| `_is_cancelled(stop_signal)` | Kiểm tra tín hiệu hủy từ người dùng | ✅ Dùng |
| `ask(question, ...)` | Entry point: vòng lặp retrieve-assess cho đến SUFFICIENT hoặc max_rounds | ✅ Dùng |
| `_extract_subquery(response, fallback)` | Trích xuất sub_query từ phản hồi LLM | ✅ Dùng |

---

### `document_processing_pipeline.py`
**Mục đích:** Xử lý ingest tài liệu — load, chunking, metadata enrichment, so sánh chiến lược chunk.

| Hàm | Mô tả | Trạng thái |
|---|---|---|
| `ingest_document(file_path, ...)` | Load file → split chunks → enrich metadata → trả về IngestResult | ✅ Dùng |
| `ingest_uploaded_file(uploaded_file, ...)` | Lưu file upload → gọi `ingest_document` | ⚠️ **Dead code** — không được gọi trực tiếp (thay bởi `ingest_multiple_uploaded_files`) |
| `ingest_multiple_uploaded_files(files, ...)` | Ingest nhiều file một lúc, gộp tất cả chunks | ✅ Dùng |
| `evaluate_chunk_strategies(file_paths, query, strategies, ...)` | So sánh nhiều chiến lược chunk (size/overlap) bằng relevance proxy score | ✅ Dùng |

---

### `prompt_engineering.py`
**Mục đích:** Xây dựng prompt gửi cho LLM, phát hiện ngôn ngữ, format lịch sử hội thoại.

| Hàm | Mô tả | Trạng thái |
|---|---|---|
| `detect_vietnamese(text)` | Phát hiện text có chứa ký tự tiếng Việt không | ✅ Dùng |
| `is_probably_english_query(text)` | Phát hiện câu hỏi viết bằng tiếng Anh | ✅ Dùng |
| `answer_without_footer(answer_text)` | Cắt bỏ phần "---" footer khỏi câu trả lời | ✅ Dùng |
| `build_chat_history_context(chat_history, max_turns)` | Format lịch sử hội thoại thành chuỗi cho prompt | ✅ Dùng |
| `build_rag_prompt(question, contexts, ...)` | Xây dựng prompt cho Basic RAG (tự động chọn Việt/Anh) | ✅ Dùng |
| `build_corag_sufficiency_check_prompt(question, contexts)` | Prompt hỏi LLM đánh giá ngữ cảnh đủ/chưa đủ | ✅ Dùng |
| `build_corag_final_prompt(question, contexts, ...)` | Prompt tổng hợp câu trả lời cuối cho Co-RAG | ✅ Dùng |

---

### `query_rewriter.py`
**Mục đích:** Phát hiện follow-up query, viết lại query độc lập hơn, multi-hop retrieval.

| Hàm | Mô tả | Trạng thái |
|---|---|---|
| `is_follow_up_query(query)` | Phát hiện câu hỏi phụ thuộc ngữ cảnh trước ("còn cái kia thì sao?") | ✅ Dùng |
| `should_include_history_in_prompt(query, used_rewrite)` | Quyết định có đưa lịch sử vào prompt không | ✅ Dùng |
| `rewrite_query_with_history(query, history, model, ...)` | Dùng LLM viết lại query follow-up thành câu độc lập | ✅ Dùng |
| `_extract_retrieval_keywords(text, max_terms)` | Trích xuất từ khóa quan trọng từ text retrieved | ✅ Dùng (bởi `_build_second_hop_queries`) |
| `_build_second_hop_queries(query, docs)` | Tạo query mở rộng cho vòng retrieval thứ 2 | ✅ Dùng (bởi `multi_hop_retrieve`) |
| `multi_hop_retrieve(index_dir, query, ...)` | Thực hiện 2 vòng retrieval: hop1 → keywords → hop2 → rerank | ✅ Dùng |

---

## `src/data_layer/`

### `faiss_vector_store.py`
**Mục đích:** Quản lý FAISS index, thực hiện Hybrid Search và Cross-Encoder Re-ranking.

| Hàm | Mô tả | Trạng thái |
|---|---|---|
| `build_and_save_faiss_index(chunks, source_name, ...)` | Tạo FAISS index từ đầu từ danh sách chunks | ✅ Dùng |
| `update_faiss_index(new_chunks, index_dir)` | Thêm chunks mới vào index có sẵn (incremental ingestion) | ✅ Dùng |
| `load_faiss_index(index_dir)` | Nạp FAISS index từ disk | ✅ Dùng |
| `clear_vector_store_data(index_root, raw_root)` | Xóa toàn bộ index và file raw | ✅ Dùng |
| `looks_like_toc(text)` | Phát hiện chunk là "mục lục" (nhiều dấu ... và số trang) | ✅ Dùng |
| `is_toc_intent(query)` | Phát hiện người dùng chủ động hỏi về mục lục | ✅ Dùng |
| `deduplicate_docs(docs)` | Loại bỏ Document trùng lặp dựa trên source+page+content | ✅ Dùng |
| `_get_cross_encoder()` | Lazy-load Cross-Encoder (cached bởi Streamlit) | ✅ Dùng |
| `rerank_docs(query, docs, top_k)` | Chấm lại mức liên quan bằng Cross-Encoder (fallback: keyword overlap) | ✅ Dùng |
| `search_similar_chunks(index_dir, query, ...)` | **Hybrid Search**: FAISS MMR + similarity + BM25 → dedup → rerank | ✅ Dùng |
| `search_vector_only_chunks(index_dir, query, ...)` | Chỉ dùng vector search thuần (để so sánh với Hybrid) | ✅ Dùng |

---

### `multilingual_mpnet_embeddings.py`
**Mục đích:** Khởi tạo và cache mô hình embedding đa ngôn ngữ.

| Hàm | Mô tả | Trạng thái |
|---|---|---|
| `_is_memory_related_error(exc)` | Phát hiện lỗi do thiếu RAM khi load model | ✅ Dùng |
| `_build_embedder_for_model(model_name)` | Khởi tạo HuggingFaceEmbeddings cho một model cụ thể | ✅ Dùng |
| `build_embedder()` | Entry point: thử load từ model chính, fallback sang model nhẹ hơn nếu OOM | ✅ Dùng |

---

### `conversation_store.py`
**Mục đích:** Lưu trữ và tải lịch sử hội thoại và trạng thái phiên làm việc dưới dạng JSON.

| Hàm | Mô tả | Trạng thái |
|---|---|---|
| `save_persistent_history(history)` | Lưu toàn bộ lịch sử hội thoại vào `history.json` | ✅ Dùng |
| `load_persistent_history()` | Tải lịch sử hội thoại, tự động migrate format cũ | ✅ Dùng |
| `save_app_session(index_dir, ...)` | Lưu trạng thái index (F5 persistence) vào `app_session.json` | ✅ Dùng |
| `load_app_session()` | Tải trạng thái index đã lưu | ✅ Dùng |

---

### `pdf_document_storage.py`
**Mục đích:** Load tài liệu PDF/DOCX, lưu file upload, chuẩn hóa metadata chunk.

| Hàm | Mô tả | Trạng thái |
|---|---|---|
| `load_pdf(path)` | Load file PDF bằng PDFPlumber | ✅ Dùng |
| `load_docx(path)` | Load file DOCX bằng python-docx | ✅ Dùng |
| `load_documents(path)` | Dispatcher: tự động chọn loader theo đuôi file | ✅ Dùng |
| `save_uploaded_file(uploaded_file, target_dir)` | Lưu file upload từ Streamlit vào disk | ✅ Dùng |
| `file_type_from_path(file_path)` | Lấy đuôi file (pdf, docx...) | ✅ Dùng |
| `upload_time_from_path(file_path)` | Lấy thời gian chỉnh sửa file | ✅ Dùng |
| `enrich_chunks_metadata(chunks, file_path)` | Bổ sung metadata (source, file_type, upload_date) vào từng chunk | ✅ Dùng |
| `read_full_text_from_source(source_path)` | Đọc toàn bộ raw text từ file (có cache) | ⚠️ **Dead code** — không được gọi từ `src/` sau khi xóa helper functions |

---

## `src/model_layer/`

### `ollama_inference_engine.py`
**Mục đích:** Tương tác trực tiếp với Ollama, xử lý fallback model, đánh giá Self-RAG.

| Hàm / Class | Mô tả | Trạng thái |
|---|---|---|
| `is_retryable_llm_error(error)` | Phát hiện lỗi có thể retry (OOM, timeout, terminated) | ✅ Dùng |
| `_build_context_for_scoring(docs)` | Format docs thành text ngắn gọn cho scoring prompt | ✅ Dùng |
| `OllamaInferenceEngine.__init__` | Khởi tạo LLM, tự chọn model hoạt động dựa trên sticky_fallbacks | ✅ Dùng |
| `OllamaInferenceEngine._get_llm(model)` | Tạo instance OllamaLLM cho model cụ thể | ✅ Dùng |
| `OllamaInferenceEngine.generate(prompt, ...)` | Gọi LLM sinh câu trả lời, tự fallback nếu model lỗi | ✅ Dùng |
| `OllamaInferenceEngine.self_rag_confidence_score(query, answer, docs)` | Cho LLM tự chấm điểm câu trả lời (1–10) | ✅ Dùng |

---

## Tổng hợp Dead Code cần xem xét

| File | Hàm/Class | Lý do |
|---|---|---|
| `src/models.py` | `RagResult` | Không được import hay dùng ở bất kỳ đâu |
| `src/utils.py` | `natural_sort_key()` | Không được gọi trong toàn bộ `src/` |
| `src/application/document_processing_pipeline.py` | `ingest_uploaded_file()` | Chỉ có định nghĩa hàm, không có nơi nào gọi (thay bởi `ingest_multiple_uploaded_files`) |
| `src/data_layer/pdf_document_storage.py` | `read_full_text_from_source()` | Được viết cho helper functions đã xóa, hiện không có caller nào |
