# Huong dan chay project SmartDoc AI (Windows)

Tai lieu nay huong dan cac buoc chay du an tu dau den cuoi trong thu muc project hien tai.

## 1. Mo terminal tai dung thu muc project

Mo PowerShell va di chuyen vao thu muc du an:

```powershell
cd "D:\sinh vien\OSSD\project"
```

## 2. Kich hoat moi truong ao Python

```powershell
.\.venv\Scripts\Activate.ps1
```

Neu thay tien to `(.venv)` o dau dong lenh thi da kich hoat thanh cong.

## 3. Cai dependencies (neu chua cai)

```powershell
pip install -r requirements.txt
```

## 4. Cai va kiem tra Ollama

### 4.1 Kiem tra lenh Ollama

```powershell
ollama --version
```

Neu bao loi khong nhan lenh, can cai Ollama cho Windows tai:
- https://ollama.com/download/windows

Sau khi cai xong, dong mo lai terminal roi chay lai lenh tren.

### 4.2 Tai model

Co 3 lua chon model tuy theo kha nang may tinh:

**Tuy chon 1: Model chat luong cao (neu may manh)**
```powershell
ollama pull qwen2.5:7b
```

**Tuy chon 2: Model nhon vua phu (khuyen nghi cho phan lon may)**
```powershell
ollama pull qwen2.5:3b
```

**Tuy chon 3: Model nhe va nhanh - cai ca 3 model (khuyen nghi cho may yeu)**
```powershell
ollama pull qwen2.5:3b
ollama pull qwen2.5:1.5b
ollama pull qwen2.5:0.5b
```

### 4.3 Chon model de chay ung dung

Sau khi cai Ollama model, can cap nhat file `src/config.py` de chon model chay:

1. Mo file `src/config.py`
2. Tim dong: `OLLAMA_MODEL = ...`
3. Thay bang model muon chay:
   - `qwen2.5:7b` - chat luong cao, toc do chap
   - `qwen2.5:3b` - can bang, khuyen nghi
   - `qwen2.5:1.5b` - nhe va nhanh
   - `qwen2.5:0.5b` - toi gian, chi test

**Vi du:**
```python
OLLAMA_MODEL = "qwen2.5:3b"  # Chang day neu dung model 3b
FALLBACK_MODELS = ["qwen2.5:1.5b", "qwen2.5:0.5b"]  # Cac model du phong neu model chinh thua
```

## 5. Chay ung dung Streamlit

Khuyen nghi chay theo cach nay de dam bao dung Python trong .venv:

```powershell
python -m streamlit run app.py
```

Sau do mo trinh duyet theo URL hien thi trong terminal, thuong la:
- http://localhost:8501

Neu cong 8501 dang ban, Streamlit se tu dong chay cong khac (vi du 8502, 8503).

## 6. Luong su dung trong giao dien

1. Vao tab Upload & Index.
2. Chon file PDF hoac DOCX.
3. Dieu chinh chunk size, chunk overlap neu can.
4. Bam Ingest va tao FAISS index.
5. Vao tab Retrieval Demo de test tim top-k chunks.
6. Vao tab Q&A voi LLM de hoi dap va xem citation/source tracking.
7. Xem lich su chat trong sidebar va tab lich su.

## 7. Loi thuong gap va cach xu ly

### Loi 1: ModuleNotFoundError: No module named app

Da duoc xu ly trong code. Neu con gap lai:
1. Chac chan dang o dung thu muc project.
2. Chay bang lenh:

```powershell
python -m streamlit run app.py
```

### Loi 2: ollama khong duoc nhan lenh

1. Cai lai Ollama.
2. Dong va mo lai PowerShell.
3. Kiem tra `ollama --version`.

### Loi 3: Khong thoat duoc moi truong ao

Lenh dung la:

```powershell
deactivate
```

Ban da go sai neu dung `deactive`.

## 8. Lenh tong hop nhanh

**Cai dat day du (neu cai 7b):**
```powershell
cd "D:\sinh vien\OSSD\project"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen2.5:7b
python -m streamlit run app.py
```

**Cai dat nhe (khuyen nghi):**
```powershell
cd "D:\sinh vien\OSSD\project"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen2.5:3b
python -m streamlit run app.py
```

**Cai dat toi gian - cai ca 3 model cho may yeu:**
```powershell
cd "D:\sinh vien\OSSD\project"
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen2.5:3b
ollama pull qwen2.5:1.5b
ollama pull qwen2.5:0.5b
python -m streamlit run app.py
```

> **Luu y:** Sau khi cai model, hay cap nhat `src/config.py` de chon model chinh va model du phong (xem phan 4.3).
