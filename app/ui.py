from __future__ import annotations

import streamlit as st

CSS = """
<style>
:root {
    --bg: #f8fafc;
    --panel: rgba(255, 255, 255, 0.82);
    --panel-border: rgba(148, 163, 184, 0.24);
    --text: #0f172a;
    --muted: #475569;
    --primary: #0f766e;
    --primary-strong: #115e59;
    --accent: #f59e0b;
    --sidebar-bg: #0f172a;
    --sidebar-text: #e2e8f0;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.10), transparent 28%),
        radial-gradient(circle at bottom right, rgba(245, 158, 11, 0.10), transparent 30%),
        linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
    color: var(--text);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
    color: var(--sidebar-text);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] [class*="css-"] {
    color: #f1f5f9 !important;
    -webkit-text-fill-color: #f1f5f9 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #0b1220 !important;
    border: 1px solid rgba(148, 163, 184, 0.35) !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: #0b1220 !important;
    border: 1px solid rgba(148, 163, 184, 0.35) !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
    color: #0f172a !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] section,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] div {
    color: #0f172a !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #0f172a !important;
}

[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="base-input"] input,
[data-testid="stSidebar"] textarea {
    color: #e2e8f0 !important;
    background: #0b1220 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
}

[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] [data-baseweb="base-input"] > div,
[data-testid="stSidebar"] .stNumberInput > div {
    background: #0b1220 !important;
    border-color: rgba(148, 163, 184, 0.35) !important;
}

[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-baseweb="base-input"],
[data-testid="stSidebar"] [data-testid="stNumberInput"],
[data-testid="stSidebar"] .stNumberInput {
    color: #e2e8f0 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
}

[data-testid="stSidebar"] [data-testid="stNumberInput"] input,
[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] div[role="spinbutton"] {
    color: #e2e8f0 !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
}

[data-testid="stSidebar"] [data-testid="stNumberInput"] button,
[data-testid="stSidebar"] .stNumberInput button {
    color: #cbd5e1 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] *:disabled,
[data-testid="stSidebar"] [aria-disabled="true"],
[data-testid="stSidebar"] [data-disabled="true"] {
    opacity: 1 !important;
    color: #e2e8f0 !important;
    -webkit-text-fill-color: #e2e8f0 !important;
}

[data-testid="stSidebar"] *:disabled::placeholder,
[data-testid="stSidebar"] [aria-disabled="true"]::placeholder {
    color: #cbd5e1 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder {
    color: #94a3b8 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] .stButton > button {
    color: #f1f5f9 !important;
    background: #0f766e !important;
    border: 1px solid rgba(15, 118, 110, 0.6) !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stButton > button:focus {
    background: #115e59 !important;
    color: #f1f5f9 !important;
    border-color: rgba(15, 118, 110, 0.8) !important;
}

[data-testid="stSidebar"] button {
    color: #f1f5f9 !important;
    background: #0f766e !important;
    border: 1px solid rgba(15, 118, 110, 0.6) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #f1f5f9 !important;
    font-weight: 600 !important;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1280px;
}

.smartdoc-hero {
    background: linear-gradient(135deg, rgba(15,118,110,0.12), rgba(245,158,11,0.10));
    border: 1px solid rgba(15, 118, 110, 0.16);
    border-radius: 24px;
    padding: 1.5rem 1.6rem;
    box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
    margin-bottom: 1rem;
}

.smartdoc-kicker {
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.78rem;
    color: var(--primary-strong);
    font-weight: 700;
    margin-bottom: 0.4rem;
}

.smartdoc-title {
    font-size: 2.1rem;
    font-weight: 800;
    line-height: 1.15;
    margin: 0;
    color: var(--text);
}

.smartdoc-subtitle {
    margin-top: 0.5rem;
    color: var(--muted);
    font-size: 0.98rem;
    max-width: 760px;
}

.smartdoc-card {
    background: var(--panel);
    backdrop-filter: blur(10px);
    border: 1px solid var(--panel-border);
    border-radius: 20px;
    padding: 1rem 1.1rem;
    box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.smartdoc-section-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.4rem;
    color: var(--text);
}

.smartdoc-muted {
    color: var(--muted);
    font-size: 0.92rem;
}

.smartdoc-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.4rem;
}

.smartdoc-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.34rem 0.7rem;
    border-radius: 999px;
    background: rgba(15, 118, 110, 0.10);
    color: var(--primary-strong);
    border: 1px solid rgba(15, 118, 110, 0.16);
    font-size: 0.84rem;
    font-weight: 600;
}

.smartdoc-step {
    border-left: 4px solid rgba(15, 118, 110, 0.65);
    padding: 0.4rem 0.8rem;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 12px;
    margin-bottom: 0.6rem;
}

.smartdoc-step-title {
    font-weight: 700;
    margin-bottom: 0.15rem;
}

.smartdoc-step-desc {
    font-size: 0.9rem;
    color: var(--muted);
}

.smartdoc-divider {
    margin: 1rem 0;
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.42), transparent);
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        f"""
        <div class="smartdoc-hero">
            <div class="smartdoc-kicker">SmartDoc AI</div>
            <h1 class="smartdoc-title">Document Q&A System với Streamlit + FAISS + Ollama</h1>
            <div class="smartdoc-subtitle">
                Giao diện web cho phép upload PDF/DOCX, chunking tài liệu, tạo FAISS index và truy xuất top-k chunk.
                Phần UI này bám sát yêu cầu giao diện trong assignment, đồng thời có thể mở rộng dần sang Q&A hoàn chỉnh.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chip_row(items: list[str]) -> None:
    chips = "".join(f'<span class="smartdoc-chip">{item}</span>' for item in items)
    st.markdown(f'<div class="smartdoc-chip-row">{chips}</div>', unsafe_allow_html=True)


def render_step(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="smartdoc-step">
            <div class="smartdoc-step-title">{title}</div>
            <div class="smartdoc-step-desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_header() -> None:
    st.sidebar.markdown("## SmartDoc AI")
    st.sidebar.caption("Giao diện web theo hướng Streamlit, có thể bổ sung CSS để đẹp hơn.")


def render_sidebar_help() -> None:
    st.sidebar.markdown("### Hướng dẫn nhanh")
    st.sidebar.markdown(
        """
        1. Chọn PDF hoặc DOCX.
        2. Chỉnh chunk size và chunk overlap.
        3. Bấm **Ingest và tạo FAISS index**.
        4. Dùng tab truy vấn để test retrieval.
        """
    )


def render_sidebar_notes() -> None:
    st.sidebar.markdown("### Ghi chú UI")
    st.sidebar.markdown(
        """
        - Streamlit là lớp giao diện chính.
        - HTML/CSS chỉ dùng để tăng tính thẩm mỹ.
        - Bố cục nên có sidebar, vùng upload, vùng kết quả và trạng thái.
        """
    )
