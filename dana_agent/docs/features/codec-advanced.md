# Codec Guide: Advanced Topics and Implementation Details

> **New to codecs?** Start with [codec-basic.md](./codec-basic.md) for a concise introduction and quick start guide.

This comprehensive guide covers advanced codec topics, implementation details, debugging techniques, and complete reference examples. We'll use the Financial Analysis Agent example from `examples/agents/financial-analysis` as our primary reference throughout.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Understanding Codec Formats](#2-understanding-codec-formats)
3. [Using CSXMLCodec](#3-using-csxmlcodec)
4. [Using KLXMLCodec](#4-using-klxmlcodec)
5. [Codec Integration in Agents](#5-codec-integration-in-agents)
6. [How Codecs Work Under the Hood](#6-how-codecs-work-under-the-hood)
7. [Practical Tips & Best Practices](#7-practical-tips--best-practices)
8. [Complete Reference Example](#8-complete-reference-example)

---

## 1. Introduction

### What Are Codecs?

**Codecs** (encoder-decoder) in Dana are structured format specifications that define how LLMs should format their responses. They provide a standardized way for agents to:

- **Parse LLM reasoning** separate from actions
- **Extract structured tool calls** from text responses
- **Enforce response contracts** that LLMs must follow
- **Enable reliable tool execution** by parsing well-defined formats

### Why Do Codecs Matter?

Without codecs, LLM responses are free-form text that's difficult to parse reliably. Consider these challenges:

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

### When to Use Different Codec Formats

Dana provides two built-in codecs:

| Codec | Format | Best For |
|-------|--------|----------|
| **CSXMLCodec** | `<function_call><invoke name="Class:method">` | General purpose, explicit wrapper structure |
| **KLXMLCodec** | `<ClassName:methodName>` | Simpler format, less verbose |

Both codecs support:
- `<thinking>` blocks for internal reasoning
- `<response>` blocks for direct answers (when no tool call needed)
- `<function_call>` or direct tool invocation blocks

---

## 2. Understanding Codec Formats

All Dana codecs follow a three-part response structure that separates reasoning from action:

### The Three-Part Response Structure

```xml
<!-- Part 1: THINKING (Private Reasoning) - REQUIRED -->
<thinking>
Internal analysis that's not shown to users.
What information do I have? What tool do I need?
How should I approach this task?
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

The LLM must follow these rules:

1. **`<thinking>` is ALWAYS required** - Contains internal reasoning only
2. **Exactly one of `<response>` or `<function_call>` must appear** - Never both
3. **If `<function_call>` is present, ignore any `<response>`** - Tool calls take priority
4. **Never output a tool call without a preceding `<thinking>`** - Reasoning before action
5. **If neither response nor tool call, thinking content becomes the reply** - Fallback behavior

### How LLM Responses Are Parsed

When an agent receives an LLM response, the codec's `parse_response()` method extracts:

```python
ParsedCodecResponse(
    thinking="Internal reasoning extracted from <thinking> block",
    response="Direct answer from <response> block (if present)",
    tool_calls=[ToolCall(...), ...]  # Parsed from <function_call> blocks
)
```

The agent then uses these components:
- **thinking** → Stored in timeline as reasoning
- **response** → Returned to user as the answer
- **tool_calls** → Executed via ToolCaller component

### Example Response Breakdown

Let's see how the Financial Analysis Agent's response is parsed:

**Raw LLM Response:**
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

**Parsed Result:**
```python
ParsedCodecResponse(
    thinking="User wants current ratio. I found current assets of $3,724M and current liabilities of $2,859M...",
    response='Current Ratio Analysis:\n- Current Assets: $3,724M\n- Current Liabilities: $2,859M...',
    tool_calls=None  # No tool calls in this response
)
```

In this case, the agent:
1. Records the **thinking** in its timeline for learning
2. Returns the **response** (financial analysis) to the user
3. No tool execution needed since **tool_calls** is None

---

## 3. Using CSXMLCodec

CSXMLCodec is Dana's general-purpose codec that uses an explicit `<invoke>` wrapper for tool calls. It's the recommended starting point for most agents.

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

Key characteristics:
- Uses `<function_call>` as the outer wrapper
- Uses `<invoke name="Class:method">` to specify the tool
- Each parameter is wrapped in `<parameter name="...">` tags
- Class name and method are separated by a colon `:`

### Complete Working Example: FinancialAnalysisAgent

Let's build a complete Financial Analysis agent using CSXMLCodec. This agent extracts and analyzes financial data from documents.

**File: `examples/agents/financial-analysis/agents/financial_analysis_agent.py`**

```python
"""
FinancialAnalysisAgent - Financial analysis agent using CSXMLCodec.
"""
import os
import sys
from dana.common.protocols import DictParams, Notifiable
from dana.core.agent.star_agent import STARAgent

# Add parent directory to path to import resources
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

from resources.semantic_search_resource import SemanticSearchResource
from resources.read_file_resource import ReadFileResource
from resources.ripgrep_search_resource import RipgrepSearchResource


class FinancialAnalysisAgent(STARAgent):
    """
    Agent specialized in extracting and analyzing financial data.
    Uses CSXMLCodec for structured LLM communication.
    """

    def __init__(
        self,
        agent_id: str | None = None,
        workspace_root: str | None = None,
        llm_provider: str = "openai",
        model: str = "gpt-4.1-mini",
        **kwargs,
    ):
        # Path to the prompt XML file
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "FinancialAnalysisAgent.xml",
        )
        prompt_path = os.path.normpath(prompt_path)

        # Initialize STARAgent with CSXMLCodec
        from dana.core.knowledge.prompts.codecs import CSXMLCodec
        
        super().__init__(
            agent_type="financial-analysis",
            agent_id=agent_id or "financial-analysis-001",
            llm_provider=llm_provider,
            model=model,
            prompt_path=prompt_path,
            codec=CSXMLCodec,  # Enable codec-based communication
            **kwargs,
        )
        
        # Register resources
        if workspace_root:
            self.with_resources(
                SemanticSearchResource(
                    resource_id="semantic-search",
                    workspace_root=workspace_root
                ),
                ReadFileResource(
                    resource_id="read-file",
                    workspace_root=workspace_root
                ),
                RipgrepSearchResource(
                    resource_id="ripgrep-search",
                    workspace_root=workspace_root
                ),
            )


if __name__ == "__main__":
    # Create and use the agent
    agent = FinancialAnalysisAgent(
        workspace_root=os.path.join(os.path.dirname(__file__), "..", "data")
    )
    
    # Query the agent
    result = agent.query(
        caller_message="Calculate the current ratio for AMD from the financial statements",
        session_id="financial-session-001"
    )
    
    print("Agent Response:", result["response"])
```

### The Agent's Prompt File

The prompt file defines the agent's identity and output format. Since we're using CSXMLCodec, the LLM automatically receives instructions about the response format.

**File: `examples/agents/financial-analysis/prompts/FinancialAnalysisAgent.xml`**

```xml
<PUBLIC_DESCRIPTION>
FinancialAnalysisAgent helps you extract, analyze, and calculate financial metrics from financial statements and reports.

I am a financial analyst that uses systematic information retrieval to:
- Extract specific financial data and line items from statements
- Calculate financial ratios and metrics with clear formulas
- Analyze trends, growth rates, and financial performance
- Locate complex financial concepts and disclosures
- Provide accurate numerical analysis with proper sourcing
</PUBLIC_DESCRIPTION>

<IDENTITY>
You are a Financial Analyst that extracts, analyzes, and computes financial metrics from financial statements and reports.

Mission: Deliver accurate, well-sourced financial analysis through systematic information retrieval and calculation.

When analyzing financial data:
1. Use semantic search to locate relevant sections
2. Extract specific values with proper sourcing
3. Calculate ratios with clear formulas
4. Provide interpretation and context
</IDENTITY>
```

### How CSXMLCodec Augments Your Prompt

When you pass `codec=CSXMLCodec` to the agent, the codec automatically adds response format instructions to every LLM request. Your prompt is enhanced with:

```xml
RESPONSE CONTRACT
PURPOSE: Enforce a clear separation between the assistant's private reasoning
         and its user-visible output (answer or tool invocation).

── OUTPUT FORMAT ────────────────────────────────────────────
Each assistant reply MUST contain 1-3 XML blocks, in the order shown:
  1. <thinking>  ← MANDATORY, *internal* reasoning only
  2. <response>  ← optional, a direct answer (omit if tool call needed)
  3. <function_call> ← optional, external-tool invocation

<thinking>
/* PRIVATE — NOT SHOWN TO USER
   Brief analysis (≈ 50-150 words):
   • What does the user need?
   • Do I have enough info? → If no, specify the tool(s) required.
   • Planned answer approach or tool workflow.
   • Whether a user confirmation question is needed.
   END PRIVATE */
</thinking>

<!-- BRANCH A: DIRECT ANSWER (no tool call) -->
<response>
  <!-- Visible answer, clarification question, or next-step guidance. -->
</response>

<!-- BRANCH B: TOOL CALL (no <response>) -->
<function_call>
  <invoke name="ClassName:methodName">
    <parameter name="parameterName">value</parameter>
    <!-- Add more <parameter> tags as needed -->
  </invoke>
</function_call>

# RULES
• <thinking> is ALWAYS required; it contains only internal reasoning.
• Exactly one of <response> or <function_call> must appear.
• If <function_call> is present, ignore any <response>.
• Never output a tool call without a preceding <thinking>.
• If you have neither a tool call nor a direct answer, the <thinking> block's user-visible section becomes the reply.
```

### Example: Financial Analysis Agent Response with CSXMLCodec

**User Query:**
```
Calculate the current ratio for AMD from the financial statements
```

**LLM Response (following CSXMLCodec format):**
```xml
<thinking>
User wants current ratio calculation. I need to find current assets and current liabilities
from AMD's balance sheet. I'll use semantic search to locate the balance sheet section first,
then extract the specific values.

Current ratio formula: Current Assets / Current Liabilities

Let me search for balance sheet data.
</thinking>

<function_call>
  <invoke name="SemanticSearchResource:search">
    <parameter name="query">current assets and current liabilities balance sheet</parameter>
    <parameter name="top_k">5</parameter>
  </invoke>
</function_call>
```

**After tool execution, LLM continues:**

```xml
<thinking>
Found balance sheet data. Current assets: $3,724M, Current liabilities: $2,859M.
Current ratio = 3,724 / 2,859 = 1.30

This indicates AMD has $1.30 in current assets for every $1.00 of current liabilities,
which is a healthy liquidity position.
</thinking>

<response>
Current Ratio Analysis:
- Current Assets: $3,724M
- Current Liabilities: $2,859M
- Current Ratio: 1.30

Interpretation: AMD has $1.30 in current assets for every $1.00 of current liabilities, indicating healthy short-term liquidity.
</response>
```

**What happens:**

1. **Codec parses the response**:
   - `thinking` → Extracted and stored in timeline for learning
   - `response` → The financial analysis returned to user
   - `tool_calls` → Parsed tool calls executed (semantic search)

2. **Agent returns the analysis**:
   ```python
   {
       "response": "Current Ratio Analysis:\n- Current Assets: $3,724M...",
       "reasoning": "User wants current ratio calculation. I need to find current assets...",
       "tool_calls": [{"function": "SemanticSearchResource:search", ...}],
       "tool_results": ["Found balance sheet section with current assets and liabilities..."]
   }
   ```

### CSXMLCodec with Tool Calls

If your agent has resources (tools), the LLM can call them using CSXMLCodec format:

**Example with a financial analysis resource:**

```python
from dana.core.resource.base_resource import BaseResource

class SemanticSearchResource(BaseResource):
    """Resource for semantic search in financial documents."""
    
    def search(self, query: str, top_k: int = 5) -> str:
        """Search for financial concepts in documents."""
        return f"Found {top_k} relevant sections for: {query}"

# Register the resource with your agent
agent.register_resource(SemanticSearchResource())
```

**LLM Response with Tool Call:**
```xml
<thinking>
I need to find current assets and current liabilities from the balance sheet.
I'll use semantic search to locate the relevant sections.
</thinking>

<function_call>
  <invoke name="SemanticSearchResource:search">
    <parameter name="query">current assets and current liabilities balance sheet</parameter>
    <parameter name="top_k">5</parameter>
  </invoke>
</function_call>
```

**What happens:**

1. **Codec parses tool call**:
   ```python
   ToolCall(
       class_name="SemanticSearchResource",
       name="search",
       parameters={"query": "current assets and current liabilities balance sheet", "top_k": "5"}
   )
   ```

2. **Agent executes the tool**:
   - Finds `SemanticSearchResource` in registered resources
   - Calls `search(query="current assets and current liabilities balance sheet", top_k=5)`
   - Returns result: `"Found 5 relevant sections for: current assets and current liabilities balance sheet"`

3. **Tool result added to conversation** for next LLM turn

---

## 4. Using KLXMLCodec

KLXMLCodec is a simpler, more concise codec format that eliminates the `<function_call>` and `<invoke>` wrappers. It's useful when you want less verbose tool calls.

### Format Specification

**KLXMLCodec Tool Call Format:**
```xml
<ClassName:methodName>
  <parameterName>value</parameterName>
  <anotherParameter>another value</anotherParameter>
</ClassName:methodName>
```

Key characteristics:
- **No outer wrappers** - Tool call uses direct `<ClassName:methodName>` tags
- **No parameter wrappers** - Parameters use direct `<paramName>` tags
- **More concise** - Fewer characters, cleaner format
- **Same thinking/response** - Still supports `<thinking>` and `<response>` blocks

### Side-by-Side Comparison

Let's compare how the same tool call looks in both codecs:

**CSXMLCodec (Explicit Wrapper):**
```xml
<thinking>
I need to search for current assets and current liabilities in the balance sheet.
</thinking>

<function_call>
  <invoke name="SemanticSearchResource:search">
    <parameter name="query">current assets and current liabilities balance sheet</parameter>
    <parameter name="top_k">5</parameter>
  </invoke>
</function_call>
```

**KLXMLCodec (Direct Format):**
```xml
<thinking>
I need to search for current assets and current liabilities in the balance sheet.
</thinking>

<SemanticSearchResource:search>
  <query>current assets and current liabilities balance sheet</query>
  <top_k>5</top_k>
</SemanticSearchResource:search>
```

**Character count:**
- CSXMLCodec: 287 characters
- KLXMLCodec: 215 characters
- **Savings: 25% fewer characters**

### When to Choose KLXMLCodec vs CSXMLCodec

| Consider KLXMLCodec When | Consider CSXMLCodec When |
|-------------------------|-------------------------|
| Token efficiency matters (smaller models, cost optimization) | You want explicit, self-documenting format |
| Your agents make many tool calls | You're just starting with codecs (more familiar syntax) |
| You want cleaner, more readable logs | You need maximum clarity for debugging |
| Your LLM handles structured formats well | You're working with less capable LLMs |

**Recommendation:** Start with CSXMLCodec for easier debugging, then switch to KLXMLCodec for production if you need the efficiency gains.

### Example: Converting Financial Analysis Agent to KLXMLCodec

Here's how to convert the FinancialAnalysisAgent from CSXMLCodec to KLXMLCodec:

**Before (CSXMLCodec):**
```python
from dana.core.knowledge.prompts.codecs import CSXMLCodec

class FinancialAnalysisAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="financial-analysis",
            agent_id="financial-analysis-001",
            codec=CSXMLCodec,  # Old codec
            **kwargs,
        )
```

**After (KLXMLCodec):**
```python
from dana.core.knowledge.prompts.codecs import KLXMLCodec

class FinancialAnalysisAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="financial-analysis",
            agent_id="financial-analysis-001",
            codec=KLXMLCodec,  # New codec - that's all!
            **kwargs,
        )
```

That's it! The codec parameter is the only change needed. Dana automatically:
- Updates the response format instructions sent to the LLM
- Changes how tool calls are parsed from responses
- Adjusts tool signature formatting in prompts

### KLXMLCodec Response Example

**User Query:**
```
Calculate the debt-to-equity ratio for AMD from the financial statements
```

**LLM Response (KLXMLCodec format):**
```xml
<thinking>
User wants debt-to-equity ratio. Need to find total debt and total equity from balance sheet.
I'll search for these values and calculate the ratio.
</thinking>

<response>
Debt-to-Equity Ratio Analysis:
- Total Debt: $1,234M
- Total Equity: $4,567M
- Debt-to-Equity Ratio: 0.27

Interpretation: AMD has $0.27 in debt for every $1.00 of equity, indicating a conservative capital structure with low financial leverage.
</response>
```

**Parsed Result:** Same as CSXMLCodec - Dana's codec system provides a consistent interface regardless of format.

### KLXMLCodec with Multiple Tool Calls

KLXMLCodec makes multiple tool calls particularly clean:

**CSXMLCodec (Verbose):**
```xml
<thinking>
I'll search for balance sheet data first, then read the specific section.
</thinking>

<function_call>
  <invoke name="SemanticSearchResource:search">
    <parameter name="query">balance sheet current assets</parameter>
    <parameter name="top_k">5</parameter>
  </invoke>
</function_call>

<function_call>
  <invoke name="ReadFileResource:read">
    <parameter name="file_path">data/AMD-AR.md</parameter>
    <parameter name="start_line">100</parameter>
    <parameter name="end_line">200</parameter>
  </invoke>
</function_call>
```

**KLXMLCodec (Concise):**
```xml
<thinking>
I'll search for balance sheet data first, then read the specific section.
</thinking>

<SemanticSearchResource:search>
  <query>balance sheet current assets</query>
  <top_k>5</top_k>
</SemanticSearchResource:search>

<ReadFileResource:read>
  <file_path>data/AMD-AR.md</file_path>
  <start_line>100</start_line>
  <end_line>200</end_line>
</ReadFileResource:read>
```

**Note:** Both formats support multiple tool calls - KLXMLCodec just makes them more compact.

### KLXMLCodec Instruction Format

When KLXMLCodec is active, the LLM receives these instructions:

```xml
RESPONSE CONTRACT
PURPOSE: Enforce a clear separation between the assistant's private reasoning
         and its user-visible output (answer or tool invocation).

── OUTPUT FORMAT ────────────────────────────────────────────
Each assistant reply MUST contain 1-3 XML blocks, in the order shown:
  1. <thinking>  ← MANDATORY, *internal* reasoning only
  2. <response>  ← optional, a direct answer (omit if tool call needed)
  3. <ClassName:methodName> ← optional, external-tool invocation

<thinking>
/* PRIVATE — NOT SHOWN TO USER
   Brief analysis (≈ 50-150 words):
   • What does the user need?
   • Do I have enough info? → If no, specify the tool(s) required.
   • Planned answer approach or tool workflow.
   • Whether a user confirmation question is needed.
   END PRIVATE */
</thinking>

<!-- BRANCH A: DIRECT ANSWER (no tool call) -->
<response>
  <!-- Visible answer, clarification question, or next-step guidance. -->
</response>

<!-- BRANCH B — ONE OR MORE TOOL CALLS (omit <response>) -->
<ClassName:methodName>
  <param name="parameterName">value</param>
  <!-- Add additional <param> tags as needed -->
</ClassName:methodName>

<!-- Example of a second tool call, if required
<OtherClass:otherMethod>
  <param name="...">...</param>
</OtherClass:otherMethod> -->

# RULES
• <thinking> is ALWAYS required; it contains only internal reasoning.
• Exactly one of <response> or tool calls must appear.
• If tool calls are present, ignore any <response>.
• Never output a tool call without a preceding <thinking>.
• If you have neither a tool call nor a direct answer, the <thinking> block's user-visible section becomes the reply.
```

---

## 5. Codec Integration in Agents

This section explains how codecs integrate into Dana's agent architecture and what happens under the hood when you pass a codec to your agent.

### Passing Codec to STARAgent Constructor

When you initialize a `STARAgent`, the `codec` parameter triggers codec-based communication:

```python
from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec

class MyAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="my-agent",
            agent_id="my-agent-001",
            llm_provider="llamastack",
            model="openai/gpt-4.1",
            codec=CSXMLCodec,  # Enable codec-based communication
            **kwargs
        )
```

**Key points:**
- `codec` parameter accepts a codec **class** (not an instance)
- Default is `CSXMLCodec` - codec system is now the default
- Pass `CSXMLCodec` or `KLXMLCodec` (or your custom codec) for codec-based system
- If explicitly set to `codec=None`, agent uses legacy format (deprecated, backward compatibility only)

### How Codec Affects Component Initialization

When you pass a codec, STARAgent initializes different internal components. Here's what happens in `STARAgent.__init__()`:

**Reference:** `dana_agent/dana/core/agent/star_agent.py:92-104`

```python
# From STARAgent initialization
self._codec = codec

if codec is not None:
    # NEW SYSTEM: Use codec-based components
    from dana.core.knowledge.prompts.prompt_api import LocalPromptAPI
    
    # Initialize PromptAPI with codec
    self._prompt_engineer = LocalPromptAPI(
        self, 
        codec=codec, 
        repository_factory=self._repository_factory
    )
    
    # Initialize CodecToolCaller (handles codec parsing)
    from .components.tool_caller import CodecToolCaller
    self._tool_caller = CodecToolCaller(self, codec=codec)
else:
    # OLD SYSTEM: Use legacy components (backward compatibility)
    self._prompt_engineer = PromptEngineer(self)
    self._tool_caller = ToolCaller(self)
```

**What changes:**

| Component | Without Codec | With Codec |
|-----------|--------------|------------|
| **Prompt Engineer** | `PromptEngineer` | `LocalPromptAPI` with codec integration |
| **Tool Caller** | `ToolCaller` | `CodecToolCaller` with codec parsing |
| **Response Format** | Free-form text | Structured `<thinking>/<response>/<function_call>` |
| **Tool Call Parsing** | Regex-based heuristics | Codec's `parse_response()` method |

### Complete Integration Example

Let's walk through a complete example showing how codec integration works in the Financial Analysis Agent:

```python
"""
Complete example showing codec integration in FinancialAnalysisAgent
"""
import os
from dana.core.agent.star_agent import STARAgent
from dana.core.knowledge.prompts.codecs import CSXMLCodec


class FinancialAnalysisAgent(STARAgent):
    """Financial Analysis Agent with CSXMLCodec integration."""
    
    def __init__(
        self,
        agent_id: str | None = None,
        workspace_root: str | None = None,
        llm_provider: str = "openai",
        model: str = "gpt-4.1-mini",
        **kwargs,
    ):
        # Prepare prompt path
        prompt_path = os.path.join(
            os.path.dirname(__file__), "..", "prompts", "FinancialAnalysisAgent.xml"
        )
        
        # Initialize with codec
        super().__init__(
            agent_type="financial-analysis",
            agent_id=agent_id or "financial-analysis-001",
            llm_provider=llm_provider,
            model=model,
            prompt_path=prompt_path,
            codec=CSXMLCodec,  # <<< Codec integration point
            **kwargs,
        )
        
        # At this point:
        # - self._codec = CSXMLCodec (class reference)
        # - self._prompt_engineer = LocalPromptAPI instance
        # - self._tool_caller = CodecToolCaller instance
        # - Response format instructions automatically added to prompts


# Usage example
if __name__ == "__main__":
    # 1. Create agent (codec components initialized automatically)
    agent = FinancialAnalysisAgent(
        workspace_root=os.path.join(os.path.dirname(__file__), "..", "data")
    )
    
    # 2. Query agent
    result = agent.query(
        caller_message="Calculate the current ratio for AMD from the financial statements",
        session_id="financial-session-001"
    )
    
    # 3. Result contains parsed codec response
    print("Response:", result["response"])      # Direct answer or analysis
    print("Reasoning:", result["reasoning"])    # Extracted from <thinking>
    print("Tool Calls:", result["tool_calls"])  # Parsed tool calls (if any)
```

### What Happens During a Query

Let's trace what happens when you call `agent.query()` with a codec:

**1. User calls `agent.query()`:**
```python
result = agent.query(caller_message="Calculate current ratio...", session_id="session-001")
```

**2. Agent's THINK phase constructs prompt:**
- `self._prompt_engineer` (LocalPromptAPI) loads your prompt XML
- Codec's `get_instruction()` adds response format contract
- Timeline context added
- Final prompt sent to LLM:

```
<YOUR_PROMPT_CONTENT>

RESPONSE CONTRACT
PURPOSE: Enforce a clear separation...
[Codec instructions here]

User: Calculate current ratio...
```

**3. LLM generates codec-formatted response:**
```xml
<thinking>
User wants current ratio. I need to find current assets and current liabilities...
</thinking>

<response>
Current Ratio Analysis:
- Current Assets: $3,724M
- Current Liabilities: $2,859M
- Current Ratio: 1.30
</response>
```

**4. CodecToolCaller parses response:**
```python
# In CodecToolCaller.parse_llm_response()
parsed = self._codec.parse_response(llm_response.content)
# Returns: ParsedCodecResponse(
#     thinking="User wants current ratio. I need to find current assets...",
#     response='Current Ratio Analysis:\n- Current Assets: $3,724M...',
#     tool_calls=None
# )
```

**5. Agent returns result:**
```python
{
    "response": "Current Ratio Analysis:\n- Current Assets: $3,724M...",
    "reasoning": "User wants current ratio. I need to find current assets...",
    "tool_calls": [],
    "tool_results": []
}
```

### Codec Integration with Resources

When your agent has resources (tools), the codec automatically handles tool call formatting and parsing:

```python
from dana.core.resource.base_resource import BaseResource

class SemanticSearchResource(BaseResource):
    """Resource for semantic search in financial documents."""
    
    def __init__(self):
        super().__init__(
            resource_id="semantic-search",
            resource_type="search"
        )
    
    def search(self, query: str, top_k: int = 5) -> str:
        """Search for financial concepts in documents.
        
        Args:
            query: Search query for financial concepts
            top_k: Number of results to return
        
        Returns:
            Search results with relevant document sections
        """
        return f"Found {top_k} relevant sections for: {query}"


# Register resource with agent
agent = FinancialAnalysisAgent()
agent.register_resource(SemanticSearchResource())

# Now when LLM returns:
# <function_call>
#   <invoke name="SemanticSearchResource:search">
#     <parameter name="query">current assets and current liabilities</parameter>
#     <parameter name="top_k">5</parameter>
#   </invoke>
# </function_call>
#
# The codec automatically:
# 1. Parses the tool call
# 2. Extracts class_name="SemanticSearchResource", name="search"
# 3. Extracts parameters={"query": "current assets...", "top_k": "5"}
# 4. Agent executes SemanticSearchResource.search(...)
# 5. Returns result to LLM for next turn
```

### Prompt Path vs Prompt Content

You can provide prompts in two ways:

**Option 1: Prompt Path (Recommended)**
```python
super().__init__(
    prompt_path="/path/to/prompts/MyAgent.xml",  # File path
    codec=CSXMLCodec,
    **kwargs
)
```

**Option 2: Direct Prompt Content**
```python
super().__init__(
    prompt_content="<IDENTITY>I am an agent...</IDENTITY>",  # Direct string
    codec=CSXMLCodec,
    **kwargs
)
```

Both work the same way - the codec instructions are automatically appended.

---

## 6. How Codecs Work Under the Hood

This section dives into the codec implementation details for advanced users who want to understand the internals or create custom codecs.

### The AbstractCodec Interface

All codecs must implement the `AbstractCodec` interface:

**Reference:** `dana_agent/dana/core/knowledge/prompts/codecs/abstract_codec.py`

```python
from abc import ABC, abstractmethod
from dana.common.schemas.tool_call import MethodSignature, ToolCall

class AbstractCodec(ABC):
    """Base class for all codec implementations."""
    
    @classmethod
    @abstractmethod
    def get_instruction(cls) -> str:
        """
        Get the instruction for the codec.
        
        Returns format contract that LLM must follow.
        This is automatically added to every prompt.
        """
        pass
    
    @classmethod
    @abstractmethod
    def construct(cls, signature: MethodSignature) -> str:
        """
        Construct a formatted string from a method signature.
        
        Converts a tool's method signature into a formatted string
        that shows the LLM how to call this tool.
        
        Args:
            signature: Method signature with name, description, parameters
        
        Returns:
            Formatted tool documentation
        """
        pass
    
    @classmethod
    @abstractmethod
    def parse_method_call(cls, xml_string: str) -> ToolCall:
        """
        Parse a method call from a formatted string.
        
        Converts LLM's tool call text back into a structured ToolCall object.
        
        Args:
            xml_string: The tool call text from LLM response
        
        Returns:
            ToolCall object with class_name, name, and parameters
        """
        pass
```

### Method 1: `get_instruction()` - Response Format Contract

This method returns the instructions that the LLM must follow. It's automatically added to every prompt.

**CSXMLCodec Example:**

```python
@classmethod
def get_instruction(cls) -> str:
    return """
RESPONSE CONTRACT
PURPOSE: Enforce a clear separation between the assistant's private reasoning
         and its user-visible output (answer or tool invocation).

── OUTPUT FORMAT ────────────────────────────────────────────
Each assistant reply MUST contain 1-3 XML blocks, in the order shown:
  1. <thinking>  ← MANDATORY, *internal* reasoning only
  2. <response>  ← optional, a direct answer (omit if tool call needed)
  3. <function_call> ← optional, external-tool invocation

[... rest of the contract ...]
"""
```

**When it's used:**
- Every time a prompt is constructed
- Appended automatically by PromptAPI/PromptEngineer
- Ensures consistent LLM response format

### Method 2: `construct()` - Tool Signature Formatting

This method formats a tool's signature into documentation that shows the LLM how to call it.

**Input: MethodSignature object**
```python
MethodSignature(
    class_name="SemanticSearchResource",
    name="search",
    description="Search for financial concepts in documents",
    parameters=[
        ParameterInfo(
            name="query",
            description="Search query for financial concepts",
            has_default=False,
            example="current assets and current liabilities"
        ),
        ParameterInfo(
            name="top_k",
            description="Number of results to return",
            has_default=False,
            example="5"
        )
    ]
)
```

**CSXMLCodec Output:**
```
### SemanticSearchResource:search
Description: Search for financial concepts in documents
Parameters:
- query: (required) Search query for financial concepts
- top_k: (required) Number of results to return
Usage:
<function_call>
<invoke name="SemanticSearchResource:search">
<parameter name="query">current assets and current liabilities</parameter>
<parameter name="top_k">5</parameter>
</invoke>
</function_call>
```

**KLXMLCodec Output:**
```
### SemanticSearchResource:search
Description: Search for financial concepts in documents
Parameters:
- query: (required) Search query for financial concepts
- top_k: (required) Number of results to return
Usage:
<SemanticSearchResource:search>
<query>current assets and current liabilities</query>
<top_k>5</top_k>
</SemanticSearchResource:search>
```

**When it's used:**
- When agent registers resources/workflows
- Tool documentation added to prompts
- LLM learns how to call each tool

### Method 3: `parse_method_call()` - Tool Call Parsing

This method parses the LLM's tool call text back into a structured `ToolCall` object.

**CSXMLCodec Implementation:**

```python
@classmethod
def parse_method_call(cls, xml_string: str) -> ToolCall:
    """Parse <function_call><invoke name="Class:method">...</invoke></function_call>"""
    
    # Extract class_name and method_name from <invoke name="ClassName:methodName">
    invoke_match = re.search(r'<invoke\s+name=["\']([^"\']+):([^"\']+)["\']', xml_string)
    if not invoke_match:
        raise ValueError("Could not find <invoke name=\"Class:method\"> in XML")
    
    class_name = invoke_match.group(1)
    method_name = invoke_match.group(2)
    
    # Extract parameters from <parameter name="...">value</parameter> tags
    parameters = {}
    param_pattern = r'<parameter\s+name=["\']([^"\']+)["\']>(.*?)</parameter>'
    for match in re.finditer(param_pattern, xml_string, re.DOTALL):
        param_name = match.group(1)
        param_value = match.group(2).strip()
        parameters[param_name] = param_value
    
    return ToolCall(
        class_name=class_name,
        name=method_name,
        parameters=parameters
    )
```

**Input (LLM text):**
```xml
<function_call>
  <invoke name="SemanticSearchResource:search">
    <parameter name="query">current assets and current liabilities balance sheet</parameter>
    <parameter name="top_k">5</parameter>
  </invoke>
</function_call>
```

**Output (Structured object):**
```python
ToolCall(
    class_name="SemanticSearchResource",
    name="search",
    parameters={"query": "current assets and current liabilities balance sheet", "top_k": "5"}
)
```

**When it's used:**
- When LLM returns a response with tool calls
- CodecToolCaller calls `codec.parse_response()`
- Parsed tool calls executed by agent

### The `parse_response()` Method

In addition to the three abstract methods, codecs typically implement `parse_response()` to handle the full response parsing:

**Reference:** `dana_agent/dana/core/knowledge/prompts/codecs/xml_format.py:162-261`

```python
@classmethod
def parse_response(cls, xml_string: str) -> ParsedCodecResponse:
    """
    Parse complete LLM response into thinking, response, and tool_calls.
    
    Args:
        xml_string: Full LLM response text
    
    Returns:
        ParsedCodecResponse with thinking, response, and tool_calls
    """
    # Extract <thinking> block
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', xml_string, re.DOTALL)
    thinking = thinking_match.group(1).strip() if thinking_match else ""
    
    # Remove XML comments from thinking
    thinking = re.sub(r'<!--.*?-->', '', thinking, flags=re.DOTALL).strip()
    
    # Extract all <function_call> blocks
    function_call_pattern = r'<function_call>(.*?)</function_call>'
    function_call_matches = re.finditer(function_call_pattern, xml_string, re.DOTALL)
    
    tool_calls = []
    for match in function_call_matches:
        function_call_content = match.group(0)
        try:
            tool_call = cls.parse_method_call(function_call_content)
            tool_calls.append(tool_call)
        except ValueError:
            continue  # Skip malformed tool calls
    
    # Extract <response> block if exists
    response_match = re.search(r'<response>(.*?)</response>', xml_string, re.DOTALL)
    response = response_match.group(1).strip() if response_match else None
    
    # Remove XML comments from response
    if response:
        response = re.sub(r'<!--.*?-->', '', response, flags=re.DOTALL).strip()
    
    # Priority: if tool_calls exist, ignore response
    if tool_calls:
        response = None
    # If only thinking exists (no response and no tool_calls), set response = thinking
    elif thinking and not response and not tool_calls:
        response = thinking
    
    return ParsedCodecResponse(
        thinking=thinking,
        tool_calls=tool_calls if tool_calls else None,
        response=response
    )
```

This method ties everything together:
1. Extracts `<thinking>` for reasoning
2. Extracts and parses all `<function_call>` blocks using `parse_method_call()`
3. Extracts `<response>` for direct answers
4. Applies priority rules (tool calls > response > thinking)
5. Returns structured `ParsedCodecResponse`

### CodecToolCaller's Role

`CodecToolCaller` is the agent component that uses the codec to parse LLM responses:

**Reference:** `dana_agent/dana/core/agent/components/tool_caller.py:1195-1272`

```python
class CodecToolCaller(WARCaller):
    """Tool caller that uses codec for parsing."""
    
    def __init__(self, agent: "STARAgent", codec: type[AbstractCodec]):
        super().__init__(agent, self)
        self._agent = agent
        self._codec = codec  # Store codec class
    
    def parse_llm_response(self, llm_response: LLMResponse) -> tuple[str | None, str | None, list[DictParams]]:
        """Parse LLM response using codec-based format."""
        if not llm_response:
            return None, None, []
        
        content = llm_response.content.strip()
        try:
            return self._parse_codec_response(llm_response, content)
        except Exception:
            return content, None, []  # Fallback on error
    
    def _parse_codec_response(self, llm_response: LLMResponse, content: str) -> tuple[str | None, str | None, list[DictParams]]:
        """Parse codec-based response format using codec's parse_response method."""
        
        # Use codec to parse the response
        parsed_response = self._codec.parse_response(content)
        
        # Extract components
        response_reasoning = parsed_response.thinking if parsed_response.thinking else None
        response_text = parsed_response.response if parsed_response.response else None
        
        # Convert ToolCall objects to dictionaries
        result_tool_calls = []
        if parsed_response.tool_calls:
            for tool_call in parsed_response.tool_calls:
                result_tool_calls.append({
                    "function": f"{tool_call.class_name}:{tool_call.name}",
                    "arguments": tool_call.parameters
                })
        
        # Validation: must have either thinking + (response OR tool_calls)
        if response_reasoning and not (parsed_response.tool_calls or response_text):
            suggestion_message = f"[Error] invalid format, please follow the following instruction.\n{self._codec.get_instruction()}"
            return "No response generated", suggestion_message, []
        
        return response_text, response_reasoning, result_tool_calls
```

**Flow:**
1. Agent calls `tool_caller.parse_llm_response(llm_response)`
2. CodecToolCaller calls `self._codec.parse_response(content)`
3. Codec returns `ParsedCodecResponse`
4. CodecToolCaller converts to format expected by agent
5. Agent uses parsed components (reasoning, response, tool_calls)

### Data Flow Summary

Here's the complete data flow with codecs:

```
1. User Query → Agent.query(message)
                    ↓
2. Agent THINK → PromptAPI constructs prompt
                    ├─ Load agent's prompt XML
                    ├─ Add codec.get_instruction() (format contract)
                    ├─ Add tool docs via codec.construct(signature)
                    └─ Add timeline context
                    ↓
3. Prompt → LLM (via llm_client)
                    ↓
4. LLM Response → CodecToolCaller.parse_llm_response()
                    ├─ Call codec.parse_response(content)
                    ├─ Extract thinking, response, tool_calls
                    └─ Validate format
                    ↓
5. Parsed Response → Agent ACT
                    ├─ If tool_calls: Execute via ToolCaller
                    ├─ If response: Return to user
                    └─ Store reasoning in timeline
                    ↓
6. Result → Returned to caller
```

---

## 7. Practical Tips & Best Practices

This section provides practical guidance for working with codecs effectively.

### Choosing the Right Codec

**Start with CSXMLCodec unless:**
- Token efficiency is critical → Use KLXMLCodec
- You need a custom format → Implement AbstractCodec

**Decision tree:**
```
Are you just starting with codecs?
  ├─ YES → Use CSXMLCodec (easier to debug)
  └─ NO  → Do you need token efficiency?
            ├─ YES → Use KLXMLCodec (25% fewer characters)
            └─ NO  → Stick with CSXMLCodec (more explicit)
```

### Debugging Codec-Related Issues

**Problem: LLM not following codec format**

1. **Check if codec instructions are being added:**
   ```python
   # Add this to verify codec instructions are in prompt
   agent = FinancialAnalysisAgent()
   print(agent._codec.get_instruction())
   ```

2. **Verify LLM model supports structured output:**
   - Some smaller models struggle with XML formats
   - Try: GPT-4, Claude 3+, or other capable models
   - Avoid: Very small or undertrained models

3. **Inspect raw LLM responses:**
   ```python
   # Enable debug logging to see raw responses
   import structlog
   structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG))
   ```

**Problem: Tool calls not being parsed**

1. **Verify tool call format matches codec:**
   ```python
   # CSXMLCodec expects:
   # <function_call><invoke name="Class:method">...</invoke></function_call>
   
   # KLXMLCodec expects:
   # <ClassName:methodName>...</ClassName:methodName>
   ```

2. **Check if tool is registered:**
   ```python
   agent = FinancialAnalysisAgent()
   agent.register_resource(MyResource())
   
   # Verify registration
   print(f"Registered resources: {len(agent.available_resources)}")
   ```

3. **Enable verbose parsing:**
   ```python
   # The codec's parse_response() returns detailed errors
   from dana.core.knowledge.prompts.codecs import CSXMLCodec
   
   try:
       parsed = CSXMLCodec.parse_response(llm_text)
       print(f"Parsed: {parsed}")
   except Exception as e:
       print(f"Parse error: {e}")
   ```

**Problem: Empty responses or reasoning**

- **Cause:** LLM returned only `<thinking>` without `<response>` or `<function_call>`
- **Solution:** Check if codec validation is too strict:
  ```python
  # If thinking exists but no response/tool_calls, codec may use thinking as response
  # This is expected behavior per codec contract rules
  ```

### Common Pitfalls

**Pitfall 1: Explicitly opting out to legacy system**

```python
# ❌ WRONG - Explicitly opts out to deprecated legacy format
class MyAgent(STARAgent):
    def __init__(self):
        super().__init__(
            agent_type="my-agent",
            codec=None  # ← Deprecated! Don't do this
        )
```

```python
# ✅ CORRECT - Codec is now the default
class MyAgent(STARAgent):
    def __init__(self):
        super().__init__(agent_type="my-agent")
        # Codec system (CSXMLCodec) is automatically used
```

```python
# ✅ ALSO CORRECT - Explicitly specify codec if desired
from dana.core.knowledge.prompts.codecs import CSXMLCodec

class MyAgent(STARAgent):
    def __init__(self):
        super().__init__(
            agent_type="my-agent",
            codec=CSXMLCodec  # Explicit but not required
        )
```

**Pitfall 2: Passing codec instance instead of class**

```python
# ❌ WRONG - Don't instantiate the codec
codec=CSXMLCodec()
```

```python
# ✅ CORRECT - Pass the class itself
codec=CSXMLCodec
```

**Pitfall 3: Mixing codec formats in prompts**

```python
# ❌ WRONG - Don't hardcode codec format in your prompt XML
<IDENTITY>
When calling tools, use:
<function_call>
  <invoke name="Tool:method">...</invoke>
</function_call>
</IDENTITY>
```

```python
# ✅ CORRECT - Let codec handle format instructions
<IDENTITY>
I am an agent that analyzes financial data.
(Codec automatically adds tool call format instructions)
</IDENTITY>
```

**Pitfall 4: Not testing with actual LLM responses**

```python
# ❌ WRONG - Only testing with handwritten examples
test_response = """<thinking>Test</thinking><response>Test response</response>"""
parsed = codec.parse_response(test_response)
```

```python
# ✅ CORRECT - Test with actual LLM output in a real scenario
agent = FinancialAnalysisAgent()
result = agent.query("Calculate the current ratio for AMD from the financial statements")
# Inspect actual LLM response format
print(f"Reasoning: {result['reasoning']}")
print(f"Response: {result['response']}")
```

### Performance Considerations

**Token usage:**
- **CSXMLCodec:** ~50-100 tokens overhead per tool call
- **KLXMLCodec:** ~30-70 tokens overhead per tool call
- **Savings:** 25-40% with KLXMLCodec in tool-heavy applications

**Example calculation:**
```
Scenario: Agent making 10 tool calls per session, 100 sessions/day

CSXMLCodec: 10 × 75 tokens × 100 = 75,000 tokens/day
KLXMLCodec: 10 × 50 tokens × 100 = 50,000 tokens/day
Savings: 25,000 tokens/day = ~750K tokens/month

At $0.01/1K tokens: ~$7.50/month savings
```

**Parsing speed:**
- Both codecs use regex-based parsing: ~0.1-1ms per response
- Negligible compared to LLM inference time (1-10 seconds)
- No meaningful performance difference between codecs

**LLM reliability:**
- More capable models (GPT-4, Claude 3+) handle both formats well
- Smaller models may struggle with either format
- If LLM errors occur, problem is usually model capability, not codec choice

### Best Practices Summary

**DO:**
- ✅ Use CSXMLCodec by default for new projects
- ✅ Pass codec as a class, not an instance
- ✅ Let codec handle format instructions automatically
- ✅ Test with actual LLM responses, not just handwritten examples
- ✅ Use capable LLM models (GPT-4, Claude 3+)
- ✅ Enable debug logging when troubleshooting
- ✅ Switch to KLXMLCodec if token efficiency matters

**DON'T:**
- ❌ Don't hardcode codec format in your prompts
- ❌ Don't instantiate codecs before passing to agent
- ❌ Don't use very small or undertrained LLM models
- ❌ Don't forget to register resources before expecting tool calls
- ❌ Don't mix multiple codec formats in the same agent
- ❌ Don't create custom codecs unless absolutely necessary

---

## 8. Complete Reference Example

This section provides a complete, end-to-end example using the Financial Analysis Agent with CSXMLCodec, including setup, execution, and analysis.

### Complete Financial Analysis Agent Implementation

Here's the full implementation from `examples/agents/financial-analysis/`:

**File structure:**
```
examples/agents/financial-analysis/
├── agents/
│   └── financial_analysis_agent.py    # Agent class with codec
├── prompts/
│   └── FinancialAnalysisAgent.xml     # Agent prompt
├── resources/
│   ├── semantic_search_resource.py    # Semantic search resource
│   ├── read_file_resource.py          # File reading resource
│   └── ripgrep_search_resource.py      # Text search resource
├── data/
│   └── AMD-AR.md                       # Financial data
└── README.md                           # Documentation
```

**File: `agents/financial_analysis_agent.py`**

```python
"""
FinancialAnalysisAgent - Complete implementation with CSXMLCodec.

This agent extracts and analyzes financial data from documents
using structured LLM communication via codecs.
"""
import os
import sys
from datetime import datetime

from dana.common.protocols import DictParams, Notifiable
from dana.core.agent.star_agent import STARAgent

# Add parent directory to path
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

from resources.semantic_search_resource import SemanticSearchResource
from resources.read_file_resource import ReadFileResource
from resources.ripgrep_search_resource import RipgrepSearchResource


class BroadcastNotificationHandler(Notifiable):
    """Optional: Notification handler for observing agent events."""
    
    def __init__(self, agent_name: str = "FinancialAnalysisAgent", verbose: bool = True):
        self.agent_name = agent_name
        self.verbose = verbose
        self.message_count = 0
    
    def notify(self, notifier: object, message: DictParams) -> None:
        """Handle broadcast notifications from agent."""
        self.message_count += 1
        if not self.verbose:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"\n🔔 NOTIFICATION #{self.message_count} [{timestamp}]")
        for key, value in message.items():
            print(f"📝 {key}: {value}")


class FinancialAnalysisAgent(STARAgent):
    """
    Agent specialized in extracting and analyzing financial data.
    
    Features:
    - Uses CSXMLCodec for structured LLM communication
    - Supports semantic search, file reading, and text search
    - Analyzes financial statements and calculates ratios
    """
    
    def __init__(
        self,
        agent_id: str | None = None,
        workspace_root: str | None = None,
        llm_provider: str = "openai",
        model: str = "gpt-4.1-mini",
        **kwargs,
    ):
        # Construct path to prompt XML
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "prompts",
            "FinancialAnalysisAgent.xml",
        )
        prompt_path = os.path.normpath(prompt_path)
        
        # Import codec
        from dana.core.knowledge.prompts.codecs import CSXMLCodec
        
        # Initialize STARAgent with codec
        super().__init__(
            agent_type="financial-analysis",
            agent_id=agent_id or "financial-analysis-001",
            llm_provider=llm_provider,
            model=model,
            prompt_path=prompt_path,
            codec=CSXMLCodec,  # Enable codec-based communication
            **kwargs,
        )
        
        # Register resources
        if workspace_root:
            self.with_resources(
                SemanticSearchResource(
                    resource_id="semantic-search",
                    workspace_root=workspace_root
                ),
                ReadFileResource(
                    resource_id="read-file",
                    workspace_root=workspace_root
                ),
                RipgrepSearchResource(
                    resource_id="ripgrep-search",
                    workspace_root=workspace_root
                ),
            )
        
        # Optional: Add notification handler
        self.notification_handler = BroadcastNotificationHandler("FinancialAnalysisAgent")
        self.with_notifiable(self.notification_handler)
    
    def enable_notifications(self, verbose: bool = True) -> None:
        """Enable/disable notification output."""
        self.notification_handler.verbose = verbose
    
    def get_notification_count(self) -> int:
        """Get total notifications received."""
        return getattr(self.notification_handler, "message_count", 0)


# Complete usage example
if __name__ == "__main__":
    print("=" * 80)
    print("Financial Analysis Agent Demo - Complete Reference Example")
    print("=" * 80)
    print()
    
    # 1. Create agent with codec
    print("1. Creating Financial Analysis Agent with CSXMLCodec...")
    workspace_root = os.path.join(os.path.dirname(__file__), "..", "data")
    agent = FinancialAnalysisAgent(workspace_root=workspace_root)
    agent.enable_notifications(verbose=False)
    
    # 2. Query agent for financial analysis
    print("2. Querying agent for financial analysis...")
    session_id = "financial-session-001"
    query = "Calculate the current ratio for AMD from the financial statements"
    
    result = agent.query(caller_message=query, session_id=session_id)
    
    # 3. Display results
    print("\n3. Agent Response:")
    print("=" * 80)
    print("\n📋 REASONING (from <thinking> block):")
    print(result.get("reasoning", "N/A"))
    
    print("\n✅ RESPONSE (from <response> block):")
    print(result.get("response", "N/A"))
    
    print("\n🔧 TOOL CALLS:")
    print(f"   {len(result.get('tool_calls', []))} tool calls made")
    for i, tool_call in enumerate(result.get('tool_calls', []), 1):
        print(f"   {i}. {tool_call.get('function', 'Unknown')}")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    
    # Summary statistics
    print("\n📊 Summary:")
    print(f"   Notifications: {agent.get_notification_count()}")
    print(f"   Session ID: {session_id}")
    print(f"   Learning storage: .dana/dana_agent/learnings/{session_id}/")
```

### Running the Example

**1. Setup (from `examples/agents/financial-analysis/`):**

```bash
# Ensure you have the financial data
ls data/AMD-AR.md

# Install dependencies if needed
pip install -r requirements.txt
```

**2. Run the agent:**

```bash
# Option A: Run standalone script
cd examples/agents/financial-analysis
python agents/financial_analysis_agent.py

# Option B: Use interactively
from agents import FinancialAnalysisAgent

agent = FinancialAnalysisAgent(workspace_root="data/")
result = agent.query("Calculate the current ratio for AMD")
print(result["response"])
```

### Expected Output

```
================================================================================
Financial Analysis Agent Demo - Complete Reference Example
================================================================================

1. Creating Financial Analysis Agent with CSXMLCodec...
2. Querying agent for financial analysis...

3. Agent Response:
================================================================================

📋 REASONING (from <thinking> block):
User wants current ratio calculation. I need to find current assets and current liabilities
from AMD's balance sheet. I'll use semantic search to locate the balance sheet section first,
then extract the specific values.

Current ratio formula: Current Assets / Current Liabilities

Let me search for balance sheet data.

✅ RESPONSE (from <response> block):
Current Ratio Analysis:
- Current Assets: $3,724M
- Current Liabilities: $2,859M
- Current Ratio: 1.30

Interpretation: AMD has $1.30 in current assets for every $1.00 of current liabilities, indicating healthy short-term liquidity.

🔧 TOOL CALLS:
   1 tool calls made
   1. SemanticSearchResource:search

================================================================================
Demo Complete!
================================================================================

📊 Summary:
   Notifications: 3
   Session ID: financial-session-001
   Learning storage: .dana/dana_agent/learnings/financial-session-001/
```

### Analyzing the Codec Flow

Let's trace how the codec worked in this example:

**1. Prompt Construction:**
```
[Agent's FinancialAnalysisAgent.xml content]

RESPONSE CONTRACT
PURPOSE: Enforce a clear separation...
[CSXMLCodec instructions]

User: Calculate the current ratio for AMD from the financial statements
```

**2. LLM Response (CSXMLCodec format):**
```xml
<thinking>
User wants current ratio calculation. I need to find current assets and current liabilities...
[... reasoning ...]
</thinking>

<function_call>
  <invoke name="SemanticSearchResource:search">
    <parameter name="query">current assets and current liabilities balance sheet</parameter>
    <parameter name="top_k">5</parameter>
  </invoke>
</function_call>
```

**3. Codec Parsing:**
```python
# CodecToolCaller calls CSXMLCodec.parse_response()
parsed = ParsedCodecResponse(
    thinking="User wants current ratio calculation. I need to find current assets...",
    response=None,  # No response yet, tool call present
    tool_calls=[ToolCall(class_name="SemanticSearchResource", name="search", ...)]
)
```

**4. Agent Returns:**
```python
{
    "reasoning": "User wants current ratio calculation. I need to find current assets...",  # From <thinking>
    "response": None,  # Tool call executed, will get response in next turn
    "tool_calls": [{"function": "SemanticSearchResource:search", ...}],  # Tool call executed
    "tool_results": ["Found balance sheet section with current assets: $3,724M..."]
}
```

**5. After Tool Execution, LLM Continues:**
```xml
<thinking>
Found balance sheet data. Current assets: $3,724M, Current liabilities: $2,859M.
Current ratio = 3,724 / 2,859 = 1.30
</thinking>

<response>
Current Ratio Analysis:
- Current Assets: $3,724M
- Current Liabilities: $2,859M
- Current Ratio: 1.30
</response>
```

### Next Steps

- **Learn about custom learners:** See `learning.md` for details on custom learners
- **Add resources:** See Dana documentation for adding tools/resources
- **Explore financial analysis:** Check out `examples/agents/financial-analysis/` for more examples
- **Customize:** Modify `prompts/FinancialAnalysisAgent.xml` to adjust agent behavior

---

**End of Codec Guide**

For questions or issues, refer to:
- Dana documentation: [docs/](../../)
- Financial Analysis Agent README: `examples/agents/financial-analysis/README.md`
- Learning Guide: `learning.md`

