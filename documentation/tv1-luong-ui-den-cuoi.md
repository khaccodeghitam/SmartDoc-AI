# TV1 - Luong theo dung thu tu goi ham (UI -> Backend -> UI) - ban theo cau truc moi

## 1) Muc tieu tai lieu

Tai lieu nay cap nhat TV1 theo call-chain hien tai cua du an sau refactor:

- bat dau tu `app.py` va `src/presentation/streamlit_app.py`
- di xuong `src/application/*` va `src/data_layer/*`
- quay lai UI de cap nhat `st.session_state`

Dong thoi doi chieu du 4 chuc nang TV1 va cac ham mat xich bat buoc.

---

## 2) Danh sach ham TV1 can co

### 2.1 Bon chuc nang TV1

1. `save_uploaded_file`
2. `ingest_document`
3. `load_docx` (qua `load_documents`)
4. `clear_vector_store_data`

### 2.2 Cac ham mat xich bat buoc trong luong ingest

1. `ingest_multiple_uploaded_files`
2. `enrich_chunks_metadata`
3. `build_and_save_faiss_index` (hoac `update_faiss_index` neu index da ton tai)

Ket luan doi chieu: da du 4 ham TV1 + cac ham mat xich can co trong code hien tai.

---

## 3) Luong chinh so 1: Ingest tu UI den tao/cap nhat FAISS

## Buoc 1 - Entry va UI nhan input

Entry:

- `app.py` goi `src.presentation.streamlit_app.main()`

Trong `src/presentation/streamlit_app.py`, UI nhan:

- `uploaded_files` tu `st.file_uploader(..., accept_multiple_files=True, type=["pdf", "docx"])`
- `chunk_size` tu `st.number_input("Chunk size", ...)`
- `chunk_overlap` tu `st.number_input("Chunk overlap", ...)`

Khi user bam `Ingest va tao FAISS index`, call-chain backend bat dau.

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
- gom tong chunks de build/cap nhat index

Gia tri tra ve:

- `IngestResult` gom `raw_docs_count`, `chunks_count`, `chunks`

---

## Buoc 3 - Ben trong ingest_multiple_uploaded_files goi save_uploaded_file cho tung file

Ham duoc goi:

- `src/data_layer/pdf_document_storage.py::save_uploaded_file`

Vai tro:

- luu file upload tu bo dem Streamlit vao `data/raw`

Gia tri tra ve:

- `file_path` (Path vat ly)

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
- noi list chunks bang `all_chunks.extend(result.chunks)`

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

Metadata duoc bo sung/chuan hoa:

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

- `streamlit_app.main()` nhan vao `ingest_result`

Du lieu quan trong chuyen tiep:

- `ingest_result.chunks` duoc dung de tao/cap nhat FAISS

---

## Buoc 9 - Main tao moi hoac cap nhat index

Nhanh 1: da co index truoc do

- goi `src/data_layer/faiss_vector_store.py::update_faiss_index`

Nhanh 2: chua co index

- goi `src/data_layer/faiss_vector_store.py::build_and_save_faiss_index`

Gia tri tra ve:

- `IndexBuildResult` gom `index_name`, `index_dir`, `chunks_count`

---

## Buoc 10 - Main cap nhat session_state va rerun UI

Main cap nhat:

- `last_index_dir`, `last_index_name`, `last_uploaded_file`
- `available_sources`, `available_file_types`, `available_upload_dates`
- `last_ingested_paths`, `ingest_notice`

Main luu trang thai F5:

- goi `save_app_session(...)`

Cuoi cung:

- `st.rerun()` de render lai giao dien

Ket qua user thay:

- ingest thanh cong
- filter metadata o sidebar co du lieu
- tab Retrieval/Q&A co the dung index vua tao

---

## 4) Luong chinh so 2: Xoa du lieu tam (chuc nang TV1 thu 4)

Day la nhanh rieng cua TV1, khong nam trong luong ingest.

## Buoc 1 - UI xac nhan xoa

Trong sidebar:

- bam `Clear Vector Store + trang thai`
- bam `Dong y xoa` de xac nhan

## Buoc 2 - Main goi clear_vector_store_data

Ham duoc goi:

- `src/data_layer/faiss_vector_store.py::clear_vector_store_data(index_root=INDEX_DIR, raw_root=RAW_DIR)`

Vai tro:

- xoa du lieu tam trong `data/index` va `data/raw`

Gia tri tra ve:

- dict gom `index_deleted`, `raw_deleted`

Noi nhan gia tri tra ve:

- `streamlit_app.main()` nhan `clear_result`
- reset cac state lien quan index/retrieval/filter
- thong bao ket qua xoa cho user

---

## 5) Bang tom tat thu tu goi ham TV1

1. `app.py` -> `streamlit_app.main()`
2. UI nhan `uploaded_files`, `chunk_size`, `chunk_overlap`
3. `main` -> `ingest_multiple_uploaded_files`
4. `ingest_multiple_uploaded_files` -> `save_uploaded_file`
5. `ingest_multiple_uploaded_files` -> `ingest_document`
6. `ingest_document` -> `load_documents`
7. `load_documents` -> `load_pdf` hoac `load_docx`
8. `ingest_document` -> `RecursiveCharacterTextSplitter.split_documents`
9. `ingest_document` -> `enrich_chunks_metadata`
10. `ingest_multiple_uploaded_files` -> tra `ingest_result`
11. `main` -> `build_and_save_faiss_index` hoac `update_faiss_index`
12. `main` cap nhat state + `save_app_session` + `st.rerun()`

Nhanh rieng TV1:

13. UI clear -> `clear_vector_store_data` -> reset state -> rerun

---

## 6) Ghi chu append va extend trong luong ingest

Trong `ingest_multiple_uploaded_files`:

- `file_paths.append(file_path)`: them tung duong dan file vao list
- `all_chunks.extend(result.chunks)`: noi cac chunk vao list phang

Ly do dung `extend`:

- giu kieu du lieu `all_chunks` la `list[Document]`, khong bi long list

---

## 7) Ket luan

Tai lieu TV1 da cap nhat theo cau truc moi `src/*`, phan anh dung call-chain hien tai cua code.

Da bao phu day du 4 ham chuc nang TV1:

- `save_uploaded_file`
- `ingest_document`
- `load_docx` (qua `load_documents`)
- `clear_vector_store_data`

Va day du cac ham mat xich bat buoc cua luong ingest:

- `ingest_multiple_uploaded_files`
- `enrich_chunks_metadata`
- `build_and_save_faiss_index`/`update_faiss_index`
