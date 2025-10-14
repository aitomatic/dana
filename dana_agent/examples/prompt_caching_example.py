"""
Example: Using Anthropic Prompt Caching

This example demonstrates how to use Anthropic's prompt caching feature
to reduce costs and latency for repeated requests with the same system prompt.

Prompt caching is especially useful for:
- Long system prompts (documentation, examples, guidelines)
- Repeated conversational contexts
- Multi-turn conversations with static context

Cost savings: ~90% reduction on cached tokens
"""

import asyncio

from dana.common.llm import LLM
from dana.common.llm.types import LLMMessage


async def example_basic_system_cache():
    """Example: Cache a system prompt across multiple requests."""
    print("\n" + "=" * 70)
    print("Example 1: System Prompt Caching")
    print("=" * 70)

    llm = LLM(provider="anthropic", model="claude-3-5-sonnet-20241022")

    # Long system prompt with cache_control
    system_prompt = """You are an expert Python developer with deep knowledge of:
    - Async/await patterns and best practices
    - Type hints and mypy
    - Testing with pytest
    - Performance optimization
    - Design patterns (SOLID, DRY, KISS)

    Always provide:
    1. Clear, well-documented code
    2. Type hints for all functions
    3. Error handling
    4. Performance considerations
    5. Testing recommendations
    """

    messages = [
        LLMMessage(
            role="system",
            content=system_prompt,
            cache_control={"type": "ephemeral"},  # Cache this system prompt
        ),
        LLMMessage(role="user", content="Write a function to calculate fibonacci numbers"),
    ]

    # First call - creates cache
    print("🔵 First call (creates cache)...")
    response1 = await llm.chat_response(messages)
    print(f"Response: {response1.content[:100]}...")
    print(f"Usage: {response1.usage}")

    # Second call with same system prompt - uses cache
    messages[1] = LLMMessage(role="user", content="Now write a function to check if a number is prime")

    print("\n🟢 Second call (uses cache)...")
    response2 = await llm.chat_response(messages)
    print(f"Response: {response2.content[:100]}...")
    print(f"Usage: {response2.usage}")
    print("\n✨ Notice the reduced input tokens in the second call!")


async def example_conversation_context_cache():
    """Example: Cache conversation history in multi-turn dialogue."""
    print("\n" + "=" * 70)
    print("Example 2: Caching Conversation History")
    print("=" * 70)

    llm = LLM(provider="anthropic", model="claude-3-5-sonnet-20241022")

    # Build conversation with the last user message marked for caching
    messages = [
        LLMMessage(role="system", content="You are a helpful coding assistant.", cache_control={"type": "ephemeral"}),
        LLMMessage(role="user", content="What is a closure in Python?"),
        LLMMessage(role="assistant", content="A closure is a function that..."),
        LLMMessage(role="user", content="Can you show an example?"),
        LLMMessage(role="assistant", content="Sure! Here's an example..."),
        LLMMessage(
            role="user",
            content="Now explain decorators",
            cache_control={"type": "ephemeral"},  # Cache up to this point
        ),
    ]

    print("🔵 Calling with cached conversation history...")
    response = await llm.chat_response(messages, max_tokens=500)
    print(f"Response: {response.content[:150]}...")
    print(f"Usage: {response.usage}")


async def example_documentation_cache():
    """Example: Cache long documentation context."""
    print("\n" + "=" * 70)
    print("Example 3: Caching API Documentation")
    print("=" * 70)

    llm = LLM(provider="anthropic", model="claude-3-5-sonnet-20241022")

    # Simulate long API documentation
    api_docs = """
    API Documentation for MyService:

    GET /api/users
    - Returns list of users
    - Query params: limit (int), offset (int), filter (string)
    - Response: { users: User[], total: int }

    POST /api/users
    - Creates a new user
    - Body: { name: string, email: string, role: string }
    - Response: { user: User, id: string }

    GET /api/users/{id}
    - Returns specific user
    - Path params: id (string)
    - Response: { user: User }

    [... imagine this is 10,000+ tokens of documentation ...]
    """

    messages = [
        LLMMessage(
            role="system",
            content="You are an API expert. Use the following documentation to answer questions.",
            cache_control={"type": "ephemeral"},
        ),
        LLMMessage(
            role="user",
            content=api_docs,
            cache_control={"type": "ephemeral"},  # Cache the documentation
        ),
        LLMMessage(role="user", content="How do I create a new user?"),
    ]

    print("🔵 Calling with cached API docs...")
    response = await llm.chat_response(messages, max_tokens=300)
    print(f"Response: {response.content}")
    print(f"Usage: {response.usage}")


async def main():
    """Run all examples."""
    print("\n🚀 Anthropic Prompt Caching Examples")
    print("=" * 70)

    await example_basic_system_cache()
    await example_conversation_context_cache()
    await example_documentation_cache()

    print("\n" + "=" * 70)
    print("📊 Cost Savings Summary:")
    print("=" * 70)
    print("✅ Cached tokens cost ~90% less than regular tokens")
    print("✅ Best for: long prompts (>1024 tokens) used multiple times")
    print("✅ Cache persists for ~5 minutes of inactivity")
    print("\n💡 Tip: Only cache prompts you'll reuse within 5 minutes!")


if __name__ == "__main__":
    asyncio.run(main())
