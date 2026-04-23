# Phan cong 5 thanh vien + co che chay tu UI den BE (ban theo cau truc moi)

## 1) Muc tieu tai lieu

- Mo ta duoc luong chay thuc te tu UI den Backend va quay lai UI.
- Chi ro ham nao goi ham nao trong cau truc moi `app.py` + `src/*`.
- Chia dung 20 chuc nang (10 cot loi + 10 phat trien), moi thanh vien 4 chuc nang.

---

## 2) Cau truc moi cua du an

- Entry point: `app.py`
- Presentation layer: `src/presentation/streamlit_app.py`, `src/presentation/ui_config.py`
- Application layer: `src/application/*`
- Data layer: `src/data_layer/*`
- Model layer: `src/model_layer/*`

Luu y: Toan bo tham chieu `app/main.py`, `app/rag_pipeline.py`, `app/document_loader.py` trong ban cu da khong con dung.

---

## 3) Luong tong tu UI -> BE (ban moi)

### 3.1 Luong A: Upload nhieu file va tao/cap nhat FAISS

Buoc 1. User thao tac o sidebar trong `src/presentation/streamlit_app.py`:

- Upload file (`accept_multiple_files=True`, ho tro PDF/DOCX)
- Nhap `chunk_size`, `chunk_overlap`
- Bam nut `Ingest va tao FAISS index`

Buoc 2. Main goi pipeline ingest:

```python
ingest_result = ingest_multiple_uploaded_files(
    uploaded_files=uploaded_files,
    chunk_size=int(chunk_size),
    chunk_overlap=int(chunk_overlap),
)
```

Buoc 3. Application layer xu ly ingest:

- `src/application/document_processing_pipeline.py::ingest_multiple_uploaded_files`
- moi file se qua:
  - `src/data_layer/pdf_document_storage.py::save_uploaded_file`
  - `src/application/document_processing_pipeline.py::ingest_document`
  - `src/data_layer/pdf_document_storage.py::load_documents`
  - `RecursiveCharacterTextSplitter.split_documents`
  - `src/data_layer/pdf_document_storage.py::enrich_chunks_metadata`

Buoc 4. Data layer tao hoac cap nhat index:

- Tao moi: `src/data_layer/faiss_vector_store.py::build_and_save_faiss_index`
- Cap nhat them: `src/data_layer/faiss_vector_store.py::update_faiss_index`

Buoc 5. UI cap nhat state:

- `last_index_dir`, `last_index_name`, `last_uploaded_file`
- `available_sources`, `available_file_types`, `available_upload_dates`
- luu session F5 qua `save_app_session(...)`

---

### 3.2 Luong B: Retrieval demo (hybrid/bi-encoder/vector-only)

Buoc 1. User nhap query + top_k + metadata filter o sidebar.

Buoc 2. Main goi 3 nhanh retrieve trong `src/presentation/streamlit_app.py`:

```python
docs = search_similar_chunks(..., use_rerank=True)
bi_encoder_docs = search_similar_chunks(..., use_rerank=False)
vector_only_docs = search_vector_only_chunks(...)
```

Buoc 3. Backend retrieval:

- `src/data_layer/faiss_vector_store.py::search_similar_chunks`
  - MMR + similarity + BM25
  - deduplicate
  - rerank cross-encoder (neu bat)
- `src/data_layer/faiss_vector_store.py::search_vector_only_chunks`
  - chi similarity vector + rerank

Buoc 4. UI render 3 tab so sanh:

- Hybrid + CrossEncoder
- Hybrid Bi-encoder
- Vector-only Baseline

---

### 3.3 Luong C: Q&A voi Basic RAG va Co-RAG

Buoc 1. User nhap cau hoi trong tab Q&A.

Buoc 2. Main khoi tao model + manager:

```python
model_engine = OllamaInferenceEngine(...)
manager = RAGChainManager(index_dir=last_index_dir, model_engine=model_engine)
co_manager = CoRAGChainManager(index_dir=last_index_dir, model_engine=model_engine, top_k=int(top_k))
```

Buoc 3. Chay 2 nhanh:

- Basic: `RAGChainManager.ask(...)`
- Co-RAG: `CoRAGChainManager.ask(...)`

Buoc 4. Co-RAG advanced:

- Danh gia du/khong du context (`build_corag_sufficiency_check_prompt`)
- Sinh `sub_query` va truy xuat them theo vong
- Tong hop context va sinh dap an cuoi
- Cham diem tin cay qua `self_rag_confidence_score`

Buoc 5. UI hien thi:

- cau tra loi
- diem tin cay
- so vong Co-RAG va sub-query moi vong

---

## 4) Bang chia 20 chuc nang (10 cot loi + 10 phat trien)

Nguyen tac:

- Moi thanh vien 4 chuc nang
- Moi muc co module/ham dang su dung trong cau truc moi

## TV1 - Tuan Tai (4 chuc nang)

Ghi chu: luong TV1 chi tiet duoc cap nhat tai `documentation/tv1-luong-ui-den-cuoi.md`.

### [Cot loi #1] Upload va xu ly file

- `src/data_layer/pdf_document_storage.py::save_uploaded_file`
- `src/data_layer/pdf_document_storage.py::load_documents`

### [Cot loi #2] Chunking tai lieu

- `src/application/document_processing_pipeline.py::ingest_document`

### [Phat trien #1] Ho tro DOCX

- `src/data_layer/pdf_document_storage.py::load_docx`

### [Phat trien #3] Xoa du lieu tam

- `src/data_layer/faiss_vector_store.py::clear_vector_store_data`

## TV2 - Thịnh  (4 chuc nang)

### [Cot loi #3] Embedding da ngon ngu

- `src/data_layer/multilingual_mpnet_embeddings.py::build_embedder`

### [Cot loi #4] FAISS store + search

- `src/data_layer/faiss_vector_store.py::build_and_save_faiss_index`
- `src/data_layer/faiss_vector_store.py::load_faiss_index`

### [Phat trien #4] Cai thien chunk strategy

- `src/application/document_processing_pipeline.py::evaluate_chunk_strategies`

### [Phat trien #8] Multi-document metadata enrich

- `src/data_layer/pdf_document_storage.py::enrich_chunks_metadata`

## TV3 (4 chuc nang)

### [Cot loi #5] Document Q&A phan retrieval context

- `src/application/rag_chain_manager.py::RAGChainManager.ask`

### [Cot loi #6] Tich hop LLM local qua Ollama

- `src/model_layer/ollama_inference_engine.py::OllamaInferenceEngine.generate`

### [Phat trien #7] Hybrid search

- `src/data_layer/faiss_vector_store.py::search_similar_chunks`

### [Phat trien #9] Re-ranking voi Cross-Encoder

- `src/data_layer/faiss_vector_store.py::rerank_docs`

## TV4 (4 chuc nang)

### [Cot loi #7] Prompt engineering + rang buoc

- `src/application/prompt_engineering.py::build_rag_prompt`
- `src/application/prompt_engineering.py::build_corag_final_prompt`

### [Cot loi #8] Nhan dien ngon ngu va phan hoi phu hop

- `src/application/prompt_engineering.py::detect_vietnamese`
- `src/application/prompt_engineering.py::is_probably_english_query`

### [Phat trien #6] Conversational RAG

- `src/application/query_rewriter.py::is_follow_up_query`
- `src/application/query_rewriter.py::rewrite_query_with_history`

Luu y trang thai hien tai: module da co, nhung chua noi full vao luong Q&A trong UI.

### [Phat trien #10] Advanced RAG / Self-RAG

- `src/application/corag_chain_manager.py::CoRAGChainManager`
- `src/model_layer/ollama_inference_engine.py::self_rag_confidence_score`

## TV5 (4 chuc nang)

### [Cot loi #9] UI Streamlit

- `src/presentation/streamlit_app.py::main`

### [Cot loi #10] Error handling cho user

- `src/presentation/streamlit_app.py::_to_user_error_message`

### [Phat trien #2] Luu lich su hoi thoai

- `src/data_layer/conversation_store.py::save_persistent_history`
- `src/data_layer/conversation_store.py::load_persistent_history`
- `src/presentation/streamlit_app.py::_append_chat`

### [Phat trien #5] Citation / source tracking

- `src/presentation/streamlit_app.py::_render_sources`

Luu y trang thai hien tai: ham render da co, nhung chua duoc noi day du vao luong Q&A de hien citation end-to-end.

---

## 5) Vi du trace tham so (ban moi)

### Vi du 1: Upload 2 file

Input:

- `uploaded_files = [A.docx, B.pdf]`
- `chunk_size = 1000`
- `chunk_overlap = 150`

Call chain:

1. `src/presentation/streamlit_app.py` -> `ingest_multiple_uploaded_files(...)`
2. `src/application/document_processing_pipeline.py::ingest_multiple_uploaded_files`
3. `save_uploaded_file` + `ingest_document` tren tung file
4. `load_documents` -> `load_pdf/load_docx`
5. `enrich_chunks_metadata`
6. `build_and_save_faiss_index` hoac `update_faiss_index`
7. cap nhat session_state + save_app_session

Output:

- Index moi/duoc cap nhat
- Metadata filter duoc cap nhat tren sidebar

### Vi du 2: Retrieval so sanh 3 nhanh

Input:

- query + top_k + filter

Call chain:

1. `search_similar_chunks(..., use_rerank=True)`
2. `search_similar_chunks(..., use_rerank=False)`
3. `search_vector_only_chunks(...)`

Output:

- UI co 3 tap ket qua de so sanh

### Vi du 3: Co-RAG

Input:

- `qa_query = "Tom tat 3 y chinh"`

Call chain:

1. `co_manager.ask(question=qa_query)`
2. retrieval vong 1
3. sufficiency check -> co the sinh sub_query
4. retrieval them theo vong
5. final prompt + answer
6. confidence scoring

Output:

- cau tra loi Co-RAG
- tong so vong
- sub-query tung vong
- diem tin cay x/10

---

## 6) Ket luan

- Hai tai lieu huong dan da duoc cap nhat theo kien truc moi `src/*`.
- Da bo toan bo tham chieu code cu trong `app/*`.
- Bang phan cong va luong goi ham hien phan anh dung trang thai code hien tai, gom ca cac muc da co module nhung chua noi full end-to-end.
