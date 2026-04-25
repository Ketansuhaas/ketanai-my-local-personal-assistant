import ollama as _ollama
from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich.text import Text

from .config import save_config
from .memory import get_memory, reset_memory
from .session import load_session, save_session, list_sessions

console = Console()

KNOWN_VERBS = {
    "/help", "/model", "/models",
    "/memory", "/remember", "/forget",
    "/sessions", "/load",
    "/exit", "/quit",
}

_HELP = [
    ("/model [name]",    "⟡", "show current model or switch"),
    ("/models",          "⟡", "list installed models"),
    ("/memory [query]",  "◈", "browse long-term memories"),
    ("/remember <fact>", "◉", "store a fact explicitly"),
    ("/forget <query>",  "◌", "delete matching memories"),
    ("/sessions",        "▤", "list past sessions"),
    ("/load <id>",       "↩", "resume a past session"),
    ("/exit",            "⏻", "save and quit"),
]


def _ok(msg: str):
    console.print(f" [green]✓[/]  {msg}")


def _err(msg: str):
    console.print(f" [red]✗[/]  {msg}")


def _get_models() -> list[str]:
    try:
        return [m.model for m in _ollama.list().models if "embed" not in m.model]
    except Exception:
        return []


def handle(
    raw: str,
    config: dict,
    session_id: str,
    messages: list[dict],
) -> tuple[str, list[dict], bool]:
    parts = raw.strip().split(None, 1)
    verb = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    if verb == "/help":
        console.print()
        console.print(Rule("commands", style="bright_cyan dim"))
        table = Table(show_header=False, box=None, padding=(0, 2), show_edge=False)
        table.add_column(style="bold cyan", no_wrap=True)
        table.add_column(style="cyan dim", no_wrap=True)
        table.add_column(style="dim")
        for cmd, icon, desc in _HELP:
            table.add_row(cmd, icon, desc)
        console.print(table)
        console.print(Rule(style="bright_cyan dim"))
        console.print()

    elif verb == "/models":
        models = _get_models()
        if not models:
            _err("Ollama not running or no models installed.")
        else:
            console.print()
            console.print(Rule("installed models", style="cyan dim"))
            for m in models:
                if m == config["model"]:
                    console.print(f"  [bold cyan]◆  {m}[/]  [green dim]← active[/]")
                else:
                    console.print(f"  [dim]◇[/]  [cyan]{m}[/]")
            console.print()

    elif verb == "/model":
        if not args:
            console.print(f"\n  [dim]active model[/]  [bold cyan]{config['model']}[/]\n")
        else:
            models = _get_models()
            if args not in models:
                _err(f"'{args}' not found — run [cyan]/models[/] to list available.")
            else:
                config["model"] = args
                save_config(config)
                reset_memory()
                _ok(f"switched to [cyan]{args}[/]")

    elif verb == "/memory":
        mem = get_memory(config)
        query = args or "user"
        results = mem.search(query, filters={"user_id": config["user_id"]}, limit=10)
        memories = results.get("results", [])
        console.print()
        console.print(Rule("long-term memory", style="cyan dim"))
        if not memories:
            console.print("  [dim]nothing stored yet.[/]")
        else:
            for i, m in enumerate(memories, 1):
                console.print(f"  [dim cyan]{i:>2}.[/]  {m['memory']}  [dim]·  {m['id'][:8]}[/]")
        console.print()

    elif verb == "/remember":
        if not args:
            _err("usage: /remember <fact>")
        else:
            mem = get_memory(config)
            mem.add(args, user_id=config["user_id"])
            _ok(f"remembered: [dim]{args}[/]")

    elif verb == "/forget":
        if not args:
            _err("usage: /forget <query>")
        else:
            mem = get_memory(config)
            results = mem.search(args, filters={"user_id": config["user_id"]}, limit=5)
            memories = results.get("results", [])
            if not memories:
                console.print("  [dim]no matching memories.[/]")
            else:
                for m in memories:
                    mem.delete(m["id"])
                    console.print(f"  [red dim]✗[/]  {m['memory']}")
                _ok(f"deleted {len(memories)} memory(s)")

    elif verb == "/sessions":
        sessions = list_sessions()
        console.print()
        console.print(Rule("sessions", style="cyan dim"))
        if not sessions:
            console.print("  [dim]no past sessions.[/]")
        else:
            table = Table(show_header=False, box=None, padding=(0, 2), show_edge=False)
            table.add_column(style="cyan", no_wrap=True)
            table.add_column(style="dim", justify="right", no_wrap=True)
            table.add_column(style="dim")
            for s in sessions[:20]:
                active = "  [green]◆[/]" if s["id"] == session_id else ""
                table.add_row(f"{s['id']}{active}", f"{s['count']} msgs", s["preview"])
            console.print(table)
        console.print()

    elif verb == "/load":
        if not args:
            _err("usage: /load <session_id>")
        else:
            loaded = load_session(args)
            if not loaded:
                _err(f"session '{args}' not found.")
            else:
                save_session(session_id, messages)
                session_id = args
                messages = loaded
                _ok(f"loaded [cyan]{args}[/]  [dim]({len(messages)} messages)[/]")

    elif verb in ("/exit", "/quit"):
        save_session(session_id, messages)
        console.print()
        console.print(Rule(style="dim"))
        console.print(Text("  session saved. goodbye.", style="dim italic"))
        console.print()
        return session_id, messages, True

    return session_id, messages, False
