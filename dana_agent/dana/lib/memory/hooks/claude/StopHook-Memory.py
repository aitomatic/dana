#!/usr/bin/env python3
"""Claude Code Stop hook for memory storage.

This hook fires when Claude finishes a turn. It:
1. Scans Claude's response for [REMEMBER: ...] patterns
2. Stores each matched memory via dana-memory

Installation:
    1. Copy this file to ~/.claude/hooks/StopHook-Memory.py
    2. Make it executable: chmod +x ~/.claude/hooks/StopHook-Memory.py
    3. Ensure dana-memory is available in PATH

Configuration (environment variables):
    DANA_MEMORY_ENABLED=1       Enable memory storage (default: 1)
    DANA_MEMORY_IDENTITY=       Default identity for stored memories (default: "agent")
    DANA_PROJECT_PATH=          Path to dana project for uv run (optional)

Usage:
    This hook is called automatically by Claude Code when Claude finishes a turn.
    It reads from stdin (JSON) and writes to stdout (JSON).

    Input: {"stop_reason": "end_turn", "transcript": [...]}
    Output: {"continue": true}

Pattern format in Claude's response:
    [REMEMBER: This project uses pytest with --tb=short]
    [REMEMBER identity=coding: Always run linting before commits]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Any


# Pattern to match [REMEMBER: ...] or [REMEMBER identity=xyz: ...]
REMEMBER_PATTERN = re.compile(
    r'\[REMEMBER(?:\s+identity=([^\]:]+))?\s*:\s*([^\]]+)\]',
    re.IGNORECASE
)


def get_config() -> dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        "enabled": os.getenv("DANA_MEMORY_ENABLED", "1") == "1",
        "default_identity": os.getenv("DANA_MEMORY_IDENTITY", "") or "agent",
        "project_path": os.getenv("DANA_PROJECT_PATH", ""),
    }


def extract_assistant_text(transcript: list[dict[str, Any]]) -> str:
    """Extract text from the last assistant message."""
    for message in reversed(transcript):
        if message.get("role") != "assistant":
            continue

        content = message.get("content", [])
        if isinstance(content, str):
            return content

        # Extract text from content blocks
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif isinstance(block, str):
                text_parts.append(block)

        return "\n".join(text_parts)

    return ""


def find_remember_patterns(text: str) -> list[tuple[str, str]]:
    """Find all [REMEMBER: ...] patterns in text.

    Returns:
        List of (identity, memory_text) tuples
    """
    matches = []
    for match in REMEMBER_PATTERN.finditer(text):
        identity = match.group(1)  # May be None
        memory_text = match.group(2).strip()
        if memory_text:
            matches.append((identity, memory_text))
    return matches


def store_memory(text: str, identity: str, config: dict[str, Any]) -> bool:
    """Store a memory via dana-memory CLI."""
    project_path = config["project_path"]

    if project_path:
        cmd = [
            "uv", "run", "--project", os.path.expanduser(project_path),
            "dana-memory",
        ]
    else:
        cmd = ["dana-memory"]

    cmd.extend([
        "store",
        text,
        "--source", "agent",
        "--identity", identity,
    ])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


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

    transcript = hook_input.get("transcript", [])

    # Extract assistant's response
    assistant_text = extract_assistant_text(transcript)
    if not assistant_text:
        print(json.dumps({"continue": True}))
        return 0

    # Find REMEMBER patterns
    memories = find_remember_patterns(assistant_text)
    if not memories:
        print(json.dumps({"continue": True}))
        return 0

    # Store each memory
    stored_count = 0
    for identity, memory_text in memories:
        # Use provided identity or default
        actual_identity = identity or config["default_identity"]
        if store_memory(memory_text, actual_identity, config):
            stored_count += 1

    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
