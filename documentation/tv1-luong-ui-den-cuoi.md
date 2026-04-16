# TV1 - Luồng theo đúng thứ tự gọi hàm (UI -> Backend -> UI)

## 1) Mục tiêu tài liệu

Tài liệu này sắp xếp lại toàn bộ TV1 theo đúng thứ tự thực thi từ trên xuống dưới:

- Bắt đầu ở UI trong main.
- Đi vào hàm được gọi đầu tiên.
- Từ bên trong hàm đó đi tiếp sang các hàm con theo đúng call-chain.
- Quay lại main để hoàn tất cập nhật trạng thái.

Đồng thời, tài liệu cũng kiểm tra đủ 4 chức năng TV1 theo file phân công và bổ sung các hàm mắt xích bắt buộc.

---

## 2) Danh sách hàm TV1 cần có (đối chiếu file phân công)

### 2.1 Bốn chức năng TV1

1. save_uploaded_file
2. ingest_document
3. load_docx (qua load_documents)
4. clear_vector_store_data

### 2.2 Các hàm mắt xích bắt buộc trong luồng ingest

1. ingest_multiple_uploaded_files
2. \_enrich_chunks_metadata
3. build_and_save_faiss_index

Kết luận đối chiếu: tài liệu này đã bao gồm đầy đủ cả 4 chức năng TV1 và 3 hàm mắt xích bắt buộc.

---

## 3) Luồng chính số 1: Ingest từ UI đến tạo FAISS

## Bước 1 - UI nhận input trong main

Nguồn tham số từ giao diện:

'file main.py dòng 314'

- uploaded_files: từ st.file_uploader(type=["pdf", "docx"], accept_multiple_files=True)
- chunk_size: từ st.number_input("Chunk size", ...)
- chunk_overlap: từ st.number_input("Chunk overlap", ...)

Ý nghĩa:

- accept_multiple_files=True cho phép ingest nhiều file trong một lần bấm nút.

Khi người dùng bấm nút Ingest và tạo FAISS index, main bắt đầu call-chain backend.

---

## Bước 2 - main gọi ingest_multiple_uploaded_files

Hàm được gọi:

- ingest_multiple_uploaded_files(uploaded_files, int(chunk_size), int(chunk_overlap))

Vai trò:

- Điều phối ingest theo lô nhiều file.
- Gọi các hàm con bên trong theo thứ tự.

Giá trị trả về:

- ingest_result (kiểu IngestResult), gồm:
  - raw_docs_count
  - chunks_count
  - chunks

Nơi nhận giá trị trả về:

- Nhận trong main để truyền ingest_result.chunks sang bước build FAISS.

---

## Bước 3 - bên trong ingest_multiple_uploaded_files gọi save_uploaded_file (mỗi file) trong file rag_pipeline dòng 163

Hàm được gọi:

- save_uploaded_file(uploaded_file, target_dir=RAW_DIR)

Vai trò:

- Lưu file upload từ bộ đệm Streamlit xuống data/raw.

Giá trị trả về:

- file_path (Path vật lý của file vừa lưu).

Nơi nhận giá trị trả về:

- Trở lại ingest_multiple_uploaded_files.
- file_path được dùng ngay để gọi ingest_document(file_path, chunk_size, chunk_overlap).

---

## Bước 4 - bên trong ingest_multiple_uploaded_files gọi ingest_document

Hàm được gọi:

- ingest_document(file_path, chunk_size, chunk_overlap)

Vai trò:

- Đọc tài liệu, tách chunk, enrich metadata.

Giá trị trả về:

- result (IngestResult cho từng file).

Nơi nhận giá trị trả về:

- ingest_multiple_uploaded_files nhận result.
- total_raw_docs cộng dồn bằng result.raw_docs_count.
- all_chunks nối phẳng bằng all_chunks.extend(result.chunks).

---

## Bước 5 - bên trong ingest_document gọi load_documents

Hàm được gọi:

- load_documents(path_obj)

Vai trò:

- Điều phối loader theo phần mở rộng file.

Nhánh gọi tiếp theo bên trong load_documents:

- Nếu .pdf -> load_pdf(path)
- Nếu .docx -> load_docx(path)
- Nếu không hỗ trợ -> raise ValueError("Unsupported file type")

Giá trị trả về:

- raw_docs (List[Document])

Nơi nhận giá trị trả về:

- ingest_document nhận raw_docs để đưa vào splitter.

---

## Bước 6 - trong ingest_document: chunking

Thao tác chính:

- Tạo RecursiveCharacterTextSplitter(chunk_size, chunk_overlap)
- Gọi split_documents(raw_docs)

Kết quả trung gian:

- chunks (danh sách đoạn văn bản đã cắt)

Nơi dùng tiếp:

- chunks được chuyển vào \_enrich_chunks_metadata(chunks, path_obj).

---

## Bước 7 - trong ingest_document gọi \_enrich_chunks_metadata

Hàm được gọi:

- \_enrich_chunks_metadata(chunks, file_path)

Vai trò:

- Chuẩn hóa metadata cho từng chunk:
  - source
  - file_name
  - file_type
  - upload_time
  - upload_date

Hàm con được gọi bên trong:

- \_file_type_from_path
- \_upload_time_from_path
- \_source_name_from_path

Giá trị trả về:

- chunks đã enrich metadata

Nơi nhận giá trị trả về:

- ingest_document nhận lại chunks đã enrich.
- ingest_document trả IngestResult về ingest_multiple_uploaded_files.

---

## Bước 8 - ingest_multiple_uploaded_files trả kết quả tổng về main

Sau khi lặp hết file:

- Trả IngestResult tổng hợp của cả batch file.

Nơi nhận:

- main nhận vào biến ingest_result.

Dữ liệu quan trọng chuyển tiếp:

- ingest_result.chunks được dùng để build FAISS ở bước kế tiếp.

---

## Bước 9 - main gọi build_and_save_faiss_index

Hàm được gọi:

- build_and_save_faiss_index(chunks=ingest_result.chunks, source_name=idx_name)

Vai trò:

- Tạo vector store FAISS từ chunks.
- Lưu index vào data/index/<index_name>.

Hàm/thao tác bên trong:

- \_build_embedder()
- FAISS.from_documents(chunks, embedder)
- vector_store.save_local(index_dir)

Giá trị trả về:

- index_result (IndexBuildResult):
  - index_name
  - index_dir
  - chunks_count

Nơi nhận giá trị trả về:

- main nhận index_result.

---

## Bước 10 - main cập nhật session_state và render lại UI

main dùng ingest_result + index_result để:

- Cập nhật last_index_dir, last_index_name, last_uploaded_file.
- Cập nhật last_chunks.
- Cập nhật danh sách filter sidebar theo metadata.
- Ghi ingest_notice.
- Gọi st.rerun().

Kết quả người dùng nhìn thấy:

- Thông báo ingest thành công.
- Có thể lọc theo nguồn, loại file, ngày upload.
- Tab Retrieval/Q&A dùng được index vừa tạo.

---

## 4) Luồng chính số 2: Xóa dữ liệu tạm (chức năng TV1 thứ 4)

Đây là nhánh riêng của TV1, không nằm trong call-chain ingest ở trên.

## Bước 1 - UI clear trong main

Người dùng bấm nút Clear Vector Store + trạng thái ở sidebar.

## Bước 2 - main gọi clear_vector_store_data

Hàm được gọi:

- clear_vector_store_data(index_root=INDEX_DIR, raw_root=RAW_DIR)

Vai trò:

- Xóa thư mục con trong data/index.
- Xóa thư mục con trong data/raw.

Giá trị trả về:

- dict có số lượng đã xóa:
  - index_deleted
  - raw_deleted

Nơi nhận giá trị trả về:

- main nhận clear_result.
- main hiển thị thông báo và reset lại session_state liên quan.

---

## 5) Bảng tóm tắt theo đúng thứ tự gọi

1. UI main nhận uploaded_files, chunk_size, chunk_overlap
2. main -> ingest_multiple_uploaded_files
3. ingest_multiple_uploaded_files -> save_uploaded_file
4. ingest_multiple_uploaded_files -> ingest_document
5. ingest_document -> load_documents
6. load_documents -> load_pdf hoặc load_docx
7. ingest_document -> split_documents (chunking)
8. ingest_document -> \_enrich_chunks_metadata
9. ingest_multiple_uploaded_files -> trả ingest_result về main
10. main -> build_and_save_faiss_index
11. build_and_save_faiss_index -> trả index_result về main
12. main cập nhật session_state + rerun

Nhánh riêng chức năng TV1: 13. UI clear -> main -> clear_vector_store_data -> trả clear_result -> main reset state

---

## 6) Ghi chú append và extend trong đúng luồng

Trong ingest_multiple_uploaded_files:

- file_paths.append(file_path): thêm 1 phần tử Path vào list.
- all_chunks.extend(result.chunks): nối toàn bộ chunk vào list phẳng.

Vì sao dùng extend:

- Để giữ kiểu dữ liệu all_chunks là List[Document] (không bị lồng list).

---

## 7) Kết luận

Tài liệu đã được sắp lại đúng yêu cầu theo thứ tự gọi từ UI xuống các hàm con bên trong.

Đồng thời đã kiểm tra và bao phủ đủ các hàm chức năng TV1 theo file phân công:

- save_uploaded_file
- ingest_document
- load_docx (qua load_documents)
- clear_vector_store_data

Và có thêm đầy đủ các hàm mắt xích bắt buộc của luồng ingest:

- ingest_multiple_uploaded_files
- \_enrich_chunks_metadata
- build_and_save_faiss_index
