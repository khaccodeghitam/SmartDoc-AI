# Chức năng đồ án SmartDoc AI (tổng hợp từ assignment)

## 1. Chức năng cốt lõi (đã mô tả/đã hoàn thành)

1. Upload và xử lý tài liệu PDF
- Cho phép người dùng tải file PDF (kéo-thả hoặc chọn file).
- Kiểm tra định dạng và thông báo lỗi nếu file không hợp lệ.
- Thực hiện trích xuất văn bản từ PDF.

2. Tách văn bản thành các đoạn (chunking)
- Chia tài liệu thành các chunk bằng RecursiveCharacterTextSplitter.
- Có cơ chế overlap để giữ ngữ cảnh giữa các đoạn.

3. Tạo vector embedding đa ngôn ngữ
- Chuyển text chunks thành vector bằng mô hình multilingual MPNet.
- Hỗ trợ tốt tiếng Việt và nhiều ngôn ngữ khác.

4. Lưu trữ và truy xuất bằng vector database
- Lưu embeddings vào FAISS index.
- Thực hiện similarity search để lấy top-k đoạn liên quan.

5. Hỏi đáp trên tài liệu (Document Q&A)
- Người dùng nhập câu hỏi ngôn ngữ tự nhiên.
- Hệ thống truy xuất context liên quan và sinh câu trả lời bằng LLM.

6. Tích hợp LLM local qua Ollama
- Sử dụng model Qwen2.5:7b để suy luận.
- Chạy local, không phụ thuộc API cloud.

7. Prompt engineering + ràng buộc câu trả lời
- Prompt có instruction rõ ràng, yêu cầu trả lời ngắn gọn.
- Có nhánh xử lý theo ngôn ngữ câu hỏi (Việt/Anh).

8. Tự động phát hiện ngôn ngữ và phản hồi phù hợp
- Hệ thống nhận diện ngôn ngữ đầu vào ở mức cơ bản.
- Trả lời theo ngôn ngữ phù hợp với người dùng.

9. Giao diện web thân thiện (Streamlit)
- Có khu vực upload file, nhập câu hỏi, hiển thị câu trả lời.
- Hiển thị trạng thái xử lý và loading spinner.

10. Error handling và thông báo người dùng
- Cảnh báo lỗi file upload, lỗi xử lý, lỗi kết nối model.
- Trả thông báo dễ hiểu cho người dùng cuối.

---

## 2. Chức năng phát triển thêm (theo yêu cầu mục 8)

1. Hỗ trợ DOCX
- Upload và xử lý file DOCX tương tự PDF.
- Trích xuất văn bản chính xác từ DOCX.

2. Lưu lịch sử hội thoại
- Lưu câu hỏi/câu trả lời theo phiên.
- Hiển thị lịch sử chat ở sidebar.

3. Xóa lịch sử và dữ liệu tạm
- Nút Clear History để xóa toàn bộ hội thoại.
- Nút Clear Vector Store để xóa tài liệu/index đã upload.
- Có xác nhận trước khi xóa.

4. Cải thiện chiến lược chunk
- Thử nhiều giá trị chunk_size/chunk_overlap.
- So sánh ảnh hưởng tới độ chính xác và chất lượng trả lời.
- Cho phép user tự chỉnh tham số chunk.

5. Citation / source tracking
- Hiển thị nguồn thông tin dùng để trả lời (trang, vị trí đoạn).
- Cho click để xem ngữ cảnh gốc.
- Highlight đoạn trích đã dùng.

6. Conversational RAG
- Bổ sung memory hội thoại.
- Xử lý câu hỏi follow-up có phụ thuộc ngữ cảnh trước đó.

7. Hybrid search
- Kết hợp semantic search (vector) với keyword search (BM25).
- Dùng ensemble retriever, so sánh với vector-only.

8. Multi-document RAG + metadata filtering
- Upload nhiều tài liệu cùng lúc.
- Lưu metadata (tên file, ngày upload, loại tài liệu).
- Lọc truy vấn theo metadata.
- Hiển thị câu trả lời đến từ tài liệu nào.

9. Re-ranking với Cross-Encoder
- Thêm bước chấm lại mức liên quan sau retrieval.
- So sánh hiệu quả với bi-encoder hiện tại.
- Tối ưu thêm latency.

10. Advanced RAG / Self-RAG
- LLM tự đánh giá câu trả lời.
- Query rewriting tự động.
- Multi-hop reasoning.
- Confidence scoring.

---

## 3. Nhóm chức năng theo góc nhìn người dùng

1. Chức năng cho End-user
- Upload tài liệu.
- Đặt câu hỏi.
- Xem câu trả lời.
- Theo dõi lịch sử hội thoại (khi triển khai).
- Xóa lịch sử/dữ liệu (khi triển khai).

2. Chức năng cho Developer
- Thay embedding model.
- Điều chỉnh chunk parameters.
- Đổi LLM model trong Ollama.
- Chỉnh retrieval strategy (similarity/MMR/hybrid).
- Thêm logging để theo dõi pipeline.

---

## 4. Chức năng ưu tiên triển khai theo thứ tự

1. Ổn định lõi RAG (PDF -> chunk -> embedding -> FAISS -> Q&A).
2. Lưu lịch sử + clear history.
3. Citation/source tracking.
4. Multi-document + metadata filtering.
5. Hybrid search.
6. Re-ranking.
7. Self-RAG.

Thứ tự này giúp đảm bảo hệ thống chạy tốt phần nền tảng trước, sau đó mới tăng chất lượng truy xuất và suy luận.

---

## 5. Kết luận về database

Dựa trên phần mô tả hiện có trong tài liệu, đồ án **có sử dụng database**, nhưng đây là **vector database** phục vụ truy xuất ngữ nghĩa cho RAG.

- **Loại database chính:** FAISS (Facebook AI Similarity Search)
- **Mục đích:** lưu embeddings của các đoạn văn bản và truy vấn similarity search để lấy các đoạn liên quan nhất
- **Không thấy mô tả** việc dùng cơ sở dữ liệu quan hệ như MySQL, PostgreSQL hay NoSQL như MongoDB trong phần tài liệu hiện tại

Nếu cần mở rộng chức năng lưu lịch sử hội thoại, tài liệu có gợi ý thêm **SQLite** hoặc **JSON file** cho dữ liệu cục bộ, nhưng đó là phần mở rộng, không phải database lõi của hệ thống.

---

## 6. Cách cài đặt và sử dụng FAISS

### 6.1 Cài đặt

Trong dự án Python, FAISS thường được cài dưới dạng package `faiss-cpu` nếu chạy trên máy thường:

```bash
pip install faiss-cpu
```

Nếu dùng môi trường có GPU và cần tăng tốc, có thể cân nhắc bản FAISS hỗ trợ GPU, nhưng với đồ án này bản CPU là đủ.

### 6.2 Cách dùng cơ bản

FAISS được dùng để lưu vector embedding của các đoạn văn bản và tìm các đoạn gần nhất với câu hỏi người dùng.

```python
import faiss
import numpy as np

# Ví dụ: tạo vector 768 chiều cho embeddings
dimension = 768
index = faiss.IndexFlatIP(dimension)  # IP = inner product, thường dùng với normalized embeddings

# vectors: numpy array kiểu float32, shape = (n, dimension)
vectors = np.array(embedding_list, dtype="float32")
index.add(vectors)

# query_vector: vector của câu hỏi, shape = (1, dimension)
distances, indices = index.search(query_vector, k=3)
```

### 6.3 Quy trình sử dụng trong đồ án

1. Tạo embedding cho từng chunk của tài liệu.
2. Chuyển embedding sang mảng `float32`.
3. Thêm vector vào FAISS index.
4. Khi người dùng hỏi, tạo embedding cho câu hỏi.
5. Dùng `search()` để lấy top-k chunk gần nhất.
6. Ghép các chunk này làm context cho LLM sinh câu trả lời.

### 6.4 Lưu và tải lại index

Nếu muốn tái sử dụng dữ liệu đã index, FAISS cho phép lưu index xuống file và tải lại sau:

```python
faiss.write_index(index, "data/index/faiss.index")

loaded_index = faiss.read_index("data/index/faiss.index")
```

### 6.5 Lưu ý quan trọng

- FAISS không phải MySQL hay MongoDB; nó là thư viện/vector database cho tìm kiếm tương đồng.
- Dữ liệu đầu vào nên là `float32` và thường nên normalize nếu dùng cosine similarity theo inner product.
- Với đồ án RAG, FAISS phù hợp để truy xuất ngữ nghĩa nhanh và nhẹ, đặc biệt khi chạy local.
