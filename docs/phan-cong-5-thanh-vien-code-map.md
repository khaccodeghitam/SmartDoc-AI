# Phan cong 5 thanh vien + co che chay tu UI den BE

## 1) Muc tieu tai lieu nay

- Tra loi duoc cau hoi van dap: chuc nang nay chay tu dau toi dich nhu the nao.
- Biet ro ham nao goi ham nao, tham so di tu dau vao, va output tra ve la gi.
- Chia dung 20 chuc nang (10 cot loi + 10 phat trien them), moi thanh vien 4 chuc nang.

---

## 2) Luong tong tu UI -> BE

### 2.1 Luong A: Upload va tao index (tu dau toi dich)

Buoc 1. User thao tac UI:

- Chon file tai sidebar uploader.
- Chon chunk_size, chunk_overlap.
- Bam nut Ingest va tao FAISS index.

Buoc 2. Main goi backend:

- Vi tri: app/main.py:461 va app/main.py:467.

```python
ingest_result = ingest_multiple_uploaded_files(
    uploaded_files=uploaded_files,
    chunk_size=int(chunk_size),
    chunk_overlap=int(chunk_overlap),
)
index_result = build_and_save_faiss_index(
    chunks=ingest_result.chunks,
    source_name=idx_name,
)
```

Buoc 3. Backend xu ly file + chunk:

- Vi tri: app/rag_pipeline.py:163 -> ingest_multiple_uploaded_files
- Vi tri: app/rag_pipeline.py:127 -> ingest_document
- Vi tri: app/document_loader.py:33 -> load_documents

```python
def load_documents(path: str | Path) -> List[Document]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(file_path)
    if suffix == ".docx":
        return load_docx(file_path)
```

Buoc 4. Tao embedding + luu FAISS:

- Vi tri: app/rag_pipeline.py:188 -> \_build_embedder
- Vi tri: app/rag_pipeline.py:198 -> build_and_save_faiss_index

Ket qua:

- st.session_state duoc cap nhat last_index_dir, available_sources, available_file_types, available_upload_dates.
- UI co du lieu de filter va QA.

#### 2.1.1 `st` là gì?

- `st` là bí danh của thư viện Streamlit, được import tại app/main.py:10:

```python
import streamlit as st
```

Nghĩa là các lệnh như `st.button`, `st.spinner`, `st.error`, `st.info`, `st.session_state`, `st.rerun` đều là API Streamlit để điều khiển UI, trạng thái và vòng render.

### 2.2 Luong B: Retrieval demo (top-k chunks)

Buoc 1. User nhap retrieval_query + top_k + filters.

Buoc 2. Main goi 3 kieu retrieve:

- Vi tri: app/main.py:626, app/main.py:635, app/main.py:645.

```python
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
```

Buoc 3. search_similar_chunks trong BE:

- Vi tri: app/rag_pipeline.py:725
- Load index -> apply filter -> MMR + similarity + BM25 -> deduplicate -> rerank.

```python
mmr_docs = vector_store.max_marginal_relevance_search(
    query,
    k=max(top_k * 3, 10),
    fetch_k=fetch_k,
    lambda_mult=0.35,
    **filter_kwargs,
)
sim_docs = vector_store.similarity_search(query, k=fetch_k, **filter_kwargs)
bm25_docs = bm25_retriever.invoke(query)
unique_docs = _deduplicate_docs(candidates)
return _rerank_docs(query=query, docs=unique_docs, top_k=top_k)
```

### 2.3 Luong C: Q&A voi LLM

Buoc 1. User nhap qa_query trong tab QA.

Buoc 2. Main goi answer_question:

- Vi tri: app/main.py:729-730.

```python
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
```

Buoc 3. answer_question route nhanh:

- Vi tri: app/rag_pipeline.py:1861.

Trinh tu ben trong:

1. load_faiss_index + docstore.
2. rewrite query neu follow-up (\_rewrite_query_with_history).
3. detect unknown source / filter conflict.
4. \_multi_hop_retrieve lay docs.
5. Nhanh deterministic neu query match:
   - count bai tap: app/rag_pipeline.py:1967
   - content bai tap: app/rag_pipeline.py:2008
   - architecture style: app/rag_pipeline.py:2038
   - advisory nguoi moi: app/rag_pipeline.py:2072
   - advisory cong nghe: app/rag_pipeline.py:2085
6. Neu khong deterministic -> \_invoke_with_model (LLM) app/rag_pipeline.py:2105.
7. Neu loi ket noi/OOM -> fallback model app/rag_pipeline.py:2127.

---

## 3) Bang chia dung 20 chuc nang (10 cot loi + 10 phat trien)

Nguyen tac chia:

- Moi thanh vien 4 chuc nang.
- Moi muc co vi tri code + snippet neo.

## TV1 - Tuấn Tài (4 chuc nang)

Ghi chu: phan TV1 chi tiet (call-chain, tham so vao/ra, noi nhan gia tri tra ve) da tach rieng tai [docs/tv1-luong-ui-den-cuoi.md](docs/tv1-luong-ui-den-cuoi.md).

### [Cot loi #1] Upload va xu ly file

- Vi tri: app/rag_pipeline.py:90

```python
def save_uploaded_file(uploaded_file: Any, target_dir: Path = RAW_DIR) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / uploaded_file.name
    file_path.write_bytes(uploaded_file.getbuffer())
    return file_path
```

### [Cot loi #2] Chunking tai lieu

- Vi tri: app/rag_pipeline.py:127

```python
def ingest_document(
    file_path: str | Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> IngestResult:
    path_obj = Path(file_path)
    raw_docs = load_documents(path_obj)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(raw_docs)
    chunks = _enrich_chunks_metadata(chunks, path_obj)

    return IngestResult(...)
```

### [Phat trien #1] Ho tro DOCX

- Vi tri: app/document_loader.py:14

```python
def load_docx(path: str | Path) -> List[Document]:
    doc = DocxDocument(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    full_text = "\n".join(paragraphs).strip()

    if not full_text:
        return []

    return [
        Document(
            page_content=full_text,
            metadata={"source": str(path), "file_type": "docx"},
        )
    ]
```

### [Phat trien #3] Xoa du lieu tam (raw + index)

- Vi tri: app/rag_pipeline.py:222

```python
def clear_vector_store_data(index_root: Path = INDEX_DIR, raw_root: Path = RAW_DIR) -> dict[str, int]:
    index_deleted = 0
    raw_deleted = 0

    if index_root.exists():
        for item in index_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                index_deleted += 1

    if raw_root.exists():
        for item in raw_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                raw_deleted += 1

    return {"index_deleted": index_deleted, "raw_deleted": raw_deleted}
```

## TV2 (4 chuc nang)

### [Cot loi #3] Embedding da ngon ngu

- Vi tri: app/rag_pipeline.py:188

```python
return HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
```

### [Cot loi #4] FAISS store + search

- Vi tri: app/rag_pipeline.py:198 va app/rag_pipeline.py:312

```python
vector_store = FAISS.from_documents(chunks, embedder)
vector_store.save_local(str(index_dir))
```

### [Phat trien #4] Cai thien chunk strategy

- Vi tri: app/rag_pipeline.py:250

```python
def evaluate_chunk_strategies(
    file_paths: list[str | Path],
    query: str,
    strategies: list[tuple[int, int]],
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    evaluations: list[dict[str, Any]] = []
    if not file_paths:
        return evaluations
```

### [Phat trien #8] Multi-document metadata enrich

- Vi tri: app/rag_pipeline.py:108

```python
def _enrich_chunks_metadata(chunks: list[Document], file_path: Path) -> list[Document]:
    source = str(file_path)
    file_name = file_path.name
    file_type = _file_type_from_path(file_path)
    upload_time = _upload_time_from_path(file_path)
    upload_date = upload_time[:10]
```

## TV3 (4 chuc nang)

### [Cot loi #5] Document Q&A phan retrieval context

- Vi tri: app/rag_pipeline.py:1861, app/rag_pipeline.py:1927

```python
docs = _multi_hop_retrieve(
    index_dir=index_dir,
    query=retrieval_query,
    top_k=effective_top_k,
    source_filter=effective_filter,
    file_type_filter=file_type_filter,
    upload_date_filter=upload_date_filter,
)
sources = _format_sources(docs)
```

### [Cot loi #6] Tich hop LLM local qua Ollama

- Vi tri: app/rag_pipeline.py:2105

```python
def _invoke_with_model(active_model: str) -> tuple[str, int]:
    llm = OllamaLLM(model=active_model, base_url=OLLAMA_BASE_URL, temperature=0.2)
    raw_answer = str(llm.invoke(prompt)).strip()
```

### [Phat trien #7] Hybrid search

- Vi tri: app/rag_pipeline.py:725

```python
mmr_docs = vector_store.max_marginal_relevance_search(query, k=max(top_k * 3, 10), fetch_k=fetch_k, lambda_mult=0.35, **filter_kwargs)
sim_docs = vector_store.similarity_search(query, k=fetch_k, **filter_kwargs)
bm25_docs = bm25_retriever.invoke(query)
```

### [Phat trien #9] Re-ranking voi Cross-Encoder

- Vi tri: app/rag_pipeline.py:686

```python
cross_encoder = _get_cross_encoder()
scores = cross_encoder.predict(pairs)
```

## TV4 (4 chuc nang)

### [Cot loi #7] Prompt engineering + rang buoc

- Vi tri: app/rag_pipeline.py:1107

```python
if _detect_vietnamese(query) or not _is_probably_english_query(query):
    return (
        "Su dung ngu canh sau day de tra loi cau hoi.\n"
        "Neu khong du thong tin, hay noi ro la khong tim thay thong tin trong tai lieu.\n"
        "Tra loi ngan gon (3-4 cau) bang tieng Viet.\n"
    )
```

### [Cot loi #8] Nhan dien ngon ngu va phan hoi phu hop

- Vi tri: app/rag_pipeline.py:856 va app/rag_pipeline.py:862

```python
def _detect_vietnamese(text: str) -> bool:
    vietnamese_chars = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    text_lower = text.lower()
    return any(char in text_lower for char in vietnamese_chars)

def _is_probably_english_query(text: str) -> bool:
    normalized = _normalize_for_match(text)
    tokens = [token for token in normalized.split() if token]
    if not tokens:
        return False

    english_markers = {
        "what", "how", "why", "when", "where", "which", "who",
        "count", "many", "number", "list", "show", "chapter", "exercise",
    }
    marker_hits = sum(1 for token in tokens if token in english_markers)
    return marker_hits >= 1
```

### [Phat trien #6] Conversational RAG

- Vi tri: app/rag_pipeline.py:911 va app/rag_pipeline.py:953

```python
def _is_follow_up_query(query: str) -> bool:
    q = _normalize_for_match(query)
    if not q:
        return False

    standalone_markers = [
        "noi dung", "chi tiet", "de bai", "la gi", "bao nhieu", "liet ke",
        "danh sach", "bai tap", "exercise", "chapter", "chuong",
    ]
    if any(marker in q for marker in standalone_markers) and len(q.split()) >= 6:
        return False

    followup_prefixes = ("con ", "vay con", "the con", "tiep theo", "what about", "and ", "then ")
    if q.startswith(followup_prefixes):
        return True

    tokens = q.split()
    referential_tokens = {"no", "do", "vay", "it", "that", "this", "those", "them"}
    if len(tokens) <= 6 and any(token in referential_tokens for token in tokens):
        return True
    return False

def _rewrite_query_with_history(query, chat_history, model_name) -> tuple[str, bool]:
    is_deterministic_intent = bool(
        _is_exercise_content_query(query) or _is_exercise_count_query(query) or _is_architecture_style_count_query(query)
    )
    if is_deterministic_intent and not _is_follow_up_query(query):
        return query, False
    if not chat_history:
        return query, False
    history_context = _build_chat_history_context(chat_history)
    if not history_context:
        return query, False
    if not _is_follow_up_query(query):
        return query, False

    rewrite_prompt = (
        "Ban la bo phan viet lai truy van retrieval cho RAG.\n"
        "Viet lai cau hoi follow-up thanh mot cau hoi doc lap ro rang dua tren lich su hoi thoai.\n"
        "Khong duoc thay doi y dinh cau hoi.\n"
        f"Lich su hoi thoai:\n{history_context}\n\n"
        f"Follow-up hien tai: {query}\n\n"
        "Cau hoi viet lai:"
    )
    tried_models = [model_name, *FALLBACK_MODELS]
    for active_model in tried_models:
        llm = OllamaLLM(model=active_model, base_url=OLLAMA_BASE_URL, temperature=0.0)
        rewritten = str(llm.invoke(rewrite_prompt)).strip().splitlines()[0].strip()
        rewritten = rewritten.strip('"').strip("'").strip()
        if rewritten and len(rewritten) >= 5:
            return rewritten, rewritten.lower() != query.lower()
    return query, False
```

### [Phat trien #10] Advanced RAG / Self-RAG

- Vi tri: app/rag_pipeline.py:1066, app/rag_pipeline.py:1774, app/rag_pipeline.py:2127

```python
def _multi_hop_retrieve(index_dir, query, top_k, source_filter, file_type_filter, upload_date_filter):
    hop1_docs = search_similar_chunks(
        index_dir=index_dir,
        query=query,
        top_k=max(top_k, 3),
        source_filter=source_filter,
        file_type_filter=file_type_filter,
        upload_date_filter=upload_date_filter,
        use_rerank=False,
    )
    if not hop1_docs:
        return []

    hop2_queries = _build_second_hop_queries(query, hop1_docs)
    hop2_docs = []
    for hop_query in hop2_queries[:2]:
        retrieved = search_similar_chunks(
            index_dir=index_dir,
            query=hop_query,
            top_k=max(top_k, 3),
            source_filter=source_filter,
            file_type_filter=file_type_filter,
            upload_date_filter=upload_date_filter,
            use_rerank=False,
        )
        hop2_docs.extend(retrieved)
    combined = _deduplicate_docs(hop1_docs + hop2_docs)
    return _rerank_docs(query=query, docs=combined, top_k=top_k)

def _self_rag_confidence_score(llm, query, answer, docs):
    context_text = _build_context_for_scoring(docs)
    scoring_prompt = (
        "Ban la bo phan kiem chung chat luong RAG.\n"
        f"Cau hoi: {query}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Cau tra loi: {answer}\n\n"
        "Diem (1-10):"
    )
    score_raw = str(llm.invoke(scoring_prompt)).strip()
    matched = re.search(r"\\d+", score_raw)
    return 6 if not matched else max(1, min(10, int(matched.group())))

if _is_retryable_llm_error(error):
    for fallback_model in FALLBACK_MODELS:
        if fallback_model == model_name:
            continue
        try:
            fallback_answer_body, confidence = _invoke_with_model(fallback_model)
            return _build_result(
                answer_body=fallback_answer_body,
                sources=sources,
                mode="Conversational Multi-hop RAG + Self-RAG (Fallback)",
                model_used=fallback_model,
                confidence=f"{confidence}/10",
                is_fallback=True,
            )
        except Exception:
            continue
```

## TV5 (4 chuc nang)

### [Cot loi #9] UI Streamlit

- Vi tri: app/main.py:283

```python
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📄", layout="wide")
    _init_state()
    tab_upload, tab_retrieve, tab_qa, tab_history = st.tabs([
        "1. Upload & Index",
        "2. Retrieval Demo",
        "3. Q&A voi LLM",
        "4. Lich su & Ghi chu",
    ])
```

### [Cot loi #10] Error handling cho user

- Vi tri: app/main.py:178

```python
def _to_user_error_message(exc: Exception, stage: str) -> str:
    raw = str(exc).strip()
    text = raw.lower()

    if "unsupported file type" in text:
        return "Dinh dang file khong duoc ho tro. Vui long dung PDF hoac DOCX."
    if "ollama" in text or "connection refused" in text or "failed to connect" in text:
        return "Khong ket noi duoc Ollama. Hay kiem tra Ollama dang chay va model da san sang."

    stage_map = {"ingest": "xu ly tai lieu", "retrieve": "truy xuat du lieu", "qa": "hoi dap voi mo hinh"}
    stage_text = stage_map.get(stage, "xu ly yeu cau")
    return f"Da xay ra loi khi {stage_text}. Chi tiet: {raw or type(exc).__name__}"
```

### [Phat trien #2] Luu lich su hoi thoai

- Vi tri: app/main.py:60, app/main.py:69, app/main.py:139

```python
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

def _append_chat(question: str, answer: str, sources: list[dict]) -> None:
    chat_history = st.session_state.get("chat_history", [])
    chat_history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "question": question, "answer": answer, "sources": sources})
    st.session_state["chat_history"] = chat_history[:20]
    _save_persistent_history(st.session_state["chat_history"])
```

### [Phat trien #5] Citation / source tracking

- Vi tri: app/main.py:226

```python
def _render_sources(sources: list[dict], query: str) -> None:
    st.markdown("#### Citation / Source tracking")
    if not sources:
        st.info("Chua co nguon trich dan.")
        return
```

---

## 4) Vi du trace tham so (tu dau den dich)

### Vi du 1: Upload 2 file

Input UI:

- uploaded_files = [Chapter 3.docx, Sockets_Trong_Python.docx]
- chunk_size = 1000
- chunk_overlap = 150

Call chain:

1. app/main.py:461 -> ingest_multiple_uploaded_files(uploaded_files, 1000, 150)
2. app/rag_pipeline.py:163 -> loop tung file, goi ingest_document
3. app/rag_pipeline.py:127 -> load_documents + split_documents + \_enrich_chunks_metadata
4. app/main.py:467 -> build_and_save_faiss_index(chunks, source_name)
5. app/rag_pipeline.py:198 -> FAISS.from_documents + save_local

Output:

- st.session_state.last_index_dir co gia tri.
- available_sources / available_file_types / available_upload_dates duoc cap nhat.

### Vi du 2: Cau deterministic

Query:

- "Chuong RESTFUL API co bao nhieu bai tap?"

Call chain:

1. app/main.py:729 -> answer_question
2. app/rag_pipeline.py:1967 match \_is_exercise_count_query == True
3. app/rag_pipeline.py:1651 \_deterministic_exercise_map
4. app/rag_pipeline.py:1978 build answer deterministic + \_build_result

Output:

- mode = Deterministic Extraction
- model_used = rule-based

### Vi du 3: Cau LLM mo rong

Query:

- "Tom tat 3 y chinh cua Sockets_Trong_Python.docx"

Call chain:

1. app/main.py:729 -> answer_question
2. app/rag_pipeline.py:1927 -> \_multi_hop_retrieve
3. app/rag_pipeline.py:2097 -> \_build_prompt
4. app/rag_pipeline.py:2105 -> \_invoke_with_model(OLLAMA_MODEL)
5. app/rag_pipeline.py:1774 -> \_self_rag_confidence_score

Output:

- mode = Conversational Multi-hop RAG + Self-RAG
- confidence = x/10
- sources co citation de render tai app/main.py:226

---

## 5) Cach hoc de bi hoi code lai van lam duoc

- Moi thanh vien hoc 4 chuc nang cua minh theo mau:
  - Input la gi
  - Ham nao nhan input do
  - Ham nao goi tiep
  - Output va mode tra ve
- Moi nguoi thuoc them 1 chuc nang backup cua nguoi ben canh.
- Luc tap code lai, viet skeleton theo call chain truoc, sau do moi bo sung chi tiet.

Mau skeleton thao luan:

```python
# UI -> lay input
# main -> goi backend
# backend -> route deterministic/llm
# build result -> tra ve UI
```
