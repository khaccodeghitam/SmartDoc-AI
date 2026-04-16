# Yêu Cầu Giao Diện Cho Đồ Án SmartDoc AI

Tài liệu này tổng hợp toàn bộ yêu cầu liên quan đến giao diện người dùng từ file assignment và các tài liệu mô tả dự án. Mục tiêu là tách riêng phần UI/UX thành một bản mô tả rõ ràng, đầy đủ, dễ dùng cho việc thiết kế và triển khai.

Nguồn tham chiếu chính:
- [docs/assignment ossd.txt](docs/assignment%20ossd.txt)
- [docs/chuc-nang-do-an-smartdoc-ai.md](docs/chuc-nang-do-an-smartdoc-ai.md)
- [docs/phan-tich-cong-nghe-va-cach-thuc-hien.md](docs/phan-tich-cong-nghe-va-cach-thuc-hien.md)

---

## 1. Phạm Vi Giao Diện

Giao diện của SmartDoc AI phải phục vụ các mục tiêu sau:

1. Cho phép người dùng tải lên tài liệu PDF, và theo phần mở rộng có thể hỗ trợ DOCX.
2. Cho phép người dùng nhập câu hỏi theo ngôn ngữ tự nhiên.
3. Hiển thị câu trả lời từ hệ thống RAG một cách rõ ràng, dễ đọc.
4. Cho phép theo dõi trạng thái xử lý tài liệu.
5. Hiển thị lỗi và thông báo cho người dùng theo cách dễ hiểu.
6. Dùng Streamlit làm nền tảng giao diện web chính.

---

## 2. Yêu Cầu Giao Diện Bắt Buộc Từ Assignment

### 2.1 Giao diện người dùng tổng thể

Theo assignment, phần giao diện phải có một khu vực trình bày rõ ràng cho người dùng cuối, bao gồm:

1. Màn hình chính để tải tài liệu lên.
2. Khu vực nhập câu hỏi.
3. Khu vực hiển thị câu trả lời.
4. Khu vực hiển thị trạng thái xử lý.
5. Thông báo lỗi khi có vấn đề xảy ra.

### 2.2 Thiết kế UI/UX

Assignment yêu cầu một phần riêng về thiết kế UI/UX, bao gồm:

1. Color Palette.
2. Layout Structure.

Điều này có nghĩa là giao diện không chỉ cần hoạt động đúng, mà còn phải có bố cục rõ ràng và bảng màu nhất quán.

### 2.3 File Upload

Các yêu cầu giao diện cho upload file gồm:

1. Có file uploader để người dùng chọn tài liệu.
2. Có thể kéo thả file nếu triển khai trên Streamlit.
3. Có kiểm tra định dạng file hợp lệ.
4. Có thông báo thành công khi upload xong.
5. Có thông báo lỗi khi file không hợp lệ hoặc quá trình xử lý thất bại.

### 2.4 Question Answering

Các yêu cầu giao diện cho chức năng hỏi đáp gồm:

1. Có ô nhập câu hỏi tự nhiên.
2. Có hiển thị trạng thái đang xử lý.
3. Có loading spinner khi hệ thống đang suy luận.
4. Có khu vực hiển thị câu trả lời rõ ràng.
5. Câu trả lời phải dễ đọc, có thể ngắn gọn và tập trung vào nội dung liên quan.

### 2.5 Error Handling

Assignment yêu cầu giao diện phải có xử lý lỗi, gồm:

1. Cảnh báo file không hợp lệ.
2. Cảnh báo lỗi xử lý tài liệu.
3. Cảnh báo lỗi kết nối model.
4. Thông báo lỗi thân thiện với người dùng, không chỉ là lỗi kỹ thuật thô.

---

## 3. Yêu Cầu Giao Diện Chi Tiết Theo Assignment

### 3.1 Color Palette

Assignment có nêu rõ phần màu sắc giao diện. Từ tài liệu, có thể rút ra các yêu cầu sau:

1. Cần một bảng màu rõ ràng cho toàn ứng dụng.
2. Có màu chủ đạo cho button và điểm nhấn.
3. Có màu nền chính cho vùng nội dung.
4. Có màu riêng cho sidebar.
5. Có màu chữ riêng để đảm bảo độ tương phản.

Trong phần mô tả chi tiết của assignment, bảng màu mẫu được đưa ra là:

- Primary Color: #007BFF
- Secondary Color: #FFC107
- Background: #F8F9FA
- Sidebar: #2C2F33
- Text: #212529
- Sidebar Text: #FFFFFF

Ý nghĩa thiết kế của bảng màu này:

1. Dễ nhìn, có độ tương phản tốt.
2. Phân tách rõ sidebar và main area.
3. Làm nổi bật các thao tác chính như upload và hỏi đáp.
4. Phù hợp với giao diện web học thuật và công cụ AI.

### 3.2 Layout Structure

Assignment mô tả bố cục giao diện theo 2 vùng chính:

1. Sidebar bên trái.
2. Main Area ở trung tâm.

Yêu cầu chi tiết cho từng vùng:

#### Sidebar

Sidebar nên chứa:

1. Instructions section.
2. Settings information.
3. Model configuration display.

#### Main Area

Main area nên chứa:

1. Title và header.
2. File uploader.
3. Question input.
4. Answer display.

### 3.3 User Flow

Assignment đã mô tả luồng người dùng cơ bản như sau:

1. Landing: Người dùng mở ứng dụng và thấy giao diện chính với hướng dẫn.
2. Upload: Người dùng chọn và upload tài liệu PDF.
3. Processing: Hệ thống xử lý tài liệu và hiển thị tiến trình.
4. Query: Người dùng nhập câu hỏi.
5. Response: Hệ thống hiển thị câu trả lời.
6. Iterate: Người dùng có thể tiếp tục đặt thêm câu hỏi.

### 3.4 Features

Assignment yêu cầu giao diện phải hỗ trợ các tính năng sau:

#### File Upload

1. Hỗ trợ định dạng PDF.
2. Có drag-and-drop interface nếu khả thi.
3. Có kiểm tra kích thước file.
4. Có thông báo thành công và thất bại.

#### Question Answering

1. Nhập câu hỏi bằng ngôn ngữ tự nhiên.
2. Xử lý gần như real-time.
3. Hiển thị loading spinner khi đang suy luận.
4. Hiển thị câu trả lời rõ ràng.

#### Error Handling

1. Cảnh báo file sai định dạng.
2. Báo lỗi trong quá trình xử lý.
3. Báo lỗi khi model không phản hồi.
4. Thông báo dễ hiểu với người dùng cuối.

---

## 4. Yêu Cầu Giao Diện Suy Ra Từ Mô Tả Hệ Thống

Ngoài phần UI/UX mô tả trực tiếp, các phần khác trong assignment cũng ngầm yêu cầu một số chức năng giao diện:

### 4.1 Hiển thị tài liệu và trạng thái xử lý

Giao diện cần cho người dùng thấy:

1. File đang được chọn.
2. Trạng thái upload.
3. Trạng thái chunking.
4. Trạng thái tạo embedding.
5. Trạng thái truy xuất.
6. Trạng thái sinh câu trả lời.

### 4.2 Hiển thị kết quả truy xuất

Vì hệ thống dùng FAISS và RAG, giao diện nên có khả năng:

1. Hiển thị nội dung chunk liên quan.
2. Hiển thị citation hoặc nguồn nếu có.
3. Cho người dùng biết câu trả lời được tạo từ phần nào của tài liệu.

### 4.3 Hỗ trợ đọc và hiểu kết quả nhanh

Giao diện nên đảm bảo:

1. Câu trả lời ngắn gọn, dễ đọc.
2. Có phân tách rõ giữa câu hỏi và câu trả lời.
3. Có thể xem lại nội dung đã truy xuất.

---

## 5. Yêu Cầu Giao Diện Cho Bản Triển Khai Streamlit

Từ tài liệu công nghệ và cách thực hiện, giao diện Streamlit nên có:

1. File uploader ở vùng dễ thấy.
2. Ô nhập câu hỏi ở main area.
3. Vùng hiển thị kết quả trả lời.
4. Sidebar chứa hướng dẫn hoặc cấu hình.
5. Nút xử lý rõ ràng cho từng bước.
6. Spinner khi đang xử lý.
7. Message thành công/thất bại.

Khi triển khai đúng theo assignment, có thể dùng giao diện một trang, nhưng vẫn cần phân lớp nội dung rõ ràng:

1. Phần upload.
2. Phần hỏi đáp.
3. Phần kết quả.
4. Phần trạng thái.

---

## 6. Đặc Tả Nội Dung Từng Khu Vực Giao Diện

### 6.1 Header / Title

Nên có:

1. Tên project.
2. Mô tả ngắn về chức năng.
3. Một dòng giới thiệu giúp người dùng hiểu đây là hệ thống hỏi đáp tài liệu.

### 6.2 Sidebar

Sidebar nên chứa:

1. Hướng dẫn sử dụng ngắn gọn.
2. Cấu hình mô hình nếu cần.
3. Thông tin chunk size, overlap nếu người dùng chỉnh.
4. Trạng thái hoặc metadata tóm tắt.

### 6.3 Upload Area

Khu vực upload nên thể hiện:

1. Nút chọn file.
2. Gợi ý định dạng hỗ trợ.
3. Thông tin file đã chọn.
4. Thông báo file đã sẵn sàng để xử lý.

### 6.4 Question Input

Khu vực nhập câu hỏi nên có:

1. Input box rõ ràng.
2. Gợi ý ví dụ câu hỏi.
3. Nút gửi câu hỏi hoặc trigger hợp lý.

### 6.5 Answer Display

Khu vực hiển thị câu trả lời nên có:

1. Kết quả ngắn gọn.
2. Định dạng dễ nhìn.
3. Có thể hiển thị markdown nếu câu trả lời có cấu trúc.
4. Nếu có citation thì đặt ngay bên dưới câu trả lời.

### 6.6 Status / Feedback Area

Khu vực phản hồi trạng thái nên có:

1. Spinner.
2. Success message.
3. Warning message.
4. Error message.
5. Progress theo từng bước nếu có thể.

---

## 7. Các Yêu Cầu Giao Diện Nâng Cao Hợp Lý Từ Assignment

Phần này không phải yêu cầu bắt buộc ghi nguyên văn, nhưng là các yêu cầu hợp lý suy ra từ assignment và rất phù hợp để làm đồ án tốt hơn:

1. Cho phép xem lịch sử câu hỏi và câu trả lời trong sidebar.
2. Cho phép clear history khi cần.
3. Cho phép xem preview chunk đã truy xuất.
4. Cho phép chọn top-k retrieval.
5. Cho phép tinh chỉnh chunk size và overlap.
6. Cho phép hiển thị tài liệu nào đã được dùng.
7. Cho phép xem trạng thái ingest và index rõ ràng hơn.

---

## 8. Gợi Ý Giao Diện Thêm Theo Ý Tưởng Thiết Kế

Phần này là gợi ý thêm, không phải bắt buộc từ assignment.

### 8.1 Gợi ý về bố cục

1. Dùng layout 2 cột: sidebar và main content.
2. Tách rõ ba khối: upload, hỏi đáp, kết quả.
3. Dùng card hoặc panel để nhóm chức năng.

### 8.2 Gợi ý về trải nghiệm người dùng

1. Hiển thị placeholder cho ô câu hỏi.
2. Hiển thị ví dụ prompt ngắn.
3. Có trạng thái empty state khi chưa upload file.
4. Có thông báo rõ ràng khi chưa có index hoặc chưa có tài liệu.

### 8.3 Gợi ý về trực quan hóa

1. Hiển thị số lượng chunk đã tạo.
2. Hiển thị tên file hiện tại.
3. Hiển thị top-k chunks được truy xuất.
4. Hiển thị nguồn dùng để trả lời.

### 8.4 Gợi ý về phong cách thiết kế

1. Chọn phong cách tối giản, chuyên nghiệp.
2. Dùng màu xanh hoặc teal làm màu nhấn.
3. Giữ độ tương phản tốt cho sidebar và main area.
4. Tránh quá nhiều màu gây rối.

---

## 9. Kết Luận

Từ file assignment, có thể kết luận rằng giao diện của SmartDoc AI phải là một giao diện web thân thiện, triển khai bằng Streamlit, có các vùng chính sau:

1. Sidebar chứa hướng dẫn và thông tin cấu hình.
2. Main area chứa upload tài liệu, nhập câu hỏi và hiển thị câu trả lời.
3. Có trạng thái xử lý rõ ràng.
4. Có thông báo lỗi và success thân thiện.
5. Có thiết kế UI/UX với color palette và layout structure cụ thể.

Nếu triển khai theo đúng định hướng này, giao diện sẽ bám sát assignment và cũng đủ rõ ràng để phát triển tiếp các chức năng RAG nâng cao.