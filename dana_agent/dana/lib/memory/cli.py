"""CLI for dana-memory.

Usage:
    dana-memory store "memory text" [--source SOURCE] [--identity DOMAIN]
    dana-memory query "query text" [--limit N] [--min-score F] [--identity D] [--json]
    dana-memory index PATH [--identity DOMAIN] [--glob PATTERN]
    dana-memory status
    dana-memory list [--identity DOMAIN] [--limit N]
    dana-memory delete ID
    dana-memory clear [--identity DOMAIN] [--force]
    dana-memory hooks install [--target TARGET]
    dana-memory hooks status
    dana-memory hooks uninstall [--target TARGET]

Requires: pip install dana[memory]
"""

from __future__ import annotations

import argparse
import importlib.resources
import json
import shutil
import stat
import sys
from pathlib import Path

try:
    from .store import MemoryStore

    _DEPS_AVAILABLE = True
except ImportError as e:
    _DEPS_AVAILABLE = False
    _IMPORT_ERROR = str(e)


def cmd_store(args: argparse.Namespace) -> int:
    """Store a memory."""
    store = MemoryStore()
    memory = store.store(
        text=args.text,
        source=args.source,
        identity=args.identity,
    )

    if args.json:
        print(json.dumps(memory.to_dict(), indent=2))
    else:
        print(f"Stored memory {memory.id} in identity '{memory.identity}'")

    return 0


def cmd_query(args: argparse.Namespace) -> int:
    """Query memories."""
    store = MemoryStore()
    memories = store.query(
        text=args.text,
        limit=args.limit,
        min_score=args.min_score,
        identity=args.identity,
        source=args.source,
    )

    if args.json:
        print(json.dumps({"memories": [m.to_dict() for m in memories]}, indent=2))
    else:
        if not memories:
            print("No relevant memories found.")
            return 0

        for m in memories:
            # Truncate text for display
            text_preview = m.text[:100] + "..." if len(m.text) > 100 else m.text
            text_preview = text_preview.replace("\n", " ")
            print(f"[{m.score:.2f}] {m.id}  {text_preview}")
            print(f"       identity={m.identity} source={m.source} created={m.created.date()}")
            print()

    return 0


def cmd_index(args: argparse.Namespace) -> int:
    """Index a directory."""
    store = MemoryStore()
    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        return 1

    print(f"Indexing {path} with pattern '{args.glob}'...")
    count = store.index_directory(
        path=path,
        identity=args.identity,
        glob_pattern=args.glob,
    )

    if args.json:
        print(json.dumps({"indexed": count, "path": str(path), "identity": args.identity}))
    else:
        print(f"Indexed {count} memories into identity '{args.identity}'")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show store status."""
    store = MemoryStore()
    status = store.status()

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(f"Store path: {status['store_path']}")
        print(f"Embedding model: {status['embedding_model']}")
        print(f"Total memories: {status['total_memories']}")
        if status["identitys"]:
            print("Domains:")
            for identity, count in sorted(status["identitys"].items()):
                print(f"  {identity}: {count}")
        else:
            print("Domains: (none)")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List memories."""
    store = MemoryStore()

    # Use a generic query to list
    # (LanceDB doesn't have a simple "list all" so we search with empty-ish query)
    if store._table is None:
        print("No memories stored.")
        return 0

    try:
        query = store._table.search().limit(args.limit)
        if args.identity:
            query = query.where(f'identity = "{args.identity}"')
        results = query.to_list()
    except Exception as e:
        print(f"Error listing memories: {e}", file=sys.stderr)
        return 1

    if args.json:
        memories = [
            {
                "id": r["id"],
                "text": r["text"],
                "source": r["source"],
                "identity": r["identity"],
                "created": r["created"],
            }
            for r in results
        ]
        print(json.dumps({"memories": memories}, indent=2))
    else:
        if not results:
            print("No memories found.")
            return 0

        for r in results:
            text_preview = r["text"][:80] + "..." if len(r["text"]) > 80 else r["text"]
            text_preview = text_preview.replace("\n", " ")
            print(f"{r['id']}  [{r['identity']}] {text_preview}")

    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a memory."""
    store = MemoryStore()
    success = store.delete(args.id)

    if success:
        print(f"Deleted memory {args.id}")
        return 0
    else:
        print(f"Memory {args.id} not found", file=sys.stderr)
        return 1


def cmd_clear(args: argparse.Namespace) -> int:
    """Clear memories."""
    if not args.force:
        if args.identity:
            prompt = f"Clear all memories in identity '{args.identity}'? [y/N] "
        else:
            prompt = "Clear ALL memories? [y/N] "
        response = input(prompt)
        if response.lower() != "y":
            print("Aborted.")
            return 0

    store = MemoryStore()
    count = store.clear(identity=args.identity)

    if args.identity:
        print(f"Cleared {count} memories from identity '{args.identity}'")
    else:
        print(f"Cleared {count} memories")

    return 0


# =============================================================================
# Hooks commands
# =============================================================================

AVAILABLE_HOOKS = {
    "claude": {
        "name": "Claude Code",
        "hooks_dir": Path.home() / ".claude" / "hooks",
        "files": ["PreToolUse.py"],
        "package": "dana.lib.memory.hooks.claude",
    },
}


def get_hook_source_path(target: str, filename: str) -> Path:
    """Get the source path for a hook file from the package."""
    hook_info = AVAILABLE_HOOKS[target]
    package = hook_info["package"]

    # Use importlib.resources to find the hook file in the package
    try:
        if sys.version_info >= (3, 11):
            files = importlib.resources.files(package)
            return Path(str(files.joinpath(filename)))
        else:
            # Python 3.9-3.10 compatibility
            with importlib.resources.path(package, filename) as p:
                return p
    except (ModuleNotFoundError, FileNotFoundError, TypeError):
        # Fall back to __file__-based resolution
        this_dir = Path(__file__).parent
        return this_dir / "hooks" / target / filename


def cmd_hooks_install(args: argparse.Namespace) -> int:
    """Install hooks for an agent system."""
    target = args.target

    if target not in AVAILABLE_HOOKS:
        print(f"Error: Unknown target '{target}'", file=sys.stderr)
        print(f"Available targets: {', '.join(AVAILABLE_HOOKS.keys())}", file=sys.stderr)
        return 1

    hook_info = AVAILABLE_HOOKS[target]
    hooks_dir = hook_info["hooks_dir"]

    # Create hooks directory if needed
    hooks_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    for filename in hook_info["files"]:
        source = get_hook_source_path(target, filename)
        dest = hooks_dir / filename

        if not source.exists():
            print(f"Error: Hook source not found: {source}", file=sys.stderr)
            return 1

        # Copy hook file
        shutil.copy2(source, dest)

        # Make executable
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        installed.append(filename)

    print(f"Installed {hook_info['name']} hooks to {hooks_dir}:")
    for f in installed:
        print(f"  - {f}")

    print()
    print("Configure with environment variables:")
    print("  DANA_MEMORY_ENABLED=1        # Enable memory injection")
    print("  DANA_MEMORY_MIN_SCORE=0.3    # Minimum relevance score")
    print("  DANA_MEMORY_LIMIT=3          # Max memories to inject")
    print("  DANA_MEMORY_DOMAIN=          # Filter by identity (optional)")

    return 0


def cmd_hooks_status(args: argparse.Namespace) -> int:
    """Show status of installed hooks."""
    found_any = False

    for target, hook_info in AVAILABLE_HOOKS.items():
        hooks_dir = hook_info["hooks_dir"]
        print(f"{hook_info['name']} ({target}):")
        print(f"  Directory: {hooks_dir}")

        if not hooks_dir.exists():
            print("  Status: Not installed")
            print()
            continue

        installed = []
        missing = []
        for filename in hook_info["files"]:
            hook_path = hooks_dir / filename
            if hook_path.exists():
                installed.append(filename)
                found_any = True
            else:
                missing.append(filename)

        if installed:
            print(f"  Installed: {', '.join(installed)}")
        if missing:
            print(f"  Missing: {', '.join(missing)}")

        print()

    if not found_any:
        print("No hooks installed. Run 'dana-memory hooks install claude' to install.")

    return 0


def cmd_hooks_uninstall(args: argparse.Namespace) -> int:
    """Uninstall hooks for an agent system."""
    target = args.target

    if target not in AVAILABLE_HOOKS:
        print(f"Error: Unknown target '{target}'", file=sys.stderr)
        print(f"Available targets: {', '.join(AVAILABLE_HOOKS.keys())}", file=sys.stderr)
        return 1

    hook_info = AVAILABLE_HOOKS[target]
    hooks_dir = hook_info["hooks_dir"]

    if not hooks_dir.exists():
        print(f"No hooks installed for {hook_info['name']}")
        return 0

    removed = []
    for filename in hook_info["files"]:
        hook_path = hooks_dir / filename
        if hook_path.exists():
            hook_path.unlink()
            removed.append(filename)

    if removed:
        print(f"Removed {hook_info['name']} hooks:")
        for f in removed:
            print(f"  - {f}")
    else:
        print(f"No hooks found to remove for {hook_info['name']}")

    return 0


def main() -> int:
    """Main CLI entry point."""
    # Check if dependencies are available
    if not _DEPS_AVAILABLE:
        print(
            f"Error: Memory module dependencies not installed.\n"
            f"Install with: pip install dana[memory]\n"
            f"Missing: {_IMPORT_ERROR}",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(
        prog="dana-memory",
        description="Semantic memory store for Dana agents",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # store
    p_store = subparsers.add_parser("store", help="Store a memory")
    p_store.add_argument("text", help="Memory text to store")
    p_store.add_argument("--source", default="agent", help="Memory source (default: agent)")
    p_store.add_argument("--identity", default="general", help="Memory identity (default: general)")
    p_store.add_argument("--json", action="store_true", help="Output as JSON")
    p_store.set_defaults(func=cmd_store)

    # query
    p_query = subparsers.add_parser("query", help="Query memories")
    p_query.add_argument("text", help="Query text")
    p_query.add_argument("--limit", "-n", type=int, default=5, help="Max results (default: 5)")
    p_query.add_argument("--min-score", type=float, default=0.0, help="Min similarity score 0-1")
    p_query.add_argument("--identity", "-d", help="Filter by identity")
    p_query.add_argument("--source", "-s", help="Filter by source")
    p_query.add_argument("--json", action="store_true", help="Output as JSON")
    p_query.set_defaults(func=cmd_query)

    # index
    p_index = subparsers.add_parser("index", help="Index a directory")
    p_index.add_argument("path", help="Directory path to index")
    p_index.add_argument("--identity", default="docs", help="Domain for indexed memories")
    p_index.add_argument("--glob", default="**/*.md", help="File glob pattern (default: **/*.md)")
    p_index.add_argument("--json", action="store_true", help="Output as JSON")
    p_index.set_defaults(func=cmd_index)

    # status
    p_status = subparsers.add_parser("status", help="Show store status")
    p_status.add_argument("--json", action="store_true", help="Output as JSON")
    p_status.set_defaults(func=cmd_status)

    # list
    p_list = subparsers.add_parser("list", help="List memories")
    p_list.add_argument("--identity", "-d", help="Filter by identity")
    p_list.add_argument("--limit", "-n", type=int, default=20, help="Max results (default: 20)")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")
    p_list.set_defaults(func=cmd_list)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a memory by ID")
    p_delete.add_argument("id", help="Memory ID to delete")
    p_delete.set_defaults(func=cmd_delete)

    # clear
    p_clear = subparsers.add_parser("clear", help="Clear memories")
    p_clear.add_argument("--identity", "-d", help="Only clear this identity")
    p_clear.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    p_clear.set_defaults(func=cmd_clear)

    # hooks (with nested subcommands)
    p_hooks = subparsers.add_parser("hooks", help="Manage agent hooks")
    hooks_subparsers = p_hooks.add_subparsers(dest="hooks_command", required=True)

    # hooks install
    p_hooks_install = hooks_subparsers.add_parser("install", help="Install hooks for an agent system")
    p_hooks_install.add_argument("target", nargs="?", default="claude", help="Target agent system (default: claude)")
    p_hooks_install.set_defaults(func=cmd_hooks_install)

    # hooks status
    p_hooks_status = hooks_subparsers.add_parser("status", help="Show installed hooks status")
    p_hooks_status.set_defaults(func=cmd_hooks_status)

    # hooks uninstall
    p_hooks_uninstall = hooks_subparsers.add_parser("uninstall", help="Uninstall hooks for an agent system")
    p_hooks_uninstall.add_argument("target", nargs="?", default="claude", help="Target agent system (default: claude)")
    p_hooks_uninstall.set_defaults(func=cmd_hooks_uninstall)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
