#!/usr/bin/env python3
"""Claude Code PreToolUse hook for semantic memory injection.

This hook fires before Claude executes a tool. It:
1. Extracts the last thinking block from the conversation
2. Queries dana-memory for relevant memories
3. Injects relevant memories into Claude's context

Installation:
    1. Copy this file to ~/.claude/hooks/PreToolUse.py
    2. Make it executable: chmod +x ~/.claude/hooks/PreToolUse.py
    3. Ensure dana-memory is available in PATH

Configuration (environment variables):
    DANA_MEMORY_ENABLED=1       Enable memory injection (default: 1)
    DANA_MEMORY_MIN_SCORE=0.3   Minimum relevance score (default: 0.3)
    DANA_MEMORY_LIMIT=3         Max memories to inject (default: 3)
    DANA_MEMORY_DOMAIN=         Filter by domain (default: all)
    DANA_MEMORY_TOOLS=          Comma-separated tools to trigger on (default: all)
    DANA_MEMORY_SKIP_TOOLS=     Comma-separated tools to skip (default: Glob,Grep,Bash)

Usage:
    This hook is called automatically by Claude Code before each tool use.
    It reads from stdin (JSON) and writes to stdout (JSON).

    Input: {"tool": "Read", "input": {...}, "transcript": [...]}
    Output: {"continue": true, "message": "Relevant memories: ..."}
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Any


def get_config() -> dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        "enabled": os.getenv("DANA_MEMORY_ENABLED", "1") == "1",
        "min_score": float(os.getenv("DANA_MEMORY_MIN_SCORE", "0.3")),
        "limit": int(os.getenv("DANA_MEMORY_LIMIT", "3")),
        "domain": os.getenv("DANA_MEMORY_DOMAIN", ""),
        "tools": [t.strip() for t in os.getenv("DANA_MEMORY_TOOLS", "").split(",") if t.strip()],
        "skip_tools": [
            t.strip()
            for t in os.getenv("DANA_MEMORY_SKIP_TOOLS", "Glob,Grep,Bash,TaskList,TaskGet").split(",")
            if t.strip()
        ],
    }


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
    cmd = [
        "dana-memory",
        "query",
        query[-1500:],  # Limit query length
        "--limit",
        str(config["limit"] * 2),  # Fetch extra for filtering
        "--json",
    ]

    if config["domain"]:
        cmd.extend(["--domain", config["domain"]])

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


def format_memories(memories: list[dict[str, Any]]) -> str:
    """Format memories for injection into Claude's context."""
    if not memories:
        return ""

    lines = ["**Relevant memories:**"]
    for m in memories:
        score = m.get("score", 0)
        text = m.get("text", "")
        domain = m.get("domain", "")

        # Truncate long memories
        if len(text) > 200:
            text = text[:200] + "..."

        lines.append(f"- [{score:.2f}] [{domain}] {text}")

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

    # Query memories
    memories = query_memories(thinking, config)

    if not memories:
        print(json.dumps({"continue": True}))
        return 0

    # Format and inject
    message = format_memories(memories)
    print(json.dumps({"continue": True, "message": message}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
