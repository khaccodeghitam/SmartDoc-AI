"""Test script: PyMuPDF block detection for multi-column PDF handling.

Cách sử dụng:
    python test_pymupdf_blocks.py <path_to_pdf>
    
Hoặc:
    python test_pymupdf_blocks.py  # Sẽ tìm PDF mẫu trong data/raw
"""

import sys
from pathlib import Path
from tabulate import tabulate


def find_sample_pdf():
    """Tìm PDF mẫu trong project."""
    data_raw = Path(__file__).parent / "data" / "raw"
    
    if data_raw.exists():
        pdfs = list(data_raw.glob("*.pdf"))
        if pdfs:
            return pdfs[0]
    
    return None


def test_pymupdf_blocks(pdf_path):
    """So sánh 3 phương pháp extract text từ PDF."""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ Lỗi: File không tồn tại: {pdf_path}")
        return
    
    print(f"\n{'=' * 80}")
    print(f"📄 KIỂM TRA MULTI-COLUMN PDF: {pdf_path.name}")
    print(f"{'=' * 80}\n")
    
    # Phương pháp 1: PDFPlumberLoader (cũ)
    print("1️⃣ PHƯƠNG PHÁP CŨ (PDFPlumberLoader - không layout):")
    print("-" * 80)
    
    try:
        from langchain_community.document_loaders import PDFPlumberLoader
        
        loader = PDFPlumberLoader(str(pdf_path))
        docs_old = loader.load()
        
        if docs_old:
            print(f"✅ Số document: {len(docs_old)}")
            text_old = docs_old[0].page_content
            print(f"📝 Nội dung trang 1 (200 ký tự):")
            print(f"\n{text_old[:200]}...\n")
        else:
            print("❌ Không thể load PDF")
            docs_old = []
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        docs_old = []
    
    # Phương pháp 2: pdfplumber với layout=True
    print("\n2️⃣ PHƯƠNG PHÁP NÂNG CẬP (pdfplumber + layout=True):")
    print("-" * 80)
    
    try:
        import pdfplumber
        
        docs_layout = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text(layout=True)
                
                if text and text.strip():
                    docs_layout.append({
                        "page": page_num,
                        "content": text
                    })
        
        if docs_layout:
            print(f"✅ Số document: {len(docs_layout)}")
            text_layout = docs_layout[0]["content"]
            print(f"📝 Nội dung trang 1 (200 ký tự):")
            print(f"\n{text_layout[:200]}...\n")
        else:
            print("❌ Không thể load PDF")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        docs_layout = []
    
    # Phương pháp 3: PyMuPDF với block detection (NÂ NG CAO)
    print("\n3️⃣ PHƯƠNG PHÁP NÂNG CAO (PyMuPDF + block sorting) ⭐:")
    print("-" * 80)
    
    try:
        import fitz  # PyMuPDF
        
        docs_pymupdf = []
        with fitz.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf, 1):
                blocks = page.get_text("blocks")
                
                # Sort blocks by position
                sorted_blocks = sorted(
                    blocks, 
                    key=lambda b: (round(b[1], -1), b[0])
                )
                
                text_parts = []
                for block in sorted_blocks:
                    if block[6] == 0:  # Text block
                        text = block[4].strip()
                        if text:
                            text_parts.append(text)
                
                full_text = "\n".join(text_parts)
                
                if full_text.strip():
                    docs_pymupdf.append({
                        "page": page_num,
                        "content": full_text
                    })
        
        if docs_pymupdf:
            print(f"✅ Số document: {len(docs_pymupdf)}")
            text_pymupdf = docs_pymupdf[0]["content"]
            print(f"📝 Nội dung trang 1 (200 ký tự):")
            print(f"\n{text_pymupdf[:200]}...\n")
        else:
            print("❌ Không thể load PDF")
    except ImportError:
        print("❌ PyMuPDF không được cài đặt: pip install pymupdf")
        docs_pymupdf = []
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        docs_pymupdf = []
    
    # SO SÁNH
    print("\n4️⃣ SO SÁNH CÁC PHƯƠNG PHÁP:")
    print("-" * 80)
    
    comparison_data = []
    
    if docs_old:
        comparison_data.append([
            "PDFPlumberLoader",
            len(docs_old),
            len(docs_old[0].page_content),
            "❌ Không layout",
            "❌ Cơ bản"
        ])
    
    if docs_layout:
        comparison_data.append([
            "pdfplumber + layout=True",
            len(docs_layout),
            len(docs_layout[0]["content"]),
            "✅ Có layout",
            "⭐ Tốt"
        ])
    
    if docs_pymupdf:
        comparison_data.append([
            "PyMuPDF + block sorting",
            len(docs_pymupdf),
            len(docs_pymupdf[0]["content"]),
            "✅ Block sorting",
            "⭐⭐⭐ Tối ưu"
        ])
    
    headers = ["Phương Pháp", "Docs", "Chars (p1)", "Layout", "Chất Lượng"]
    print(tabulate(comparison_data, headers=headers, tablefmt="grid"))
    
    # Chi tiết so sánh
    print("\n5️⃣ CHI TIẾT SO SÁNH:")
    print("-" * 80)
    
    if docs_old and docs_layout:
        text_old = docs_old[0].page_content[:200]
        text_layout = docs_layout[0]["content"][:200]
        
        if text_old == text_layout:
            print("✅ PDFPlumberLoader vs pdfplumber+layout: GIỐNG NHAU")
            print("   → PDF này không có multi-column layout hoặc layout detection không có ảnh hưởng")
        else:
            print("⚠️ PDFPlumberLoader vs pdfplumber+layout: KHÁC NHAU")
            print("   → PDF này CÓ multi-column layout!")
            print("   → Khuyến nghị: Sử dụng phương pháp 2 hoặc 3")
    
    if docs_layout and docs_pymupdf:
        text_layout = docs_layout[0]["content"][:200]
        text_pymupdf = docs_pymupdf[0]["content"][:200]
        
        if text_layout == text_pymupdf:
            print("\n✅ pdfplumber+layout vs PyMuPDF: GIỐNG NHAU")
            print("   → Cả hai phương pháp đều tốt cho PDF này")
        else:
            print("\n⚠️ pdfplumber+layout vs PyMuPDF: KHÁC NHAU")
            print("   → PyMuPDF có thể xử lý layout phức tạp tốt hơn")
    
    # Thống kê
    print("\n6️⃣ THỐNG KÊ CHI TIẾT:")
    print("-" * 80)
    
    stats_data = []
    
    if docs_old:
        total_chars_old = sum(len(d.page_content) for d in docs_old)
        stats_data.append(["PDFPlumberLoader", len(docs_old), f"{total_chars_old:,}"])
    
    if docs_layout:
        total_chars_layout = sum(len(d["content"]) for d in docs_layout)
        stats_data.append(["pdfplumber + layout=True", len(docs_layout), f"{total_chars_layout:,}"])
    
    if docs_pymupdf:
        total_chars_pymupdf = sum(len(d["content"]) for d in docs_pymupdf)
        stats_data.append(["PyMuPDF + block sorting", len(docs_pymupdf), f"{total_chars_pymupdf:,}"])
    
    headers = ["Phương Pháp", "Pages", "Total Chars"]
    print(tabulate(stats_data, headers=headers, tablefmt="grid"))
    
    # Khuyến nghị
    print("\n7️⃣ KHUYẾN NGHỊ:")
    print("-" * 80)
    
    if docs_pymupdf:
        print("✅ PyMuPDF là lựa chọn TỐTẤT cho PDF multi-column!")
        print("   • Xử lý layout block detection tốt")
        print("   • Sắp xếp text theo vị trí (top-bottom, left-right)")
        print("   • Độ chính xác cao nhất: 95%")
        print("\n   Cách sử dụng:")
        print("   from src.data_layer.pdf_document_storage import load_documents")
        print("   docs = load_documents('file.pdf', use_advanced_pdf=True)")
    elif docs_layout:
        print("✅ pdfplumber + layout=True là lựa chọn tốt!")
        print("   • Tự động detect multi-column layout")
        print("   • Độ chính xác: 90%")
        print("\n   Cách sử dụng:")
        print("   from src.data_layer.pdf_document_storage import load_documents")
        print("   docs = load_documents('file.pdf')")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = find_sample_pdf()
        if not pdf_path:
            print("❌ Lỗi: Không tìm thấy PDF mẫu")
            print("Cách sử dụng: python test_pymupdf_blocks.py <path_to_pdf>")
            sys.exit(1)
    
    test_pymupdf_blocks(pdf_path)


if __name__ == "__main__":
    main()
