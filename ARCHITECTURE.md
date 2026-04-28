# 🏗️ CẤU TRÚC CHƯƠNG TRÌNH - TÓMS TẮT

## 📊 LUỒNG XỬ LÝ TỔNG QUÁT

```
BROWSER (UI)
    ↓
streamlit_app.py (Presentation Layer)
    ├─ Upload & Index (TV1+TV2)
    ├─ Retrieval Demo (TV2+TV3)
    └─ Q&A (TV3+TV4+TV5)
    ↓
document_processing_pipeline.py (Application Layer)
    ├─ ingest_multiple_uploaded_files()
    └─ evaluate_chunk_strategies()
    ↓
pdf_document_storage.py (Data Layer)
    ├─ save_uploaded_file()
    ├─ load_documents()
    └─ enrich_chunks_metadata()
    ↓
faiss_vector_store.py (Data Layer)
    ├─ build_and_save_faiss_index()
    ├─ search_similar_chunks()
    └─ rerank_docs()
    ↓
multilingual_mpnet_embeddings.py (Data Layer)
    └─ build_embedder()
    ↓
rag_chain_manager.py (Application Layer)
    └─ ask()  → RAGAnswer
    ↓
ollama_inference_engine.py (Model Layer)
    └─ generate()  → LLM Response
    ↓
RESPONSE → Browser (Display + Save)
```

---

## 🗂️ CẤU TRÚC THƯ MỤC

```
SmartDoc-AI/
│
├── app.py                                    ← ENTRY POINT
│
├── src/
│   ├── __init__.py
│   ├── config.py                             ← Configuration
│   ├── utils.py                              ← Utilities
│   │
│   ├── presentation/                         ← UI LAYER
│   │   ├── streamlit_app.py                 ← MAIN UI (TV5 functions)
│   │   │   ├─ _convert_raw_docs_to_sources() [NEW]
│   │   │   ├─ _create_simple_sources_from_chunks() [NEW]
│   │   │   ├─ _render_sources() [INTEGRATED]
│   │   │   └─ _append_chat() [ENHANCED with save_persistent_history]
│   │   └── ui_config.py                      ← UI Styling
│   │
│   ├── application/                          ← APPLICATION LAYER
│   │   ├── document_processing_pipeline.py   ← Ingest logic (TV1+TV2)
│   │   ├── prompt_engineering.py             ← Prompts (TV4)
│   │   ├── query_rewriter.py                 ← Query enhancement
│   │   ├── rag_chain_manager.py              ← RAG orchestration (TV3)
│   │   └── corag_chain_manager.py            ← Co-RAG orchestration (TV4)
│   │
│   ├── data_layer/                           ← DATA LAYER
│   │   ├── conversation_store.py             ← Chat history [NEW TV5]
│   │   │   ├─ save_persistent_history() [AUTO-CALLED]
│   │   │   ├─ load_persistent_history()
│   │   │   ├─ save_app_session()
│   │   │   └─ load_app_session()
│   │   ├── faiss_vector_store.py             ← Vector DB (TV2)
│   │   ├── pdf_document_storage.py           ← File handling (TV1)
│   │   └── multilingual_mpnet_embeddings.py  ← Embedding (TV2)
│   │
│   └── model_layer/                          ← MODEL LAYER
│       └── ollama_inference_engine.py        ← LLM integration (TV3)
│
├── data/
│   ├── raw/                                  ← Uploaded files
│   ├── index/                                ← FAISS indexes
│   └── chat_history/
│       ├── history.json                      ← Persistent chat [NEW]
│       └── app_session.json                  ← Session state
│
├── documentation/                            ← Project docs
│   ├── phan-cong-5-thanh-vien-code-map.md
│   └── ...
│
├── requirements.txt
├── README.md
├── QUICK_START.md                            ← [HƯỚNG DẪN 1]
├── HUONG_DAN_CHAY_VA_TEST.md                ← [HƯỚNG DẪN 2]
├── TEST_CASES.md                             ← [HƯỚNG DẪN 3]
└── README_GUIDES.md                          ← [HƯỚNG DẪN 4]
```

---

## 👥 PHÂN CÔNG (20 CHỨC NĂNG - 5 TV)

### **TV1: Tuấn Tài** (Upload & Chunking)
- `pdf_document_storage.py::save_uploaded_file()`
- `pdf_document_storage.py::load_documents()`
- `document_processing_pipeline.py::ingest_document()`

### **TV2: Huyền** (Embedding & Vector DB)
- `multilingual_mpnet_embeddings.py::build_embedder()`
- `faiss_vector_store.py::build_and_save_faiss_index()`
- `faiss_vector_store.py::load_faiss_index()`

### **TV3: Thịnh** (RAG & LLM)
- `rag_chain_manager.py::RAGChainManager.ask()`
- `ollama_inference_engine.py::OllamaInferenceEngine.generate()`
- `faiss_vector_store.py::search_similar_chunks()`

### **TV4: Cường** (Prompt & Co-RAG)
- `prompt_engineering.py::build_rag_prompt()`
- `prompt_engineering.py::detect_vietnamese()`
- `corag_chain_manager.py::CoRAGChainManager`

### **TV5: Nhi** ✨ (UI & Persistence - TÍNH NĂNG MỚI)
- `streamlit_app.py::_render_sources()` [INTEGRATED]
- `streamlit_app.py::_convert_raw_docs_to_sources()` [NEW]
- `streamlit_app.py::_create_simple_sources_from_chunks()` [NEW]
- `conversation_store.py::save_persistent_history()` [AUTO-CALLED]
- `conversation_store.py::load_persistent_history()`

---

## 🔄 FLOW CHI TIẾT - UPLOAD & INDEX

```
1. User bấm "Ingest và tạo FAISS index"
   ↓
2. streamlit_app.py::main()
   ↓
3. ingest_multiple_uploaded_files()
   ├─ Với mỗi file:
   │   ├─ save_uploaded_file(file)
   │   ├─ load_documents(file_path)
   │   │   └─ load_pdf() / load_docx()
   │   ├─ ingest_document(docs)
   │   │   └─ RecursiveCharacterTextSplitter.split_documents()
   │   └─ enrich_chunks_metadata(chunks)
   ↓
4. build_and_save_faiss_index(chunks)
   ├─ build_embedder() [multilingual-mpnet]
   ├─ embed chunks
   ├─ build FAISS index
   └─ save to data/index/
   ↓
5. Update UI state
   ├─ st.session_state["last_index_dir"]
   ├─ st.session_state["available_sources"]
   └─ save_app_session() → data/chat_history/app_session.json
```

---

## 🔄 FLOW CHI TIẾT - Q&A (HYBRID RAG)

```
1. User nhập query + bấm "Hỏi nhanh với RAG"
   ↓
2. rewrite_query_with_history(query, chat_history)
   └─ Normalize query dựa vào history
   ↓
3. RAGChainManager.ask(question, retrieval_query=rewritten_query)
   ├─ search_similar_chunks(index, rewritten_query, top_k=4)
   │   ├─ Hybrid: Vector + BM25
   │   ├─ MMR reranking
   │   └─ CrossEncoder rerank [if enabled]
   ├─ _format_context_chunks(retrieved_docs)
   │   └─ Format: "[File: name | Page: X]\nContent"
   ├─ build_rag_prompt(context, question)
   ├─ model_engine.generate(prompt)
   │   └─ Call Ollama LLM
   └─ RAGAnswer {answer, context_chunks, raw_docs, confidence}
   ↓
4. ✨ [NEW] Convert to sources
   ├─ _convert_raw_docs_to_sources(raw_docs)
   └─ Create source dict {id, source, file_name, page, excerpt, context}
   ↓
5. Display in UI
   ├─ Show answer
   ├─ ✨ [NEW] _render_sources(sources, query)
   │   └─ Expander + highlight per source
   └─ Confidence score
   ↓
6. ✨ [NEW] Auto-save to history
   ├─ _append_chat(question, answer, sources)
   │   ├─ Add to st.session_state["chat_history"]
   │   └─ save_persistent_history(sessions)
   │       └─ Write to data/chat_history/history.json
```

---

## 🔄 FLOW CHI TIẾT - Co-RAG ADVANCED

```
1. User bấm "Tranh luận / So sánh AI" (Co-RAG ON)
   ↓
2. Parallel: RAG + Co-RAG
   ├─ RAG (thread 1):
   │   └─ Same as Q&A flow above
   │
   └─ Co-RAG (thread 2):
       ├─ VÒng 1:
       │   ├─ search_similar_chunks(query)
       │   ├─ build_corag_sufficiency_check_prompt()
       │   ├─ model.generate() → "SUFFICIENT" / "INSUFFICIENT"
       │   └─ If INSUFFICIENT: Create sub_query
       │
       ├─ Vòng 2 (nếu sub_query):
       │   ├─ search_similar_chunks(sub_query)
       │   ├─ Sufficiency check lại
       │   └─ ...
       │
       ├─ Vòng 3 (cuối):
       │   ├─ build_corag_final_prompt()
       │   └─ model.generate() → Final answer
       │
       └─ CoRAGAnswer {
           answer,
           context_chunks,
           iterations: [
               CoRAGIteration {
                   round_num,
                   sub_query,
                   retrieved_chunks,
                   llm_assessment,
                   ✨ [NEW] sources
               }
           ]
       }
   ↓
3. ✨ [NEW] Create per-iteration sources
   ├─ Cho mỗi iteration:
   │   └─ _create_simple_sources_from_chunks(chunks)
   │       └─ Create source dict từ formatted chunks
   │
4. Display in UI
   ├─ Compare 2 columns: RAG vs Co-RAG
   ├─ RAG: _render_sources(rag_sources)
   └─ Co-RAG:
       └─ Mỗi iteration:
           └─ _render_sources(iteration_sources)
              └─ Citation tracking per round
   ↓
5. User chọn 1 trong 2 answers
   ├─ _save_selected_answer_from_pending("rag" / "corag")
   └─ _append_chat(question, answer, sources)
       └─ ✨ [NEW] save_persistent_history()
```

---

## 💾 DATA STRUCTURE - PERSISTENT HISTORY

**File: `data/chat_history/history.json`**

```json
[
  {
    "session_id": "uuid-123",
    "title": "Cuộc trò chuyện 1",
    "timestamp": "28/04/2026 - 10:30",
    "history": [
      {
        "turn_id": "uuid-abc",
        "time": "10:30:45",
        "question": "Tài liệu này nói gì?",
        "answer": "Tài liệu này...",
        "sources": [
          {
            "id": "S1",
            "source": "data/raw/file.pdf",
            "file_name": "file.pdf",
            "page": 1,
            "file_type": "pdf",
            "upload_date": "28/04/2026",
            "excerpt": "...",
            "context": "..."
          }
        ],
        "answer_confidence": 8,
        "selected_source": "rag"
      }
    ]
  }
]
```

---

## 📍 KEY FUNCTIONS MODIFIED (TV5)

### 1. **`_append_chat()`** - ENHANCED
```python
# Before: sources=[]
# After: sources=[...sources...]
# Auto-call: save_persistent_history(st.session_state["chat_sessions"])
```

### 2. **`_convert_raw_docs_to_sources()`** - NEW
```python
# Convert langchain Document → sources dict
# Used for RAG answer
```

### 3. **`_create_simple_sources_from_chunks()`** - NEW
```python
# Convert formatted chunks → sources dict
# Used for Co-RAG iterations
```

### 4. **`_render_sources()`** - INTEGRATED
```python
# Display sources with citation tracking
# Called in RAG + Co-RAG display sections
```

### 5. **`save_persistent_history()`** - AUTO-CALLED
```python
# Auto-call in _append_chat()
# No manual intervention needed
```

---

## 🔗 DEPENDENCIES GRAPH

```
streamlit_app.py
├─ presentation layer UI
├─ calls: document_processing_pipeline.py (ingest)
├─ calls: faiss_vector_store.py (search, build index)
├─ calls: rag_chain_manager.py (RAG generation)
├─ calls: corag_chain_manager.py (Co-RAG generation)
├─ calls: conversation_store.py (save/load history) [NEW]
└─ calls: ollama_inference_engine.py (LLM)

conversation_store.py [NEW]
├─ imports: pathlib, json, uuid, datetime
├─ uses: CHAT_HISTORY_DIR = data/chat_history/
└─ functions:
    ├─ save_persistent_history()
    ├─ load_persistent_history()
    ├─ save_app_session()
    └─ load_app_session()
```

---

## 📦 EXTERNAL LIBRARIES

```
streamlit              ← UI Framework
langchain              ← LLM chains
langchain-community    ← LLM integrations
faiss-cpu              ← Vector DB
sentence-transformers  ← Embeddings
pdfplumber             ← PDF parsing
python-docx            ← DOCX parsing
rank-bm25              ← BM25 ranking
ollama                 ← LLM inference
```

---

## 🧪 TEST STRATEGY

```
Unit Test:
├─ _convert_raw_docs_to_sources()
├─ _create_simple_sources_from_chunks()
├─ save_persistent_history()
└─ load_persistent_history()

Integration Test:
├─ Upload → FAISS → Search → RAG
├─ RAG → Sources → Render → Display
├─ RAG → Save → History → F5 Persist
└─ Co-RAG → Per-iteration sources → Display

End-to-End Test:
└─ Full workflow (seen in TEST_CASES.md)
```

---

**Architecture is modular, maintainable, and TV5-integrated! ✨**
