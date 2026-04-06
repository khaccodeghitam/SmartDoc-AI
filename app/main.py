import streamlit as st

from app.config import APP_TITLE


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📄", layout="wide")
    st.title(APP_TITLE)
    st.caption("Khởi tạo môi trường ban đầu cho SmartDoc AI")

    st.sidebar.header("Cấu hình")
    uploaded_file = st.sidebar.file_uploader("Upload tài liệu PDF/DOCX", type=["pdf", "docx"])

    st.subheader("Trạng thái dự án")
    st.info("Môi trường Python, thư viện cần thiết và cấu trúc thư mục đã được dựng xong.")

    if uploaded_file is not None:
        st.success(f"Đã chọn file: {uploaded_file.name}")
    else:
        st.write("Chưa chọn tài liệu.")

    st.divider()
    st.write("Bước tiếp theo: implement ingest tài liệu, tạo FAISS index và pipeline hỏi đáp.")


if __name__ == "__main__":
    main()
