# Codec Guide: Getting Started with Structured LLM Communication

> **Looking for advanced details?** See [codec-advanced.md](./codec-advanced.md) for comprehensive implementation details, debugging guides, and architecture deep-dives.

This guide shows you how to use codecs to enable structured communication between your Dana agents and LLMs. We'll use the Financial Analysis Agent example from `examples/agents/financial-analysis` as our primary reference.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Understanding Codec Formats](#2-understanding-codec-formats)
3. [Using CSXMLCodec](#3-using-csxmlcodec)
4. [Using KLXMLCodec](#4-using-klxmlcodec)
5. [Quick Integration Guide](#5-quick-integration-guide)

---

## 1. Introduction

### What Are Codecs?

**Codecs** (encoder-decoder) in Dana are structured format specifications that define how LLMs should format their responses. They provide a standardized way for agents to:

- **Parse LLM reasoning** separate from actions
- **Extract structured tool calls** from text responses
- **Enable reliable tool execution** by parsing well-defined formats

### Why Do Codecs Matter?

Without codecs, LLM responses are free-form text that's difficult to parse reliably:

**Without Codecs:**
```
I need to calculate the current ratio. Let me search for current assets and
current liabilities in the balance sheet, then I'll divide them...
```
*Problem: How do we extract the tool call? Is this just reasoning or an action?*

**With Codecs:**
```xml
<thinking>
User wants current ratio calculation. I need to find current assets and current liabilities
from the balance sheet. I'll use semantic search to locate the balance sheet section.
</thinking>

<function_call>
  <invoke name="SemanticSearchResource:search">
    <parameter name="query">current assets and current liabilities balance sheet</parameter>
    <parameter name="top_k">5</parameter>
  </invoke>
</function_call>
```
*Solution: Clear separation between reasoning and action. Easy to parse.*

### Available Codecs

Dana provides two built-in codecs:

| Codec | Format | Best For |
|-------|--------|----------|
| **CSXMLCodec** | `<function_call><invoke name="Class:method">` | General purpose, explicit structure |
| **KLXMLCodec** | `<ClassName:methodName>` | Simpler format, less verbose |

**Recommendation:** Start with CSXMLCodec for easier debugging.

---

## 2. Understanding Codec Formats

All Dana codecs follow a three-part response structure:

```xml
<!-- Part 1: THINKING (Private Reasoning) - REQUIRED -->
<thinking>
Internal analysis that's not shown to users.
What information do I have? What tool do I need?
</thinking>

<!-- Part 2: RESPONSE (Direct Answer) - Optional -->
<response>
A direct answer to the user when no tool call is needed.
</response>

<!-- Part 3: FUNCTION_CALL (Tool Invocation) - Optional -->
<function_call>
  <!-- Tool call structure depends on the codec -->
</function_call>
```

### Response Contract Rules

1. **`<thinking>` is ALWAYS required** - Contains internal reasoning only
2. **Exactly one of `<response>` or `<function_call>` must appear** - Never both
3. **If `<function_call>` is present, ignore any `<response>`** - Tool calls take priority
4. **Never output a tool call without a preceding `<thinking>`** - Reasoning before action

### How Responses Are Parsed

When an agent receives an LLM response, the codec extracts:

- **thinking** → Stored in timeline for learning
- **response** → Returned to user as the answer
- **tool_calls** → Executed via ToolCaller component

**Example:**

**LLM Response:**
```xml
<thinking>
User wants current ratio. I found current assets of $3,724M and current liabilities of $2,859M
from the balance sheet. I'll calculate: current ratio = current assets / current liabilities = 1.30.
</thinking>

<response>
Current Ratio Analysis:
- Current Assets: $3,724M
- Current Liabilities: $2,859M
- Current Ratio: 1.30

Interpretation: AMD has $1.30 in current assets for every $1.00 of current liabilities, indicating healthy short-term liquidity.
</response>
```

**Agent receives:**
- `reasoning`: "User wants current ratio. I found current assets of $3,724M..."
- `response`: `'Current Ratio Analysis:\n- Current Assets: $3,724M...'`
- `tool_calls`: `[]` (empty, no tool calls)

---

## 3. Using CSXMLCodec

CSXMLCodec is Dana's general-purpose codec. It's the recommended starting point for most agents.

### Format Specification

**CSXMLCodec Tool Call Format:**
```xml
<function_call>
  <invoke name="ClassName:methodName">
    <parameter name="parameterName">value</parameter>
    <parameter name="anotherParameter">another value</parameter>
  </invoke>
</function_call>
```

### Basic Example: FinancialAnalysisAgent

Here's how to create an agent (codecs are now the default!):

```python
import os
from dana.core.agent.star_agent import STARAgent

class FinancialAnalysisAgent(STARAgent):
    def __init__(self, **kwargs):
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "FinancialAnalysisAgent.xml"
        )
        
        super().__init__(
            agent_type="financial-analysis",
            agent_id="financial-analysis-001",
            llm_provider="openai",
            model="gpt-4.1-mini",
            prompt_path=prompt_path,
            # codec=CSXMLCodec is now the default - no need to specify!
            **kwargs,
        )

# Usage
agent = FinancialAnalysisAgent()
result = agent.query(
    caller_message="Calculate the current ratio for AMD from the financial statements",
    session_id="session-001"
)
print(result["response"])  # The parsed response
```

### What Happens

1. **Codec automatically adds format instructions** to your prompt
2. **LLM generates structured response** with `<thinking>`, `<response>`, or `<function_call>`
3. **Codec parses the response** into structured components
4. **Agent returns** parsed reasoning, response, and tool calls

### With Tool Calls

If your agent has resources (tools), the LLM can call them:

```python
from dana.core.resource.base_resource import BaseResource

class SemanticSearchResource(BaseResource):
    def search(self, query: str, top_k: int = 5) -> str:
        """Search for financial concepts in documents."""
        return f"Found {top_k} relevant sections for: {query}"

# Register resource
agent.register_resource(SemanticSearchResource())

# LLM can now call it:
# <function_call>
#   <invoke name="SemanticSearchResource:search">
#     <parameter name="query">current assets and current liabilities</parameter>
#     <parameter name="top_k">5</parameter>
#   </invoke>
# </function_call>
```

---

## 4. Using KLXMLCodec

KLXMLCodec is a simpler, more concise format that eliminates wrapper tags.

### Format Specification

**KLXMLCodec Tool Call Format:**
```xml
<ClassName:methodName>
  <parameterName>value</parameterName>
  <anotherParameter>another value</anotherParameter>
</ClassName:methodName>
```

### Comparison

**CSXMLCodec (Explicit):**
```xml
<function_call>
  <invoke name="SemanticSearchResource:search">
    <parameter name="query">current assets and current liabilities</parameter>
    <parameter name="top_k">5</parameter>
  </invoke>
</function_call>
```

**KLXMLCodec (Direct):**
```xml
<SemanticSearchResource:search>
  <query>current assets and current liabilities</query>
  <top_k>5</top_k>
</SemanticSearchResource:search>
```

**Savings:** ~25% fewer characters with KLXMLCodec.

### When to Use KLXMLCodec

| Use KLXMLCodec When | Use CSXMLCodec When |
|---------------------|---------------------|
| Token efficiency matters | You're just starting with codecs |
| Your agents make many tool calls | You want explicit, self-documenting format |
| You want cleaner logs | You need maximum clarity for debugging |

**Recommendation:** Start with CSXMLCodec, switch to KLXMLCodec for production if you need efficiency gains.

### Converting to KLXMLCodec

Simply change the codec parameter:

```python
# Before (CSXMLCodec)
from dana.core.knowledge.prompts.codecs import CSXMLCodec
super().__init__(..., codec=CSXMLCodec, ...)

# After (KLXMLCodec)
from dana.core.knowledge.prompts.codecs import KLXMLCodec
super().__init__(..., codec=KLXMLCodec, ...)
```

That's it! Dana automatically handles the rest.

---

## 5. Quick Integration Guide

### Step 1: Import the Codec

```python
from dana.core.knowledge.prompts.codecs import CSXMLCodec
```

### Step 2: Codec is Now the Default!

```python
class MyAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="my-agent",
            agent_id="my-agent-001",
            # codec=CSXMLCodec is now the default - no need to specify!
            **kwargs
        )
```

**Note:** Codecs are now the default. You only need to specify a codec if you want:
- A different codec (e.g., `codec=KLXMLCodec`)
- To explicitly opt-out to legacy system (not recommended): `codec=None`

**Important:** Pass the codec **class**, not an instance:
- ✅ `codec=CSXMLCodec` (or omit for default)
- ❌ `codec=CSXMLCodec()` (don't instantiate)

### Step 3: Use Your Agent

```python
agent = MyAgent()
result = agent.query(
    caller_message="Your query here",
    session_id="session-001"
)

# Access parsed components
print(result["response"])    # Direct answer
print(result["reasoning"])   # From <thinking> block
print(result["tool_calls"])  # Parsed tool calls
```

### Complete Minimal Example

```python
"""
Minimal example: Agent with CSXMLCodec
"""
import os
from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec

class SimpleAgent(STARAgent):
    def __init__(self, **kwargs):
        # Create a simple prompt
        prompt_content = """
<IDENTITY>
I am a helpful assistant that answers questions clearly.
</IDENTITY>
"""
        
        super().__init__(
            agent_type="simple-agent",
            agent_id="simple-001",
            prompt_content=prompt_content,
            # codec=CSXMLCodec is now the default - no need to specify!
            **kwargs
        )

# Use it
agent = SimpleAgent()
result = agent.query("What is 2+2?", session_id="test-session")
print(result["response"])  # "4" (or reasoning + answer)
```

### Common Issues

**Issue: Codec not working**
- ✅ Codecs are now the default - you don't need to pass `codec=CSXMLCodec` unless you want a different codec
- ✅ Verify your LLM model supports structured output (GPT-4, Claude 3+)
- ✅ If you explicitly pass `codec=None`, you'll get a deprecation warning and legacy system

**Issue: Tool calls not parsed**
- ✅ Verify tool is registered: `agent.register_resource(MyResource())`
- ✅ Check tool call format matches codec (CSXMLCodec vs KLXMLCodec)

### Next Steps

- **Learn more:** See [codec-advanced.md](./codec-advanced.md) for:
  - How codecs work under the hood
  - Debugging techniques
  - Performance optimization
  - Complete reference examples
- **Try it:** Check out `examples/agents/financial-analysis/` for a full working example

---

**End of Basic Codec Guide**

For advanced topics, see [codec-advanced.md](./codec-advanced.md).

