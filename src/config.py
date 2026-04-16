from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
INDEX_DIR = DATA_DIR / "index"
CHAT_HISTORY_DIR = DATA_DIR / "chat_history"

APP_TITLE = "SmartDoc AI"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 3
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"

FALLBACK_MODELS = ("qwen2.5:1.5b", "qwen2.5:0.5b")
SCORING_MAX_DOCS = 8
SCORING_EXCERPT_CHARS = 320
SCORING_CONTEXT_MAX_CHARS = 3200
