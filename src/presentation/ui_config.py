"""UI configuration and Streamlit styling components."""
from __future__ import annotations

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

:root {
    --bg-0: #0b1020;
    --bg-1: #121a32;
    --panel: rgba(20, 28, 51, 0.82);
    --panel-soft: rgba(24, 35, 67, 0.60);
    --panel-border: rgba(135, 167, 255, 0.26);
    --text-main: #f3f7ff;
    --text-soft: #cfddfb;
    --accent: #56c8ff;
    --accent-2: #8f8cff;
    --ok: #35d49a;
    --warn: #ffc06b;
    --danger: #ff6f7f;
    --sidebar: linear-gradient(180deg, #0d1328 0%, #101935 55%, #0e1429 100%);
}

html, body, [class*="css"] {
    font-family: "Space Grotesk", "Segoe UI", sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(900px 380px at 12% -12%, rgba(86, 200, 255, 0.20), transparent 65%),
        radial-gradient(900px 380px at 90% -18%, rgba(143, 140, 255, 0.18), transparent 64%),
        linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 100%);
    color: var(--text-main);
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2.1rem;
    max-width: 1240px;
}

[data-testid="stSidebar"] {
    background: var(--sidebar);
    border-right: 1px solid rgba(132, 161, 245, 0.26);
}

[data-testid="stSidebar"] * {
    color: #eff5ff !important;
}

[data-testid="stSidebar"] .stAlert {
    background: rgba(75, 139, 255, 0.16) !important;
    border: 1px solid rgba(98, 158, 255, 0.42) !important;
    border-radius: 14px !important;
}

.smartdoc-sidebar-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.36rem;
    padding: 0.36rem 0.72rem;
    border-radius: 999px;
    background: rgba(86, 200, 255, 0.16);
    border: 1px solid rgba(86, 200, 255, 0.35);
    color: #d9f2ff;
    font-size: 0.81rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}

[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] [data-baseweb="base-input"] > div,
[data-testid="stSidebar"] .stNumberInput > div,
[data-testid="stSidebar"] .stMultiSelect > div {
    background: rgba(13, 22, 45, 0.86) !important;
    border-color: rgba(126, 154, 230, 0.36) !important;
    border-radius: 12px !important;
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] div[role="combobox"] {
    color: #f5f8ff !important;
}

[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder {
    color: #cad8f7 !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: rgba(14, 23, 46, 0.92) !important;
    border: 1px solid rgba(126, 154, 230, 0.42) !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
    color: #e8f1ff !important;
    -webkit-text-fill-color: #e8f1ff !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
    background: #18325f !important;
    color: #f3f8ff !important;
    border: 1px solid rgba(131, 169, 255, 0.52) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #f3f8ff !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
    background: #22467f !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
[data-testid="stSidebar"] [data-testid="stFileUploader"] p,
[data-testid="stSidebar"] [data-testid="stFileUploader"] span {
    color: #eaf2ff !important;
    -webkit-text-fill-color: #eaf2ff !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] ul,
[data-testid="stSidebar"] [data-testid="stFileUploader"] li {
    background: rgba(14, 23, 46, 0.92) !important;
    border-color: rgba(126, 154, 230, 0.42) !important;
    color: #f2f7ff !important;
}

[data-testid="stSidebar"] [data-testid="stFileChip"] {
    background: rgba(16, 27, 52, 0.96) !important;
    border: 1px solid rgba(126, 154, 230, 0.42) !important;
}

[data-testid="stSidebar"] [data-testid="stFileChipName"],
[data-testid="stSidebar"] [data-testid="stFileChip"] [title],
[data-testid="stSidebar"] [data-testid="stFileChip"] small,
[data-testid="stSidebar"] [data-testid="stFileChip"] span {
    color: #f3f8ff !important;
    -webkit-text-fill-color: #f3f8ff !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stFileChipDeleteBtn"] {
    background: rgba(27, 45, 82, 0.92) !important;
    color: #e7f0ff !important;
    fill: #e7f0ff !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stBaseButton-borderlessIcon"] {
    background: rgba(24, 49, 95, 0.96) !important;
    color: #eff5ff !important;
    fill: #eff5ff !important;
    border: 1px solid rgba(126, 154, 230, 0.52) !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] svg {
    fill: #d9e7ff !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] {
    background: #e8edf7 !important;
    border: 1px solid rgba(110, 136, 196, 0.72) !important;
    border-radius: 12px !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #1d355f !important;
    -webkit-text-fill-color: #1d355f !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] [title="Choose options"],
[data-testid="stSidebar"] [data-baseweb="select"] [aria-live="polite"] {
    color: #284776 !important;
    -webkit-text-fill-color: #284776 !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] input::placeholder,
[data-testid="stSidebar"] [data-baseweb="select"] [class*="placeholder"],
[data-testid="stSidebar"] [data-baseweb="select"] [class*="singleValue"],
[data-testid="stSidebar"] [data-baseweb="select"] [class*="valueContainer"] {
    color: #1d355f !important;
    -webkit-text-fill-color: #1d355f !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] svg,
[data-testid="stSidebar"] [data-baseweb="select"] path {
    fill: #35588f !important;
}

[data-testid="stSidebar"] [data-baseweb="select"][aria-disabled="true"],
[data-testid="stSidebar"] [data-baseweb="select"][aria-disabled="true"] * {
    color: #4b6a9f !important;
    -webkit-text-fill-color: #4b6a9f !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] [data-testid="stNumberInput"] button,
[data-testid="stSidebar"] .stNumberInput button,
[data-testid="stSidebar"] [data-testid="stNumberInput"] button svg,
[data-testid="stSidebar"] .stNumberInput button svg {
    background: rgba(26, 41, 76, 0.96) !important;
    color: #eef4ff !important;
    fill: #eef4ff !important;
    opacity: 1 !important;
    border-color: rgba(126, 154, 230, 0.42) !important;
}

[data-testid="stSidebar"] [data-testid="stNumberInput"] button:disabled,
[data-testid="stSidebar"] .stNumberInput button:disabled {
    background: rgba(34, 48, 82, 0.95) !important;
    color: #d4e2ff !important;
    fill: #d4e2ff !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] .stButton > button {
    border-radius: 12px !important;
    border: 1px solid rgba(118, 171, 255, 0.44) !important;
    background: linear-gradient(140deg, #1b3e8f, #1f65cc) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    transition: transform 160ms ease, box-shadow 160ms ease;
}

[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 22px rgba(31, 101, 204, 0.28) !important;
    background: linear-gradient(140deg, #22467f, #1f65cc) !important; /* Slightly lighter for hover effect */
    border: 1px solid rgba(118, 171, 255, 0.55) !important;
    color: #ffffff !important;
}

[data-testid="stSidebar"] .stButton[data-testid*="tertiary"] > button {
    background: transparent !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    color: #e7f0ff !important;
}

[data-testid="stSidebar"] .stButton[data-testid*="tertiary"] > button:hover {
    background: rgba(255, 60, 60, 0.25) !important;
    border: 1px solid rgba(255, 90, 90, 0.4) !important;
    transform: translateY(-1px);
}

.smartdoc-hero {
    position: relative;
    background: linear-gradient(145deg, rgba(20, 30, 56, 0.92), rgba(19, 27, 46, 0.76));
    border: 1px solid rgba(132, 164, 255, 0.34);
    border-radius: 24px;
    padding: 1.35rem 1.55rem;
    box-shadow: 0 24px 44px rgba(3, 8, 24, 0.42);
    overflow: hidden;
    margin-bottom: 1rem;
}

.smartdoc-hero::before {
    content: "";
    position: absolute;
    width: 340px;
    height: 340px;
    right: -140px;
    top: -190px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(86, 200, 255, 0.36), rgba(86, 200, 255, 0));
}

.smartdoc-kicker {
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-size: 0.74rem;
    color: #9fceff;
    font-weight: 700;
    margin-bottom: 0.45rem;
}

.smartdoc-title {
    font-family: "Manrope", "Space Grotesk", sans-serif;
    font-size: 2.15rem;
    font-weight: 800;
    line-height: 1.15;
    margin: 0;
    color: var(--text-main);
}

.smartdoc-subtitle {
    margin-top: 0.52rem;
    color: var(--text-soft);
    font-size: 0.96rem;
    max-width: 780px;
    line-height: 1.6;
}

.smartdoc-card {
    background: var(--panel);
    border: 1px solid var(--panel-border);
    border-radius: 18px;
    padding: 1rem 1.08rem;
    box-shadow: 0 18px 34px rgba(3, 9, 26, 0.26);
    backdrop-filter: blur(12px);
}

.smartdoc-section-title {
    font-size: 1.03rem;
    font-weight: 700;
    margin-bottom: 0.38rem;
    color: #f4f8ff;
}

.smartdoc-muted {
    color: #d6e3ff;
    font-size: 0.92rem;
}

.smartdoc-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.32rem;
}

.smartdoc-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.34rem 0.74rem;
    border-radius: 999px;
    background: rgba(73, 120, 255, 0.17);
    color: #d7e5ff;
    border: 1px solid rgba(138, 171, 255, 0.36);
    font-size: 0.81rem;
    font-weight: 600;
}

.smartdoc-step {
    border: 1px solid rgba(143, 171, 255, 0.28);
    padding: 0.52rem 0.82rem;
    background: rgba(18, 26, 47, 0.5);
    border-radius: 12px;
    margin-bottom: 0.52rem;
}

.smartdoc-step-title {
    font-weight: 700;
    margin-bottom: 0.12rem;
    color: #eaf1ff;
}

.smartdoc-step-desc {
    font-size: 0.9rem;
    color: #adc1e8;
}

.smartdoc-divider {
    margin: 1rem 0;
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(136, 162, 227, 0.45), transparent);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.34rem;
    border-bottom: 0 !important;
    box-shadow: none !important;
}

.stTabs [data-baseweb="tab"] {
    background: rgba(26, 38, 67, 0.72);
    border: 1px solid rgba(131, 160, 238, 0.3);
    border-radius: 999px;
    color: #b9caeb;
    padding: 0.45rem 0.92rem;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(140deg, rgba(44, 103, 235, 0.48), rgba(79, 198, 255, 0.35));
    color: #ffffff !important;
    border-color: rgba(121, 210, 255, 0.62) !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
    height: 0 !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] {
    color: #f0f6ff !important;
}

.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(118, 171, 255, 0.42);
    background: linear-gradient(130deg, #1d4cae, #2f7ee7);
    color: #ffffff;
    font-weight: 700;
    transition: transform 160ms ease, box-shadow 160ms ease;
    -webkit-text-fill-color: #ffffff;
}

.stButton > button,
.stButton > button p,
.stButton > button span {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 20px rgba(46, 126, 231, 0.28);
}

.stButton > button:disabled {
    background: linear-gradient(130deg, #365f9c, #446ea8) !important;
    color: #e7f0ff !important;
    -webkit-text-fill-color: #e7f0ff !important;
    opacity: 1 !important;
    border-color: rgba(152, 186, 255, 0.45) !important;
}

.stTextArea textarea,
[data-baseweb="input"] input,
.stNumberInput input {
    background: rgba(13, 22, 45, 0.82) !important;
    border: 1px solid rgba(126, 154, 230, 0.36) !important;
    color: #f3f7ff !important;
    border-radius: 12px !important;
}

.stTextArea textarea::placeholder,
[data-baseweb="input"] input::placeholder,
.stNumberInput input::placeholder {
    color: #cfdcff !important;
    -webkit-text-fill-color: #cfdcff !important;
    opacity: 1 !important;
}

[data-testid="stExpander"] {
    border: 1px solid rgba(130, 160, 236, 0.34) !important;
    border-radius: 12px !important;
    background: rgba(17, 26, 46, 0.72) !important;
}

[data-testid="stExpander"] details summary {
    background: rgba(21, 33, 61, 0.94) !important;
    color: #edf4ff !important;
}

[data-testid="stExpander"] details summary * {
    color: #edf4ff !important;
    -webkit-text-fill-color: #edf4ff !important;
    opacity: 1 !important;
}

/* Fix chat message text visibility */
[data-testid="stChatMessage"] {
    background: rgba(20, 30, 58, 0.75) !important;
    border: 1px solid rgba(131, 160, 238, 0.25) !important;
    border-radius: 14px !important;
    margin-bottom: 0.5rem !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] li {
    color: #eef3ff !important;
    -webkit-text-fill-color: #eef3ff !important;
}

/* Fix code block visibility */
code {
    background: rgba(13, 22, 45, 0.95) !important;
    color: #56c8ff !important;
    padding: 0.15rem 0.35rem !important;
    border-radius: 6px !important;
    border: 1px solid rgba(135, 167, 255, 0.35) !important;
    font-family: monospace !important;
}

pre {
    background: rgba(13, 22, 45, 0.95) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(135, 167, 255, 0.35) !important;
    padding: 1rem !important;
}

pre code {
    background: transparent !important;
    padding: 0 !important;
    border: none !important;
    color: #f3f7ff !important;
}

/* User bubble - slightly different tint */
[data-testid="stChatMessageUser"] [data-testid="stChatMessage"] {
    background: rgba(31, 55, 115, 0.72) !important;
}

@media (max-width: 840px) {
    .smartdoc-title {
        font-size: 1.58rem;
    }
    .block-container {
        padding-top: 1.1rem;
        padding-left: 0.85rem;
        padding-right: 0.85rem;
    }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def render_hero() -> None:
    st.markdown(
        """
        <div class="smartdoc-hero">
            <div class="smartdoc-kicker">SmartDoc AI Workspace</div>
            <h1 class="smartdoc-title">AI Retrieval Console for Documents</h1>
            <div class="smartdoc-subtitle">
                Thiết kế lại theo ngôn ngữ giao diện AI hiện đại: bảng điều khiển rõ ràng, sidebar điều khiển,
                citation minh bạch và luồng hỏi đáp tối ưu cho RAG production.
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
    st.sidebar.caption("AI document cockpit cho ingest, retrieval, QA và tracking nguồn.")


def render_model_badge(model_name: str, is_fallback: bool, target=None) -> None:
    icon = "🟢" if not is_fallback else "🟠"
    fallback_text = "Fallback" if is_fallback else "Primary"
    html = f"<div class='smartdoc-sidebar-badge'>{icon} {fallback_text}: {model_name}</div>"
    if target is not None:
        target.markdown(html, unsafe_allow_html=True)
        return
    st.sidebar.markdown(html, unsafe_allow_html=True)
