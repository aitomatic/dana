#!/usr/bin/env python3
"""
Agent with Memory - Full Demo

Demonstrates both STMemory (session timeline) and LTMemory (persistent knowledge)
working together to enable learning across sessions.
"""

import shutil
import tempfile
from pathlib import Path

from dana.core.memory import LTMemory, STMemory


def simulate_session(session_num: int, stmem: STMemory, ltmem: LTMemory):
    """Simulate an agent session with memory."""
    print(f"\n{'='*60}")
    print(f"SESSION {session_num}")
    print("=" * 60)

    if session_num == 1:
        # First session: Debug auth issue
        print("\nUser: 'Find the auth bug'")
        stmem.append("user", "Find the auth bug")

        # Check if we have past knowledge
        past_auth = ltmem.query("What do I know about auth bugs?")
        print(f"\nRecalling past knowledge about auth bugs...")
        print(f"  -> {past_auth}")

        # Agent works on the problem
        stmem.append("agent", "Searching codebase for auth-related files...")
        stmem.append("observation", "Found auth modules: login.py, token.py, session.py")
        stmem.append("agent", "Analyzing token.py...")
        stmem.append("observation", "Token expiry not checked in refresh flow")
        stmem.append("agent", "Fixed by adding expiry validation")

        print("\nSession work complete. Timeline:")
        print("-" * 40)
        print(stmem.to_text())

        # End of session: Store lessons learned
        ltmem.store({
            "type": "lesson",
            "content": "Auth bugs often relate to token expiry edge cases. Check refresh flow.",
            "context": "debugging session",
        })
        ltmem.store({
            "type": "episode",
            "content": "Fixed auth bug where token expiry wasn't checked in refresh flow.",
            "context": "bug fix",
        })
        print(f"\nStored {ltmem.count()} memories to long-term storage")

    elif session_num == 2:
        # Second session: Similar issue
        print("\nUser: 'Users are getting logged out unexpectedly'")
        stmem.append("user", "Users are getting logged out unexpectedly")

        # Check past knowledge - this time we have it!
        past_auth = ltmem.query("What do I know about auth bugs and logout issues?")
        print(f"\nRecalling past knowledge...")
        print("-" * 40)
        print(past_auth)
        print("-" * 40)

        stmem.append("agent", "Based on past experience, checking token expiry...")
        stmem.append("observation", "Found similar issue - token not refreshed before API call")
        stmem.append("agent", "Fixed by adding proactive token refresh")

        print("\nSession work complete. Timeline:")
        print("-" * 40)
        print(stmem.to_text())

        # Store new learning
        ltmem.store({
            "type": "lesson",
            "content": "Unexpected logouts often caused by stale tokens. Add proactive refresh.",
            "context": "debugging session",
        })
        print(f"\nTotal memories: {ltmem.count()}")


def main():
    print("=" * 60)
    print("Agent with Memory - Full Demo")
    print("=" * 60)
    print("\nThis demo shows how an agent learns across sessions:")
    print("- STMemory tracks the current session timeline")
    print("- LTMemory persists lessons for future sessions")

    # Use temp directory for demo
    demo_path = Path(tempfile.mkdtemp()) / "memories"

    try:
        # Session 1
        stmem1 = STMemory(max_entries=100)
        ltmem = LTMemory(path=str(demo_path))
        simulate_session(1, stmem1, ltmem)

        # Session 2 - New STMemory (new session), same LTMemory (persistent)
        stmem2 = STMemory(max_entries=100)
        ltmem2 = LTMemory(path=str(demo_path))  # Same path = same memories
        simulate_session(2, stmem2, ltmem2)

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"\nSession 1 timeline entries: {len(stmem1)}")
        print(f"Session 2 timeline entries: {len(stmem2)}")
        print(f"Total long-term memories: {ltmem2.count()}")

        print("\nKey insight: In Session 2, the agent immediately knew to check")
        print("token expiry because it REMEMBERED the lesson from Session 1!")

    finally:
        shutil.rmtree(demo_path.parent)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
