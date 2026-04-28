# 📋 HƯỚNG DẪN CHẠY VÀ TEST SmartDoc AI - ĐẦY ĐỦ

> **Cập nhật tính năng TV5:** Citation/Source Tracking + Persistent Chat History

---

## 🚀 PHẦN 1: CHUẨN BỊ BAN ĐẦU

### **Bước 1.1: Mở Terminal PowerShell**
```powershell
# Mở PowerShell và điều hướng đến thư mục project
cd "C:\Users\nthon\Desktop\SmartDoc\SmartDoc-AI"
```

### **Bước 1.2: Kích hoạt Virtual Environment**
```powershell
# Chạy lệnh kích hoạt venv
.\.venv\Scripts\Activate.ps1

# Bạn sẽ thấy tiền tố (.venv) xuất hiện trước dòng lệnh
# (.venv) PS C:\Users\nthon\Desktop\SmartDoc\SmartDoc-AI>
```

**Nếu gặp lỗi "không được phép chạy script":**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### **Bước 1.3: Kiểm tra & Cài Dependencies**
```powershell
# Kiểm tra pip
pip --version

# Cài đặt requirements nếu chưa cài
pip install -r requirements.txt
```

### **Bước 1.4: Kiểm tra Ollama**
```powershell
# Kiểm tra version Ollama
ollama --version

# Nếu chưa cài: https://ollama.com/download/windows

# Tải model
ollama pull qwen2.5:7b

# Nếu đã tải rồi, khởi động Ollama daemon (nếu chưa chạy)
ollama serve
```

> ⚠️ **QUAN TRỌNG**: Ollama phải đang chạy (background) khi bạn test Q&A!  
> Khuyến cáo: Mở tab Terminal khác chạy `ollama serve`

---

## 🎯 PHẦN 2: CHẠY CHƯƠNG TRÌNH

### **Bước 2.1: Khởi động Streamlit App**
```powershell
# Chắc chắn bạn đã kích hoạt venv (.venv)
# Rồi chạy lệnh:
python -m streamlit run app.py
```

**Output kỳ vọng:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### **Bước 2.2: Mở Trình Duyệt**
- Bấm Ctrl+Click trên link `http://localhost:8501` hoặc
- Copy & Paste vào trình duyệt
- Bạn sẽ thấy giao diện SmartDoc AI

---

## 📁 PHẦN 3: TEST CHỨC NĂNG UPLOAD & INDEX (TV1 + TV2)

### **Bước 3.1: Chuẩn Bị Tài Liệu Test**

Tạo file tài liệu để test (nên dùng PDF hoặc DOCX có nội dung):
- Có thể dùng file trong `documentation/` folder
- Hoặc tạo file test đơn giản

**Ví dụ sử dụng file hiện có:**
```
documentation/Ôn thi lịch sử đảng.txt  → Rename thành .pdf hoặc .docx
```

### **Bước 3.2: Upload File**

1. **Vào tab "Upload & Index"**
   - Bên trái: "Nạp tài liệu"
   - Bên phải: "So sánh chunk strategy"

2. **Bấm nút chọn file** (trong sidebar, phần "⚙️ Cấu hình hệ thống & Index")
   - Chọn 1-3 file PDF/DOCX
   - Hỗ trợ: PDF, DOCX

3. **Điều chỉnh cấu hình (tuỳ chọn)**
   - **Chunk size**: 1000 (mặc định)
   - **Chunk overlap**: 150 (mặc định)
   - **Top-k search**: 4 (mặc định)

4. **Bấm "Ingest và tạo FAISS index"**

**Kết quả kỳ vọng:**
```
✅ Đã tạo mới XXX docs, YYY chunks, index On_thi_lich_su_ang
```

> **Test Checkpoint 1**: File được upload thành công ✓

---

## 🔍 PHẦN 4: TEST RETRIEVAL (HYBRID SEARCH)

### **Bước 4.1: Vào Tab "Retrieval Demo"**

1. Bạn sẽ thấy form:
   - **Nhập câu hỏi để test retrieval**
   - **Filter**: Tài liệu, loại file, ngày upload
   - **Nút**: "Tìm chunks liên quan"

### **Bước 4.2: Nhập Query & Search**

**Ví dụ query (tuỳ nội dung file):**
```
- "Tài liệu này nói gì về X?"
- "Có bao nhiêu chương trong file này?"
- "Danh sách những vấn đề chính là gì?"
```

1. Nhập query vào text area
2. Bấm **"Tìm chunks liên quan"**

### **Bước 4.3: So Sánh 3 Phương Pháp Search**

Bạn sẽ thấy **3 tabs**:
- **Hybrid + CrossEncoder**: MMR + BM25 + Rerank
- **Hybrid Bi-encoder**: MMR + BM25 (không rerank)
- **Vector-only Baseline**: Chỉ vector similarity

**Mỗi tab hiển thị:**
- Số chunks trả về
- Chunk ID, source, relevance score

> **Test Checkpoint 2**: 3 retrieval methods hoạt động ✓

---

## 💬 PHẦN 5: TEST Q&A (RAG + Co-RAG) - TÍNH NĂNG MỚI TV5

### **Bước 5.1: Vào Tab "Q&A với LLM"**

1. Bạn sẽ thấy:
   - Toggle: "Bật suy nghĩ thông minh Co-RAG" (mặc định ON)
   - Text area: Nhập câu hỏi
   - Nút: "Tranh luận / So sánh AI" (khi Co-RAG ON)
   - Nút: "Hỏi nhanh với RAG" (khi Co-RAG OFF)

### **Bước 5.2: TEST MODE 1 - RAG ONLY (Tắt Co-RAG)**

1. **Tắt toggle "Co-RAG"**
   - Status sẽ show: "TẮT Co-RAG (chỉ chạy và trả RAG)"

2. **Nhập câu hỏi**
   ```
   Ví dụ: "Tóm tắt 3 điểm chính trong tài liệu này"
   ```

3. **Bấm "Hỏi nhanh với RAG"**

4. **Chờ xử lý** (sẽ thấy progress)
   ```
   🔄 Đang phân tích câu hỏi và lịch sử hội thoại...
   🔄 Đang khởi tạo pipeline RAG...
   ✅ Hoàn tất chế độ chỉ RAG
   ```

### **Bước 5.3: Kiểm Tra Output RAG**

**✨ TÍNH NĂNG MỚI - CITATION/SOURCE TRACKING:**

Dưới "🤖 Basic RAG":
- Câu trả lời được hiển thị
- **Độ tự tin**: X/10

**Phía dưới là "#### Citation / Source tracking":**
```
[S1] | Ôn thi lịch sử đảng.pdf | page: 1
[S2] | Ôn thi lịch sử đảng.pdf | page: 5
```

**Bấm vào Expander để xem:**
- ✅ ID nguồn
- ✅ Tên file
- ✅ Đường dẫn
- ✅ Loại file
- ✅ Ngày upload
- ✅ Excerpt (500 ký tự đầu)
- ✅ **Nút "Xem ngữ cảnh gốc + highlight"**

**Bấm nút highlight:**
- Ngữ cảnh đầy đủ hiển thị với từ khóa được highlight bằng tag `<mark>`
- Dễ dàng tìm chỗ hệ thống trích dẫn

> **Test Checkpoint 3**: Citation/Source Tracking hoạt động ✓

### **Bước 5.4: Lưu Câu Trả Lời**

Trong mode RAG only:
- Sau khi RAG done, câu trả lời sẽ **tự động lưu**
- Status: "Đã lưu câu trả lời RAG."

> **Test Checkpoint 4**: Automatic save RAG answer ✓

---

## 🧠 PHẦN 6: TEST Co-RAG ADVANCED MODE

### **Bước 6.1: Bật Co-RAG**

1. **Bật toggle "Co-RAG"**
   - Status: "BẬT Co-RAG (trả cả RAG và Co-RAG)"

2. **Nhập câu hỏi phức tạp** (yêu cầu suy luận đa bước)
   ```
   Ví dụ: "Phân tích sự liên hệ giữa các yếu tố X, Y, Z trong tài liệu?"
   ```

3. **Bấm "Tranh luận / So sánh AI"**

### **Bước 6.2: Chờ Xử Lý Co-RAG**

Bạn sẽ thấy **2 cột song song:**

**Cột trái - 🤖 Basic RAG:**
- Độc lập trích xuất 1 lần
- Sinh 1 câu trả lời

**Cột phải - 🧠 Co-RAG:**
- Trải qua nhiều vòng (≤3 vòng)
- Mỗi vòng:
  1. Đánh giá context có đủ?
  2. Nếu không → sinh sub-query
  3. Trích xuất thêm
  4. Lặp lại

**Progress:**
```
🔄 Co-RAG: Vòng 1/3 - Đánh giá sufficiency...
🔄 Co-RAG: Vòng 1/3 - Sub-query: "Yếu tố X là gì?"
🔄 Co-RAG: Vòng 2/3 - Đánh giá sufficiency...
✅ Co-RAG đã hoàn tất (Trải qua 2 vòng)
```

### **Bước 6.3: Xem Chi Tiết Co-RAG**

**Cột 🧠 Co-RAG:**
- Câu trả lời cuối cùng
- **Độ tự tin**: Y/10
- **Số vòng**: Trải qua 2 vòng

**Expand mỗi vòng:**
```
### Vòng 1 | Đánh giá & Sub-query
- Ý kiến LLM: "SUFFICIENT" / "Cần thêm context"
- Sub-query tạo ra: "Yếu tố X có ảnh hưởng thế nào?"
- Số lượng đoạn trích: 4 chunks
```

**✨ TÍNH NĂNG MỚI - CITATION PER ITERATION:**

Trong mỗi vòng, bấm expand "Ngữ cảnh đã dùng ở vòng này":
- Xem **sources từng vòng** với citation tracking
- Highlight keyword theo sub-query của vòng đó
- Theo dõi tính logic của Co-RAG

> **Test Checkpoint 5**: Co-RAG multi-round ✓
> **Test Checkpoint 6**: Per-iteration sources ✓

### **Bước 6.4: Chọn & Lưu Câu Trả Lời**

Khi cả RAG và Co-RAG hoàn tất:

**Nút trái:** "Lưu đoạn RAG này"
**Nút phải:** "Lưu đoạn Co-RAG này"

1. Chọn 1 trong 2 câu trả lời
2. Bấm nút tương ứng
3. Kết quả sẽ được **lưu vào lịch sử chat**

> **Test Checkpoint 7**: Save RAG vs Co-RAG selection ✓

---

## 💾 PHẦN 7: TEST PERSISTENT CHAT HISTORY (TÍNH NĂNG MỚI TV5)

### **Bước 7.1: Kiểm Tra Chat History Được Lưu**

**Trong sidebar:**
- Xem "### Lịch sử cuộc trò chuyện"
- Bạn sẽ thấy những Q&A vừa lưu

### **Bước 7.2: TEST Refresh (F5)**

1. **Bấm F5 để refresh page**
2. **Kiểm tra:**
   - Lịch sử chat vẫn còn?
   - ✅ Có = Persistent ✓
   - ❌ Không = Bug

> **Test Checkpoint 8**: Persistent history survive F5 ✓

### **Bước 7.3: Tạo Cuộc Trò Chuyện Mới**

Trong sidebar:
1. Bấm **"➕ Cuộc trò chuyện mới"**
2. Chat history sẽ reset
3. Có thể quay lại cuộc trò chuyện cũ

> **Test Checkpoint 9**: Multiple sessions work ✓

### **Bước 7.4: Xóa Lịch Sử**

Sidebar button:
1. Bấm **"Clear History"**
2. Confirm xóa
3. Lịch sử được xóa (kiểm tra file `data/chat_history/history.json`)

> **Test Checkpoint 10**: Clear history ✓

---

## 📊 PHẦN 8: TEST RETRIEVAL DEMO (HYBRID SEARCH)

### **Bước 8.1: So Sánh Chunk Strategy**

Trong tab "Upload & Index", phía **bên phải**:

1. Nhập **"Câu truy vấn để benchmark"**
2. Bấm **"So sánh 3 cấu hình chunk"**
3. Kết quả hiển thị bảng:
   - Chunk size
   - Chunk overlap
   - Relevance proxy
   - Retrieval time

> **Test Checkpoint 11**: Chunk strategy benchmark ✓

---

## 🧪 PHẦN 9: CHECKLIST TEST TOÀN BỘ

Sau khi hoàn thành tất cả, bạn đã test:

| # | Chức Năng | Status | Checkpoint |
|---|-----------|--------|-----------|
| 1 | Upload PDF/DOCX | ✓ | Upload & FAISS Index |
| 2 | Chunking & Embedding | ✓ | Index creation |
| 3 | Hybrid Search (3 method) | ✓ | Retrieval Demo |
| 4 | RAG - Single Shot | ✓ | Basic RAG answer |
| 5 | Citation/Source Tracking | ✓ | Expander + Highlight |
| 6 | Co-RAG Multi-round | ✓ | Multiple iterations |
| 7 | Per-iteration Sources | ✓ | Citation per round |
| 8 | Save Chat History | ✓ | Persistent F5 survive |
| 9 | Multiple Chat Sessions | ✓ | Session management |
| 10 | Clear History | ✓ | Data cleanup |
| 11 | Chunk Strategy Benchmark | ✓ | Performance tuning |

---

## 🐛 PHẦN 10: TROUBLESHOOTING

### **Lỗi 1: "Không kết nối được Ollama"**
```powershell
# Mở tab terminal khác và chạy:
ollama serve

# Hoặc kiểm tra process:
Get-Process | findstr "ollama"
```

### **Lỗi 2: "FAISS index không tìm thấy"**
```powershell
# Xóa data cũ và tạo mới:
# Bấm nút "Clear Vector Store" trong sidebar
# Rồi upload lại
```

### **Lỗi 3: "ModuleNotFoundError"**
```powershell
# Cài lại requirements
pip install -r requirements.txt

# Hoặc activate venv chưa đúng:
.\.venv\Scripts\Activate.ps1
```

### **Lỗi 4: Port 8501 đang dùng**
```powershell
# Streamlit sẽ tự dùng port khác (8502, 8503, ...)
# Hoặc dừng process cũ:
Get-Process | findstr "streamlit" | Stop-Process -Force
```

---

## 📝 PHẦN 11: GHI CHÚ VỀ TÍNH NĂNG TV5

### **Citation/Source Tracking (Mới)**
- ✅ Xem sources với metadata đầy đủ
- ✅ Highlight keyword theo query
- ✅ Expander UI dễ sử dụng
- ✅ Hoạt động cả RAG và Co-RAG per iteration

### **Persistent Chat History (Mới)**
- ✅ Tự động lưu sau mỗi `_append_chat()`
- ✅ Survive F5 refresh
- ✅ Lưu sources đầy đủ
- ✅ Multiple sessions support

### **Integration Points**
```python
_convert_raw_docs_to_sources()      # Convert RAG docs
_create_simple_sources_from_chunks() # Convert Co-RAG chunks
_render_sources()                    # Display with citation
save_persistent_history()            # Auto-save on chat
```

---

## 🎓 KẾT LUẬN

**Bạn đã test đầy đủ:**
1. ✅ Document ingestion (Upload, Chunking, Embedding)
2. ✅ Hybrid retrieval (Vector + BM25 + Rerank)
3. ✅ Basic RAG generation
4. ✅ Co-RAG advanced reasoning
5. ✅ **Citation/Source tracking** (TV5 NEW)
6. ✅ **Persistent history** (TV5 NEW)

**Tất cả đều hoạt động và kết nối đầy đủ!** 🚀
