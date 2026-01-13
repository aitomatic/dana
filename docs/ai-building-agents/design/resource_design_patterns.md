# Resource Design Patterns

## Overview

Resources provide domain-agnostic capabilities to agents and workflows. This document catalogs proven patterns for designing resources that are reusable, testable, and maintainable.

## Core Resource Concepts

### What Are Resources?

Resources provide access to external capabilities:
- **Domain-agnostic**: Useful across many domains
- **Stateless**: Each method call is independent
- **Composable**: Can be used by multiple workflows/agents
- **Observable**: Decorated for monitoring
- **Tool-callable**: Can be invoked by LLM agents

### Resource vs Workflow

| Aspect | Resource | Workflow |
|--------|----------|----------|
| **Purpose** | External capabilities | Orchestration logic |
| **Domain** | Domain-agnostic | Domain-specific |
| **State** | Stateless (mostly) | Stateless execution |
| **Reusability** | Very high | Moderate |
| **Composition** | By workflows | Of workflows + resources |
| **Examples** | Search, LLM calls, file ops | Analysis pipeline, interview flow |

---

## Structural Patterns

### Pattern 1: Multiple Focused Methods

**Intent**: Provide several related but independent capabilities

**Structure**:
```python
class MultiMethodResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Provides multiple focused capabilities for [domain]:
    - **method1**: Does X
    - **method2**: Does Y
    - **method3**: Does Z
    </PUBLIC_DESCRIPTION>
    """

    @tool_use
    @observable
    def method1(self, param1: str, **kwargs) -> DictParams:
        """Focused capability 1"""
        pass

    @tool_use
    @observable
    def method2(self, param2: int, **kwargs) -> DictParams:
        """Focused capability 2"""
        pass

    @tool_use
    @observable
    def method3(self, param3: list, **kwargs) -> DictParams:
        """Focused capability 3"""
        pass
```

**Real Example**: ConversationResource
```python
class ConversationResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Comprehensive conversation analysis resource.

    Provides methods for:
    - **summarize**: Extract key topics, insights, expertise level, conversation stage
    - **detect_intent**: Classify message intent with context-aware rewriting
    - **extract_topics**: Identify topics with original terminology preservation
    </PUBLIC_DESCRIPTION>
    """

    @tool_use
    @observable
    def detect_intent(self, message: str, conversation_history: list | None = None, **kwargs):
        """Detect user intent and rewrite message with context"""
        pass

    @tool_use
    @observable
    def extract_topics(self, message: str, conversation_history: list | None = None, **kwargs):
        """Extract topics with original terminology preservation"""
        pass
```

**Benefits**:
- Each method is focused and testable
- Methods share underlying infrastructure (LLM, config)
- Agent can choose appropriate method
- High reusability across different workflows

**When to Use**:
- Related capabilities that share infrastructure
- Multiple ways to analyze/process same domain
- Want agent to choose appropriate method

---

### Pattern 2: LLM-Powered Resource

**Intent**: Provide LLM-based capabilities as a resource

**Structure**:
```python
class LLMPoweredResource(BaseResource):
    def __init__(self, llm_provider="anthropic", model=None, **kwargs):
        super().__init__(**kwargs)
        self.llm = LLM(provider=llm_provider, model=model)

    @tool_use
    @observable
    def analyze(self, text: str, **kwargs) -> DictParams:
        """LLM-based analysis"""
        result = asyncio.run(self._do_analyze(text, **kwargs))
        return result

    async def _do_analyze(self, text: str, **kwargs) -> DictParams:
        """Async LLM call"""
        prompt = self._build_prompt(text, **kwargs)
        response = await self.llm.chat_response(
            messages=[LLMMessage(role="user", content=prompt)],
            system_message="System message here",
            max_tokens=500,
            temperature=0.1
        )
        return self._parse_response(response)
```

**Real Example**: ConversationResource
```python
class ConversationResource(BaseResource):
    def __init__(self, llm_provider="anthropic", model=None, **kwargs):
        super().__init__(resource_id="conversation", **kwargs)
        self.llm = LLM(provider=llm_provider, model=model)

    @tool_use
    @observable
    def detect_intent(self, message: str, conversation_history: list | None = None, **kwargs):
        result = asyncio.run(self._detect_intent(message, conversation_history, **kwargs))
        return result

    async def _detect_intent(self, message: str, conversation_history: list | None = None, **kwargs):
        """Async LLM-powered intent detection"""
        context = self._format_conversation(conversation_history) if conversation_history else ""
        prompt = self._build_intent_detection_prompt(message, context)

        response = await self.llm.chat_response(
            messages=[LLMMessage(role="user", content=prompt)],
            system_message="You are an expert conversation analyst...",
            max_tokens=500,
            temperature=0.1
        )

        # Parse JSON response
        content = response.content
        result = json.loads(content.strip())
        return result
```

**Key Features**:
- Own LLM client (configurable provider/model)
- Async/await for LLM calls
- Structured output (JSON)
- Error handling with fallbacks

**When to Use**:
- Need LLM reasoning/generation capabilities
- Multiple related LLM-powered methods
- Want to abstract LLM complexity

---

### Pattern 3: External API Resource

**Intent**: Wrap external API calls as a resource

**Structure**:
```python
class APIResource(BaseResource):
    def __init__(self, api_key=None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv("API_KEY")
        self.client = APIClient(api_key=self.api_key)

    @tool_use
    @observable
    def fetch_data(self, query: str, **kwargs) -> DictParams:
        """Fetch data from external API"""
        try:
            response = self.client.get(query, **kwargs)
            return {
                "success": True,
                "data": response.data,
                "metadata": response.metadata
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
```

**Real Example**: SearchResource
```python
class SearchResource(BaseResource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.web_fetcher = WebFetcher()

    @tool_use
    @observable
    def search_web(self, query: str, max_results: int = 5) -> DictParams:
        """
        Perform web search and return results.

        Uses Google Custom Search API.
        """
        import os

        # Check for required credentials
        if not os.getenv("GOOGLE_API_KEY") or not os.getenv("GOOGLE_SEARCH_ENGINE_ID"):
            return {
                "success": False,
                "error": "Google API credentials not found...",
                "query": query,
                "results": [],
            }

        return self.web_fetcher.search_web(query, max_results, "google")
```

**Key Features**:
- Configuration from environment
- Error handling with structured responses
- Client instantiation in `__init__`
- Consistent return format

---

## Behavioral Patterns

### Pattern 4: Graceful Degradation

**Intent**: Never fail completely; always return useful information

**Structure**:
```python
class GracefulResource(BaseResource):
    @tool_use
    @observable
    def analyze(self, data: str, **kwargs) -> DictParams:
        try:
            # Primary path
            result = self._do_analysis(data, **kwargs)
            return result
        except Exception as e:
            # Fallback path
            return self._create_fallback_result(data, error=str(e))

    def _create_fallback_result(self, data: str, error: str) -> DictParams:
        """Return degraded but useful result"""
        return {
            "success": False,
            "error": error,
            "partial_result": self._simple_analysis(data),
            "fallback": True
        }
```

**Real Example**: ConversationResource
```python
class ConversationResource(BaseResource):
    async def _detect_intent(self, message: str, conversation_history: list | None = None, **kwargs):
        try:
            # LLM-powered intent detection
            context = self._format_conversation(conversation_history)
            prompt = self._build_intent_detection_prompt(message, context)
            response = await self.llm.chat_response(...)
            result = json.loads(content.strip())
            return result

        except Exception as e:
            # Fallback to simple intent
            return self._create_fallback_intent(message, str(e))

    def _create_fallback_intent(self, message: str, error: str | None = None):
        """Fallback when intent detection fails"""
        return {
            "intent": "question",
            "rewritten_message": message,
            "context_analysis": "Unable to analyze context",
            "search_keywords": [],
            "unclear_terms": [],
            "context_switch_detected": False,
            "processing_time": 0.001,
            "error": error,
        }
```

**Benefits**:
- System never fails completely
- Degraded service better than no service
- Clear error information
- Supports debugging

---

### Pattern 5: Fast Path Optimization

**Intent**: Optimize common, simple cases

**Structure**:
```python
class OptimizedResource(BaseResource):
    @tool_use
    @observable
    def process(self, data: str, **kwargs) -> DictParams:
        # Fast path for simple cases
        if self._is_simple_case(data):
            return self._fast_path_result(data)

        # Full processing for complex cases
        return self._full_processing(data, **kwargs)
```

**Real Example**: ConversationResource (via SummarizeConversationWorkflow)
```python
def _do_execute(self, **kwargs):
    conversation_history = kwargs.get("conversation_history", [])

    # Fast path for minimal conversations (no LLM call!)
    if len(conversation_history) < 2:
        return self.conversation_resource._create_minimal_summary(
            conversation_history,
            current_message
        )

    # Full LLM-powered summary
    workflow = (...)
    return workflow.execute(**kwargs)

def _create_minimal_summary(self, history: list, current_message: str | None = None):
    """Create minimal summary for short conversations - no LLM needed"""
    return {
        "key_topics": [],
        "technical_areas": [],
        "expert_insights": [],
        "terminology_introduced": [],
        "context_switches": [],
        "conversation_stage": "early",
        "expertise_level": "unknown",
        "conversation_summary": "Beginning of conversation",
        "conversation_length": len(history),
        "processing_time": 0.001,
        "timestamp": time.time(),
    }
```

**Performance Impact**:
- Avoid expensive operations (LLM calls, API requests) when unnecessary
- Immediate return for simple cases
- Significant cost and latency savings

---

### Pattern 6: Configurable Behavior

**Intent**: Allow customization without subclassing

**Structure**:
```python
class ConfigurableResource(BaseResource):
    def __init__(
        self,
        option1="default",
        option2=None,
        custom_values=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.option1 = option1
        self.option2 = option2 or self._get_defaults()
        self.custom_values = custom_values or []

    @tool_use
    @observable
    def process(self, data: str, **kwargs) -> DictParams:
        # Use configured options
        return self._process_with_config(data, self.option1, self.option2)
```

**Real Example**: ConversationResource
```python
class ConversationResource(BaseResource):
    def __init__(
        self,
        llm_provider: str = "anthropic",
        model: str | None = None,
        intent_types: list[str] | None = None,
        resource_id: str | None = None,
        **kwargs,
    ):
        super().__init__(resource_id=resource_id or "conversation", **kwargs)
        self.llm = LLM(provider=llm_provider, model=model)

        # Configurable intent types
        self.intent_types = intent_types or [
            "question",
            "sharing",
            "clarification",
            "context_switch",
        ]

    def _build_intent_detection_prompt(self, message: str, context: str) -> str:
        """Build prompt using configured intent types"""
        intent_list = "\n".join([f"- {intent}" for intent in self.intent_types])
        return f"""TASK: Analyze this message...

ALLOWED INTENT TYPES:
{intent_list}
..."""
```

**Benefits**:
- Customization without inheritance
- Clear configuration points
- Reusable across different contexts
- Easy to extend

---

## Interface Patterns

### Pattern 7: Consistent Return Format

**Intent**: Always return structured dictionary with predictable keys

**Structure**:
```python
class ConsistentResource(BaseResource):
    @tool_use
    @observable
    def operation(self, input: str, **kwargs) -> DictParams:
        """Always returns consistent structure"""
        try:
            result = perform_operation(input)
            return {
                "success": True,
                "result": result,
                "metadata": {
                    "timestamp": time.time(),
                    "input_length": len(input)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None,
                "metadata": {
                    "timestamp": time.time(),
                    "input_length": len(input)
                }
            }
```

**Real Example**: SearchResource
```python
@tool_use
@observable
def search_web(self, query: str, max_results: int = 5) -> DictParams:
    """Always returns consistent format"""
    # Error case
    if not os.getenv("GOOGLE_API_KEY"):
        return {
            "success": False,
            "error": "Google API credentials not found...",
            "query": query,
            "results": [],
            "total_results": 0,
        }

    # Success case
    return self.web_fetcher.search_web(query, max_results, "google")
    # Returns:
    # {
    #     "success": True,
    #     "query": query,
    #     "results": [...],
    #     "total_results": N,
    #     "search_time_ms": T
    # }
```

**Key Elements**:
- `success: bool` - Always present
- `error: str` - Present when success=False
- `result` or domain-specific keys - The actual data
- `metadata` - Additional context

**Benefits**:
- Predictable interface
- Easy error handling
- Self-documenting
- Consistent across all resources

---

### Pattern 8: Method Decorators

**Intent**: Mark methods as tool-callable and observable

**Required Decorators**:
```python
@tool_use        # Makes method callable by LLM agents
@observable      # Enables monitoring/logging
def method(self, **kwargs) -> DictParams:
    pass
```

**Real Example**: ConversationResource
```python
class ConversationResource(BaseResource):
    @tool_use
    @observable
    def detect_intent(self, message: str, conversation_history: list | None = None, **kwargs):
        """Both decorators enable tool calling and monitoring"""
        result = asyncio.run(self._detect_intent(message, conversation_history, **kwargs))
        return result

    @tool_use
    @observable
    def extract_topics(self, message: str, conversation_history: list | None = None, **kwargs):
        """Every public method uses both decorators"""
        result = asyncio.run(self._extract_topics(message, conversation_history, **kwargs))
        return result
```

**Decorator Order**:
```python
@tool_use       # Outer decorator (applied second)
@observable     # Inner decorator (applied first)
def method(...):
    pass
```

**Why Both**:
- `@tool_use`: Registers method for LLM tool calling
- `@observable`: Enables monitoring, logging, debugging

---

### Pattern 9: PUBLIC_DESCRIPTION Documentation

**Intent**: Provide comprehensive documentation for agents

**Structure**:
```python
class DocumentedResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Brief description of what this resource does.

    Provides methods for:
    - **method1**: What it does
    - **method2**: What it does
    - **method3**: What it does

    USE CASES:
    - Use case 1
    - Use case 2
    - Use case 3

    FEATURES:
    - Feature 1
    - Feature 2
    - Feature 3
    </PUBLIC_DESCRIPTION>
    """
```

**Real Example**: ConversationResource
```python
class ConversationResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Comprehensive conversation analysis resource.

    Provides methods for:
    - **summarize**: Extract key topics, insights, expertise level, conversation stage
    - **detect_intent**: Classify message intent with context-aware rewriting
    - **extract_topics**: Identify topics with original terminology preservation

    All methods share the same LLM client and can leverage conversation context.

    USE CASES:
    - Context-aware dialogue systems
    - Interview and survey applications
    - Customer support session analysis
    - Multi-turn conversation routing
    - Knowledge extraction from conversations

    FEATURES:
    - Configurable intent types for domain-specific classification
    - Automatic terminology preservation
    - Context switch detection
    - Fast path for minimal conversations (no LLM call)
    - Graceful fallback on errors
    </PUBLIC_DESCRIPTION>
    """
```

**Why Important**:
- Appears in agent's system prompt
- Helps agent choose appropriate resource/method
- Documents capabilities clearly
- Explains when to use the resource

---

## Composition Patterns

### Pattern 10: Internal Helper Methods

**Intent**: Break down complex operations into testable helpers

**Structure**:
```python
class WellStructuredResource(BaseResource):
    @tool_use
    @observable
    def public_method(self, input: str, **kwargs) -> DictParams:
        """Public API method"""
        # Orchestrate internal helpers
        processed = self._preprocess(input)
        result = self._core_operation(processed, **kwargs)
        formatted = self._postprocess(result)
        return formatted

    def _preprocess(self, input: str) -> str:
        """Internal helper - preprocessing"""
        pass

    def _core_operation(self, data: str, **kwargs) -> DictParams:
        """Internal helper - core logic"""
        pass

    def _postprocess(self, result: DictParams) -> DictParams:
        """Internal helper - formatting"""
        pass
```

**Real Example**: ConversationResource
```python
class ConversationResource(BaseResource):
    @tool_use
    @observable
    def detect_intent(self, message: str, conversation_history: list | None = None, **kwargs):
        """Public method"""
        result = asyncio.run(self._detect_intent(message, conversation_history, **kwargs))
        return result

    async def _detect_intent(self, message: str, conversation_history: list | None = None, **kwargs):
        """Internal async implementation"""
        context = self._format_conversation(conversation_history)
        prompt = self._build_intent_detection_prompt(message, context)
        response = await self.llm.chat_response(...)
        return self._parse_response(response)

    def _format_conversation(self, history: list, **kwargs) -> str:
        """Internal helper - formatting"""
        pass

    def _build_intent_detection_prompt(self, message: str, context: str) -> str:
        """Internal helper - prompt building"""
        pass

    def _parse_response(self, response) -> DictParams:
        """Internal helper - parsing"""
        pass
```

**Benefits**:
- Each helper is focused and testable
- Clear separation of concerns
- Easier to debug
- Can be reused across methods

---

### Pattern 11: Resource Composition

**Intent**: Use other resources internally

**Structure**:
```python
class CompositeResource(BaseResource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.helper_resource1 = HelperResource1()
        self.helper_resource2 = HelperResource2()

    @tool_use
    @observable
    def complex_operation(self, input: str, **kwargs) -> DictParams:
        """Use other resources internally"""
        data1 = self.helper_resource1.fetch(input)
        data2 = self.helper_resource2.process(data1)
        return self._synthesize(data1, data2)
```

**Real Example**: SearchResource
```python
class SearchResource(BaseResource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.web_fetcher = WebFetcher()  # Internal helper resource

    @tool_use
    @observable
    def search_web(self, query: str, max_results: int = 5) -> DictParams:
        """Uses web_fetcher internally"""
        return self.web_fetcher.search_web(query, max_results, "google")

    @observable
    def rank_by_relevance(self, query: str, results: list, criteria: str = "relevance"):
        """Uses web_fetcher for ranking too"""
        return self.web_fetcher.rank_search_results(query, results, criteria)
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Domain-Specific Resource

**Problem**: Resource too specific to be reusable

**Bad**:
```python
class CrystallizationProcessResource(BaseResource):
    """Too specific - only useful for crystallization domain"""
    def analyze_supersaturation(self, ...):
        pass
```

**Good**:
```python
class ProcessAnalysisResource(BaseResource):
    """Domain-agnostic - useful for any process analysis"""
    def analyze_parameters(self, process_data, thresholds, ...):
        pass

# Crystallization workflow uses it with crystallization-specific parameters
```

---

### Anti-Pattern 2: Stateful Resource

**Problem**: Resource maintains state between calls

**Bad**:
```python
class StatefulResource(BaseResource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.accumulated_data = []  # Bad: state between calls

    def add_data(self, data):
        self.accumulated_data.append(data)  # Stateful!

    def process_all(self):
        return process(self.accumulated_data)
```

**Good**:
```python
class StatelessResource(BaseResource):
    def process_batch(self, data_list: list) -> DictParams:
        """Stateless - all data passed in"""
        return {"result": process(data_list)}
```

**Exception**: Configuration state in `__init__` is okay (llm client, api keys, etc.)

---

### Anti-Pattern 3: Missing Error Handling

**Problem**: No graceful error handling

**Bad**:
```python
@tool_use
@observable
def fetch_data(self, query: str) -> DictParams:
    response = api.get(query)  # Could raise exception!
    return {"result": response.data}
```

**Good**:
```python
@tool_use
@observable
def fetch_data(self, query: str) -> DictParams:
    try:
        response = api.get(query)
        return {
            "success": True,
            "result": response.data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "result": None
        }
```

---

### Anti-Pattern 4: God Resource

**Problem**: Resource does too many unrelated things

**Bad**:
```python
class GodResource(BaseResource):
    def search_web(self, ...): pass
    def analyze_sentiment(self, ...): pass
    def send_email(self, ...): pass
    def generate_report(self, ...): pass
    def backup_database(self, ...): pass
    # Too many unrelated capabilities!
```

**Good**: Split into focused resources
```python
class SearchResource(BaseResource):
    def search_web(self, ...): pass
    def rank_results(self, ...): pass

class AnalysisResource(BaseResource):
    def analyze_sentiment(self, ...): pass
    def extract_topics(self, ...): pass

class CommunicationResource(BaseResource):
    def send_email(self, ...): pass
    def send_notification(self, ...): pass
```

---

## Quick Reference

| Pattern | Use Case | Key Feature |
|---------|----------|-------------|
| Multiple Focused Methods | Related capabilities | 2-5 focused methods |
| LLM-Powered | AI reasoning/generation | Async LLM calls |
| External API | Wrap API calls | Error handling, credentials |
| Graceful Degradation | Never fail completely | Fallback results |
| Fast Path | Optimize common cases | Early return |
| Configurable Behavior | Customization | Constructor parameters |
| Consistent Return Format | Predictable interface | Always include success/error |
| Method Decorators | Tool calling + monitoring | @tool_use @observable |
| PUBLIC_DESCRIPTION | Agent documentation | Comprehensive docstring |
| Internal Helpers | Break down complexity | Private methods |
| Resource Composition | Use other resources | Instantiate in __init__ |

---

## Design Checklist

Before implementing a resource, verify:

- [ ] **Domain-agnostic**: Could this be useful in other domains?
- [ ] **Stateless**: Are methods independent of each other?
- [ ] **Error handling**: Does every method handle errors gracefully?
- [ ] **Consistent format**: Do all methods return consistent structure?
- [ ] **Decorators**: Are public methods marked with @tool_use and @observable?
- [ ] **Documentation**: Is there a clear PUBLIC_DESCRIPTION?
- [ ] **Focused**: Does each method do one thing well?
- [ ] **Fallbacks**: Are there fallback paths for failures?
- [ ] **Configuration**: Can behavior be customized without subclassing?

---

## Examples Reference

- **ConversationResource**: LLM-powered, multiple methods, graceful degradation
- **SearchResource**: External API, consistent format, configurable
- **ExpertInsightAnalyzer**: Domain-specific analysis with generic capabilities
- **KnowledgeGapDetector**: Comparison and analysis resource

See the codebase for full implementations:
- `dana/lib/resources/conversation.py`
- `dana/lib/resources/web_research/search.py`
- `contrib/expert_interview/resources/`
