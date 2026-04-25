"""
Custom memory layer — no function calling required.

Extract facts from conversations using a plain prompt,
embed them with nomic-embed-text, store/search in ChromaDB.
"""

import json
import uuid
import ollama
import chromadb
from .config import CHROMA_DIR


_client: chromadb.ClientAPI | None = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name="ketanai_memory",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _embed(text: str, embed_model: str) -> list[float]:
    resp = ollama.embeddings(model=embed_model, prompt=text)
    return resp["embedding"]


def _extract_facts(user_msg: str, ai_msg: str, model: str) -> list[str]:
    """Ask the model to pull out memorable facts — plain text, no tool calls."""
    prompt = (
        "Extract concise, factual statements about the user from this conversation. "
        "Output ONLY a JSON array of short strings, one fact per item. "
        "If there are no memorable facts, output an empty array [].\n\n"
        f"User: {user_msg}\nAssistant: {ai_msg}"
    )
    resp = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 2048, "temperature": 0},
    )
    raw = resp["message"]["content"].strip()
    # pull JSON array out of the response even if wrapped in markdown
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        facts = json.loads(raw[start: end + 1])
        return [f for f in facts if isinstance(f, str) and f.strip()]
    except json.JSONDecodeError:
        return []


# ── public API ────────────────────────────────────────────────────────────────

def add(user_msg: str, ai_msg: str, config: dict):
    facts = _extract_facts(user_msg, ai_msg, config["model"])
    if not facts:
        return
    col = _get_collection()
    for fact in facts:
        embedding = _embed(fact, config["embed_model"])
        col.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[fact],
            metadatas=[{"user_id": config["user_id"]}],
        )


def search(query: str, config: dict, limit: int = 5) -> list[str]:
    col = _get_collection()
    if col.count() == 0:
        return []
    embedding = _embed(query, config["embed_model"])
    results = col.query(
        query_embeddings=[embedding],
        n_results=min(limit, col.count()),
        where={"user_id": config["user_id"]},
    )
    return results["documents"][0] if results["documents"] else []


def remember(fact: str, config: dict):
    """Explicitly store a single fact string."""
    col = _get_collection()
    embedding = _embed(fact, config["embed_model"])
    col.add(
        ids=[str(uuid.uuid4())],
        embeddings=[embedding],
        documents=[fact],
        metadatas=[{"user_id": config["user_id"]}],
    )


def forget(query: str, config: dict) -> int:
    """Delete memories semantically matching the query. Returns count deleted."""
    col = _get_collection()
    if col.count() == 0:
        return 0
    embedding = _embed(query, config["embed_model"])
    results = col.query(
        query_embeddings=[embedding],
        n_results=min(5, col.count()),
        where={"user_id": config["user_id"]},
    )
    ids = results["ids"][0] if results["ids"] else []
    if ids:
        col.delete(ids=ids)
    return len(ids)


def all_memories(config: dict) -> list[dict]:
    """Return all stored memories for display."""
    col = _get_collection()
    if col.count() == 0:
        return []
    results = col.get(where={"user_id": config["user_id"]})
    return [
        {"id": mid[:8], "memory": doc}
        for mid, doc in zip(results["ids"], results["documents"])
    ]


def reset():
    global _client, _collection
    _client = None
    _collection = None
