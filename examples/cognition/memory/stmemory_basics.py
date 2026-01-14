#!/usr/bin/env python3
"""
STMemory Basics Example

Demonstrates session timeline tracking with STMemory.
"""

from dana.core.memory import STMemory


def main():
    print("=" * 60)
    print("STMemory Basics - Session Timeline Tracking")
    print("=" * 60)

    # Create a session memory with small limit for demo
    stmem = STMemory(max_entries=5)

    # Simulate a debugging session
    print("\n1. Recording session events...")
    stmem.append("user", "Find the auth bug")
    stmem.append("agent", "Searching codebase for auth-related files...")
    stmem.append("observation", "Found 3 auth modules: login.py, token.py, session.py")
    stmem.append("agent", "Analyzing token.py...")
    stmem.append("observation", "Token expiry not checked in refresh flow")
    stmem.append("agent", "Fixed by adding expiry validation")

    # Show timeline
    print("\n2. Full Timeline:")
    print("-" * 40)
    print(stmem.to_text())

    # Note: We started with 6 entries but max is 5
    print(f"\n3. Entry count: {len(stmem)} (max was 5, so oldest dropped)")

    # Get recent entries
    print("\n4. Most recent 2 entries:")
    print("-" * 40)
    for entry in stmem.recent(2):
        print(f"  [{entry.role}] {entry.content}")

    # Token estimation
    print(f"\n5. Estimated tokens: {stmem.estimate_tokens()}")

    # Clear memory
    stmem.clear()
    print(f"\n6. After clear: {len(stmem)} entries")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
