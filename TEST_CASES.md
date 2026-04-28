# 🧪 TEST SCRIPT - CÁC TEST CASE CHI TIẾT

> Sử dụng file này để test từng chức năng một cách có tổ chức

---

## TEST CASE 1: Upload & Index

**Mục tiêu**: Kiểm tra upload file và tạo FAISS index

**Điều kiện tiên quyết**: 
- App đang chạy
- Có file test sẵn (PDF hoặc DOCX)

**Các bước**:

1. Vào tab "Upload & Index"
2. Bấm nút "Upload tài liệu PDF/DOCX (Có thể chọn nhiều file)"
3. Chọn 1 file (VD: `documentation/Ôn thi lịch sử đảng.txt`)
4. Kiểm tra:
   - Tên file xuất hiện
   - `chunk_size = 1000`
   - `chunk_overlap = 150`

5. Bấm "Ingest và tạo FAISS index"
6. Chờ xử lý (thấy spinner)

**Kết quả mong đợi**:
```
✅ Đã tạo mới X docs. Tổng số file đang khả dụng: 1
```

**Lưu ý metadata cập nhật**:
- `available_sources`: Tên file
- `available_file_types`: Loại file (pdf, txt, docx)
- `available_upload_dates`: Ngày hôm nay

**Test Pass**: ✅ Index được tạo, metadata cập nhật

---

## TEST CASE 2: Upload Nhiều File

**Mục tiêu**: Kiểm tra incremental update FAISS index

**Các bước**:

1. Chọn **2 file khác nhau**
2. Bấm "Ingest và tạo FAISS index"
3. Kiểm tra hành vi:
   - Nếu index cũ tồn tại → Incremental update
   - Nếu index không tồn tại → Tạo mới

**Kết quả mong đợi**:
```
✅ Đã nạp thêm X docs. Tổng số file đang khả dụng: 2
```

**Test Pass**: ✅ Multiple files indexed

---

## TEST CASE 3: Retrieval - Hybrid Search

**Mục tiêu**: Kiểm tra 3 phương pháp search

**Các bước**:

1. Vào tab "Retrieval Demo"
2. Nhập query: **"Vấn đề chính của tài liệu"** (hoặc query phù hợp nội dung)
3. Bấm "Tìm chunks liên quan"
4. Chờ xử lý

**Kiểm tra kết quả 3 tabs**:

### Tab 1: Hybrid + CrossEncoder
- Kết quả: Danh sách chunks
- Có score relevance
- Số chunks ≤ top_k

### Tab 2: Hybrid Bi-encoder
- Kết quả: Danh sách chunks
- Có score relevance
- **Có thể khác Tab 1** (rerank khác)

### Tab 3: Vector-only Baseline
- Kết quả: Danh sách chunks
- Chỉ dùng vector similarity
- **Có thể khác Tab 1 & 2**

**Test Pass**: ✅ 3 tabs có kết quả khác nhau

---

## TEST CASE 4: RAG Mode (Co-RAG OFF)

**Mục tiêu**: Kiểm tra RAG generation + new Citation feature

**Điều kiện**:
- Index đã được tạo
- Co-RAG toggle ở OFF

**Các bước**:

1. Vào tab "Q&A với LLM"
2. **TẮT toggle "Bật suy nghĩ thông minh Co-RAG"**
   - Status hiển thị: "TẮT Co-RAG (chỉ chạy và trả RAG)"

3. Nhập câu hỏi:
   ```
   "Tài liệu này tìm hiểu về những chủ đề nào?"
   ```

4. Bấm "Hỏi nhanh với RAG"
5. Chờ xử lý (progress bar)

**Xem output**:

### Phần RAG Answer:
```
✅ Hoàn tát Basic RAG
**Câu trả lời:**
[AI trả lời...]

Độ tự tin: 7/10
```

### ✨ NEW: Citation / Source Tracking
```
#### Citation / Source tracking

[S1] | Ôn thi lịch sử đảng.pdf | page: 1
[S2] | Ôn thi lịch sử đảng.pdf | page: 3
```

**Expand [S1]**:
```
ID nguồn: S1
Tên file: Ôn thi lịch sử đảng.pdf
Đường dẫn nguồn: data/raw/Ôn thi lịch sử đảng.pdf
Loại file: pdf
Ngày upload: 28/04/2026

Excerpt:
[500 ký tự đầu của chunk...]

[Nút: "Xem ngữ cảnh gốc + highlight"]
```

**Bấm nút "Xem ngữ cảnh gốc + highlight"**:
```
Ngữ cảnh gốc (đã highlight theo từ khóa câu hỏi)

[Full context với từ khóa được bao quanh <mark></mark>]
```

**Kiểm tra**:
- [ ] Keyword được highlight (có <mark> tag)
- [ ] Context đầy đủ
- [ ] Metadata chính xác

**Kết quả lưu**:
- Chat history tự động lưu
- Sidebar hiển thị Q&A

**Test Pass**: ✅ RAG works + Citation tracking works

---

## TEST CASE 5: Co-RAG Mode (Co-RAG ON)

**Mục tiêu**: Kiểm tra Co-RAG multi-round + per-iteration sources

**Điều kiện**:
- Index đã được tạo
- Co-RAG toggle ở ON

**Các bước**:

1. **BẬT toggle "Bật suy nghĩ thông minh Co-RAG"**
   - Status: "BẬT Co-RAG (trả cả RAG và Co-RAG)"

2. Nhập câu hỏi **phức tạp**:
   ```
   "Tài liệu này có mấy chương? Mỗi chương nói gì?"
   ```

3. Bấm "Tranh luận / So sánh AI"

4. Chờ xử lý (process 2 cột: RAG + Co-RAG)

**Output - Cột 1 (RAG)**:
```
🤖 Basic RAG

✅ Hoàn tát Basic RAG
**Câu trả lời:** [...]
Độ tự tin: 8/10

#### Citation / Source tracking
[S1] | ... | page: 1
[S2] | ... | page: 5
```

**Output - Cột 2 (Co-RAG)**:
```
🧠 Co-RAG (Advanced)

✅ Hoàn tát (Trải qua 2 vòng)
**Câu trả lời:** [...]
Độ tự tin: 9/10
```

### ✨ NEW: Co-RAG Iterations with Per-Iteration Sources

```
### Vòng 1 | Đánh giá & Sub-query
**Ý kiến LLM:** INSUFFICIENT
**Sub-query tạo ra:** `Tài liệu này có mấy chương?`
**Số lượng đoạn trích:** 4 chunks

[Expand: Ngữ cảnh đã dùng ở vòng này]
[S1] | ... | page: 1
[S2] | ... | page: 3
[S3] | ... | page: 5
[S4] | ... | page: 7
```

**Expand S1 trong vòng 1**:
- Xem context specific cho sub-query của vòng 1
- Highlight theo sub-query: "Tài liệu này có mấy chương?"

```
### Vòng 2 | Đánh giá & Sub-query
**Ý kiến LLM:** SUFFICIENT
**Sub-query tạo ra:** `Nội dung từng chương là gì?`
**Số lượng đoạn trích:** 3 chunks

[Expand: Ngữ cảnh đã dùng ở vòng này]
[S1] | ... | page: 2
[S2] | ... | page: 4
[S3] | ... | page: 6
```

**Kiểm tra**:
- [ ] Vòng 1 assessment: INSUFFICIENT
- [ ] Vòng 1 sub-query được sinh
- [ ] Vòng 1 sources khác Vòng 2 (trích dẫn khác nhau)
- [ ] Vòng 2 assessment: SUFFICIENT
- [ ] Highlight keyword đúng theo từng vòng

### Chọn & Lưu

```
[Nút trái: Lưu đoạn RAG này]
[Nút phải: Lưu đoạn Co-RAG này]
```

1. Bấm nút phải "Lưu đoạn Co-RAG này"
2. Status: "✅ Đã lưu câu trả lời Co-RAG"

**Test Pass**: ✅ Co-RAG multi-round + per-iteration sources work

---

## TEST CASE 6: Persistent Chat History

**Mục tiêu**: Kiểm tra lưu lịch sử chat và survive F5

**Các bước**:

1. Trong sidebar, xem "### Lịch sử cuộc trò chuyện"
2. Kiểm tra:
   - [ ] Q&A vừa lưu xuất hiện
   - [ ] Format: "User: [question]" → "Assistant: [answer]"
   - [ ] Số lượng: Tất cả Q&A được lưu

**File check** (optional):
```powershell
# Mở PowerShell
cat "data/chat_history/history.json" | ConvertFrom-Json | Format-List
```

**Persist test**:
1. **Bấm F5** trên browser
2. Chờ page reload
3. Kiểm tra:
   - [ ] Lịch sử chat vẫn còn?
   - [ ] Sidebar vẫn hiển thị Q&A?
   - ✅ = Persistent ✓

**Test Pass**: ✅ History saved + F5 persistent

---

## TEST CASE 7: Multiple Chat Sessions

**Mục tiêu**: Kiểm tra quản lý nhiều sessions

**Các bước**:

1. Sidebar → Bấm "➕ Cuộc trò chuyện mới"
2. Kiểm tra:
   - [ ] Chat history clear
   - [ ] Session ID mới được tạo
   - [ ] Có thể quay lại session cũ

3. Tạo Q&A mới trong session 2
4. Kiểm tra:
   - [ ] Lịch sử session 2 độc lập
   - [ ] Session 1 vẫn có dữ liệu cũ

5. Quay lại session 1 (nếu có nút)
6. Kiểm tra:
   - [ ] Q&A của session 1 vẫn còn

**Test Pass**: ✅ Multiple sessions work independently

---

## TEST CASE 8: Clear History

**Mục tiêu**: Kiểm tra xóa lịch sử

**Các bước**:

1. Sidebar → Bấm "Clear History"
2. Confirm: "Đồng ý xóa"
3. Kiểm tra:
   - [ ] Chat history trống
   - [ ] Sidebar: không có Q&A

4. **File check**:
```powershell
cat "data/chat_history/history.json"
# Nên hiển thị: [] (empty array)
```

**Test Pass**: ✅ History cleared

---

## TEST CASE 9: Chunk Strategy Benchmark

**Mục tiêu**: Kiểm tra so sánh chunk strategies

**Các bước**:

1. Tab "Upload & Index" → phía bên phải
2. Nhập "Câu truy vấn để benchmark":
   ```
   "Vấn đề chính"
   ```

3. Bấm "So sánh 3 cấu hình chunk"
4. Chờ xử lý

**Kết quả**:
```
chunk_size | chunk_overlap | relevance_proxy | retrieval_time
    700    |      100      |     0.85        |    0.12s
   1000    |      150      |     0.90        |    0.15s
   1300    |      210      |     0.88        |    0.18s
```

**Kiểm tra**:
- [ ] Bảng có 3 hàng (3 strategies)
- [ ] relevance_proxy có giá trị 0-1
- [ ] retrieval_time hợp lý

**Test Pass**: ✅ Chunk benchmark works

---

## TEST CASE 10: Error Handling

**Mục tiêu**: Kiểm tra xử lý lỗi

**Scenario 1: Không có index**
- [ ] Q&A: "Chưa có index trong session"
- [ ] Upload form: "Chưa chọn tài liệu"

**Scenario 2: Ollama không chạy**
- [ ] Q&A: "Không kết nối được Ollama"
- [ ] Error message rõ ràng

**Scenario 3: Upload file không hợp lệ**
- [ ] Q&A: "Định dạng file không được hỗ trợ"

**Test Pass**: ✅ Error handling user-friendly

---

## 📊 SUMMARY TABLE

| Test Case # | Tên | Status | Notes |
|-------------|-----|--------|-------|
| 1 | Upload & Index | ✓ | Single file |
| 2 | Multiple Files | ✓ | Incremental |
| 3 | Hybrid Search | ✓ | 3 methods |
| 4 | RAG + Citation | ✓ | NEW TV5 |
| 5 | Co-RAG + Sources | ✓ | NEW TV5 |
| 6 | Persistent History | ✓ | NEW TV5 |
| 7 | Multiple Sessions | ✓ | Session mgmt |
| 8 | Clear History | ✓ | Data cleanup |
| 9 | Chunk Benchmark | ✓ | Tuning |
| 10 | Error Handling | ✓ | UX |

---

**Tất cả test pass → ✅ Ready for production!**
