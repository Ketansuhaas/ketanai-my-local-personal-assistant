from mem0 import Memory
from .config import CHROMA_DIR

_mem: Memory | None = None
_mem_model: str | None = None


def get_memory(config: dict) -> Memory:
    global _mem, _mem_model
    if _mem is None or _mem_model != config["model"]:
        _mem = Memory.from_config({
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": config["model"],
                    "ollama_base_url": config["ollama_url"],
                },
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": config["embed_model"],
                    "ollama_base_url": config["ollama_url"],
                },
            },
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "ketanai_memory",
                    "path": str(CHROMA_DIR),
                },
            },
        })
        _mem_model = config["model"]
    return _mem


def reset_memory():
    global _mem, _mem_model
    _mem = None
    _mem_model = None
