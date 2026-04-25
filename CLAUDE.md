# KetanAI — Codebase Guide

Personal AI assistant CLI built with Ollama + ChromaDB. Runs locally, no API keys.

## Project layout

```
personalAI/
├── ketanai/
│   ├── main.py       # entry point, chat loop, streaming, status display
│   ├── memory.py     # custom memory layer (ChromaDB + nomic-embed-text)
│   ├── session.py    # session ID generation, save/load/list sessions
│   ├── commands.py   # /command handlers (/memory, /forget, /sessions, etc.)
│   ├── config.py     # load/save ~/.ketanai/config.json, path constants
│   └── __init__.py
├── pyproject.toml    # package + entry point (ketanai = ketanai.main:main)
├── install.sh        # full setup script (ollama, models, venv, alias)
└── README.md
```

## Data directories

```
~/.ketanai/
  ├─ config.json      # model, embed_model, user_id, ollama_url
  ├─ chroma_db/       # ChromaDB persistent vector store
  └─ sessions/        # one JSON file per session
```

## Key design decisions

**Custom memory layer** (`memory.py`) — mem0 was dropped because it requires function calling for fact extraction, which small Ollama models don't support. The custom layer uses a plain JSON extraction prompt, embeds with `nomic-embed-text`, stores directly in ChromaDB.

**Async memory search** — memory search runs in a `ThreadPoolExecutor` with a 2s timeout before each response. Never blocks the prompt.

**Background memory storage** — `mem.add()` runs in a daemon thread after each response. Non-blocking.

**num_ctx=4096** — Ollama context window capped at 4096 tokens. Reduces time-to-first-token significantly vs default (128K for some models).

**Session naming** — sessions start as a timestamp ID (`2026-04-24_220943`), renamed to a slug after the first message (`2026-04-24_what-is-quantum`). If slug already exists, keeps timestamp to avoid overwriting.

**Ollama lifecycle** — tracks whether ketanai started Ollama. Stops it on exit only if it started it.

## Memory API

```python
mem.add(user_msg, ai_msg, config)     # extract + store facts (background)
mem.search(query, config, limit=5)    # semantic search, returns list[str]
mem.remember(fact, config)            # store a plain string fact directly
mem.forget(query, config)             # delete semantically matching facts
mem.all_memories(config)              # return all stored facts
mem.reset()                           # clear cached ChromaDB client
```

## Running locally

```bash
cd personalAI
source venv/bin/activate
ketanai
# or without activating:
./venv/bin/ketanai
```

## Adding a new command

1. Add the verb to `KNOWN_VERBS` in `commands.py`
2. Add it to the `_HELP` list
3. Add an `elif verb == "/yourcommand":` block in `handle()`

## Dependencies

Core: `ollama`, `chromadb`, `rich`
Dev: `mem0ai` (kept for potential future use, not actively used), `litellm` (installed but unused)
