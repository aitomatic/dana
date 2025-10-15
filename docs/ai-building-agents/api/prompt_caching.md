# Anthropic Prompt Caching Guide

## Overview

Anthropic's prompt caching feature allows you to cache parts of your prompts to reduce costs and latency for repeated requests. Cached tokens cost **90% less** than regular tokens.

## When to Use Caching

✅ **Good use cases:**
- Long system prompts (>1024 tokens) that don't change
- API documentation or code context
- Multi-turn conversations with static context
- Repeated requests within 5 minutes

❌ **Don't cache if:**
- Prompt changes frequently
- Prompt is short (<1024 tokens)
- Requests are >5 minutes apart (cache expires)

## How It Works

1. **Cache Duration**: ~5 minutes of inactivity
2. **Minimum Size**: 1024 tokens (Anthropic's requirement)
3. **Cost Savings**: ~90% reduction on cached tokens
4. **Models**: Only works with Claude 3+ models (Sonnet, Opus, Haiku)
5. **Beta Header**: Automatically included (`anthropic-beta: prompt-caching-2024-07-31`)

## Usage

### Basic System Prompt Caching

```python
from dana.common.llm import LLM
from dana.common.llm.types import LLMMessage

llm = LLM(provider="anthropic", model="claude-3-5-sonnet-20241022")

messages = [
    LLMMessage(
        role="system",
        content="Long system prompt here...",
        cache_control={"type": "ephemeral"}  # ← Enable caching
    ),
    LLMMessage(role="user", content="Your question here")
]

response = await llm.chat_response(messages)
```

### Caching User Messages

You can also cache user messages (useful for long documentation):

```python
messages = [
    LLMMessage(
        role="system",
        content="You are a helpful assistant",
        cache_control={"type": "ephemeral"}
    ),
    LLMMessage(
        role="user",
        content="<very long documentation here>",
        cache_control={"type": "ephemeral"}  # Cache this too
    ),
    LLMMessage(
        role="user",
        content="Question about the docs?"
    )
]
```

### Multi-Turn Conversations

Cache the conversation history to save on repeated context:

```python
# Initial conversation
messages = [
    LLMMessage(role="system", content="You are helpful", cache_control={"type": "ephemeral"}),
    LLMMessage(role="user", content="First question"),
]
response1 = await llm.chat_response(messages)

# Add to conversation and cache up to a certain point
messages.extend([
    LLMMessage(role="assistant", content=response1.content),
    LLMMessage(role="user", content="Second question", cache_control={"type": "ephemeral"})
])
response2 = await llm.chat_response(messages)
# The system prompt and conversation history are now cached!
```

## Cache Placement Strategy

Anthropic processes cache_control markers in order:
1. Only the **last** cache_control in system messages is used
2. You can have **multiple** cache points in conversation messages
3. Place cache_control at **strategic breakpoints** (e.g., after docs, before Q&A)

### Example: Multiple Cache Points

```python
messages = [
    # Cache the system prompt
    LLMMessage(
        role="system",
        content="System instructions...",
        cache_control={"type": "ephemeral"}
    ),
    # Cache the documentation
    LLMMessage(
        role="user",
        content="<long API documentation>",
        cache_control={"type": "ephemeral"}
    ),
    # Cache the conversation context
    LLMMessage(role="user", content="Question 1"),
    LLMMessage(role="assistant", content="Answer 1"),
    LLMMessage(role="user", content="Question 2"),
    LLMMessage(role="assistant", content="Answer 2"),
    LLMMessage(
        role="user",
        content="Question 3",
        cache_control={"type": "ephemeral"}  # Cache all conversation up to here
    ),
]
```

## Cost Analysis

### Without Caching
```
Input: 10,000 tokens × $3.00/MTok = $0.030
Output: 1,000 tokens × $15.00/MTok = $0.015
Total per request: $0.045
10 requests: $0.45
```

### With Caching (after first request)
```
Cached: 8,000 tokens × $0.30/MTok = $0.0024
Fresh: 2,000 tokens × $3.00/MTok = $0.006
Output: 1,000 tokens × $15.00/MTok = $0.015
Total per request: $0.0234
10 requests: $0.0234 × 9 + $0.045 = $0.2556

Savings: 43% on multi-request scenarios!
```

## Monitoring Cache Usage

Check the response usage to see cache hits:

```python
response = await llm.chat_response(messages)
print(response.usage)
# {
#   'prompt_tokens': 2000,
#   'completion_tokens': 500,
#   'total_tokens': 2500,
#   'cache_creation_input_tokens': 8000,  # First call only
#   'cache_read_input_tokens': 8000       # Subsequent calls
# }
```

## Best Practices

1. **Cache Long, Static Content**: System prompts, docs, examples
2. **Strategic Breakpoints**: Cache after docs but before dynamic content
3. **Reuse Within 5min**: Group requests to maximize cache hits
4. **Monitor Usage**: Check `cache_read_input_tokens` to verify caching
5. **Minimum 1024 tokens**: Anthropic only caches segments >1024 tokens

## Examples

See `scripts/prompt_caching_example.py` for complete working examples.

## References

- [Anthropic Prompt Caching Docs](https://docs.anthropic.com/claude/docs/prompt-caching)
- [Pricing Information](https://www.anthropic.com/pricing)
