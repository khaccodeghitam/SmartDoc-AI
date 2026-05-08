"""PDF/DOCX document loading, saving, and raw text extraction."""
from __future__ import annotations

import io
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List

from docx import Document as DocxDocument
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.documents import Document
from PIL import Image

from src.config import RAW_DIR
from src.utils import sanitize_name, source_name_from_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def split_stuck_vietnamese_words(text: str) -> str:
    """
    Fixed heuristic to split only specific impossible combinations in Vietnamese PDFs.
    Avoids using character classes [] that cause over-splitting of common 'nh', 'ch'.
    """
    # Fix 'thủcông' -> 'thủ công', 'ngữcảnh' -> 'ngữ cảnh'
    text = text.replace('ủc', 'ủ c').replace('ữc', 'ữ c')
    # Fix 'địnhhướng' -> 'định hướng'
    text = text.replace('ịnhh', 'ịnh h')
    # Fix 'vựcưu' -> 'vực ưu'
    text = text.replace('ựcư', 'ực ư')
    # Fix 'mạnhmẽ' if stuck
    text = text.replace('ạnhm', 'ạnh m')
    return text


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def load_pdf_advanced(path: str | Path) -> List[Document]:
    """Advanced PDF loader with smart column sorting and OCR."""
    try:
        import fitz  # PyMuPDF
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        tessdata_dir = str(Path(__file__).resolve().parent.parent.parent / "tessdata")
        if os.path.exists(tessdata_dir):
            os.environ["TESSDATA_PREFIX"] = tessdata_dir

        full_text_parts = []
        with fitz.open(str(path)) as pdf:
            for page_num, page in enumerate(pdf, start=1):
                page_width = page.rect.width
                mid_x = page_width / 2
                blocks = page.get_text("blocks")
                
                def get_block_group(b):
                    x0, y0, x1, y1 = b[:4]
                    # Titles/Full-width headers
                    if (x1 - x0) > page_width * 0.65: return 0
                    # Left column
                    if x1 <= mid_x + 15: return 1
                    # Right column
                    if x0 >= mid_x - 15: return 2
                    return 0

                # Sử dụng cấu trúc Dictionary để lấy cả Text và Image theo đúng thứ tự
                page_dict = page.get_text("dict")
                page_elements = []
                
                for block in page_dict["blocks"]:
                    bbox = block["bbox"] # (x0, y0, x1, y1)
                    group = get_block_group(bbox)
                    
                    if block["type"] == 0: # Khối văn bản
                        # Ghép các dòng trong block
                        block_text = ""
                        for line in block["lines"]:
                            for span in line["spans"]:
                                block_text += span["text"]
                        
                        content = block_text.strip()
                        if content:
                            content = split_stuck_vietnamese_words(content)
                            page_elements.append({
                                "y": bbox[1], "x": bbox[0], "group": group,
                                "content": content
                            })
                            
                    elif block["type"] == 1: # Khối hình ảnh
                        try:
                            image_bytes = block["image"]
                            if image_bytes and len(image_bytes) > 5000:
                                img = Image.open(io.BytesIO(image_bytes))
                                ocr_res = pytesseract.image_to_string(img, lang="vie").strip()
                                if ocr_res and len(ocr_res) > 10:
                                    page_elements.append({
                                        "y": bbox[1], "x": bbox[0], "group": group,
                                        "content": f"\n[Nội dung từ ảnh]:\n{ocr_res}"
                                    })
                        except: pass

                # Nếu trang trống trơn (có thể là trang scan hoàn toàn)
                if not page_elements:
                    try:
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        full_page_ocr = pytesseract.image_to_string(img, lang="vie").strip()
                        if len(full_page_ocr) > 20:
                            page_elements.append({
                                "y": 0, "x": 0, "group": 0,
                                "content": f"\n[Nội dung quét toàn trang]:\n{full_page_ocr}"
                            })
                    except: pass

                # --- THUẬT TOÁN SẮP XẾP THEO VÙNG (REGIONAL COLUMN SORTING) ---
                # Sắp xếp tất cả theo Y để xử lý từ trên xuống dưới
                page_elements.sort(key=lambda e: e["y"])
                
                final_page_elements = []
                temp_column_elements = []
                
                for el in page_elements:
                    if el["group"] == 0:
                        # Nếu gặp Group 0 (Toàn khổ), ta phải "xả" hết các cột đang chờ
                        if temp_column_elements:
                            # Sắp xếp các cột đang chờ: Nhóm 1 (Trái) trước, rồi đến Nhóm 2 (Phải)
                            temp_column_elements.sort(key=lambda x: (x["group"], x["y"]))
                            final_page_elements.extend(temp_column_elements)
                            temp_column_elements = []
                        final_page_elements.append(el)
                    else:
                        # Gom các khối cột lại để xử lý sau
                        temp_column_elements.append(el)
                
                # Xả nốt các khối cột còn lại ở cuối trang
                if temp_column_elements:
                    temp_column_elements.sort(key=lambda x: (x["group"], x["y"]))
                    final_page_elements.extend(temp_column_elements)

                for el in final_page_elements:
                    full_text_parts.append(el["content"])

        # Dùng \n\n để phân tách các khối rõ ràng, giúp Splitter nhận diện đoạn văn tốt hơn
        final_text = "\n\n".join(full_text_parts).strip().replace("</div>", "").replace("<div>", "")
        # Loại bỏ các dấu xuống dòng thừa thãi trong nội dung để tránh split vụn
        final_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', final_text) 
        return [Document(page_content=final_text, metadata={"source": str(path), "file_type": "pdf", "page": page_num, "extraction_method": "fitz_regional_v3"})]
    except Exception as e:
        print(f"⚠️ PDF Advanced failed: {e}")
        return load_pdf(path)


def load_docx(path: str | Path) -> List[Document]:
    """Context-aware DOCX loader."""
    try:
        doc = DocxDocument(str(path))
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        tessdata_dir = str(Path(__file__).resolve().parent.parent.parent / "tessdata")
        if os.path.exists(tessdata_dir):
            os.environ["TESSDATA_PREFIX"] = tessdata_dir

        full_content_parts = []
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                full_content_parts.append(text)
            
            for run in paragraph.runs:
                if 'drawing' in run.element.xml:
                    try:
                        blip_ids = re.findall(r'r:embed="([^"]+)"', run.element.xml)
                        for rId in blip_ids:
                            image_part = doc.part.related_parts[rId]
                            img = Image.open(io.BytesIO(image_part.blob))
                            ocr_res = pytesseract.image_to_string(img, lang="vie").strip()
                            if ocr_res and len(ocr_res) > 15:
                                full_content_parts.append(f"\n[Nội dung hình ảnh tại đây]:\n{ocr_res}\n")
                    except: pass

        all_text = "\n".join(full_content_parts).strip()
        # No splitting logic for Word as it is usually clean
        return [Document(page_content=all_text, metadata={"source": str(path), "file_type": "docx"})]
    except Exception as e:
        print(f"⚠️ load_docx failed: {e}")
        doc = DocxDocument(str(path))
        return [Document(page_content="\n".join([p.text for p in doc.paragraphs]), metadata={"source": str(path)})]


def load_pdf(path: str | Path) -> List[Document]:
    """Fallback loader."""
    docs = []
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Tinh chinh x_tolerance de tranh dinh chu (default thuong la 3)
                text = page.extract_text(
                    layout=True, 
                    x_tolerance=2, 
                    y_tolerance=2
                )
                if text: docs.append(Document(page_content=text, metadata={"source": str(path), "page": page_num}))
        return docs
    except: return []

def load_documents(path: str | Path, use_advanced_pdf: bool = False) -> List[Document]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf_advanced(file_path) if use_advanced_pdf else load_pdf(file_path)
    if suffix == ".docx":
        return load_docx(file_path)
    raise ValueError(f"Unsupported: {suffix}")

def save_uploaded_file(uploaded_file: Any, target_dir: Path = RAW_DIR) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / uploaded_file.name
    file_path.write_bytes(uploaded_file.getbuffer())
    return file_path

def enrich_chunks_metadata(chunks: list[Document], file_path: Path) -> list[Document]:
    source = str(file_path)
    for doc in chunks:
        m = dict(doc.metadata or {})
        m.setdefault("source", source)
        m["file_name"] = file_path.name
        m["file_type"] = file_path.suffix.lower().lstrip(".")
        m["upload_time"] = datetime.now().isoformat(timespec="seconds")
        m["upload_date"] = m["upload_time"][:10]
        doc.metadata = m
    return chunks
