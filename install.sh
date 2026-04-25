#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO_DIR/venv"
PYTHON=""

# ── helpers ────────────────────────────────────────────────────────────────
green()  { echo -e "\033[32m$*\033[0m"; }
yellow() { echo -e "\033[33m$*\033[0m"; }
red()    { echo -e "\033[31m$*\033[0m"; }
step()   { echo; green "▶ $*"; }

# ── Python 3.10+ ────────────────────────────────────────────────────────────
step "Checking Python..."
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" &>/dev/null; then
    ver=$("$candidate" -c 'import sys; print(sys.version_info[:2])')
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
      PYTHON=$(command -v "$candidate")
      green "  Using $PYTHON ($ver)"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  yellow "  Python 3.10+ not found — installing via Homebrew..."
  brew install python@3.13
  PYTHON="$(brew --prefix)/bin/python3.13"
fi

# ── Homebrew ────────────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  red "Homebrew is required. Install it from https://brew.sh then re-run this script."
  exit 1
fi

# ── Ollama ──────────────────────────────────────────────────────────────────
step "Checking Ollama..."
if ! command -v ollama &>/dev/null; then
  yellow "  Installing Ollama..."
  brew install ollama
else
  green "  Ollama already installed."
fi

step "Starting Ollama service..."
brew services start ollama 2>/dev/null || true
sleep 2

# ── Models ──────────────────────────────────────────────────────────────────
step "Pulling gemma4:e2b (~7 GB)..."
ollama pull gemma4:e2b

step "Pulling nomic-embed-text (memory embeddings)..."
ollama pull nomic-embed-text

# ── Python venv ─────────────────────────────────────────────────────────────
step "Setting up Python environment..."
if [ ! -d "$VENV" ]; then
  "$PYTHON" -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -e "$REPO_DIR"
"$VENV/bin/pip" install --quiet "mem0ai[nlp]"
"$VENV/bin/python" -m spacy download en_core_web_sm --quiet
green "  Done."

# ── Shell alias ─────────────────────────────────────────────────────────────
step "Installing 'ketanai' command..."
ALIAS_LINE="alias ketanai=\"$VENV/bin/ketanai\""

add_to_rc() {
  local rc="$1"
  if [ -f "$rc" ] && grep -q "alias ketanai=" "$rc"; then
    # update existing alias in case path changed
    sed -i '' "s|alias ketanai=.*|$ALIAS_LINE|" "$rc"
    green "  Updated alias in $rc"
  elif [ -f "$rc" ]; then
    echo "" >> "$rc"
    echo "$ALIAS_LINE" >> "$rc"
    green "  Added alias to $rc"
  fi
}

add_to_rc "$HOME/.zshrc"
add_to_rc "$HOME/.bashrc"

# ── Done ────────────────────────────────────────────────────────────────────
echo
green "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
green "  KetanAI installed!"
green "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "  Run in a new terminal:  ketanai"
echo "  Or right now:           source ~/.zshrc && ketanai"
echo
