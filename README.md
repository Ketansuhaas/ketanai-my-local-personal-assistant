# KetanAI

A personal AI assistant that runs entirely on your machine — no cloud, no API keys, no subscriptions.

Built with [Ollama](https://ollama.com) for local LLM inference and a custom memory layer using ChromaDB for persistent long-term memory across all sessions.

```
 ██╗  ██╗███████╗████████╗ █████╗ ███╗   ██╗ █████╗ ██╗
 ██║ ██╔╝██╔════╝╚══██╔══╝██╔══██╗████╗  ██║██╔══██╗██║
 █████╔╝ █████╗     ██║   ███████║██╔██╗ ██║███████║██║
 ██╔═██╗ ██╔══╝     ██║   ██╔══██║██║╚██╗██║██╔══██║██║
 ██║  ██╗███████╗   ██║   ██║  ██║██║ ╚████║██║  ██║██║
 ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝
                                               ketan.ai
```

---

## Features

- **100% local** — runs on your machine via Ollama, nothing leaves your device
- **Long-term memory** — facts are extracted and stored in ChromaDB, persists across all sessions forever
- **Session history** — every chat is saved, auto-named from your first message
- **Streaming responses** — tokens appear as they're generated
- **Fast** — async memory search, small context window, lightweight models
- **Transparent** — shows exactly what's happening before each response

---

## Install

Requires macOS with [Homebrew](https://brew.sh).

```bash
git clone git@github.com:Ketansuhaas/ketanai-my-local-personal-assistant.git
cd ketanai-my-local-personal-assistant
bash install.sh
```

Open a new terminal:

```bash
ketanai
```

`install.sh` handles everything: Ollama, models, Python venv, and shell alias.

---

## Commands

| Command | Description |
|---|---|
| `/model [name]` | Show current model or switch to another |
| `/models` | List all installed Ollama models |
| `/memory [query]` | Browse long-term memories |
| `/remember <fact>` | Explicitly store a fact |
| `/forget <query>` | Delete memories matching a query |
| `/sessions` | List past sessions (sorted by recent) |
| `/load <id>` | Resume a past session |
| `/exit` | Save session and quit |

---

## Adding models

```bash
ollama pull mistral
ollama pull llama3.2
ollama pull phi4
ollama pull qwen2.5:3b
```

Switch inside ketanai with `/model <name>`.

---

## Architecture

```
You type a message
    │
    ├─ search memory (ChromaDB, 2s timeout, background thread)
    ├─ build prompt (system + memory facts + last 10 messages)
    ├─ stream response (Ollama, num_ctx=4096)
    └─ store new facts (background thread, non-blocking)
```

**Storage** — all data lives in `~/.ketanai/`:

```
~/.ketanai/
  ├─ config.json      # active model, user settings
  ├─ chroma_db/       # long-term memory vector store
  └─ sessions/        # chat history, one JSON file per session
```

**Two separate memories:**

| | Session history | Long-term memory |
|---|---|---|
| Storage | JSON files | ChromaDB vectors |
| Scope | One session | All sessions forever |
| Used for | Conversation context | System prompt injection |
| Cleared by | Starting a new session | `/forget <query>` |

---

## Stack

- [Ollama](https://ollama.com) — local LLM inference
- [ChromaDB](https://www.trychroma.com) — vector store for memory
- [nomic-embed-text](https://ollama.com/library/nomic-embed-text) — local embeddings
- [Rich](https://github.com/Textualize/rich) — terminal UI
- [llama3.2:1b](https://ollama.com/library/llama3.2) — default model (fast, 1.3GB)
