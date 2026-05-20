# Đề xuất cải thiện và mở rộng cho SmartDoc AI

Tài liệu này tổng hợp các hướng có thể làm thêm hoặc cải thiện thêm cho đồ án SmartDoc AI, dựa trên kiến trúc hiện tại của hệ thống RAG, Co-RAG, xử lý PDF/DOCX, lưu lịch sử hội thoại và giao diện Streamlit.

Mục tiêu của tài liệu là giúp nhóm xác định các hạng mục ưu tiên để nâng chất lượng đồ án theo cả ba góc nhìn: người dùng cuối, chất lượng truy xuất, và độ hoàn thiện kỹ thuật.

---

## 1. Nhóm cải thiện trải nghiệm người dùng

### 1.1. Làm rõ trạng thái xử lý theo từng bước

Hiện tại hệ thống đã có luồng ingest và hỏi đáp, nhưng có thể hiển thị chi tiết hơn từng trạng thái như:

1. Đang đọc file.
2. Đang trích xuất văn bản.
3. Đang tách chunk.
4. Đang tạo embedding.
5. Đang cập nhật FAISS.
6. Đang truy xuất ngữ cảnh.
7. Đang sinh câu trả lời.

Việc này giúp người dùng hiểu hệ thống đang làm gì thay vì chỉ thấy spinner chung chung.





### thêm Nút ghim câu hỏi quan trọng.




---

## 2. Nhóm cải thiện chất lượng RAG

### 2.1. Thêm cơ chế đánh giá chất lượng truy xuất

Có thể log và hiển thị các chỉ số như:

1. Số chunk được truy xuất.
2. Số chunk sau rerank.
3. Độ tự tin của câu trả lời.
4. Tỷ lệ câu hỏi có đủ ngữ cảnh hay phải hỏi lại.

Những chỉ số này rất hữu ích khi báo cáo đồ án vì thể hiện rõ hệ thống hoạt động như thế nào.

### 2.2. Bổ sung bộ kiểm tra câu trả lời đủ hay chưa

Hệ thống Co-RAG đã là một bước tốt, nhưng có thể bổ sung thêm:

1. Kiểm tra thiếu thông tin trước khi trả lời.
2. Tự động đặt truy vấn phụ nếu context còn mỏng.
3. Gắn nhãn câu trả lời là “đủ chắc chắn” hoặc “cần kiểm tra thêm”.

Điều này giảm nguy cơ trả lời mơ hồ hoặc bịa nội dung.


### 2.4. Bổ sung hybrid search nâng cao

Ngoài semantic search, có thể mở rộng để:

1. Kết hợp keyword search chặt chẽ hơn.
2. Có trọng số riêng cho semantic và lexical search.
3. Ưu tiên tài liệu có match tiêu đề hoặc từ khóa chính xác.

Điều này hữu ích khi người dùng hỏi các thuật ngữ chuyên ngành hoặc tên mục trong tài liệu.

### 2.5. Làm tốt hơn cho câu hỏi follow-up

Có thể cải thiện xử lý hội thoại bằng cách:

1. Viết lại câu hỏi phụ thuộc ngữ cảnh thành câu độc lập.
2. Nhớ thực thể đã nhắc trong câu trước.
3. Giữ mạch truy vấn theo chủ đề đang nói tới.

Nhóm này đặc biệt quan trọng nếu đồ án được dùng như một chatbot tài liệu thật.

---

## 3. Nhóm cải thiện xử lý tài liệu

### 3.1. Nâng chất lượng đọc PDF

Với PDF nhiều cột, scan ảnh, hoặc tài liệu bị lỗi bố cục, nên cân nhắc:

1. Thêm chế độ xem trước văn bản đã trích xuất.
2. Cho phép chọn loader theo loại tài liệu.
3. Log rõ file nào OCR, file nào text-based.
4. Cho phép người dùng tải lại hoặc loại bỏ file trích xuất lỗi.



### 3.3. Chuẩn hóa metadata đầy đủ hơn

Có thể bổ sung metadata cho mỗi chunk như:

1. Trang.
2. Vị trí đoạn.
3. Loại tài liệu.
4. Phiên ingest.
5. Chiến lược chunk đã dùng.

Metadata tốt sẽ giúp debug dễ hơn và hỗ trợ truy xuất có lọc sau này.

---

## 4. Nhóm cải thiện độ ổn định và khả năng bảo trì

### 4.1. Tách rõ logging và error handling

Nên chuẩn hóa lỗi theo từng lớp:

1. Lỗi upload.
2. Lỗi đọc file.
3. Lỗi embedding.
4. Lỗi FAISS.
5. Lỗi LLM/Ollama.

Nếu có log nhất quán, việc debug khi demo hoặc nộp báo cáo sẽ nhanh hơn nhiều.


### 4.3. Dọn sạch các state cũ không còn hợp lệ

Khi làm việc với lịch sử chat và index lưu cục bộ, nên có cơ chế:

1. Phát hiện lịch sử lỗi thời.
2. Phát hiện pending session còn sót.
3. Đồng bộ lại state khi mở app.

Việc này giúp giảm lỗi “state ma” khi reload ứng dụng.

### 4.4. Chuẩn hóa cấu hình môi trường và cho phép chọn model sử dụng

Nên tách cấu hình vào file rõ ràng cho:

1. Model chính.
2. Model dự phòng.
3. Đường dẫn index.
4. Tesseract.
5. Chunk size và overlap.

Cách này làm dự án dễ triển khai trên máy khác hơn.

---

## 5. Nhóm cải thiện về đánh giá và báo cáo đồ án

### 5.1. Có bộ dữ liệu câu hỏi kiểm thử

Nên chuẩn bị một tập câu hỏi chuẩn để đo chất lượng hệ thống:

1. Câu hỏi fact-based.
2. Câu hỏi yêu cầu suy luận.
3. Câu hỏi đa tài liệu.
4. Câu hỏi follow-up.
5. Câu hỏi ngoài phạm vi.

Bộ này giúp chứng minh hiệu quả của đồ án bằng số liệu cụ thể.

### 5.2. So sánh các chiến lược truy xuất

Có thể đưa vào báo cáo các so sánh:

1. Vector-only vs hybrid search.
2. RAG một vòng vs Co-RAG.
3. Chunk nhỏ vs chunk lớn.
4. Có rerank vs không rerank.

Đây là phần rất mạnh khi thuyết trình vì cho thấy nhóm có đánh giá dựa trên thực nghiệm.

### 5.3. Ghi lại ví dụ đầu vào/đầu ra thực tế

Nên lưu một số case study trong tài liệu:

1. File PDF nhiều cột.
2. File scan ảnh.
3. File DOCX nhiều bảng.
4. Câu hỏi có follow-up.

Mỗi case nên có ảnh chụp màn hình hoặc trích đoạn kết quả để làm minh chứng.

---

## 6. Nhóm cải thiện mở rộng tính năng

### 6.1. Hỗ trợ nhiều định dạng hơn

Ngoài PDF và DOCX, có thể cân nhắc:

1. TXT.
2. HTML.
3. PPTX.
4. CSV hoặc bảng dữ liệu đơn giản.

Điều này giúp đồ án dùng được rộng hơn trong thực tế.

### 6.2. Thêm chế độ xuất kết quả

Nên cho phép:

1. Xuất lịch sử chat ra file.
2. Xuất câu trả lời kèm nguồn.
3. Xuất báo cáo truy xuất.

Tính năng này hữu ích cho người dùng cần nộp báo cáo hoặc lưu kết quả nghiên cứu.

### 6.3. Thêm trang dashboard nhỏ

Một dashboard có thể hiển thị:

1. Số file đã upload.
2. Số chunk đã tạo.
3. Số phiên hội thoại.
4. Model đang chạy.
5. Trạng thái index.

Điều này làm ứng dụng trông hoàn chỉnh hơn và dễ demo hơn.

---

## 7. Đề xuất ưu tiên triển khai

Nếu nhóm muốn làm theo mức độ hiệu quả, có thể ưu tiên như sau:

### Mức 1: Nên làm trước

1. Citation/source tracking rõ ràng.
2. Lịch sử hội thoại dễ xem lại.
3. Logging và error handling chuẩn hóa.
4. Bộ test cho các luồng chính.

### Mức 2: Nên làm tiếp

1. Tối ưu chunking.
2. Hybrid search và rerank.
3. Cải thiện follow-up query.
4. Hiển thị trạng thái xử lý chi tiết hơn.

### Mức 3: Mở rộng nâng cao

1. Multi-document RAG.
2. Dashboard thống kê.
3. Xuất báo cáo kết quả.
4. Hỗ trợ thêm định dạng tài liệu.

---

## 8. Kết luận

SmartDoc AI đã có nền tảng tốt để trở thành một đồ án RAG hoàn chỉnh: có ingest tài liệu, vector search, Co-RAG, OCR, lưu lịch sử và giao diện Streamlit. Phần nên tập trung tiếp theo không phải chỉ là thêm tính năng, mà là làm cho các bước hiện có rõ hơn, đo được chất lượng tốt hơn, và dễ dùng hơn cho người cuối.

Nếu cần một hướng ưu tiên ngắn gọn, nên tập trung vào ba việc: hiển thị nguồn trích dẫn, cải thiện chất lượng truy xuất, và thêm bộ kiểm thử để chứng minh độ ổn định của hệ thống.