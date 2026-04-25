# ketanai — my local personal assistant

A personal AI assistant that runs entirely on your machine using local Ollama models and persistent long-term memory via mem0.

## Features

- Runs locally — no API keys, no cloud
- Long-term memory across all sessions (mem0 + Chroma)
- Session history with auto-generated titles
- Streaming responses
- Beautiful geeky terminal UI

## Install

```bash
git clone git@github.com:Ketansuhaas/ketanai-my-local-personal-assistant.git
cd ketanai-my-local-personal-assistant
bash install.sh
```

Open a new terminal and run:

```bash
ketanai
```

## Commands

| Command | Description |
|---|---|
| `/model [name]` | Show or switch model |
| `/models` | List installed Ollama models |
| `/memory [query]` | Browse long-term memories |
| `/remember <fact>` | Store a fact explicitly |
| `/forget <query>` | Delete matching memories |
| `/sessions` | List past sessions |
| `/load <id>` | Resume a past session |
| `/exit` | Save and quit |

## Adding models

```bash
ollama pull mistral
ollama pull llama3.2
ollama pull phi4
```

Then switch inside ketanai with `/model <name>`.

## Data

All data is stored locally in `~/.ketanai/`:
- `chroma_db/` — long-term memory vector store
- `sessions/` — chat history (JSON)
- `config.json` — model preference
