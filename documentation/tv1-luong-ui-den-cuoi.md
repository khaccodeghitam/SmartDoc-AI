# Luong cong viec TV1 - Tuan Tai (Updated: Self-RAG & Advanced Processing)

## 1) Muc tieu va Trach nhiem

TV1 chiu trach nhiem chinh cho toan bo pipeline "Dau vao" va "Danh gia dau ra", bao gom:
- **Core #1 & #2:** Xu ly tai lieu PDF (ho tro layout 2 cot phuc tap) va Chunking.
- **Phat trien #1:** Ho tro dinh dang DOCX.
- **Phat trien #3:** Co che xoa du lieu tam va reset he thong.
- **Phat trien #10:** Advanced RAG / Self-RAG (AI tu danh gia do tu tin).

---

## 2) Danh sach cac ham/module quan trong

1. `load_pdf`: Su dung `PDFPlumber` de phan tich layout 2 cot, dam bao thu tu doc chinh xac.
2. `load_docx`: Trich xuat van ban tu file Word qua `Docx2txtLoader`.
3. `ingest_document`: Dieu phoi toan bo luong tu load -> OCR (TV5) -> chunking -> metadata.
4. `self_rag_confidence_score`: (Diem nhan) LLM tu danh gia cau tra loi va tinh diem tu tin (1-10).
5. `clear_vector_store_data`: Don dep index FAISS va cache file.

---

## 3) Chi tiet cac Luong xu ly chinh

### 3.1 Luong Ingest & Xu ly PDF 2 cot
Khi user upload file, `load_pdf` trong `src/data_layer/pdf_document_storage.py` se:
- Phan tich cau truc trang.
- Neu trang co layout 2 cot, he thong se trich xuat theo vung (region-based) de tranh viec cac dong bi dinh vao nhau giua 2 cot.
- **OCR Integration:** Neu phat hien block anh hoac trang quet, he thong goi den module OCR (TV5) de lay van ban.

### 3.2 Luong Ho tro DOCX (Phat trien #1)
- Module `load_docx` dam bao trich xuat dong nhat voi PDF de dua vao pipeline chunking chung.

### 3.3 Luong Clear History & Store (Phat trien #3)
- Tai UI, khi bam "Clear All", `streamlit_app.py` goi `clear_vector_store_data`.
- Luong: Xoa file trong `data/raw/` -> Xoa thu muc FAISS index -> Reset `st.session_state`.

### 3.4 Luong Self-RAG & Confidence Scoring (Phat trien #10)
Day la phan quan trong nhat cua TV1 de dat diem cao:
1. **Answer Generation:** AI sinh cau tra loi.
2. **Self-Assessment:** AI goi them 1 luot (Model 0.5B) de so sanh cau tra loi voi ngu canh (Context).
3. **Hybrid Scoring:** Ket hop diem tu AI va diem Heuristic (Keyword overlap) de ra con so cuoi cung (x/10).
4. **Co-RAG Early Exit:** Trong luong Co-RAG, TV1 trien khai thuat toan kiem tra tu khoa de ngat som vong lap neu da du thong tin, giup tang toc 300%.

---

## 4) Trace tham so end-to-end (TV1 perspective)

### Case: User hoi mot cau kho ve anh/bang bieu trong PDF 2 cot
1. `streamlit_app.py` -> Nhap cau hoi.
2. `CoRAGChainManager.ask(...)` (TV1/TV4) -> Truy xuat vong 1.
3. `search_similar_chunks` (TV2/TV3) -> Tra ve cac doan van ban tu PDF 2 cot (da duoc `load_pdf` cua TV1 xu ly dung thu tu).
4. `is_explicit_sufficient_signal` (TV1) -> Kiem tra tu khoa de quyet dinh co chay tiep vong 2 hay khong.
5. `self_rag_confidence_score` (TV1) -> Cham diem cuoi cung truoc khi hien thi cho User.

---

## 5) Ket luan
TV1 nam giu "Dau" va "Cuoi" cua pipeline. Viec toi uu hoa cach doc file (PDF 2 cot) va cach danh gia (Self-RAG) la yeu to then chot giup SmartDoc AI tro nen thong minh va chuyen nghiep hon cac he thong RAG thong thuong.
