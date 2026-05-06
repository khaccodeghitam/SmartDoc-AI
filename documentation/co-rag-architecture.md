# Kiến trúc và Quy trình Hoạt động của Co-RAG (Advanced RAG)

Co-RAG (Chain-of-Retrieval Augmented Generation hay Corrective/Conversational RAG) là tính năng nâng cao trong đồ án SmartDoc AI, bao hàm 4 thành phần kỹ thuật hiện đại: **Self-RAG**, **Query Rewriting**, **Multi-hop Reasoning**, và **Confidence Scoring**.

Dưới đây là tài liệu phân tích luồng chạy chi tiết của module `CoRAGChainManager` trong hệ thống.

---

## Các Bước Hoạt Động Chi Tiết Của Co-RAG

### Bước 1: Khởi tạo và Truy xuất ban đầu (Initial Retrieval)

- **Hoạt động:** Khi người dùng đặt câu hỏi, Co-RAG lấy chính câu hỏi đó để thực hiện việc tìm kiếm lần đầu tiên trong kho tài liệu. Hệ thống sẽ lọc bớt các đoạn (chunk) quá ngắn hoặc có chất lượng thấp để giữ luồng ngữ cảnh sạch nhất.
- **Công nghệ / Thành phần sử dụng:**
  - **Mô hình nhúng:** `Multilingual MPNet` (để chuyển câu hỏi thành vector).
  - **Vector Database:** `FAISS` (so sánh độ tương đồng Cosine/Inner Product để lấy top-k đoạn văn bản).
  - **Hàm xử lý:** `search_similar_chunks()` và `filter_low_quality_chunks()` trong file `faiss_vector_store.py`.
- **Ví dụ cơ bản:**
  - _Người dùng hỏi:_ "Tại sao dự án SmartDoc thất bại trong Q1 và hướng khắc phục trong Q2 là gì?"
  - _Kết quả truy xuất vòng 1:_ Lấy được đoạn tài liệu "Dự án SmartDoc thất bại trong Q1 do thiếu ngân sách mua GPU." (hoàn toàn chưa có thông tin về Q2).

### Bước 2: Tự đánh giá mức độ đầy đủ của ngữ cảnh (Self-RAG - Khâu "Tự kiểm định")

- **Hoạt động:** Thay vì vội vàng trả lời ngay, hệ thống cấu trúc một **Prompt Kiểm định** (Sufficiency Check) gửi cho AI. Prompt này cung cấp câu hỏi gốc và ngữ cảnh vừa tìm được, ép model AI phải trả lời bằng 1 từ khóa đầu tiên: `SUFFICIENT` (Đủ) hoặc `INSUFFICIENT` (Thiếu).
- **Công nghệ / Thành phần sử dụng:**
  - **Mô hình suy luận:** Local LLM `Qwen2.5:7b` chạy qua `OllamaInferenceEngine`.
  - **Kỹ thuật Prompting:** `build_corag_sufficiency_check_prompt()` ép model đánh giá tư duy.
- **Ví dụ tiếp nối:**
  - AI đọc câu hỏi trên và nhận ra: "Có lý do thất bại Q1, nhưng không có thông tin Q2".
  - Do đó AI sẽ trả về: `INSUFFICIENT. Ngữ cảnh bị thiếu thông tin về hướng khắc phục trong quý 2.`

### Bước 3: Tự động viết lại truy vấn (Query Rewriting)

- **Hoạt động:** Chỉ được kích hoạt nếu ở Bước 2 AI trả về `INSUFFICIENT`. Khi đó, thay vì chịu thua, hệ thống sẽ trích xuất lý do thiếu hụt do AI vừa sinh ra để chuyển đổi thành một truy vấn con (sub-query) mới tinh.
- **Công nghệ / Thành phần sử dụng:**
  - Hàm phân tích chuỗi `_extract_subquery()` trong chuỗi Co-RAG.
- **Ví dụ tiếp nối:**
  - Từ giải thích `Ngữ cảnh bị thiếu thông tin về hướng khắc phục trong quý 2.`, thuật toán trích xuất biến nó thành câu truy vấn mới: `"hướng khắc phục dự án SmartDoc trong Q2"`.

### Bước 4: Lặp lại quá trình tìm kiếm (Multi-hop Reasoning)

- **Hoạt động:** Hệ thống ném cái **sub-query** ở Bước 3 qua lại FAISS Vector Store để tìm tài liệu vòng 2. Sau khi tìm được, nó gộp (accumulate) các ngữ cảnh này với đám ngữ cảnh vòng 1, đồng thời loại bỏ phần trùng lặp. Vòng lặp 2->3->4 này diễn ra tối đa một số lần (mặc định trong mã nguồn `max_rounds=3`) để tránh bị treo vô tận.
- **Công nghệ / Thành phần sử dụng:**
  - Vòng lặp lặp lại truy vấn trong hàm `ask()` của `CoRAGChainManager`.
  - Hàm chống trùng lặp `_deduplicate_chunks()`.
- **Ví dụ tiếp nối:**
  - Sub-query `"hướng khắc phục dự án SmartDoc trong Q2"` đi vào FAISS và tìm được đoạn tài liệu thứ 2: "Trong Q2, ban giám đốc quyết định cắt giảm nhân sự và cấu hình lại Ollama để dùng CPU.".
  - Ngữ cảnh 1 + Ngữ cảnh 2 được nối lại. AI kiểm tra vòng 2 và lần này trả về `SUFFICIENT` và phá vỡ vòng lặp.

### Bước 5: Sinh câu trả lời cuối và tự chấm điểm (Generation & Confidence Scoring)

- **Hoạt động:** Khi có dấu hiệu ĐỦ (`SUFFICIENT`) hoặc đã hết số vòng quy định, Co-RAG biên dịch toàn bộ ngữ cảnh tổng hợp được đưa vào **Prompt Sinh câu trả lời cuối** (Final Prompt). Yêu cầu AI sinh ra câu trả lời cuối cùng và đánh giá độ tự tin trên thang 10 (vd: Confidence: 8/10).
- **Công nghệ / Thành phần sử dụng:**
  - `build_corag_final_prompt()` yêu cầu model suy luận từ kết quả nhiều vòng để trả lời cấu trúc rõ ràng và chấm điểm (Score).
  - Trích xuất điểm tự tin bằng Regex trong chuỗi kết quả.
- **Ví dụ ở giao diện:**
  - Trả về câu trả lời phân tích được 2 hướng giải quyết. Kèm thêm chỉ số cuối màn hình: `Độ tự tin: 9/10`. Dưới cùng sẽ có Button `> Vòng 1 | Đánh giá & Sub-query` (Như hình lúc nãy bạn gửi) để xem lại chi tiết quá trình vất vả mà AI đã trải qua.

---

## Bảng so sánh nhanh RAG và Co-RAG (Tóm lại tính ứng dụng)

| Đặc điểm                     | Basic RAG (Truyền thống)                                                    | Co-RAG (Advanced RAG)                                                                                                                  |
| :--------------------------- | :-------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| **Lần tìm kiếm (Retrieval)** | Chỉ một lần duy nhất (Single-shot).                                         | Lặp lại nhiều lần (Multi-hop).                                                                                                         |
| **Khi thông tin bị thiếu**   | Do chỉ tìm 1 lần nên dễ sinh ảo giác (Hallucination), Cố "chém gió" bù vào. | Có khả năng nhận diện cái mình không biết (Self-RAG), tự đặt lại câu hỏi ngắn hơn để tìm trúng đích (Query Rewriting).                 |
| **Độ tin cậy sinh ra**       | Không rõ ràng (Black-box).                                                  | Có điểm số Confidence Score 0-10 và rành mạch chỉ ra các bước vòng lặp cho user xem lại.                                               |
| **Tài nguyên Tiêu thụ**      | Thấp. Lấy và nối text rất nhanh.                                            | Rất Cao. Yêu cầu LLM Model tự "Ping" với chính nó nhiều lần để sinh prompt tự đánh giá, gây độ trễ lớn (~15s đến 1 phút tùy cấu hình). |

_TL;DR: Cơ chế này giả lập cách tư duy của 1 thủ thư đi tìm tài liệu. Thay vì chỉ tìm từ khóa theo yêu cầu 1 lần báo cáo lại, nó sẽ lấy kết quả ra đọc lại, thấy chưa liên kết hoặc đứt gãy -> viết cái ghi chú (Subquery) -> đi tìm lại trong tủ sách lần nữa cho đủ._
