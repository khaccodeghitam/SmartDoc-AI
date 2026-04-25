# TV1 - Luong theo dung thu tu goi ham (UI -> Backend -> UI) - ban cap nhat sau refactor

## 1) Muc tieu tai lieu

Tai lieu nay cap nhat TV1 theo call-chain hien tai cua du an sau khi sua code va sua ham:

- bat dau tu `app.py` va `src/presentation/streamlit_app.py`
- di xuong `src/application/*`, `src/data_layer/*`, `src/model_layer/*`
- quay lai UI de cap nhat `st.session_state`, `save_app_session(...)` va lich su hoi thoai

Tai lieu tap trung vao 2 phan:

- luong ingest -> tao/cap nhat FAISS
- luong clear/reset va cac helper lien quan den retrieval demo

---

## 2) Danh sach ham can doi chieu

### 2.1 Nhom ham TV1 chinh

1. `save_uploaded_file`
2. `ingest_document`
3. `ingest_multiple_uploaded_files`
4. `load_documents` -> `load_pdf` / `load_docx`
5. `build_and_save_faiss_index`
6. `update_faiss_index`
7. `clear_vector_store_data`

### 2.2 Nhom ham mat xich bat buoc trong ingest

1. `enrich_chunks_metadata`
2. `RecursiveCharacterTextSplitter.split_documents`
3. `save_app_session`
4. `load_app_session`

### 2.3 Nhom ham lien quan den retrieval demo va filter

1. `search_similar_chunks`
2. `search_vector_only_chunks`
3. `resolve_effective_source_filter`
4. `detect_sources_mentioned_in_query`
5. `metadata_matches_filters`
6. `source_matches_filter`
7. `source_name_core`

Ket luan doi chieu: code hien tai khong chi co ingest, ma con co luong retrieval demo va filter source dong bo voi query.

---

## 3) Luong chinh so 1: Ingest tu UI den tao/cap nhat FAISS

## Buoc 1 - Entry va UI nhan input

Entry:

- `app.py` goi `src.presentation.streamlit_app.main()`

Trong `src/presentation/streamlit_app.py`, UI nhan:

- `uploaded_files` tu `st.file_uploader(..., accept_multiple_files=True, type=["pdf", "docx"])`
- `chunk_size` tu `st.number_input("Chunk size", ...)`
- `chunk_overlap` tu `st.number_input("Chunk overlap", ...)`
- `top_k` tu `st.number_input("Top-k search", ...)`

Khi user bam `Ingest va tao FAISS index`, backend bat dau call-chain ingest.

---

## Buoc 2 - Main goi ingest_multiple_uploaded_files

Ham duoc goi:

```python
ingest_result = ingest_multiple_uploaded_files(
    uploaded_files=uploaded_files,
    chunk_size=int(chunk_size),
    chunk_overlap=int(chunk_overlap),
)
```

Vai tro:

- dieu phoi ingest theo lo nhieu file
- gop tong `raw_docs_count` va `chunks`

Gia tri tra ve:

- `IngestResult` gom `file_path`, `raw_docs_count`, `chunks_count`, `chunks`

---

## Buoc 3 - Ben trong ingest_multiple_uploaded_files goi save_uploaded_file cho tung file

Ham duoc goi:

- `src/data_layer/pdf_document_storage.py::save_uploaded_file`

Vai tro:

- luu file upload tu Streamlit vao `data/raw`
- tra ve `Path` vat ly de dung cho cac buoc sau

Noi nhan gia tri tra ve:

- quay lai `ingest_multiple_uploaded_files`
- dung `file_path` de goi tiep `ingest_document(file_path, chunk_size, chunk_overlap)`

---

## Buoc 4 - Ben trong ingest_multiple_uploaded_files goi ingest_document

Ham duoc goi:

- `src/application/document_processing_pipeline.py::ingest_document`

Vai tro:

- doc tai lieu
- chunking
- enrich metadata

Gia tri tra ve:

- `IngestResult` cho tung file

Noi nhan gia tri tra ve:

- `ingest_multiple_uploaded_files` cong don `raw_docs_count`
- `all_chunks.extend(result.chunks)` de gom chunk phang theo lo

---

## Buoc 5 - Ben trong ingest_document goi load_documents

Ham duoc goi:

- `src/data_layer/pdf_document_storage.py::load_documents`

Nhanh noi bo:

- `.pdf` -> `load_pdf(...)`
- `.docx` -> `load_docx(...)`
- khac dinh dang -> `raise ValueError("Unsupported file type")`

Gia tri tra ve:

- `raw_docs: list[Document]`

---

## Buoc 6 - Chunking trong ingest_document

Thao tac:

- tao `RecursiveCharacterTextSplitter(chunk_size, chunk_overlap)`
- goi `split_documents(raw_docs)`

Ket qua trung gian:

- `chunks`

---

## Buoc 7 - Enrich metadata cho chunks

Ham duoc goi:

- `src/data_layer/pdf_document_storage.py::enrich_chunks_metadata`

Metadata duoc bo sung / chuan hoa:

- `source`
- `file_name`
- `file_type`
- `upload_time`
- `upload_date`

Gia tri tra ve:

- danh sach `chunks` da enrich

---

## Buoc 8 - ingest_multiple_uploaded_files tra ket qua tong hop ve main

Sau khi loop het file:

- tra `IngestResult` tong hop

Noi nhan:

- `streamlit_app.main()` nhan `ingest_result`

Du lieu quan trong chuyen tiep:

- `ingest_result.chunks` duoc dung de tao/cap nhat FAISS
- `ingest_result.raw_docs_count` va `ingest_result.chunks_count` duoc dung de thong bao cho user

---

## Buoc 9 - Main tao moi hoac cap nhat index

Nhanh 1: da co index truoc do

- goi `src/data_layer/faiss_vector_store.py::update_faiss_index`

Nhanh 2: chua co index

- goi `src/data_layer/faiss_vector_store.py::build_and_save_faiss_index`

Gia tri tra ve:

- `IndexBuildResult` gom `index_name`, `index_dir`, `chunks_count`

Luu y sau refactor:

- luong hien tai cho phep ingest nhieu lan va cap nhat index tang dan
- `last_index_dir` duoc dung de quyet dinh update hay build moi

---

## Buoc 10 - Main cap nhat session_state va luu session

Main cap nhat:

- `last_index_dir`, `last_index_name`, `last_uploaded_file`
- `available_sources`, `available_file_types`, `available_upload_dates`
- `last_ingested_paths`, `ingest_notice`
- `last_chunks`, `last_bi_encoder_chunks`, `last_vector_only_chunks`, `last_query`

Main luu trang thai F5:

- goi `save_app_session(...)`

Main cung cap nhat session hoi thoai dang mo:

- cap nhat `rag_state` trong `chat_sessions`
- goi `save_persistent_history(...)` khi can dong bo

Cuoi cung:

- `st.rerun()` de render lai giao dien

Ket qua user thay:

- ingest thanh cong
- filter metadata o sidebar co du lieu
- tab Retrieval Demo va Q&A co the dung index vua tao

---

## 4) Luong chinh so 2: Xoa du lieu tam va reset state

Day la nhanh rieng cua TV1, khong nam trong luong ingest.

## Buoc 1 - UI xac nhan xoa

Trong sidebar:

- bam `Clear Vector Store + trạng thái`
- bam `Đồng ý xóa` de xac nhan

## Buoc 2 - Main goi clear_vector_store_data

Ham duoc goi:

- `src/data_layer/faiss_vector_store.py::clear_vector_store_data(index_root=INDEX_DIR, raw_root=RAW_DIR)`

Vai tro:

- xoa du lieu tam trong `data/index` va `data/raw`

Gia tri tra ve:

- dict gom `index_deleted`, `raw_deleted`

Noi nhan gia tri tra ve:

- `streamlit_app.main()` nhan `clear_result`
- reset cac state lien quan index / retrieval / filter
- thong bao ket qua xoa cho user

State bi reset thuc te:

- `last_index_dir`, `last_index_name`, `last_uploaded_file`
- `retrieval_history`, `last_chunks`, `last_bi_encoder_chunks`, `last_vector_only_chunks`, `last_query`
- `available_sources`, `available_file_types`, `available_upload_dates`
- `last_ingested_paths`, `chunk_benchmark_rows`, `ingest_notice`
- `pending_sidebar_filter_reset`

---

## 5) Luong phu: Retrieval Demo va nhom helper lien quan den filter

Phan nay khong phai ingest, nhung dang duoc UI goi truc tiep va lien quan den dong bo source/filter sau refactor.

## Buoc 1 - UI nhan filter va top_k

Trong sidebar, UI co the nhan:

- `sidebar_source_filter`
- `sidebar_file_type_filter`
- `sidebar_upload_date_filter`
- `top_k`

Gia tri nay duoc truyen xuong cac ham retrieve.

## Buoc 2 - Main goi cac nhanh retrieve

UI goi:

- `search_similar_chunks(..., use_rerank=True)` cho hybrid search
- `search_similar_chunks(..., use_rerank=False)` cho bi-encoder style fallback path
- `search_vector_only_chunks(...)` cho vector-only comparison

## Buoc 3 - Backend tinh filter hieu luc

Trong `src/utils.py`:

- `detect_sources_mentioned_in_query(query, available_sources)` tim source duoc nhac den trong cau hoi
- `resolve_effective_source_filter(query, source_filter, all_docs)` uu tien source trong query neu co
- `metadata_matches_filters(...)` kiem tra source / file_type / upload_date
- `source_matches_filter(...)` so sanh source da normalize

Y nghia thuc te:

- neu query nhac ro ten file, filter UI co the bi thu hep theo file do
- neu user chon filter khac voi source trong query, helper se xu ly theo quy tac uu tien hien tai

## Buoc 4 - Rerank va noi ket qua ve UI

Trong `src/data_layer/faiss_vector_store.py`:

- `deduplicate_docs(...)` loai chunk trung lap
- `rerank_docs(...)` xep hang lai chunk theo cross-encoder hoac keyword overlap fallback
- `_balance_docs_by_source(...)` giu can bang giua cac source

UI nhan ket qua va cap nhat:

- `last_bi_encoder_chunks`
- `last_vector_only_chunks`
- `retrieval_history`

---

## 6) Ghi chu ve append va extend trong luong ingest

Trong `ingest_multiple_uploaded_files`:

- `file_paths.append(file_path)`: them tung duong dan file vao list
- `all_chunks.extend(result.chunks)`: noi cac chunk vao list phang

Ly do dung `extend`:

- giu kieu du lieu `all_chunks` la `list[Document]`
- tranh long list khi gop ket qua nhieu file

---

## 7) Bang tom tat thu tu goi ham

1. `app.py` -> `streamlit_app.main()`
2. UI nhan `uploaded_files`, `chunk_size`, `chunk_overlap`, `top_k`
3. `main` -> `ingest_multiple_uploaded_files`
4. `ingest_multiple_uploaded_files` -> `save_uploaded_file`
5. `ingest_multiple_uploaded_files` -> `ingest_document`
6. `ingest_document` -> `load_documents`
7. `load_documents` -> `load_pdf` hoac `load_docx`
8. `ingest_document` -> `RecursiveCharacterTextSplitter.split_documents`
9. `ingest_document` -> `enrich_chunks_metadata`
10. `ingest_multiple_uploaded_files` -> tra `ingest_result`
11. `main` -> `build_and_save_faiss_index` hoac `update_faiss_index`
12. `main` cap nhat state + `save_app_session` + `save_persistent_history` + `st.rerun()`

Nhanh rieng TV1 clear:

13. UI clear -> `clear_vector_store_data` -> reset state -> rerun

Nhanh retrieval demo:

14. UI retrieve -> `search_similar_chunks` / `search_vector_only_chunks` -> rerank/dedup -> cap nhat state

---

## 8) Ket luan

Tai lieu TV1 da duoc cap nhat theo cau truc moi `src/*` va phan anh dung call-chain hien tai sau khi sua code.

Da bao phu cac ham chinh:

- `save_uploaded_file`
- `ingest_document`
- `ingest_multiple_uploaded_files`
- `load_docx` / `load_documents`
- `build_and_save_faiss_index`
- `update_faiss_index`
- `clear_vector_store_data`

Va da bo sung cac helper lien quan den retrieval/filter de tai lieu khong bi lech so voi code hien tai.
