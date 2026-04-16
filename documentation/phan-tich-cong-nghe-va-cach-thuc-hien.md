# Phân tích công nghệ và cách thực hiện đồ án SmartDoc AI

## 1) Mục tiêu bài toán
Xây dựng hệ thống **RAG (Retrieval-Augmented Generation)** cho phép:
- Upload tài liệu (trọng tâm: PDF, mở rộng thêm DOCX).
- Đặt câu hỏi theo nội dung tài liệu.
- Trả lời tốt tiếng Việt và đa ngôn ngữ.
- Chạy local bằng mô hình open-source.

---

## 2) Công nghệ cần sử dụng

## 2.1 Nhóm công nghệ cốt lõi (bám sát đề)
1. **Frontend/UI**
- **Streamlit**: xây giao diện web nhanh cho upload file + hỏi đáp.
- HTML/CSS (nếu cần) để tùy biến giao diện.

2. **Backend & Orchestration AI**
- **Python 3.10+**: ngôn ngữ chính.
- **LangChain** + **langchain-community**: dựng pipeline RAG (loader, splitter, retriever, chain).

3. **Document Processing**
- **PDFPlumberLoader** (qua LangChain): đọc PDF.
- **(Mở rộng câu hỏi 1)**: thêm parser DOCX, ví dụ `Docx2txtLoader` hoặc `python-docx`.

4. **Embedding**
- **HuggingFace sentence-transformers**.
- Model đề xuất theo đề: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (768 chiều, hỗ trợ tiếng Việt tốt).

5. **Vector Database / Retrieval**
- **FAISS**: lưu vector + truy vấn similarity top-k.

6. **LLM Runtime**
- **Ollama** để chạy local model.
- Model chính: **Qwen2.5:7b**.

## 2.2 Nhóm công nghệ nên bổ sung (để làm tốt phần nâng cao)
1. **Lưu hội thoại**
- SQLite (đơn giản, local) hoặc JSON file.

2. **Hybrid Search (câu 7)**
- BM25 (thư viện `rank-bm25`) + vector search FAISS.

3. **Re-ranking (câu 9)**
- Cross-Encoder từ `sentence-transformers` (ví dụ họ `ms-marco-*`).

4. **Observability / Debug**
- Logging chuẩn Python (`logging`) + timing để đo latency.

5. **Đóng gói môi trường**
- `venv` + `requirements.txt` (hoặc Poetry).

---

## 3) Kiến trúc hệ thống đề xuất

1. **Presentation Layer**
- Streamlit UI: upload file, nhập câu hỏi, hiển thị câu trả lời/citation.

2. **Application Layer**
- Pipeline xử lý tài liệu (load -> split -> embedding -> index).
- Pipeline truy vấn (embed query -> retrieve -> prompt -> generate).

3. **Data Layer**
- Tài liệu gốc, chunks, metadata, FAISS index, lịch sử chat.

4. **Model Layer**
- Ollama + Qwen2.5:7b.

---

## 4) Cách thực hiện (roadmap từng bước)

## Giai đoạn 1: Setup môi trường
1. Tạo môi trường Python và cài thư viện:
- `streamlit`, `langchain`, `langchain-community`, `faiss-cpu`, `sentence-transformers`, `pypdf`, `pdfplumber`.
2. Cài **Ollama**, pull model `qwen2.5:7b`.
3. Tạo cấu trúc thư mục cơ bản:
- `app/` (UI + backend)
- `data/raw/` (file upload)
- `data/index/` (FAISS)
- `data/chat_history/` (lịch sử hội thoại)

## Giai đoạn 2: Xây pipeline ingest tài liệu
1. Upload file PDF.
2. Load text bằng PDFPlumberLoader.
3. Chunk bằng RecursiveCharacterTextSplitter (`chunk_size`, `chunk_overlap`).
4. Tạo embedding cho chunks.
5. Index vào FAISS, lưu kèm metadata (tên file, trang, vị trí chunk).

## Giai đoạn 3: Xây pipeline hỏi đáp
1. Nhận câu hỏi người dùng.
2. Embed câu hỏi.
3. Retrieve top-k chunks liên quan từ FAISS.
4. Build prompt có context + instruction (ngắn gọn, đúng ngôn ngữ).
5. Gọi Ollama (Qwen2.5:7b) để sinh câu trả lời.
6. Trả về UI, kèm nguồn tham chiếu (citation).

## Giai đoạn 4: Hoàn thiện các yêu cầu phát triển (mục 8 trong đề)
1. **DOCX support**: thêm loader DOCX vào ingest pipeline.
2. **Lưu hội thoại**: ghi câu hỏi/trả lời vào SQLite/JSON.
3. **Nút xóa lịch sử**: xóa theo session hoặc toàn bộ.
4. **Cải thiện chunk strategy**: tách theo heading/semantic, tune `chunk_size` động.
5. **Citation/source tracking**: hiển thị trang/chunk đã dùng.
6. **Conversational RAG**: thêm memory theo phiên chat.
7. **Hybrid search**: kết hợp BM25 + vector, rồi fusion score.
8. **Multi-document + metadata filtering**: lọc theo file, thời gian, chủ đề.
9. **Re-ranking**: cross-encoder để sắp xếp lại top-k ứng viên.
10. **Advanced RAG / Self-RAG**: self-check, reflection, answer verification.

## Giai đoạn 5: Đánh giá và tối ưu
1. Đo chất lượng: độ đúng, độ đầy đủ, hallucination rate.
2. Đo hiệu năng: latency, throughput, RAM/CPU.
3. Tinh chỉnh tham số: `k`, `chunk_size`, `chunk_overlap`, prompt template.

---

## 5) Danh sách thư viện Python gợi ý
- `streamlit`
- `langchain`
- `langchain-community`
- `langchain-text-splitters`
- `faiss-cpu`
- `sentence-transformers`
- `pdfplumber`
- `python-docx` (khi thêm DOCX)
- `rank-bm25` (khi thêm hybrid search)
- `sqlite3` (built-in) hoặc ORM nhẹ

---

## 6) Kết luận
Đồ án này cần một stack xoay quanh **RAG local**: Streamlit + LangChain + Embedding đa ngôn ngữ + FAISS + Ollama/Qwen2.5.
Cách thực hiện phù hợp nhất là triển khai theo pipeline từ ingest tài liệu đến query, sau đó mở rộng dần theo 10 yêu cầu nâng cao trong đề để tăng độ chính xác, tính thực tế và khả năng đánh giá.
