#!/usr/bin/env python3
"""Claude Code PreToolUse hook for memory recall.

Part of the dana-memory system:
- PreToolUse (this file): RECALL - retrieves relevant memories before tool use
- Stop: STORE - saves [REMEMBER: ...] patterns after Claude's turn

This hook fires before Claude executes a tool. It:
1. Extracts the last thinking block from the conversation
2. Queries dana-memory for relevant memories
3. Injects relevant memories into Claude's context

Installation:
    1. Copy this file to ~/.claude/hooks/PreToolUseHook-Memory.py
    2. Make it executable: chmod +x ~/.claude/hooks/PreToolUseHook-Memory.py
    3. Ensure dana-memory is available in PATH

Configuration (environment variables):
    DANA_MEMORY_ENABLED=1       Enable memory injection (default: 1)
    DANA_MEMORY_MIN_SCORE=0.3   Minimum relevance score (default: 0.3)
    DANA_MEMORY_LIMIT=3         Max memories to inject (default: 3)
    DANA_MEMORY_MAX_WORDS=1500  Max total words in payload (default: 1500)
    DANA_MEMORY_IDENTITY=         Filter by identity (default: all)
    DANA_MEMORY_TOOLS=          Comma-separated tools to trigger on (default: all)
    DANA_MEMORY_SKIP_TOOLS=     Comma-separated tools to skip (default: Glob,Grep,Bash)

Usage:
    This hook is called automatically by Claude Code before each tool use.
    It reads from stdin (JSON) and writes to stdout (JSON).

    Input: {"tool": "Read", "input": {...}, "transcript": [...]}
    Output: {"continue": true, "message": "Relevant memories: ..."}
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def get_config() -> dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        "enabled": os.getenv("DANA_MEMORY_ENABLED", "1") == "1",
        "min_score": float(os.getenv("DANA_MEMORY_MIN_SCORE", "0.3")),
        "limit": int(os.getenv("DANA_MEMORY_LIMIT", "3")),
        "max_words": int(os.getenv("DANA_MEMORY_MAX_WORDS", "1500")),
        "identity": os.getenv("DANA_MEMORY_IDENTITY", ""),
        "tools": [t.strip() for t in os.getenv("DANA_MEMORY_TOOLS", "").split(",") if t.strip()],
        "skip_tools": [
            t.strip()
            for t in os.getenv("DANA_MEMORY_SKIP_TOOLS", "Glob,Grep,Bash,TaskList,TaskGet").split(",")
            if t.strip()
        ],
    }


# =============================================================================
# Session-based deduplication
# =============================================================================

def get_session_id(transcript: list[dict[str, Any]]) -> str:
    """Generate session ID from first transcript message."""
    if not transcript:
        return "empty"
    first_msg = transcript[0]
    content = str(first_msg.get("content", ""))[:500]
    return hashlib.md5(content.encode()).hexdigest()[:12]


def get_cache_path(session_id: str) -> Path:
    """Get path to session cache file."""
    return Path(f"/tmp/dana-memory-{session_id}.json")


def load_injected_ids(session_id: str) -> set[str]:
    """Load set of already-injected memory IDs for this session."""
    cache_path = get_cache_path(session_id)
    try:
        if cache_path.exists():
            data = json.loads(cache_path.read_text())
            return set(data.get("injected_ids", []))
    except (json.JSONDecodeError, OSError):
        pass
    return set()


def save_injected_ids(session_id: str, ids: set[str]) -> None:
    """Save injected memory IDs for this session."""
    cache_path = get_cache_path(session_id)
    try:
        cache_path.write_text(json.dumps({"injected_ids": list(ids)}))
    except OSError:
        pass


def extract_last_thinking(transcript: list[dict[str, Any]]) -> str:
    """Extract the last thinking block from the transcript.

    Claude's thinking blocks contain reasoning about what to do next,
    which is ideal for semantic memory retrieval.
    """
    # Walk transcript backwards to find the last assistant message with thinking
    for message in reversed(transcript):
        if message.get("role") != "assistant":
            continue

        content = message.get("content", [])
        if isinstance(content, str):
            continue

        # Look for thinking blocks in content
        for block in reversed(content):
            if isinstance(block, dict) and block.get("type") == "thinking":
                thinking = block.get("thinking", "")
                if thinking:
                    return thinking

    return ""


def extract_recent_context(transcript: list[dict[str, Any]], max_chars: int = 2000) -> str:
    """Extract recent context from transcript if no thinking block found.

    Falls back to recent user messages and assistant responses.
    """
    context_parts = []
    total_chars = 0

    for message in reversed(transcript):
        role = message.get("role", "")
        content = message.get("content", "")

        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = " ".join(text_parts)

        if content and role in ("user", "assistant"):
            context_parts.append(f"{role}: {content[:500]}")
            total_chars += len(content[:500])

            if total_chars >= max_chars:
                break

    return "\n".join(reversed(context_parts))


def query_memories(query: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Query dana-memory for relevant memories."""
    # Get project path for uv run (required if dana-memory not in PATH)
    project_path = os.getenv("DANA_PROJECT_PATH", "")

    if project_path:
        cmd = [
            "uv", "run", "--project", os.path.expanduser(project_path),
            "dana-memory",
        ]
    else:
        cmd = ["dana-memory"]

    cmd.extend([
        "query",
        query[-1500:],  # Limit query length
        "--limit",
        str(config["limit"] * 2),  # Fetch extra for filtering
        "--json",
    ])

    if config["identity"]:
        cmd.extend(["--identity", config["identity"]])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout (model loading can be slow)
        )

        if result.returncode != 0:
            return []

        # Parse JSON output, handling potential logging prefix
        stdout = result.stdout.strip()
        # Find the JSON part (starts with {)
        json_start = stdout.find("{")
        if json_start == -1:
            return []

        data = json.loads(stdout[json_start:])
        memories = data.get("memories", [])

        # Filter by min_score
        return [m for m in memories if m.get("score", 0) >= config["min_score"]][: config["limit"]]

    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []


def format_memories(memories: list[dict[str, Any]], max_words: int = 1500) -> str:
    """Format memories for injection into Claude's context.

    Args:
        memories: List of memory dicts with text, score, identity fields
        max_words: Maximum total words across all memories (default: 1500)
    """
    if not memories:
        return ""

    lines = ["**Relevant memories:**"]
    total_words = 0

    for m in memories:
        score = m.get("score", 0)
        text = m.get("text", "")
        identity = m.get("identity", "")

        memory_words = len(text.split())

        # Check if adding this memory would exceed the limit
        if total_words + memory_words > max_words:
            # Truncate to fit remaining budget
            remaining = max_words - total_words
            if remaining > 0:
                text = " ".join(text.split()[:remaining]) + "..."
                lines.append(f"- [{score:.2f}] [{identity}] {text}")
            break

        total_words += memory_words
        lines.append(f"- [{score:.2f}] [{identity}] {text}")

    # Infer identity from most recent memory
    recent_identity = None
    for m in memories:
        if m.get("identity"):
            recent_identity = m.get("identity")
            break  # First in list is most recent/relevant

    lines.append("")
    if recent_identity:
        lines.append(f"_You are **{recent_identity}**. Use [REMEMBER identity={recent_identity}: ...] to save discoveries._")
    else:
        lines.append("_Use [REMEMBER identity=<your-agent>: ...] to save discoveries._")

    return "\n".join(lines)


def should_process_tool(tool_name: str, config: dict[str, Any]) -> bool:
    """Check if this tool should trigger memory lookup."""
    # Skip if tool is in skip list
    if tool_name in config["skip_tools"]:
        return False

    # If specific tools are configured, only process those
    if config["tools"]:
        return tool_name in config["tools"]

    return True


def main() -> int:
    """Main hook entry point."""
    config = get_config()

    # Check if enabled
    if not config["enabled"]:
        print(json.dumps({"continue": True}))
        return 0

    # Read hook input
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    tool_name = hook_input.get("tool", "")
    transcript = hook_input.get("transcript", [])

    # Check if we should process this tool
    if not should_process_tool(tool_name, config):
        print(json.dumps({"continue": True}))
        return 0

    # Extract context for query
    thinking = extract_last_thinking(transcript)
    if not thinking or len(thinking) < 50:
        # Fall back to recent context
        thinking = extract_recent_context(transcript)

    if not thinking or len(thinking) < 50:
        # Not enough context
        print(json.dumps({"continue": True}))
        return 0

    # Get session ID and load already-injected memories
    session_id = get_session_id(transcript)
    injected_ids = load_injected_ids(session_id)

    # Query memories
    memories = query_memories(thinking, config)

    if not memories:
        print(json.dumps({"continue": True}))
        return 0

    # Filter out already-injected memories
    new_memories = [m for m in memories if m.get("id") not in injected_ids]

    if not new_memories:
        print(json.dumps({"continue": True}))
        return 0

    # Track newly injected IDs
    new_ids = {m.get("id") for m in new_memories if m.get("id")}
    save_injected_ids(session_id, injected_ids | new_ids)

    # Format and inject
    message = format_memories(new_memories, max_words=config["max_words"])
    print(json.dumps({"continue": True, "message": message}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
