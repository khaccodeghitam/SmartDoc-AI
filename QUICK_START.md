# ⚡ QUICK START - TÓMS TẮT CHẠY & TEST (5 PHÚT)

## 🔧 SETUP (Chạy một lần)

```powershell
cd "C:\Users\nthon\Desktop\SmartDoc\SmartDoc-AI"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 🚀 CHẠY CHƯƠNG TRÌNH

**Terminal 1 (Ollama):**
```powershell
ollama serve
```

**Terminal 2 (App):**
```powershell
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py
# Truy cập: http://localhost:8501
```

---

## ✅ TEST CHECKLIST (Thứ tự chạy)

### **1️⃣ Upload & Index (Tab 1)**
- [ ] Chọn 1-2 file PDF/DOCX
- [ ] Bấm "Ingest và tạo FAISS index"
- [ ] Kiểm tra: ✅ Đã tạo X docs, Y chunks

### **2️⃣ Retrieval Demo (Tab 2)**
- [ ] Nhập query: "Tài liệu này nói về gì?"
- [ ] Bấm "Tìm chunks liên quan"
- [ ] Xem 3 tabs kết quả (Hybrid, Bi-encoder, Vector-only)

### **3️⃣ RAG Only Mode (Tab 3 - TẮT Co-RAG)**
- [ ] Tắt toggle "Co-RAG"
- [ ] Nhập câu hỏi: "Tóm tắt 3 điểm chính"
- [ ] Bấm "Hỏi nhanh với RAG"
- [ ] Kiểm tra:
  - [ ] Câu trả lời hiển thị
  - [ ] **✨ NEW: Citation/Source Tracking** (expandable)
  - [ ] Xem "Xem ngữ cảnh gốc + highlight"
  - [ ] Tự động lưu

### **4️⃣ Co-RAG Advanced (Tab 3 - BẬT Co-RAG)**
- [ ] Bật toggle "Co-RAG"
- [ ] Nhập câu hỏi phức tạp
- [ ] Bấm "Tranh luận / So sánh AI"
- [ ] Chờ xử lý: 2 cột (RAG + Co-RAG)
- [ ] Kiểm tra:
  - [ ] RAG answer với sources
  - [ ] **✨ NEW: Per-iteration sources** trong Co-RAG
  - [ ] Expand mỗi vòng xem sources + highlight
  - [ ] Chọn 1 câu trả lời để lưu

### **5️⃣ Persistent History (Sidebar)**
- [ ] Kiểm tra lịch sử chat trong sidebar
- [ ] **Bấm F5** để refresh page
- [ ] **✨ NEW: Kiểm tra**: Lịch sử vẫn còn? ✅ YES
- [ ] Bấm "➕ Cuộc trò chuyện mới"
- [ ] Kiểm tra: Chat reset, session mới được tạo

### **6️⃣ Cleanup**
- [ ] Sidebar: Bấm "Clear History"
- [ ] Confirm xóa
- [ ] Kiểm tra: Lịch sử gone

---

## 📊 KẾT QUẢ TEST

Tất cả nên ✅:
```
✅ Upload & Index
✅ Hybrid Search (3 methods)
✅ RAG generation
✅ Citation/Source Tracking (NEW)
✅ Co-RAG multi-round
✅ Per-iteration sources (NEW)
✅ Chat History Auto-save (NEW)
✅ Persistent History F5 survive (NEW)
✅ Multiple Sessions
✅ Clear History
```

---

## 🎯 TÍNH NĂNG MỚI (TV5)

### 1. Citation / Source Tracking
- Xem sources trong expandable cards
- Highlight keyword trong context
- View metadata (file, page, upload date)
- **Cả RAG lẫn Co-RAG**

### 2. Persistent Chat History  
- Auto-save sau mỗi câu trả lời
- Survive page refresh (F5)
- **File: `data/chat_history/history.json`**

### 3. Per-Iteration Sources
- Co-RAG iterations hiển thị sources riêng
- Citation tracking cho từng vòng
- Sub-query specific highlight

---

## 🐛 Nếu Có Vấn Đề

| Vấn đề | Giải pháp |
|--------|----------|
| Ollama not found | `ollama serve` ở terminal khác |
| Port 8501 occupied | Streamlit tự dùng 8502, 8503, ... |
| No FAISS index | Bấm "Clear Vector Store" → Upload lại |
| History không save | Check `data/chat_history/history.json` |

---

## 📁 File Quan Trọng

- `src/presentation/streamlit_app.py` - Main app (chứa UI + helpers mới)
- `src/data_layer/conversation_store.py` - Chat history persistence
- `data/chat_history/history.json` - Persistent data
- `data/index/` - FAISS indexes
- `data/raw/` - Uploaded files

---

**Chúc bạn test thành công! 🎉**
