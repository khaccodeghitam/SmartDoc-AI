"""Multilingual MPNet embedding model singleton."""
from __future__ import annotations

import importlib
import warnings
from functools import lru_cache
import streamlit as st

from langchain_core._api.deprecation import LangChainDeprecationWarning

try:
    _hf_module = importlib.import_module("langchain_huggingface")
    HuggingFaceEmbeddings = _hf_module.HuggingFaceEmbeddings
except ModuleNotFoundError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

from src.config import EMBEDDING_MODEL_NAME


EMBEDDING_FALLBACK_MODELS = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/all-MiniLM-L6-v2",
)


def _is_memory_related_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        phrase in text
        for phrase in (
            "paging file is too small",
            "os error 1455",
            "out of memory",
            "insufficient memory",
            "cannot allocate memory",
        )
    )


def _build_embedder_for_model(model_name: str) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@st.cache_resource(show_spinner=False)
def build_embedder() -> HuggingFaceEmbeddings:
    """Build and cache the multilingual MPNet embedding model (768-dimensional)."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
        candidate_models: list[str] = []
        for model_name in (EMBEDDING_MODEL_NAME, *EMBEDDING_FALLBACK_MODELS):
            if model_name not in candidate_models:
                candidate_models.append(model_name)

        last_error: Exception | None = None
        for model_name in candidate_models:
            try:
                if model_name != EMBEDDING_MODEL_NAME:
                    print(f"Embedding fallback active: {model_name}")
                return _build_embedder_for_model(model_name)
            except Exception as exc:
                last_error = exc
                if not _is_memory_related_error(exc):
                    continue

        if last_error is not None:
            raise RuntimeError(
                "Unable to load embedding model. "
                "Please free RAM or increase Windows virtual memory (paging file)."
            ) from last_error

        raise RuntimeError("Unable to load embedding model for unknown reasons.")
