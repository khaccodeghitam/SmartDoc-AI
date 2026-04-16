"""Chat history persistence using JSON file storage."""
from __future__ import annotations

import json
from pathlib import Path

from src.config import CHAT_HISTORY_DIR

SESSION_STATE_FILE = CHAT_HISTORY_DIR / "app_session.json"


def save_persistent_history(history: list) -> None:
    """Save chat history to a JSON file."""
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    history_file = CHAT_HISTORY_DIR / "history.json"
    try:
        history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), "utf-8")
    except Exception as e:
        print(f"Error saving chat history: {e}")


def load_persistent_history() -> list:
    """Load chat history from a JSON file. Automatically migrates old data format."""
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    history_file = CHAT_HISTORY_DIR / "history.json"
    if history_file.exists():
        try:
            data = json.loads(history_file.read_text("utf-8"))
            if not isinstance(data, list):
                return []
            
            # Migration check: if the first element doesn't have "session_id", it's the old format
            if len(data) > 0 and "session_id" not in data[0]:
                import uuid
                from datetime import datetime
                migrated_session = {
                    "session_id": str(uuid.uuid4()),
                    "title": "Cuộc trò chuyện cũ",
                    "timestamp": datetime.now().strftime("%d/%m/%Y - %H:%M"),
                    "history": data
                }
                save_persistent_history([migrated_session])
                return [migrated_session]
                
            return data
        except Exception:
            return []
    return []


def save_app_session(index_dir: str, index_name: str, uploaded_file: str,
                     sources: list, file_types: list, upload_dates: list) -> None:
    """Persist index session state so it survives page refresh (F5)."""
    CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "last_index_dir": index_dir,
        "last_index_name": index_name,
        "last_uploaded_file": uploaded_file,
        "available_sources": sources,
        "available_file_types": file_types,
        "available_upload_dates": upload_dates,
    }
    try:
        SESSION_STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    except Exception as e:
        print(f"Error saving app session: {e}")


def load_app_session() -> dict:
    """Load persisted index session state. Returns empty dict if not found."""
    if SESSION_STATE_FILE.exists():
        try:
            data = json.loads(SESSION_STATE_FILE.read_text("utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}
