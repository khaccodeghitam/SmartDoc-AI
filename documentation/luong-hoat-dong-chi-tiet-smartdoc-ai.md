# Luồng hoạt động chi tiết của SmartDoc AI

## 1. Mục tiêu hệ thống

SmartDoc AI là ứng dụng hỏi đáp tài liệu (PDF/DOCX) chạy local với Streamlit, sử dụng:
- Embedding để biến tài liệu thành vector.
- FAISS để lưu/chỉ mục vector.
- Hybrid Retrieval (FAISS + BM25) + rerank để tìm ngữ cảnh tốt hơn.
- Ollama LLM để sinh câu trả lời.
- Hai chế độ suy luận:
  - Basic RAG: 1-shot retrieval + generation.
  - Co-RAG: truy xuất nhiều vòng có tự đánh giá đủ/chưa đủ thông tin.

---

## 2. Toàn cảnh cấu trúc project theo vai trò

- `app.py`: entrypoint chạy Streamlit.
- `src/presentation/streamlit_app.py`: điều phối toàn bộ UI + luồng nghiệp vụ phía người dùng.
- `src/application/*`: tầng nghiệp vụ RAG/Co-RAG, query rewriting, pipeline ingest.
- `src/data_layer/*`: thao tác lưu file, FAISS index, hội thoại, embedding.
- `src/model_layer/ollama_inference_engine.py`: lớp gọi LLM Ollama + fallback + chấm điểm tin cậy.
- `src/utils.py`: hàm tiện ích chuẩn hóa text, lọc metadata, nhận diện nguồn tài liệu.
- `scripts/inspect_index.py`: script kiểm tra trực tiếp cấu trúc index FAISS.
- `tests/test_rag_deterministic.py`: unit test cho logic deterministic quan trọng.
- `data/`: nơi lưu dữ liệu chạy thực tế (raw file, index, chat history).
- `documentation/`: tài liệu phân tích, thiết kế, yêu cầu, checklist.

---

## 3. Luồng khởi động ứng dụng

### Bước 1: Chạy app
- Người dùng chạy: `streamlit run app.py`.
- `app.py` gọi `main()` trong `src/presentation/streamlit_app.py`.

### Bước 2: Thiết lập phiên làm việc ban đầu
Trong `main()`:
1. `st.set_page_config(...)` cấu hình trang.
2. `_init_state()` khởi tạo toàn bộ `st.session_state`.
3. Nếu có session cũ (F5/reload), `load_app_session()` khôi phục trạng thái index gần nhất.
4. `load_persistent_history()` nạp lịch sử hội thoại từ `data/chat_history/history.json`.
5. Áp CSS/UI bằng `apply_styles()`, render hero và sidebar.

Kết quả: app sẵn sàng với đúng trạng thái trước đó (nếu có), không mất ngữ cảnh khi refresh.

---

## 4. Luồng Upload và tạo/chỉnh sửa FAISS Index

Nằm ở tab **Upload & Index**.

### Bước 1: Người dùng upload file
- Sidebar nhận nhiều file PDF/DOCX (`st.file_uploader`).
- Cấu hình kèm theo:
  - `chunk_size`
  - `chunk_overlap`
  - `top_k`
  - các filter nguồn, loại file, ngày upload.

### Bước 2: Ingest tài liệu
Khi bấm “Ingest và tạo FAISS index”:
1. `ingest_multiple_uploaded_files(...)` được gọi.
2. Mỗi file đi qua:
   - `save_uploaded_file()` lưu vào `data/raw`.
   - `load_documents()`:
     - PDF: `PDFPlumberLoader`
     - DOCX: đọc paragraphs bằng `python-docx`
   - `RecursiveCharacterTextSplitter` để chunk.
   - `enrich_chunks_metadata()` thêm metadata:
     - source, file_name, file_type, upload_time, upload_date.

### Bước 3: Build hoặc update index
- Nếu đã có index trước đó (`last_index_dir` tồn tại):
  - gọi `update_faiss_index(new_chunks, index_dir)` để add_documents.
- Nếu chưa có:
  - gọi `build_and_save_faiss_index(chunks, source_name)` để tạo index mới.
- Embedding model được lấy từ `build_embedder()` (cache resource).

### Bước 4: Cập nhật state và persistence
Sau ingest thành công:
1. Cập nhật `last_index_dir`, `last_index_name`, `last_uploaded_file`.
2. Gộp metadata vào danh sách filter khả dụng:
   - `available_sources`
   - `available_file_types`
   - `available_upload_dates`
3. `save_app_session(...)` lưu trạng thái index ra `app_session.json`.
4. Nếu có phiên chat active, cập nhật `rag_state` bên trong phiên đó.

---

## 5. Luồng Retrieval Demo (không sinh câu trả lời)

Nằm ở tab **Retrieval Demo**.

### Bước 1: Nhập truy vấn
- Người dùng nhập câu hỏi test retrieval.
- Có thể kết hợp filter source/file type/upload date.

### Bước 2: Chạy 3 nhánh retrieval để so sánh
App gọi đồng thời logic:
1. `search_similar_chunks(..., use_rerank=True)`
   - Hybrid + CrossEncoder rerank.
2. `search_similar_chunks(..., use_rerank=False)`
   - Hybrid không rerank (bi-encoder baseline).
3. `search_vector_only_chunks(...)`
   - Vector-only baseline.

### Bước 3: Cách `search_similar_chunks` hoạt động
1. `load_faiss_index(index_dir)`.
2. Lấy toàn bộ docs trong docstore.
3. `resolve_effective_source_filter(...)` để ưu tiên nguồn tài liệu được nhắc trong query.
4. Thu ứng viên từ 3 nguồn:
   - MMR search từ FAISS.
   - Similarity search từ FAISS.
   - BM25 retrieval.
5. `deduplicate_docs(...)` loại trùng.
6. `rerank_docs(...)`:
   - ưu tiên CrossEncoder `cross-encoder/ms-marco-MiniLM-L-6-v2`.
   - fallback sang điểm overlap keyword nếu thiếu dependency/lỗi.
   - phạt chunk dạng mục lục hoặc quá ngắn.
7. `_balance_docs_by_source(...)` để tránh top-k dồn hết về một file.

Kết quả được hiển thị thành 3 tab so sánh chunk.

---

## 6. Luồng Q&A cơ bản (Basic RAG)

Nằm ở tab **Q&A với LLM**, khi tắt Co-RAG.

### Bước 1: Chuẩn hóa truy vấn
1. Người dùng nhập câu hỏi.
2. `rewrite_query_with_history(...)`:
   - chỉ rewrite khi nhận diện follow-up query.
   - dùng Ollama model hiện tại; lỗi thì thử fallback models.
3. `should_include_history_in_prompt(...)` quyết định có đưa chat history vào prompt hay không.

### Bước 2: Gọi RAG pipeline
`RAGChainManager.ask(...)` thực hiện:
1. `search_similar_chunks(...)` để lấy context chunks.
2. `_format_context_chunks(...)` gắn header file/trang.
3. `build_rag_prompt(...)` sinh prompt theo ngôn ngữ truy vấn.
4. `OllamaInferenceEngine.generate(...)` sinh câu trả lời.
5. `clean_generated_answer(...)` loại prompt-echo/noise.
6. `self_rag_confidence_score(...)` chấm điểm tin cậy 1-10.

### Bước 3: Lưu kết quả
- Với mode chỉ RAG, app lưu ngay vào lịch sử bằng `_append_chat(...)`.
- Xóa ô nhập bằng `_request_clear_qa_query()`.

---

## 7. Luồng Q&A nâng cao (Co-RAG so với RAG)

Khi bật toggle Co-RAG, hệ thống chạy RAG trước rồi Co-RAG để người dùng chọn câu trả lời tốt hơn.

### Bước 1: Chạy Basic RAG trước
- RAG chạy xong sẽ hiển thị kết quả tạm thời ngay.
- Đồng thời tạo một bản ghi `pending_qa` qua `_append_pending_dual_chat(...)`.

### Bước 2: Chạy Co-RAG nhiều vòng
`CoRAGChainManager.ask(...)`:
1. Vòng 1: retrieve initial chunks bằng `search_similar_chunks` (không aggressive rerank).
2. LLM tự đánh giá đủ/chưa đủ qua `build_corag_sufficiency_check_prompt(...)`.
3. Nếu chưa đủ, trích `SUB_QUERY`, ghép anchor với câu hỏi gốc, rồi retrieve vòng tiếp.
4. Lặp đến khi:
   - nhận tín hiệu `SUFFICIENT`, hoặc
   - đạt `max_rounds`.
5. Tạo final prompt bằng `build_corag_final_prompt(...)` và sinh câu trả lời cuối.
6. Chấm confidence score giống RAG.

### Bước 3: Chờ người dùng chọn lưu
- App hiển thị song song:
  - Basic RAG answer
  - Co-RAG answer + từng iteration
- Người dùng bấm:
  - “Lưu đoạn RAG này”, hoặc
  - “Lưu đoạn Co-RAG này”.
- `_save_selected_answer_from_pending(...)` finalize bản ghi pending thành bản ghi chính thức.

### Bước 4: Cơ chế Pause
- Nút Pause cho phép dừng lượt hỏi hiện tại.
- `_pause_and_store_current_question(...)` ưu tiên lưu câu trả lời đã có (Co-RAG nếu đã xong, nếu không thì RAG).
- Nếu chưa có kết quả nào, lưu trạng thái “Dừng trả lời”.

### 7.1 Luồng code theo phân công TV3

TV3 phụ trách nhánh xử lý hỏi đáp cốt lõi, tức là phần nhận câu hỏi, truy xuất ngữ cảnh, gọi LLM và so sánh các kiểu retrieval. Luồng code thực tế của TV3 đi qua các file sau:
- `src/application/rag_chain_manager.py`
- `src/model_layer/ollama_inference_engine.py`
- `src/data_layer/faiss_vector_store.py`
- `src/presentation/streamlit_app.py` (phần gọi luồng Q&A và retrieval demo)

#### Bước 1: Nhận câu hỏi từ UI
- Người dùng nhập câu hỏi trong tab Q&A.
- `src/presentation/streamlit_app.py` kiểm tra câu hỏi, rewrite nếu là follow-up, rồi khởi tạo `OllamaInferenceEngine` và `RAGChainManager`.
- Nếu đang ở chế độ so sánh retrieval, UI cũng gọi thêm `search_similar_chunks(...)` và `search_vector_only_chunks(...)`.

#### Bước 2: Truy xuất ngữ cảnh cho Basic RAG
- `RAGChainManager.ask(...)` gọi `search_similar_chunks(...)` để lấy top-k đoạn liên quan nhất.
- Hàm `_format_context_chunks(...)` của `RAGChainManager` gắn metadata file/trang vào từng đoạn trích.
- Nếu không có context phù hợp, hàm trả về thông báo lỗi thân thiện cho UI.

#### Bước 3: Sinh prompt và gọi LLM
- `build_rag_prompt(...)` dựng prompt theo câu hỏi và context đã truy xuất.
- `OllamaInferenceEngine.generate(...)` gửi prompt sang Ollama để sinh câu trả lời.
- Kết quả sau đó được làm sạch bằng `clean_generated_answer(...)` để loại bỏ phần nhiễu hoặc lặp prompt.

#### Bước 4: Chấm độ tin cậy câu trả lời
- Sau khi có đáp án, `RAGChainManager.ask(...)` gọi `self_rag_confidence_score(...)`.
- Hàm này dùng context đã truy xuất để chấm điểm tin cậy theo thang 1-10, giúp UI hiển thị mức độ đáng tin của câu trả lời.

#### Bước 5: Retrieval demo để so sánh
- `search_similar_chunks(...)` là nhánh hybrid search chính: kết hợp FAISS similarity, MMR, BM25, deduplicate và rerank.
- `search_vector_only_chunks(...)` là nhánh baseline chỉ dùng vector search rồi rerank lại.
- Kết quả của hai nhánh này được hiển thị trong UI để so sánh với nhau.

#### Ý nghĩa của phần TV3
- TV3 chịu phần “xương sống” của chức năng hỏi đáp: từ truy xuất, sinh câu trả lời đến đánh giá chất lượng.
- Các file của TV3 được tách theo trách nhiệm rõ ràng: `faiss_vector_store.py` lo retrieval, `rag_chain_manager.py` lo orchestration Q&A, còn `ollama_inference_engine.py` lo gọi model và chấm điểm.
- Cách tách này giúp các phần Basic RAG, hybrid search và scoring có thể kiểm thử hoặc thay thế độc lập mà không làm vỡ toàn bộ luồng UI.

---

## 8. Quản lý hội thoại và phiên chat

### Dữ liệu lưu
- `data/chat_history/history.json`: danh sách session chat.
- `data/chat_history/app_session.json`: trạng thái index hiện hành (để survive F5).

### Cấu trúc quản lý
- Mỗi session có:
  - `session_id`, `title`, `timestamp`
  - `history` (các lượt hỏi đáp)
  - `rag_state` (index, file, filter khả dụng theo phiên)

### Hành vi quan trọng
- `_sync_current_session_history(...)` luôn cắt tối đa 50 lượt gần nhất.
- Có migration tự động nếu history.json cũ chưa có `session_id`.
- Có chức năng xóa từng session hoặc clear toàn bộ lịch sử.

---

## 9. Cơ chế chống lỗi và fallback

### Embedding fallback
Trong `build_embedder()`:
- Thử model chính trước.
- Nếu lỗi RAM/virtual memory, thử model fallback nhẹ hơn.
- Nếu vẫn lỗi, ném RuntimeError có hướng dẫn tăng paging file.

### LLM fallback
Trong `OllamaInferenceEngine.generate()`:
- Nếu lỗi retryable (OOM, connection, timeout, 500...),
- đánh dấu model hiện tại lỗi tạm thời (sticky fallback),
- tự động thử model fallback khác.

### Chuyển lỗi kỹ thuật sang thông điệp người dùng
`_to_user_error_message(...)` map các lỗi phổ biến:
- unsupported file type
- thiếu quyền truy cập
- lỗi kết nối Ollama
- lỗi FAISS/index
- thiếu virtual memory

---

## 10. Luồng benchmark chunk strategy

Nằm ở tab Upload & Index, card “So sánh chunk strategy”.

Quy trình:
1. Lấy danh sách file đã ingest (`last_ingested_paths`).
2. Sinh 3 cấu hình chunk quanh giá trị hiện tại.
3. Với mỗi cấu hình:
   - ingest lại tài liệu theo cặp size/overlap đó,
   - build vector tạm,
   - chạy retrieval theo query benchmark,
   - tính `relevance_proxy` bằng `keyword_overlap_score`.
4. Hiển thị bảng so sánh để chọn cấu hình phù hợp.

---

## 11. Script và test hỗ trợ

### Script kiểm tra index
`scripts/inspect_index.py` dùng để:
- đọc trực tiếp `index.faiss` + `index.pkl`,
- in thông tin dimension, số vectors, số doc,
- in sample metadata/excerpt.

### Test deterministic
`tests/test_rag_deterministic.py` kiểm thử các logic cốt lõi không phụ thuộc model ngẫu nhiên:
- nhận diện file được nhắc trong query,
- xử lý conflict giữa query và source filter,
- phát hiện source không tồn tại,
- follow-up detection,
- include history decision,
- giới hạn độ dài context cho scoring.

---

## 12. Luồng dữ liệu end-to-end (tóm tắt tuyến tính)

1. User mở app.
2. App khôi phục state + lịch sử.
3. User upload tài liệu.
4. Tài liệu được lưu raw, chunk, enrich metadata.
5. Chunks được embed và ghi vào FAISS index.
6. User đặt truy vấn.
7. Query có thể được rewrite theo lịch sử hội thoại.
8. Retriever lấy top-k chunks (hybrid + rerank).
9. Prompt được dựng từ context (+ lịch sử nếu cần).
10. LLM sinh câu trả lời.
11. Hệ thống chấm confidence và hiển thị kết quả.
12. Ở Co-RAG, hệ thống lặp retrieve-assess trước khi trả lời cuối.
13. User chọn lưu đáp án, app persist vào history/session.

---

## 13. Điểm mạnh kiến trúc hiện tại

- Phân tầng rõ ràng: Presentation, Application, Data, Model.
- Co-RAG tách riêng khỏi Basic RAG, dễ so sánh và cải tiến.
- Có persistence cho cả lịch sử chat và trạng thái index.
- Retrieval tương đối mạnh nhờ hybrid + rerank + source balancing.
- Có fallback cho cả embedding và LLM, phù hợp môi trường local dễ thiếu tài nguyên.
- Có test deterministic và script inspect index để debug vận hành.

---

## 14. Kết luận

Project đã có luồng hoàn chỉnh từ ingest tài liệu đến hỏi đáp đa chiến lược (RAG/Co-RAG), kèm cơ chế lưu phiên, fallback khi lỗi tài nguyên, và công cụ kiểm thử/giám sát cơ bản. Luồng xử lý được tổ chức tốt, dễ mở rộng thêm tính năng như citation nâng cao, đánh giá tự động chất lượng câu trả lời, hoặc tối ưu hiệu năng retrieval theo domain tài liệu.
