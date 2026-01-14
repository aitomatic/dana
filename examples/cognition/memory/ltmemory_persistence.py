#!/usr/bin/env python3
"""
LTMemory Persistence Example

Demonstrates cross-session memory persistence and retrieval.
"""

import shutil
import tempfile
from pathlib import Path

from dana.core.memory import LTMemory


def main():
    print("=" * 60)
    print("LTMemory Persistence - Cross-Session Memory Recall")
    print("=" * 60)

    # Use a temp directory for demo
    demo_path = Path(tempfile.mkdtemp()) / "memories"

    try:
        # === Session 1: Store knowledge ===
        print("\n--- SESSION 1: Learning ---")

        ltmem1 = LTMemory(path=str(demo_path))
        print(f"Memory path: {demo_path}")
        print(f"Initial memory count: {ltmem1.count()}")

        # Store various memory types
        ltmem1.store({
            "type": "lesson",
            "content": "Auth bugs often relate to token expiry edge cases",
            "context": "debugging session",
        })

        ltmem1.store({
            "type": "episode",
            "content": "Helped user debug logout issue. Root cause was missing token refresh.",
            "context": "user support",
        })

        ltmem1.store({
            "type": "fact",
            "content": "Auth module uses JWT with 1hr expiry configured in config/auth.yaml",
            "context": "codebase exploration",
        })

        print(f"After storing: {ltmem1.count()} memories")

        # Show what's stored
        print("\nStored memories file content:")
        print("-" * 40)
        content = demo_path.joinpath("memories.md").read_text()
        # Show first part of content
        lines = content.strip().split("\n")
        for line in lines[:15]:
            print(f"  {line}")
        if len(lines) > 15:
            print("  ...")

        # === Session 2: New instance recalls knowledge ===
        print("\n--- SESSION 2: Recalling (New Instance) ---")

        # Create new LTMemory pointing to same path
        ltmem2 = LTMemory(path=str(demo_path))
        print(f"New session, same path: {ltmem2.count()} memories found")

        # Query past knowledge
        print("\nQuerying: 'What do I know about auth issues?'")
        print("-" * 40)
        result = ltmem2.query("What do I know about auth issues?")
        print(result)

    finally:
        # Cleanup
        shutil.rmtree(demo_path.parent)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
