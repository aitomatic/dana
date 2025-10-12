# BaseWAR Reason Method Specification

## Overview

The `reason()` method provides structured LLM reasoning capability for all Workflows, Agents, and Resources (WAR components). It enables any WAR component to leverage LLM intelligence for decision-making, classification, planning, and structured extraction while maintaining type safety and observability.

## Method Signature

```python
def reason(self, params: DictParams) -> DictParams:
    """
    Perform structured LLM reasoning with typed inputs and outputs.
    
    Args:
        params: Dictionary containing:
            - task: str (required) - Description of reasoning task
            - input: DictParams (required) - Input data for reasoning
            - output_schema: DictParams (required) - Expected output structure
            - context: DictParams (optional) - Additional context
            - examples: list[DictParams] (optional) - Few-shot examples
            - temperature: float (optional) - LLM temperature (default: 0.1)
            - max_tokens: int (optional) - Max response tokens (default: 2000)
            - cache_key: str (optional) - Key for caching (default: auto-generated)
            - fallback: DictParams (optional) - Return this if LLM unavailable
    
    Returns:
        DictParams: Response matching output_schema structure
        
    Raises:
        ValueError: If required params missing or output doesn't match schema
        RuntimeError: If LLM call fails and no fallback provided
    """
```

## Input Parameter Specifications

### 1. task (required, str)

**Purpose**: Clear description of what reasoning is needed

**Guidelines**:
- Use imperative voice: "Classify intent", not "Classifying intent"
- Be specific: "Select appropriate web browsing workflow" not "Choose workflow"
- Include key constraints: "Rank search results by authority and recency"

**Examples**:
```python
"Classify user intent for web browsing request"
"Select appropriate workflow for structured data extraction"
"Assess content quality for tutorial extraction"
"Rank search results by relevance and authority"
"Plan synthesis strategy for multiple research sources"
"Detect content type from HTML structure and metadata"
```

### 2. input (required, DictParams)

**Purpose**: Structured data for LLM to reason about

**Guidelines**:
- Use flat structure when possible (avoid deep nesting)
- Include only relevant data (filter out noise)
- Truncate large text fields (use previews)
- Use consistent naming conventions (snake_case)
- Include metadata that aids reasoning (lengths, counts, presence flags)

**Examples**:

```python
# Intent classification
{
    "request": "Compare React vs Vue for enterprise applications",
    "has_url": False,
    "request_length": 47,
    "contains_question": False
}

# Content quality assessment
{
    "url": "https://docs.python.org/3/library/asyncio.html",
    "purpose": "Extract tutorial steps for async programming",
    "content_length": 12453,
    "has_headings": True,
    "has_code_blocks": True,
    "has_tables": False,
    "content_preview": "asyncio is a library to write concurrent code..."
}

# Search result ranking
{
    "query": "Python error handling best practices 2024",
    "results": [
        {
            "url": "https://realpython.com/python-exceptions/",
            "title": "Python Exception Handling Best Practices",
            "snippet": "Learn modern approaches to handling errors...",
            "domain": "realpython.com"
        }
        # ... more results
    ],
    "num_results": 5
}
```

### 3. output_schema (required, DictParams)

**Purpose**: Define expected output structure with types and descriptions

**Guidelines**:
- Use string descriptions for types: "str", "int", "bool", "float", "list[str]", "dict[str, float]"
- For enums, list all options: "str (fact_finding|comparison|trend_analysis)"
- Mark optional fields: "int | null" or "str (optional)"
- Include descriptions in parentheses: "float (0.0-1.0, confidence score)"
- Nest structures as needed but keep shallow when possible

**Examples**:

```python
# Simple classification
{
    "intent": "str (fact_finding|comparison|trend_analysis|how_to|research)",
    "confidence": "float (0.0-1.0)",
    "reasoning": "str (explanation of classification)"
}

# Complex workflow selection
{
    "workflow": "str (structured_data_navigation|research_synthesis|single_source_deep_dive|documentation_site|data_portal|news_site|fact_finding|comparison|trend_analysis|how_to)",
    "confidence": "float (0.0-1.0)",
    "reasoning": "str (why this workflow was chosen)",
    "parameters": {
        "max_sources": "int | null (number of sources to fetch)",
        "require_recent": "bool | null (filter by recency)",
        "extract_code": "bool | null (extract code examples)",
        "rate_limit_sec": "float | null (seconds between requests)"
    },
    "fallback_workflow": "str | null (alternative if primary fails)"
}

# Content assessment
{
    "is_sufficient": "bool (whether content meets purpose)",
    "quality_score": "float (0.0-1.0, overall quality)",
    "content_type": "str (article|documentation|tutorial|forum|news|data_table)",
    "missing_elements": "list[str] (what's needed but absent)",
    "recommendations": "list[str] (suggestions for improvement or alternatives)"
}

# Ranking output
{
    "ranked_results": "list[dict] (results ordered by score, each with 'url' and 'score' keys)",
    "reasoning": "dict[str, str] (url -> explanation of ranking)",
    "recommended_count": "int (how many results to fetch)"
}
```

### 4. context (optional, DictParams)

**Purpose**: Provide additional background information to aid reasoning

**Guidelines**:
- Use for domain knowledge that doesn't fit in input/output
- Include relevant constraints, preferences, or rules
- Provide lists of available options/choices
- Add success criteria or quality standards

**Examples**:

```python
# Workflow selection context
{
    "available_workflows": {
        "structured_data_navigation": "For extracting tables, lists, statistics (5+ items)",
        "research_synthesis": "Understanding topics across 3-5 sources",
        "fact_finding": "Quick factual answers (Wikipedia, authoritative)"
        # ... more workflows
    },
    "user_preferences": {
        "prefer_recent": True,
        "max_time_budget_sec": 30
    }
}

# Content quality context
{
    "purpose_requirements": {
        "tutorial": ["step_by_step_instructions", "code_examples", "explanations"],
        "research": ["multiple_perspectives", "citations", "recent_date"],
        "fact_finding": ["authoritative_source", "concise_answer"]
    },
    "quality_standards": {
        "min_content_length": 500,
        "require_code_if_technical": True
    }
}

# Ranking context
{
    "ranking_factors": [
        "Relevance to query (most important)",
        "Source authority (domain reputation)",
        "Content freshness (prefer recent)",
        "Snippet quality (does it answer query?)",
        "Content type match (tutorial vs article vs docs)"
    ],
    "domain_authority_scores": {
        "stackoverflow.com": 0.9,
        "github.com": 0.85,
        "realpython.com": 0.8
        # ... more domains
    }
}
```

### 5. examples (optional, list[DictParams])

**Purpose**: Few-shot examples to guide LLM reasoning

**Guidelines**:
- Include 2-5 examples (more usually doesn't help)
- Show diverse cases (cover edge cases)
- Each example has input and output keys matching param schemas
- Include reasoning/explanation in outputs

**Examples**:

```python
[
    {
        "input": {
            "request": "What is asyncio?",
            "has_url": False,
            "request_length": 17
        },
        "output": {
            "intent": "fact_finding",
            "confidence": 0.95,
            "reasoning": "Simple factual question with 'what is' pattern, needs quick authoritative answer"
        }
    },
    {
        "input": {
            "request": "Compare React vs Vue for enterprise applications",
            "has_url": False,
            "request_length": 47
        },
        "output": {
            "intent": "comparison",
            "confidence": 0.98,
            "reasoning": "Explicit comparison request with 'compare X vs Y' pattern, needs balanced coverage"
        }
    },
    {
        "input": {
            "request": "Top 10 Python packages for data science",
            "has_url": False,
            "request_length": 42
        },
        "output": {
            "intent": "structured_data",
            "confidence": 0.92,
            "reasoning": "Requesting structured list ('top 10'), likely needs table extraction and navigation"
        }
    }
]
```

### 6. temperature (optional, float, default: 0.1)

**Purpose**: Control LLM randomness/creativity

**Guidelines**:
- 0.0-0.2: Classification, structured extraction (deterministic)
- 0.3-0.5: Planning, synthesis (some creativity)
- 0.6-1.0: Creative tasks (rarely needed for reasoning)

**Recommendations by task type**:
```python
{
    "classification": 0.0,       # Most deterministic
    "intent_detection": 0.1,
    "workflow_selection": 0.1,
    "ranking": 0.1,
    "quality_assessment": 0.2,
    "synthesis_planning": 0.3,   # Slight creativity
    "content_summarization": 0.4
}
```

### 7. max_tokens (optional, int, default: 2000)

**Purpose**: Limit LLM response length

**Guidelines**:
- Simple classification: 200-500 tokens
- Complex reasoning: 1000-2000 tokens
- Planning/synthesis: 2000-4000 tokens

**Recommendations**:
```python
{
    "simple_classification": 200,
    "workflow_selection": 500,
    "content_assessment": 1000,
    "search_ranking": 1500,
    "synthesis_planning": 2000
}
```

### 8. cache_key (optional, str, default: auto-generated)

**Purpose**: Enable caching of identical reasoning calls

**Guidelines**:
- Auto-generated by default from hash(task + input)
- Override for custom cache behavior
- Set to None to disable caching for this call

**Examples**:
```python
# Let system auto-generate (recommended)
cache_key=None  # or omit

# Custom cache key for grouped caching
cache_key=f"workflow_select:{request_type}"

# Disable caching
cache_key=False  # or special sentinel value
```

### 9. fallback (optional, DictParams)

**Purpose**: Value to return if LLM is unavailable or fails

**Guidelines**:
- Should match output_schema structure
- Use for graceful degradation
- Typically a safe default or error indicator

**Examples**:
```python
# Safe default workflow
{
    "workflow": "research_synthesis",
    "confidence": 0.0,
    "reasoning": "LLM unavailable, using safe default",
    "parameters": {"max_sources": 3}
}

# Error indicator
{
    "error": True,
    "message": "LLM reasoning unavailable",
    "fallback_used": True
}
```

## Implementation Requirements

### 1. Prompt Construction

The implementation should build an LLM prompt with this structure:

```
TASK: {task}

INPUT DATA:
{json.dumps(input, indent=2)}

OUTPUT SCHEMA:
{json.dumps(output_schema, indent=2)}

[If context provided:]
CONTEXT:
{json.dumps(context, indent=2)}

[If examples provided:]
EXAMPLES:
{for each example:}
Input: {json.dumps(example['input'], indent=2)}
Output: {json.dumps(example['output'], indent=2)}

INSTRUCTIONS:
- Analyze the input data carefully
- Consider the provided context and examples
- Respond with valid JSON matching the output schema exactly
- Include reasoning/explanation fields where specified
- Use the exact keys specified in output schema
- Ensure all required fields are present
```

### 2. Response Validation

After LLM returns response:
1. Parse JSON (handle parse errors gracefully)
2. Validate against output_schema:
   - Check all required keys present
   - Verify types match (str, int, float, bool, list, dict)
   - For enums, check value is in allowed list
   - For ranges (e.g., "0.0-1.0"), validate bounds
3. If validation fails:
   - Log validation error with details
   - Retry once with clearer instructions (optional)
   - If retry fails, use fallback or raise ValueError

### 3. Caching Strategy

```python
# Cache structure
_reasoning_cache: dict[str, tuple[DictParams, float]] = {}
# cache_key -> (result, timestamp)

# Cache behavior
def reason(self, params: DictParams) -> DictParams:
    cache_key = params.get("cache_key") or self._generate_cache_key(params)

    if cache_key and cache_key in self._reasoning_cache:
        result, timestamp = self._reasoning_cache[cache_key]
        if time.time() - timestamp < self.cache_ttl:  # e.g., 3600 seconds
            logger.debug(f"Cache hit for reasoning: {params['task']}")
            return result

    # Call LLM
    result = self._do_reasoning(params)

    # Cache result
    if cache_key:
        self._reasoning_cache[cache_key] = (result, time.time())

    return result

def _generate_cache_key(self, params: DictParams) -> str:
    """Generate cache key from task + input."""
    cache_input = {
        "task": params["task"],
        "input": params["input"],
        "output_schema": params["output_schema"]
    }
    return hashlib.sha256(
        json.dumps(cache_input, sort_keys=True).encode()
    ).hexdigest()[:16]
```

### 4. Observability

Emit trace events for debugging and monitoring:

```python
def reason(self, params: DictParams) -> DictParams:
    start_time = time.time()

    # Emit trace: reasoning started
    self.send_notification({
        "trace_reasoning_start": {
            "task": params["task"],
            "component": self.__class__.__name__,
            "component_id": getattr(self, "object_id", "unknown"),
            "timestamp": start_time
        }
    })

    try:
        result = self._do_reasoning(params)

        # Emit trace: reasoning completed
        self.send_notification({
            "trace_reasoning_complete": {
                "task": params["task"],
                "component": self.__class__.__name__,
                "duration_ms": (time.time() - start_time) * 1000,
                "cache_hit": False,  # or True if from cache
                "output_preview": str(result)[:200]
            }
        })

        return result

    except Exception as e:
        # Emit trace: reasoning failed
        self.send_notification({
            "trace_reasoning_error": {
                "task": params["task"],
                "component": self.__class__.__name__,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
        })

        if "fallback" in params:
            logger.warning(f"Reasoning failed, using fallback: {e}")
            return params["fallback"]
        else:
            raise
```

### 5. LLM Client Integration

The implementation should support multiple LLM clients:

```python
def _do_reasoning(self, params: DictParams) -> DictParams:
    """Execute LLM reasoning call."""

    if not self.llm_client:
        if "fallback" in params:
            return params["fallback"]
        raise RuntimeError("LLM client not configured and no fallback provided")

    # Build prompt
    prompt = self._build_prompt(params)

    # Call LLM (adapts to different clients)
    response = self.llm_client.generate(
        prompt=prompt,
        temperature=params.get("temperature", 0.1),
        max_tokens=params.get("max_tokens", 2000),
        response_format="json"  # Request JSON output
    )

    # Parse and validate
    try:
        result = json.loads(response)
        self._validate_output(result, params["output_schema"])
        return result
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"LLM response validation failed: {e}")
        logger.debug(f"Raw response: {response}")

        if "fallback" in params:
            return params["fallback"]
        raise
```

## Usage Examples

### Example 1: Intent Classification (Simple)

```python
# In WorkflowSelectorResource
def classify_intent(self, request: str) -> str:
    """Classify user intent from request."""

    result = self.reason({
        "task": "Classify user intent for web browsing request",
        "input": {
            "request": request,
            "request_length": len(request),
            "has_question_mark": "?" in request
        },
        "output_schema": {
            "intent": "str (fact_finding|comparison|trend_analysis|how_to|structured_data|research)",
            "confidence": "float (0.0-1.0)",
            "reasoning": "str"
        },
        "temperature": 0.0,
        "max_tokens": 200
    })

    return result["intent"]
```

### Example 2: Workflow Selection (Complex)

```python
# In WorkflowSelectorResource
def select_workflow(
    self, 
    request: str, 
    target_url: str | None = None
) -> DictParams:
    """Select appropriate workflow with parameters."""

    result = self.reason({
        "task": "Select appropriate web browsing workflow and configure parameters",
        "input": {
            "request": request,
            "target_url": target_url,
            "has_url": bool(target_url),
            "domain": urlparse(target_url).netloc if target_url else None
        },
        "output_schema": {
            "workflow": "str (structured_data_navigation|research_synthesis|single_source_deep_dive|documentation_site|data_portal|news_site|fact_finding|comparison|trend_analysis|how_to)",
            "confidence": "float (0.0-1.0)",
            "reasoning": "str (why this workflow was chosen)",
            "parameters": {
                "max_sources": "int | null",
                "require_recent": "bool | null",
                "extract_code": "bool | null",
                "rate_limit_sec": "float | null",
                "max_pages": "int | null"
            },
            "fallback_workflow": "str | null"
        },
        "context": {
            "available_workflows": self._get_workflow_descriptions(),
            "known_domains": {
                "documentation": ["docs.python.org", "developer.mozilla.org"],
                "data_portal": ["pypi.org", "github.com", "npmjs.com"]
            }
        },
        "examples": [
            {
                "input": {"request": "What is asyncio?", "has_url": False},
                "output": {
                    "workflow": "fact_finding",
                    "confidence": 0.95,
                    "reasoning": "Simple factual question",
                    "parameters": {"max_sources": 2},
                    "fallback_workflow": "research_synthesis"
                }
            },
            {
                "input": {"request": "Top 10 PyPI packages", "has_url": False},
                "output": {
                    "workflow": "structured_data_navigation",
                    "confidence": 0.98,
                    "reasoning": "Structured list extraction needed",
                    "parameters": {"max_pages": 10, "extract_tables": True},
                    "fallback_workflow": "research_synthesis"
                }
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500,
        "fallback": {
            "workflow": "research_synthesis",
            "confidence": 0.0,
            "reasoning": "LLM unavailable, using safe default",
            "parameters": {"max_sources": 3},
            "fallback_workflow": None
        }
    })

    return result
```

### Example 3: Content Quality Assessment

```python
# In ContentExtractorResource
def assess_content_quality(
    self,
    html: str,
    url: str,
    purpose: str
) -> DictParams:
    """Assess if content is sufficient for intended purpose."""

    # Extract basic metrics first
    content = self._extract_main_content(html)
    metadata = self._extract_metadata(html)

    result = self.reason({
        "task": "Assess content quality and sufficiency for intended purpose",
        "input": {
            "url": url,
            "purpose": purpose,
            "content_length": len(content),
            "has_metadata": bool(metadata),
            "has_headings": bool(re.search(r'<h[1-6]', html)),
            "has_code": bool(re.search(r'<code|<pre', html)),
            "has_tables": bool(re.search(r'<table', html)),
            "content_preview": content[:500],
            "title": metadata.get("title", ""),
            "publish_date": metadata.get("date")
        },
        "output_schema": {
            "is_sufficient": "bool (is content adequate for purpose)",
            "quality_score": "float (0.0-1.0, overall quality)",
            "content_type": "str (article|documentation|tutorial|forum|news|data_table|other)",
            "missing_elements": "list[str] (what's needed but absent)",
            "recommendations": "list[str] (suggestions for improvement)",
            "confidence": "float (0.0-1.0)"
        },
        "context": {
            "purpose_requirements": {
                "tutorial": ["step_by_step_instructions", "code_examples", "explanations"],
                "research": ["multiple_perspectives", "citations", "recent_date"],
                "fact_finding": ["authoritative_source", "concise_answer"],
                "structured_data": ["tables", "lists", "statistics"]
            },
            "quality_indicators": {
                "high": ["long_content", "code_examples", "headings", "metadata"],
                "low": ["very_short", "no_structure", "ads_heavy"]
            }
        },
        "temperature": 0.2,
        "max_tokens": 1000
    })

    return result
```

### Example 4: Search Result Ranking

```python
# In WebFetcherResource
def rank_search_results(
    self,
    query: str,
    results: list[DictParams],
    criteria: str = "relevance and authority"
) -> list[DictParams]:
    """Rank search results intelligently."""

    ranking_result = self.reason({
        "task": "Rank search results by relevance, quality, and specified criteria",
        "input": {
            "query": query,
            "num_results": len(results),
            "results": [
                {
                    "url": r["url"],
                    "title": r["title"],
                    "snippet": r["snippet"],
                    "domain": urlparse(r["url"]).netloc
                }
                for r in results
            ],
            "criteria": criteria
        },
        "output_schema": {
            "ranked_results": "list[dict] (results ordered by score, each with 'url', 'score' (0.0-1.0), and 'rank' (1-N) keys)",
            "reasoning": "dict[str, str] (url -> explanation of ranking)",
            "recommended_count": "int (how many results to fetch, typically 3-5)",
            "quality_assessment": "str (overall quality of search results)"
        },
        "context": {
            "ranking_factors": [
                "Relevance to query (most important)",
                "Source authority (domain reputation)",
                "Content freshness (prefer recent if relevant)",
                "Snippet quality (does it answer the query?)",
                "Content type match (tutorial vs article vs docs)"
            ],
            "known_authoritative_domains": [
                "stackoverflow.com", "github.com", "python.org", "mozilla.org",
                "wikipedia.org", "realpython.com", ".gov", ".edu"
            ]
        },
        "temperature": 0.1,
        "max_tokens": 1500
    })

    return ranking_result["ranked_results"]
```

### Example 5: Synthesis Planning (Workflow)

```python
# In ResearchSynthesisWorkflow
def plan_synthesis(
    self,
    sources: list[DictParams],
    query: str
) -> DictParams:
    """Plan how to synthesize multiple sources."""

    plan = self.reason({
        "task": "Plan synthesis strategy for multiple research sources",
        "input": {
            "query": query,
            "num_sources": len(sources),
            "sources": [
                {
                    "url": s["url"],
                    "title": s.get("title", ""),
                    "content_length": len(s.get("content", "")),
                    "content_preview": s.get("content", "")[:200],
                    "domain": urlparse(s["url"]).netloc
                }
                for s in sources
            ]
        },
        "output_schema": {
            "synthesis_approach": "str (compare|merge|timeline|themes|pros_cons)",
            "key_dimensions": "list[str] (what aspects to compare/synthesize on)",
            "source_weights": "dict[str, float] (url -> importance weight 0.0-1.0)",
            "output_structure": "str (narrative|table|bullet_points|sections)",
            "synthesis_steps": "list[str] (ordered steps for synthesis)",
            "reasoning": "str (why this approach)"
        },
        "context": {
            "synthesis_approaches": {
                "compare": "Side-by-side comparison of sources on key dimensions",
                "merge": "Combine complementary information from all sources",
                "timeline": "Organize by temporal sequence or chronology",
                "themes": "Group by common themes/topics across sources",
                "pros_cons": "Organize by advantages and disadvantages"
            }
        },
        "temperature": 0.3,  # Allow some creativity in planning
        "max_tokens": 2000
    })

    return plan
```

## Error Handling

### Expected Exceptions

1. **ValueError**: Invalid params or output validation failure
   ```python
   raise ValueError(f"Output missing required key: {key}")
   raise ValueError(f"Output type mismatch for '{key}': expected {expected}, got {actual}")
   ```

2. **RuntimeError**: LLM call failed and no fallback
   ```python
   raise RuntimeError(f"LLM reasoning failed: {error_msg}")
   ```

3. **KeyError**: Required param missing
   ```python
   raise KeyError(f"Required parameter missing: {param_name}")
   ```

### Graceful Degradation

```python
# Usage pattern with try-except
try:
    result = self.reason({
        "task": "Classify intent",
        "input": {"request": request},
        "output_schema": {"intent": "str", "confidence": "float"}
    })
    intent = result["intent"]
except RuntimeError as e:
    logger.warning(f"LLM reasoning failed: {e}")
    # Fall back to rule-based
    intent = self._rule_based_intent_classification(request)
```

## Performance Considerations

### Expected Latency

- Simple classification: 200-500ms (with caching: <1ms)
- Complex reasoning: 1-3 seconds (with caching: <1ms)
- Batch reasoning: 2-5 seconds for 5-10 items

### Optimization Strategies

1. **Caching**: Cache identical reasoning calls (TTL: 1 hour)
2. **Truncation**: Limit input text to necessary preview (e.g., first 500 chars)
3. **Batch calls**: Group multiple reasoning calls when possible
4. **Async execution**: Use async LLM calls for concurrent reasoning
5. **Fallback chains**: Rule-based → LLM → fallback value

## Testing Requirements

### Unit Tests

```python
def test_reason_simple_classification():
    """Test simple intent classification."""
    war = MockWAR(llm_client=mock_llm)

    result = war.reason({
        "task": "Classify intent",
        "input": {"request": "What is asyncio?"},
        "output_schema": {"intent": "str", "confidence": "float"}
    })

    assert "intent" in result
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0

def test_reason_validation_error():
    """Test output validation catches schema mismatch."""
    war = MockWAR(llm_client=mock_llm_bad_output)

    with pytest.raises(ValueError, match="Output missing required key"):
        war.reason({
            "task": "Test",
            "input": {},
            "output_schema": {"required_key": "str"}
        })

def test_reason_fallback():
    """Test fallback when LLM unavailable."""
    war = MockWAR(llm_client=None)

    result = war.reason({
        "task": "Test",
        "input": {},
        "output_schema": {"value": "str"},
        "fallback": {"value": "fallback_value"}
    })

    assert result["value"] == "fallback_value"

def test_reason_caching():
    """Test that identical calls use cache."""
    war = MockWAR(llm_client=mock_llm)

    # First call
    result1 = war.reason({
        "task": "Test",
        "input": {"x": 1},
        "output_schema": {"y": "int"}
    })

    # Second identical call (should hit cache)
    result2 = war.reason({
        "task": "Test",
        "input": {"x": 1},
        "output_schema": {"y": "int"}
    })

    assert result1 == result2
    assert mock_llm.generate.call_count == 1  # Only called once
```

## Summary

The `BaseWAR.reason(DictParams) -> DictParams` method provides structured LLM reasoning for all WAR components with:

- **Typed I/O**: Structured input/output schemas with validation
- **Observability**: Trace events for monitoring and debugging
- **Caching**: Automatic caching with TTL for performance
- **Fallback**: Graceful degradation when LLM unavailable
- **Flexibility**: Few-shot examples, context, temperature control

### Key Design Principles

1. **All reasoning goes through single consistent interface**
2. **Output validation ensures type safety**
3. **Caching improves performance (identical calls < 1ms)**
4. **Observability via trace events for debugging**
5. **Graceful fallback for robustness**

This design enables any Workflow, Agent, or Resource to leverage LLM intelligence for decisions while maintaining the benefits of structured programming (types, validation, testing).
