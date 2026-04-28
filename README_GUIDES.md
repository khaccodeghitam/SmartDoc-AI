# 📚 TÓM TẮT - CÁC FILE HƯỚNG DẪN

Dự án SmartDoc AI có 3 file hướng dẫn chi tiết:

## 1️⃣ **QUICK_START.md** ⚡ (5 PHÚT - NHANH NHẤT)

**Sử dụng khi**: Bạn muốn chạy nhanh và test cơ bản

**Nội dung**:
- 🔧 Setup command (1 lần)
- 🚀 Chạy app (2 terminal)
- ✅ Test checklist (6 test cơ bản)
- 🎯 Tính năng mới TV5 highlight

**Thời gian**: ~5 phút

---

## 2️⃣ **HUONG_DAN_CHAY_VA_TEST.md** 📋 (30 PHÚT - ĐẦY ĐỦ)

**Sử dụng khi**: Bạn muốn hiểu chi tiết mỗi bước

**Nội dung**:
- 📁 Chuẩn bị ban đầu (Setup, Ollama, Dependencies)
- 🎯 Chạy chương trình
- 📁 Test Upload & Index (TV1 + TV2)
- 🔍 Test Retrieval (Hybrid Search)
- 💬 Test RAG (TV3 + TV5 NEW)
- 🧠 Test Co-RAG (TV4 + TV5 NEW)
- 💾 Test Persistent History (TV5 NEW)
- 🧪 Troubleshooting

**Thời gian**: ~30 phút (trực tiếp + test)

---

## 3️⃣ **TEST_CASES.md** 🧪 (CHI TIẾT TỪNG TEST)

**Sử dụng khi**: Bạn muốn test chuyên nghiệp với test cases cụ thể

**Nội dung** (10 test cases):
- TC1: Upload & Index
- TC2: Upload Multiple Files
- TC3: Hybrid Search (3 methods)
- TC4: RAG Mode + Citation
- TC5: Co-RAG Mode + Per-iteration Sources
- TC6: Persistent History
- TC7: Multiple Sessions
- TC8: Clear History
- TC9: Chunk Benchmark
- TC10: Error Handling

**Mỗi test case có**:
- Mục tiêu rõ ràng
- Điều kiện tiên quyết
- Các bước chi tiết
- Kết quả mong đợi
- Checklist ✓

**Thời gian**: ~1 giờ (full test suite)

---

## 🎯 CÁCH CHỌN FILE DỰA VÀO NHU CẦU

| Nhu cầu | File | Thời gian |
|--------|------|----------|
| Muốn test nhanh, chỉ cơ bản | QUICK_START.md | 5 phút |
| Muốn hiểu luồng từ A-Z | HUONG_DAN_CHAY_VA_TEST.md | 30 phút |
| Muốn test chuyên nghiệp, full | TEST_CASES.md | 1 giờ |
| Muốn làm tất cả | Tất cả 3 files | 1.5 giờ |

---

## 📍 VỊ TRÍ FILE

```
SmartDoc-AI/
├── QUICK_START.md                    ← File 1 (5 phút)
├── HUONG_DAN_CHAY_VA_TEST.md        ← File 2 (30 phút)  
├── TEST_CASES.md                    ← File 3 (1 giờ)
├── app.py                           ← Main entry
├── requirements.txt
├── documentation/
├── src/
│   ├── presentation/streamlit_app.py (có tính năng TV5 mới)
│   └── data_layer/conversation_store.py (persistent history)
└── data/
    ├── chat_history/history.json    ← Persistent data
    ├── raw/                         ← Uploaded files
    └── index/                       ← FAISS indexes
```

---

## 🚀 MỚI LẦN ĐẦU? LÀM THEO ĐÂY:

```
1️⃣ Đọc QUICK_START.md
   ↓
2️⃣ Chạy lệnh setup & app
   ↓
3️⃣ Test các checkpoint cơ bản (5 phút)
   ↓
4️⃣ Nếu muốn chi tiết → Đọc HUONG_DAN_CHAY_VA_TEST.md
   ↓
5️⃣ Nếu muốn test kỹ lưỡng → Chạy TEST_CASES.md
```

---

## ✨ TÍNH NĂNG MỚI TV5 (HIGHLIGHT)

### 1. Citation / Source Tracking
- **File**: `src/presentation/streamlit_app.py`
- **Helper**: `_render_sources()`, `_convert_raw_docs_to_sources()`
- **Cách test**: QUICK_START.md bước 3.3

### 2. Persistent Chat History
- **File**: `src/data_layer/conversation_store.py`
- **Helper**: `save_persistent_history()` (gọi tự động)
- **Cách test**: QUICK_START.md bước 5.5

### 3. Per-Iteration Sources (Co-RAG)
- **File**: `src/presentation/streamlit_app.py`
- **Helper**: `_create_simple_sources_from_chunks()`
- **Cách test**: HUONG_DAN_CHAY_VA_TEST.md phần Co-RAG

---

## 📞 CÓ LỖI GỌI ĐẠO?

**Troubleshooting:**
- Ollama: HUONG_DAN_CHAY_VA_TEST.md → Phần 10
- FAISS: TEST_CASES.md → TC10
- Port 8501: QUICK_START.md → Mục 🐛

---

## 🎓 KỲ VỌNG SAU KHI TEST

✅ Bạn sẽ:
- Biết cách chạy app
- Test tất cả 10 chức năng
- Thấy citations hoạt động
- Verify history được lưu
- Hiểu flow: Upload → Search → RAG → Save

✅ App sẽ:
- Upload & chunk documents
- Search hybrid + rerank
- Generate RAG answers
- Display sources beautifully
- Save history persistent

---

## 📊 PROGRESS TRACKING

Sử dụng TEST_CASES.md bảng Summary:

```
[ ] Test 1: Upload & Index
[ ] Test 2: Multiple Files
[ ] Test 3: Hybrid Search
[ ] Test 4: RAG + Citation ✨ NEW
[ ] Test 5: Co-RAG + Sources ✨ NEW
[ ] Test 6: History Persist ✨ NEW
[ ] Test 7: Sessions
[ ] Test 8: Clear
[ ] Test 9: Benchmark
[ ] Test 10: Error Handling

✅ All pass → Ready!
```

---

**Chọn file phù hợp và bắt đầu! 🚀**
