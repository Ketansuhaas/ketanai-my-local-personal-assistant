import sys
import subprocess
import threading
import ollama
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime
from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from .config import load_config, save_config
from . import memory as mem
from .session import new_session_id, save_session, title_from_message, rename_session
from . import commands

console = Console()

BANNER = """\
 ██╗  ██╗███████╗████████╗ █████╗ ███╗   ██╗ █████╗ ██╗
 ██║ ██╔╝██╔════╝╚══██╔══╝██╔══██╗████╗  ██║██╔══██╗██║
 █████╔╝ █████╗     ██║   ███████║██╔██╗ ██║███████║██║
 ██╔═██╗ ██╔══╝     ██║   ██╔══██║██║╚██╗██║██╔══██║██║
 ██║  ██╗███████╗   ██║   ██║  ██║██║ ╚████║██║  ██║██║
 ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝"""

_executor = ThreadPoolExecutor(max_workers=2)


def _print_banner(config: dict, session_id: str):
    console.print()
    console.print(BANNER, style="bold bright_cyan")
    console.print(Text("                                               ketan.ai", style="dim cyan italic"))
    console.print()
    console.print(Rule(style="bright_cyan dim"))
    meta = Text()
    meta.append("  model  ", style="dim")
    meta.append(config["model"], style="bold cyan")
    meta.append("     session  ", style="dim")
    meta.append(session_id, style="bold cyan")
    meta.append("     ", style="dim")
    meta.append(datetime.now().strftime("%Y-%m-%d %H:%M"), style="dim")
    console.print(meta)
    console.print(Rule(style="bright_cyan dim"))
    console.print(Text("  type /help for commands", style="dim italic"))
    console.print()


def _fetch_memories(config: dict, user_input: str) -> str:
    facts = mem.search(user_input, config, limit=5)
    return "\n".join(f"- {f}" for f in facts) if facts else ""


def _build_prompt_with_facts(config: dict, messages: list[dict], user_input: str, facts: str) -> list[dict]:

    system = (
        f"You are KetanAI, an AI assistant built by Ketan and running locally on {config['model']} via Ollama. "
        "You are NOT Ketan — Ketan is the human user you are talking to. "
        "You have persistent long-term memory across all sessions. "
        "Never claim you lack memory. If no facts appear below, nothing has been stored yet."
    )
    system += f"\n\nMemory:\n{facts}" if facts else ""

    return (
        [{"role": "system", "content": system}]
        + messages[-10:]
        + [{"role": "user", "content": user_input}]
    )


def _store_memory(config: dict, user_input: str, reply: str):
    try:
        mem.add(user_input, reply, config)
    except Exception:
        pass


_started_ollama = False


def _ensure_ollama() -> bool:
    """Start ollama if not running. Returns True if we started it."""
    try:
        ollama.list()
        return False  # already running
    except Exception:
        console.print(Text("  starting ollama...", style="dim"))
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import time
        for _ in range(10):
            time.sleep(0.5)
            try:
                ollama.list()
                return True
            except Exception:
                pass
        console.print("[red]✗  Could not start Ollama.[/]")
        sys.exit(1)


def _pick_model_interactively(config: dict) -> dict:
    global _started_ollama
    _started_ollama = _ensure_ollama()
    try:
        models = [m.model for m in ollama.list().models if "embed" not in m.model]
    except Exception:
        console.print("[red]✗  Cannot connect to Ollama.[/]")
        sys.exit(1)

    if not models:
        console.print("[red]✗  No chat models installed.[/]  Run: [dim]ollama pull gemma4:e2b[/]")
        sys.exit(1)

    if config["model"] in models:
        return config

    console.print()
    console.print(Rule("select a model", style="yellow"))
    for i, m in enumerate(models, 1):
        console.print(f"  [dim]{i:>2}.[/]  [cyan]{m}[/]")
    console.print()
    choice = console.input("[yellow]❯[/] ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(models):
        config["model"] = models[int(choice) - 1]
    elif choice in models:
        config["model"] = choice
    else:
        config["model"] = models[0]

    save_config(config)
    return config


def _shutdown():
    if _started_ollama:
        subprocess.run(["killall", "ollama"], capture_output=True)
        console.print(Text("  ollama stopped.", style="dim"))


def main():
    config = load_config()
    config = _pick_model_interactively(config)

    session_id = new_session_id()
    messages: list[dict] = []

    _print_banner(config, session_id)

    while True:
        try:
            user_input = console.input("\n [bold bright_cyan]❯[/]  ").strip()
        except (KeyboardInterrupt, EOFError):
            save_session(session_id, messages)
            console.print()
            console.print(Rule(style="dim"))
            console.print(Text("  session saved. goodbye.", style="dim italic"))
            _shutdown()
            console.print()
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            verb = user_input.split()[0].lower()
            if verb in commands.KNOWN_VERBS:
                session_id, messages, should_exit = commands.handle(
                    user_input, config, session_id, messages
                )
                if should_exit:
                    _shutdown()
                    break
                continue
            user_input = user_input.lstrip("/")

        try:
            print()

            def status(msg: str):
                sys.stdout.write(f"\r  \033[2m{msg}\033[0m" + " " * 10)
                sys.stdout.flush()

            def clear_status():
                sys.stdout.write("\r" + " " * 60 + "\r")
                sys.stdout.flush()

            # step 1 — memory search
            status("searching memory…")
            try:
                future = _executor.submit(_fetch_memories, config, user_input)
                facts = future.result(timeout=2.0)
            except (FuturesTimeout, Exception):
                facts = ""

            # step 2 — build prompt
            status("building prompt…")
            prompt = _build_prompt_with_facts(config, messages, user_input, facts)

            # step 3 — sending to model, waiting for first token
            status(f"generating response…")
            stream = ollama.chat(
                model=config["model"],
                messages=prompt,
                stream=True,
                options={"num_ctx": 4096},
            )
            first = next(stream, None)
            clear_status()

            # stream output
            sys.stdout.write(" \033[1;36m◆\033[0m  ")
            sys.stdout.flush()
            reply_chunks = []
            if first:
                token = first["message"]["content"]
                reply_chunks.append(token)
                sys.stdout.write(token)
                sys.stdout.flush()
            for chunk in stream:
                token = chunk["message"]["content"]
                reply_chunks.append(token)
                sys.stdout.write(token)
                sys.stdout.flush()
            print()

            reply = "".join(reply_chunks)

            # store memory in background
            threading.Thread(
                target=_store_memory, args=(config, user_input, reply), daemon=True
            ).start()

            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": reply})

            if len(messages) == 2:
                date = session_id.split("_")[0]
                new_id = f"{date}_{title_from_message(user_input)}"
                session_id = rename_session(session_id, new_id)

            save_session(session_id, messages)

        except KeyboardInterrupt:
            console.print(" " * 60, end="\r")
            console.print("  [dim]interrupted.[/]")
        except Exception as e:
            console.print(f"\n [red]✗[/]  {e}")
