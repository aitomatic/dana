#!/usr/bin/env python3
"""Smart context assembly with ContextBuilder.

This example demonstrates how ContextBuilder automatically handles
different source types:
- Strings: included directly if they fit the budget
- RLMResource/LTMemory: queried via RLM with the task context

Run: python examples/cognition/context/smart_context_assembly.py
"""

import tempfile
from pathlib import Path

from dana.common.resource import RLMResource
from dana.core.context import ContextBuilder
from dana.core.memory import LTMemory


def main():
    print("=" * 60)
    print("ContextBuilder Demo: Smart Context Assembly")
    print("=" * 60)

    # Create temporary directory for demo files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # 1. Create some sample data sources
        print("\n--- Setting Up Sources ---\n")

        # Timeline (small, will be included directly)
        timeline_text = """
[10:00] User: Help me review the authentication code
[10:01] Agent: I'll analyze the auth module for security issues
[10:05] Agent: Found potential token expiry bug in verify_token()
        """.strip()
        print(f"Timeline: {len(timeline_text)} chars (direct inclusion)")

        # LTMemory (uses RLM query)
        ltmem_path = tmpdir / "memories"
        ltmem = LTMemory(path=str(ltmem_path))
        ltmem.store({
            "type": "lesson",
            "content": "Auth bugs often relate to token expiry edge cases",
            "context": "past debugging session",
        })
        ltmem.store({
            "type": "fact",
            "content": "JWT tokens should have short expiry times (15 min)",
            "context": "security best practices",
        })
        print(f"LTMemory: {ltmem.count()} memories stored (RLM query)")

        # RLMResource for codebase (uses RLM query)
        codebase_file = tmpdir / "codebase.md"
        codebase_file.write_text("""
# Auth Module

## src/auth/login.py
```python
def login(username: str, password: str) -> str:
    user = db.get_user(username)
    if not user or not verify_password(password, user.hash):
        raise AuthError("Invalid credentials")
    return create_token(user.id)
```

## src/auth/token.py
```python
def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # BUG: Not checking token expiry!
        return payload
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")

def create_token(user_id: int) -> str:
    payload = {"user_id": user_id, "exp": time.time() + 3600}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```
        """)
        codebase = RLMResource(file=str(codebase_file))
        print(f"Codebase: {len(codebase_file.read_text())} chars (RLM query)")

        # 2. Build context with ContextBuilder
        print("\n--- Building Context ---\n")

        ctx = ContextBuilder(token_budget=50000)
        ctx.add_source("timeline", timeline_text)
        ctx.add_source("ltmemory", ltmem)
        ctx.add_source("codebase", codebase)

        task = "Find security vulnerabilities in authentication"
        print(f'Task: "{task}"\n')

        context = ctx.build(task=task)

        # 3. Show results
        print("--- Results ---\n")
        print(f"Token budget: {context.budget:,}")
        print(f"Tokens used: {context.tokens_used:,}")
        print(f"Sources used: {context.sources_used}")
        print()
        print("Assembled context preview (first 500 chars):")
        print("-" * 40)
        print(context.text[:500] + "..." if len(context.text) > 500 else context.text)
        print("-" * 40)

        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)


if __name__ == "__main__":
    main()
