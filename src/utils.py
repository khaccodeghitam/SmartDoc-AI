"""Shared text processing and path utilities used across all layers."""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.documents import Document


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def sanitize_name(name: str) -> str:
    """Convert a filename with accents into a safe ASCII folder name."""
    name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    safe = re.sub(r"[^a-zA-Z0-9.-]", "_", name)
    safe = re.sub(r"_+", "_", safe)
    return safe.strip("_") or "document"


def strip_accents(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")


def normalize_for_match(text: str) -> str:
    normalized = strip_accents(text).lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))


def keyword_overlap_score(query: str, text: str) -> float:
    query_tokens = normalize_tokens(query)
    if not query_tokens:
        return 0.0
    text_tokens = normalize_tokens(text)
    if not text_tokens:
        return 0.0
    overlap = query_tokens.intersection(text_tokens)
    return len(overlap) / len(query_tokens)


# ---------------------------------------------------------------------------
# Source / path helpers
# ---------------------------------------------------------------------------

def source_name_from_path(path_value: str) -> str:
    return Path(path_value).name if path_value else ""


def source_name_core(path_value: str) -> str:
    stem = Path(path_value).stem
    stem = normalize_for_match(stem)
    stem = re.sub(r"^(bai\s*tap|bai|thuc\s*hanh|lab|exercise|chapter)\s*\d*\s*", "", stem).strip()
    return stem


# ---------------------------------------------------------------------------
# Source / metadata filtering
# ---------------------------------------------------------------------------

def source_matches_filter(doc_source: str, source_filter: list[str] | None) -> bool:
    if not source_filter:
        return True

    doc_name = source_name_from_path(doc_source)
    doc_norm = normalize_for_match(doc_name)

    for selected in source_filter:
        selected_name = source_name_from_path(selected)
        selected_norm = normalize_for_match(selected_name)
        if not selected_norm:
            continue
        if selected_norm == doc_norm:
            return True
        if selected_norm in normalize_for_match(doc_source):
            return True

    return False


def metadata_matches_filters(
    metadata: dict[str, Any],
    source_filter: list[str] | None,
    file_type_filter: list[str] | None,
    upload_date_filter: list[str] | None,
) -> bool:
    source_value = str(metadata.get("source", ""))
    if source_filter and not source_matches_filter(source_value, source_filter):
        return False

    if file_type_filter:
        allowed_types = {value.lower().lstrip(".") for value in file_type_filter}
        doc_type = str(metadata.get("file_type", "")).lower().lstrip(".")
        if doc_type not in allowed_types:
            return False

    if upload_date_filter:
        allowed_dates = {value.strip() for value in upload_date_filter if value and value.strip()}
        doc_date = str(metadata.get("upload_date", "")).strip()
        if doc_date not in allowed_dates:
            return False

    return True


def sources_from_docs(docs: list[Document]) -> list[str]:
    source_names = {
        source_name_from_path(str(doc.metadata.get("source", "")))
        for doc in docs
        if (doc.metadata or {}).get("source")
    }
    return sorted(name for name in source_names if name)


@lru_cache(maxsize=256)
def _detect_sources_mentioned_in_query_cached(query_normalized: str, available_sources: tuple[str, ...]) -> tuple[str, ...]:
    query_norm = f" {query_normalized} "
    query_tokens = {token for token in query_normalized.split() if len(token) >= 2}
    query_compact = query_normalized.replace(" ", "")
    stop_tokens = {
        "bai", "tap", "thuc", "hanh", "exercise", "chapter", "file", "pdf", "docx",
    }
    mentioned: list[str] = []

    for source_name in available_sources:
        candidates = [
            normalize_for_match(Path(source_name).stem),
            source_name_core(source_name),
        ]
        candidates = [cand for cand in candidates if len(cand) >= 3]
        if not candidates:
            continue

        matched = False
        for candidate in candidates:
            if f" {candidate} " in query_norm:
                matched = True
                break

            candidate_compact = candidate.replace(" ", "")
            if candidate_compact and candidate_compact in query_compact:
                matched = True
                break

            candidate_tokens = {
                token for token in candidate.split()
                if len(token) >= 2 and token not in stop_tokens
            }
            if not candidate_tokens:
                continue

            overlapped = candidate_tokens.intersection(query_tokens)
            overlap_ratio = len(overlapped) / len(candidate_tokens)
            min_overlap = 1 if len(candidate_tokens) <= 2 else 2
            if len(overlapped) >= min_overlap and overlap_ratio >= 0.5:
                matched = True
                break

            if any(token.isdigit() for token in overlapped) and overlap_ratio >= 0.34:
                matched = True
                break

        if matched:
            mentioned.append(source_name)

    return tuple(sorted(set(mentioned)))


def detect_sources_mentioned_in_query(query: str, available_sources: list[str]) -> list[str]:
    return list(_detect_sources_mentioned_in_query_cached(normalize_for_match(query), tuple(sorted(available_sources))))


def extract_explicit_source_reference(query: str) -> str | None:
    q_norm = normalize_for_match(query)
    if not q_norm:
        return None

    tokens = [token for token in q_norm.split() if token]
    if not tokens:
        return None

    stop_tokens = {
        "co", "bao", "nhieu", "la", "gi", "trong", "gom", "so", "luong",
        "bai", "tap", "exercise", "question", "task", "content", "noi", "dung", "chi", "tiet", "chapter",
    }
    pronouns = {"do", "nay", "kia", "ay", "no"}
    generic_tail_starters = {
        "nao", "co", "la", "gi", "hien", "dang", "da", "tren", "duoi", "khac", "nay", "do", "kia", "ay",
    }

    def collect_tail(start_index: int) -> str | None:
        tail_tokens = [token for token in tokens[start_index:] if token]
        if not tail_tokens:
            return None

        first_token = tail_tokens[0]
        second_token = tail_tokens[1] if len(tail_tokens) > 1 else ""
        if first_token in pronouns or first_token in generic_tail_starters:
            return None
        if (first_token, second_token) in {("hien", "co"), ("dang", "loc"), ("da", "nap")}:
            return None

        collected: list[str] = []
        for token in tokens[start_index:]:
            if token in stop_tokens and collected:
                break
            if token in stop_tokens and not collected:
                continue
            collected.append(token)
            if len(collected) >= 8:
                break

        if not collected:
            return None
        if len(collected) == 1 and collected[0] in pronouns:
            return None

        return " ".join(collected).strip()

    for idx in range(len(tokens)):
        if tokens[idx] == "file":
            return collect_tail(idx + 1)
        if tokens[idx] in {"document", "doc"}:
            return collect_tail(idx + 1)
        if tokens[idx] == "tai" and idx + 1 < len(tokens) and tokens[idx + 1] == "lieu":
            return collect_tail(idx + 2)

    return None


def resolve_effective_source_filter(
    query: str,
    source_filter: list[str] | None,
    all_docs: list[Document],
) -> list[str] | None:
    available_sources = sources_from_docs(all_docs)
    mentioned_sources = detect_sources_mentioned_in_query(query, available_sources)
    if mentioned_sources:
        if source_filter:
            narrowed = [source for source in mentioned_sources if source_matches_filter(source, source_filter)]
            if narrowed:
                return narrowed
            return source_filter
        return mentioned_sources
    return source_filter if source_filter else None


def detect_source_filter_conflict(
    query: str,
    source_filter: list[str] | None,
    all_docs: list[Document],
) -> tuple[bool, list[str]]:
    if not source_filter:
        return False, []

    available_sources = sources_from_docs(all_docs)
    mentioned_sources = detect_sources_mentioned_in_query(query, available_sources)
    if not mentioned_sources:
        return False, []

    narrowed = [source for source in mentioned_sources if source_matches_filter(source, source_filter)]
    if narrowed:
        return False, []

    return True, mentioned_sources


def detect_unknown_source_reference(
    query: str,
    all_docs: list[Document],
) -> tuple[bool, str]:
    explicit_ref = extract_explicit_source_reference(query)
    if not explicit_ref:
        return False, ""

    available_sources = sources_from_docs(all_docs)
    mentioned_sources = detect_sources_mentioned_in_query(query, available_sources)
    if mentioned_sources:
        return False, ""

    return True, explicit_ref
