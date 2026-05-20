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

## Vì sau khi “embedding”, mỗi đoạn văn và câu hỏi đều được đổi thành vector để máy tính so sánh ý nghĩa giữa chúng.
 ## Vector có tác dụng:

biểu diễn nội dung dưới dạng số;
giúp tìm đoạn gần nghĩa nhất với câu hỏi;
làm retrieval nhanh và chính xác hơn so với chỉ tìm bằng từ khóa.

## Retrieval là bước tìm và lấy ra các đoạn tài liệu liên quan nhất với câu hỏi của người dùng.
Nói ngắn gọn:
Người dùng hỏi
Hệ thống đi tìm những chunk phù hợp nhất trong index
Lấy chúng ra làm ngữ cảnh để LLM trả lời

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

## BM25 là gì?

BM25 là một cách tìm kiếm theo từ khóa rất phổ biến. Nó chấm điểm các đoạn văn dựa trên việc từ trong câu hỏi xuất hiện nhiều hay ít trong tài liệu, rồi ưu tiên đoạn có khả năng liên quan cao hơn.

Hiểu đơn giản: BM25 giống như cách tra cứu bằng từ khóa thông minh hơn. Nó không hiểu nghĩa sâu như embedding, nhưng rất mạnh khi câu hỏi chứa đúng các từ quan trọng có trong tài liệu.

Trong SmartDoc AI, BM25 thường được dùng chung với vector search để tăng độ chính xác: một bên tìm theo ý nghĩa, một bên tìm theo từ khóa.

---

## Hybrid Retrieval là gì?

Hybrid Retrieval là cách kết hợp 2 kiểu tìm kiếm cùng lúc:
- Vector search: tìm theo ngữ nghĩa (ý nghĩa câu hỏi)
- BM25: tìm theo từ khóa xuất hiện thật trong tài liệu

Hiểu ngắn gọn: Hybrid = vừa hiểu ý, vừa bám từ khóa, nên thường trả về ngữ cảnh đúng hơn so với chỉ dùng một cách tìm kiếm.

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

## 9) query rewriting là gì?
- chuyển đổi/sửa câu hỏi người dùng (đặc biệt follow-up) thành một truy vấn độc lập, rõ ràng và đầy đủ ngữ cảnh 
- ví dụ: resolve đại từ, bổ sung thông tin từ lịch sử hội thoại, chuẩn hoá cú pháp. Mục đích: giúp bộ retriever/LLM hiểu đúng ý và tìm ngữ cảnh liên quan chính xác hơn.

## Embedding là cách biến một đoạn văn, câu hỏi hoặc từ thành vector số để máy tính hiểu và so sánh ý nghĩa của chúng.
- Embedding = “nội dung đã được mã hoá thành số”

## Metadata là thông tin mô tả đi kèm dữ liệu, như tên file, loại file, trang, nguồn, ngày upload, hoặc chunk thuộc tài liệu nào.
- Metadata = “thông tin nhãn đi kèm để quản lý và lọc”

## 9) pipeline ingest là gì?
- quy trình đưa tài liệu vào hệ thống tìm kiếm — gồm lưu file thô, tách thành chunk, enrich metadata, sinh embedding và lưu/ghi vào FAISS index. Mục đích: chuẩn hoá và tiền xử lý dữ liệu để retrieval nhanh, chính xác và có thể lọc theo nguồn/metadata.

