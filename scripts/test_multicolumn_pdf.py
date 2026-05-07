"""Test script: Kiểm tra khả năng xử lý PDF multi-column layout.

Cách sử dụng:
    python test_multicolumn_pdf.py <path_to_pdf>
    
Hoặc:
    python test_multicolumn_pdf.py  # Sẽ tìm PDF mẫu trong data/raw
"""

import sys
from pathlib import Path
import pdfplumber
from langchain_community.document_loaders import PDFPlumberLoader


def find_sample_pdf():
    """Tìm PDF mẫu trong project."""
    data_raw = Path(__file__).parent / "data" / "raw"
    
    if data_raw.exists():
        pdfs = list(data_raw.glob("*.pdf"))
        if pdfs:
            return pdfs[0]
    
    return None


def test_pdf_extraction(pdf_path):
    """So sánh 2 cách extract text từ PDF."""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ Lỗi: File không tồn tại: {pdf_path}")
        return
    
    print(f"\n📄 Kiểm tra PDF: {pdf_path.name}")
    print("=" * 70)
    
    # Cách 1: PDFPlumberLoader (hiện tại)
    print("\n1️⃣ CÁC HIỆN TẠI (PDFPlumberLoader - không layout):")
    print("-" * 70)
    
    loader = PDFPlumberLoader(str(pdf_path))
    docs_current = loader.load()
    
    if docs_current:
        print(f"✅ Số document: {len(docs_current)}")
        print(f"📝 Nội dung trang 1 (150 ký tự đầu):")
        print(f"\n{docs_current[0].page_content[:150]}...\n")
    
    # Cách 2: pdfplumber với layout=True (được đề xuất)
    print("\n2️⃣ CÁC ĐƯỢC ĐỀ XUẤT (pdfplumber + layout=True):")
    print("-" * 70)
    
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
        print(f"📝 Nội dung trang 1 (150 ký tự đầu):")
        print(f"\n{docs_layout[0]['content'][:150]}...\n")
    
    # So sánh
    print("\n3️⃣ SO SÁNH:")
    print("-" * 70)
    
    if docs_current and docs_layout:
        current_text = docs_current[0].page_content[:200]
        layout_text = docs_layout[0]["content"][:200]
        
        if current_text == layout_text:
            print("✅ GIỐNG NHAU - PDF này không có multi-column layout")
            print("   (Hoặc layout detection không có ảnh hưởng)")
        else:
            print("⚠️ KHÁC NHAU - PDF này CÓ multi-column layout!")
            print("   📊 Khuyến nghị: Sử dụng phương án 2️⃣ (layout=True)")
            print("\n💡 Ảnh hưởng:")
            print("   - RAG sẽ lấy context SAI")
            print("   - Embedding vector sẽ encode text KHÔNG CHÍNH XÁC")
            print("   - LLM trả lời sẽ KHÔNG ĐÚNG")
    
    # Thống kê
    print("\n4️⃣ THỐNG KÊ:")
    print("-" * 70)
    
    if docs_current:
        total_chars_current = sum(len(d.page_content) for d in docs_current)
        print(f"PDFPlumberLoader (hiện tại): {total_chars_current:,} ký tự")
    
    if docs_layout:
        total_chars_layout = sum(len(d["content"]) for d in docs_layout)
        print(f"pdfplumber + layout=True:    {total_chars_layout:,} ký tự")
    
    if docs_current and docs_layout:
        diff = abs(len(docs_current[0].page_content) - len(docs_layout[0]["content"]))
        if diff > 0:
            print(f"\n⚠️ Chênh lệch nội dung trang 1: {diff} ký tự")
    
    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = find_sample_pdf()
        if not pdf_path:
            print("❌ Lỗi: Không tìm thấy PDF mẫu")
            print("Cách sử dụng: python test_multicolumn_pdf.py <path_to_pdf>")
            sys.exit(1)
    
    test_pdf_extraction(pdf_path)


if __name__ == "__main__":
    main()
