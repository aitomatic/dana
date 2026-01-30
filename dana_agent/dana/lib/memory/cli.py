"""CLI for dana-memory.

Usage:
    dana-memory store "memory text" [--source SOURCE] [--domain DOMAIN]
    dana-memory query "query text" [--limit N] [--min-score F] [--domain D] [--json]
    dana-memory index PATH [--domain DOMAIN] [--glob PATTERN]
    dana-memory status
    dana-memory list [--domain DOMAIN] [--limit N]
    dana-memory delete ID
    dana-memory clear [--domain DOMAIN] [--force]

Requires: pip install dana[memory]
"""

from __future__ import annotations

import argparse
import json
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
        domain=args.domain,
    )

    if args.json:
        print(json.dumps(memory.to_dict(), indent=2))
    else:
        print(f"Stored memory {memory.id} in domain '{memory.domain}'")

    return 0


def cmd_query(args: argparse.Namespace) -> int:
    """Query memories."""
    store = MemoryStore()
    memories = store.query(
        text=args.text,
        limit=args.limit,
        min_score=args.min_score,
        domain=args.domain,
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
            print(f"       domain={m.domain} source={m.source} created={m.created.date()}")
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
        domain=args.domain,
        glob_pattern=args.glob,
    )

    if args.json:
        print(json.dumps({"indexed": count, "path": str(path), "domain": args.domain}))
    else:
        print(f"Indexed {count} memories into domain '{args.domain}'")

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
        if status["domains"]:
            print("Domains:")
            for domain, count in sorted(status["domains"].items()):
                print(f"  {domain}: {count}")
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
        if args.domain:
            query = query.where(f'domain = "{args.domain}"')
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
                "domain": r["domain"],
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
            print(f"{r['id']}  [{r['domain']}] {text_preview}")

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
        if args.domain:
            prompt = f"Clear all memories in domain '{args.domain}'? [y/N] "
        else:
            prompt = "Clear ALL memories? [y/N] "
        response = input(prompt)
        if response.lower() != "y":
            print("Aborted.")
            return 0

    store = MemoryStore()
    count = store.clear(domain=args.domain)

    if args.domain:
        print(f"Cleared {count} memories from domain '{args.domain}'")
    else:
        print(f"Cleared {count} memories")

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
    p_store.add_argument("--domain", default="general", help="Memory domain (default: general)")
    p_store.add_argument("--json", action="store_true", help="Output as JSON")
    p_store.set_defaults(func=cmd_store)

    # query
    p_query = subparsers.add_parser("query", help="Query memories")
    p_query.add_argument("text", help="Query text")
    p_query.add_argument("--limit", "-n", type=int, default=5, help="Max results (default: 5)")
    p_query.add_argument("--min-score", type=float, default=0.0, help="Min similarity score 0-1")
    p_query.add_argument("--domain", "-d", help="Filter by domain")
    p_query.add_argument("--source", "-s", help="Filter by source")
    p_query.add_argument("--json", action="store_true", help="Output as JSON")
    p_query.set_defaults(func=cmd_query)

    # index
    p_index = subparsers.add_parser("index", help="Index a directory")
    p_index.add_argument("path", help="Directory path to index")
    p_index.add_argument("--domain", default="docs", help="Domain for indexed memories")
    p_index.add_argument("--glob", default="**/*.md", help="File glob pattern (default: **/*.md)")
    p_index.add_argument("--json", action="store_true", help="Output as JSON")
    p_index.set_defaults(func=cmd_index)

    # status
    p_status = subparsers.add_parser("status", help="Show store status")
    p_status.add_argument("--json", action="store_true", help="Output as JSON")
    p_status.set_defaults(func=cmd_status)

    # list
    p_list = subparsers.add_parser("list", help="List memories")
    p_list.add_argument("--domain", "-d", help="Filter by domain")
    p_list.add_argument("--limit", "-n", type=int, default=20, help="Max results (default: 20)")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")
    p_list.set_defaults(func=cmd_list)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a memory by ID")
    p_delete.add_argument("id", help="Memory ID to delete")
    p_delete.set_defaults(func=cmd_delete)

    # clear
    p_clear = subparsers.add_parser("clear", help="Clear memories")
    p_clear.add_argument("--domain", "-d", help="Only clear this domain")
    p_clear.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    p_clear.set_defaults(func=cmd_clear)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
