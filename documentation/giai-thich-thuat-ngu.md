# Giải thích thuật ngữ trong SmartDoc AI

Tại màn hình upload, bạn thấy dòng:

"Tải file lên, sau đó chunking và build FAISS index thật"

Nói đơn giản, hệ thống đang làm 3 việc lớn:

1. Lưu file bạn vừa upload vào kho dữ liệu
2. Cắt nội dung thành các đoạn nhỏ để dễ tìm kiếm
3. Tạo bộ chỉ mục để tìm nhanh các đoạn liên quan khi bạn đặt câu hỏi

---

## 1) Chunking là gì?

Chunking = chia nội dung tài liệu thành nhiều "mảnh" nhỏ (gọi là chunk).

Ví dụ một file PDF có 100 trang, thay vì coi nó là 1 khối lớn, hệ thống cắt thành nhiều đoạn ngắn (mỗi đoạn vài trăm ký tự và có thể chồng lên nhau một ít).

### Vì sao phải tách chunk?

- Mô hình AI không nên đọc một lần quá dài
- Tìm kiếm sẽ chính xác hơn (tìm đúng đoạn liên quan, không bị loãng)
- Trả lời nhanh hơn vì chỉ xử lý các đoạn cần thiết
- Giữ được ngữ cảnh nhờ overlap (chồng lấn), tránh mất ý ở ranh giới 2 đoạn

Hiểu nhanh: Chunking giống như cắt sách thành nhiều thẻ ghi chú nhỏ để tra cứu nhanh.

---

## 2) Ingest là gì?

Ingest = bước "nạp" tài liệu vào hệ thống để sẵn sàng cho hỏi đáp.

Thường bao gồm:

1. Nhận file upload
2. Đọc nội dung text từ file (PDF, DOCX...)
3. Chunking (tách đoạn)
4. Chuyển mỗi chunk thành vector số học (embedding)
5. Lưu vào bộ chỉ mục tìm kiếm (FAISS)

Sau khi ingest xong, tài liệu mới thật sự "vào hệ thống" và có thể được hỏi đáp.

---

## 3) FAISS index là gì?

FAISS là thư viện giúp tìm kiếm vector rất nhanh (do Facebook AI Research phát triển).

- Mỗi chunk sau khi được embedding sẽ thành 1 vector (dãy số)
- FAISS index là cấu trúc dữ liệu lưu các vector này để tìm "gần nhất" rất nhanh
- Khi bạn hỏi, câu hỏi cũng được đổi thành vector
- Hệ thống tìm trong index những chunk có vector gần câu hỏi nhất

Hiểu nhanh: FAISS index giống "mục lục thông minh" của thư viện.
Không đọc lại toàn bộ sách, chỉ nhảy đến đúng vài đoạn khả năng cao là liên quan.

---

## 4) Lưu trữ và truy xuất bằng vector database là gì?

Nói dễ hiểu, đây là cách hệ thống "ghi nhớ" nội dung tài liệu và tìm lại phần liên quan khi bạn đặt câu hỏi.

- Mỗi đoạn văn trong tài liệu được biến thành một vector, tức là một dãy số thể hiện ý nghĩa của đoạn đó.
- Các vector này được lưu vào FAISS index, giống như cất từng đoạn vào một kho tìm kiếm đặc biệt.
- Khi người dùng nhập câu hỏi, câu hỏi cũng được đổi thành vector.
- Hệ thống sẽ so sánh vector của câu hỏi với các vector đã lưu để tìm ra những đoạn giống nhất về mặt ý nghĩa.

### Similarity search là gì?

Similarity search là bước tìm các đoạn có độ tương đồng cao nhất với câu hỏi.

Ví dụ, nếu bạn hỏi "tài liệu nói về FAISS là gì?", hệ thống không đọc toàn bộ file từ đầu đến cuối, mà chỉ tìm những đoạn có nội dung gần nhất với câu hỏi đó.

### Top-k đoạn liên quan là gì?

Top-k nghĩa là lấy ra `k` đoạn phù hợp nhất.

- Nếu `k = 3`, hệ thống sẽ lấy 3 đoạn liên quan nhất.
- Các đoạn này được đưa cho LLM làm ngữ cảnh để trả lời chính xác hơn.

Hiểu ngắn gọn: lưu vào vector database để tìm nhanh đúng đoạn, thay vì phải dò thủ công trong cả tài liệu.

---

## 5) Build FAISS index là gì?

Build FAISS index = tạo/cập nhật bộ chỉ mục FAISS từ các chunk vừa tách.

Trong app của bạn, thông điệp cho biết:

- File được lưu vào data/raw
- Tách chunk bằng RecursiveCharacterTextSplitter
- Lưu chung vào một FAISS index tại data/index

Nghĩa là mỗi lần bạn nạp file mới, hệ thống sẽ đưa nội dung file đó vào "kho tìm kiếm" chung để lần sau hỏi đáp nhanh và đúng tài liệu.

---

## 6) Luồng xử lý đầy đủ (dễ nhớ)

Upload file -> Ingest -> Chunking -> Embedding -> Build/Update FAISS index -> Hỏi câu hỏi -> Tìm chunk liên quan -> LLM trả lời

---

## 7) Ví dụ dễ hiểu

Bạn có file chapter2.pdf.

- Nếu không chunking: hệ thống phải vất vả với một khối text lớn
- Nếu có chunking + FAISS:
  - Cắt chapter2 thành đoạn nhỏ
  - Lưu vector từng đoạn vào index
  - Lúc bạn hỏi "Bài tập 3 nói về gì?"
  - Hệ thống tìm nhanh đúng vài chunk chứa bài tập 3
  - Gửi đúng ngữ cảnh đó cho LLM để trả lời chính xác hơn

---

## 8) Tóm tắt 1 câu mỗi thuật ngữ

- Chunking: Chia tài liệu lớn thành đoạn nhỏ để dễ xử lý và tìm kiếm.
- Ingest: Nạp tài liệu vào hệ thống qua các bước đọc -> cắt -> vector hóa -> lưu.
- FAISS index: Bộ chỉ mục vector để tìm đoạn liên quan cực nhanh.
- Build FAISS index: Quá trình tạo/cập nhật bộ chỉ mục FAISS từ dữ liệu vừa nạp.
