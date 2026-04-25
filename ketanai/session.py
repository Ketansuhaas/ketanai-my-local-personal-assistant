import json
import re
from datetime import datetime
from .config import SESSIONS_DIR


def new_session_id() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def title_from_message(text: str) -> str:
    words = text.lower().split()[:6]
    slug = "-".join(re.sub(r"[^a-z0-9]", "", w) for w in words)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "chat"


def rename_session(old_id: str, new_id: str) -> str:
    old_path = SESSIONS_DIR / f"{old_id}.json"
    new_path = SESSIONS_DIR / f"{new_id}.json"
    if old_path.exists() and not new_path.exists():
        old_path.rename(new_path)
    return new_id


def load_session(session_id: str) -> list[dict]:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_session(session_id: str, messages: list[dict]):
    if not messages:
        return
    path = SESSIONS_DIR / f"{session_id}.json"
    path.write_text(json.dumps(messages, indent=2))


def list_sessions() -> list[dict]:
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        try:
            msgs = json.loads(f.read_text())
            first_user = next((m["content"] for m in msgs if m["role"] == "user"), "")
            sessions.append({
                "id": f.stem,
                "count": len(msgs),
                "preview": first_user[:60],
            })
        except Exception:
            pass
    return sessions
