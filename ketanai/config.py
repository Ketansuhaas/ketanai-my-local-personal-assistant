import json
from pathlib import Path

DATA_DIR = Path.home() / ".ketanai"
SESSIONS_DIR = DATA_DIR / "sessions"
CHROMA_DIR = DATA_DIR / "chroma_db"
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULTS = {
    "model": "gemma4:e2b",
    "embed_model": "nomic-embed-text",
    "user_id": "ketan",
    "ollama_url": "http://localhost:11434",
}


def init_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    SESSIONS_DIR.mkdir(exist_ok=True)
    CHROMA_DIR.mkdir(exist_ok=True)


def load_config() -> dict:
    init_dirs()
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULTS, indent=2))
        return DEFAULTS.copy()
    return {**DEFAULTS, **json.loads(CONFIG_FILE.read_text())}


def save_config(config: dict):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
