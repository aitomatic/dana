# LLM Integration API Reference

## Overview

Dana provides the `LLM` class for integrating with various LLM providers.

**Location**: `dana/common/llm/llm.py`

## Basic Usage

```python
from dana.common.llm.llm import LLM, LLMMessage

# Initialize LLM
llm = LLM(provider="anthropic", model="claude-3-5-sonnet-20241022")

# Make async call
async def call_llm():
    response = await llm.chat_response(
        messages=[LLMMessage(role="user", content="Hello")],
        system_message="You are a helpful assistant",
        max_tokens=500,
        temperature=0.7
    )
    return response.content

# Use in sync context
import asyncio
result = asyncio.run(call_llm())
```

## Supported Providers

- `"anthropic"` - Claude models
- `"openai"` - GPT models
- `"groq"` - Groq models
- `"deepseek"` - DeepSeek models

## See Examples

**Best examples in codebase**:
- `dana/lib/resources/conversation.py` - LLM-powered resource
- `contrib/expert_interview/resources/` - Analysis resources

For detailed usage, refer to these implementations.
