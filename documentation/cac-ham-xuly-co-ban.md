Bạn nên xem đúng các đoạn sau:

Điểm vào ứng dụng
app.py:1: gọi hàm main của giao diện Streamlit.
Luồng chính UI (nơi điều phối toàn bộ)
streamlit_app.py:764
Upload nhiều file PDF/DOCX: streamlit_app.py:798
Bấm ingest và tạo/cập nhật FAISS index: streamlit_app.py:889 và streamlit_app.py:906
Nhập câu hỏi và chạy RAG: streamlit_app.py:1208 và streamlit_app.py:1226
Xử lý ingest tài liệu (cốt lõi bước 1)
Ingest 1 file: document_processing_pipeline.py:24
Ingest nhiều file: document_processing_pipeline.py:53
Load PDF/DOCX: pdf_document_storage.py:18, pdf_document_storage.py:23, pdf_document_storage.py:43
Tạo và tìm kiếm index (cốt lõi bước 2)
Tạo index FAISS: faiss_vector_store.py:25
Tìm chunk liên quan: faiss_vector_store.py:206
Sinh câu trả lời (cốt lõi bước 3)
Hàm ask của Basic RAG: rag_chain_manager.py:258
Tạo prompt từ context: prompt_engineering.py:63
Gọi Ollama để generate: ollama_inference_engine.py:75
Tóm tắt cực ngắn luồng chạy:

User upload file ở sidebar → lưu raw + chunk + metadata → build FAISS index.
User hỏi câu hỏi ở tab Q&A → retrieve top-k chunks từ FAISS → build prompt → gọi Ollama → trả lời ra UI.