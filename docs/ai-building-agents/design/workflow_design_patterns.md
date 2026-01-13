# Workflow Design Patterns

## Overview

Workflows provide the deterministic orchestration layer in the Dana architecture. This document catalogs proven patterns for designing workflows that are composable, testable, and maintainable.

## Core Workflow Concepts

### What Are Workflows?

Workflows encode deterministic, multi-step processes:
- **Deterministic**: Same inputs produce same outputs
- **Composable**: Can be chained and nested
- **Observable**: Each step can be monitored
- **Testable**: Clear inputs and outputs
- **Domain-specific**: Encode business logic and domain knowledge

### Workflow vs Resource

| Aspect | Workflow | Resource |
|--------|----------|----------|
| **Purpose** | Orchestration and logic | External capabilities |
| **Composition** | Other workflows + resources | Other resources (internally) |
| **Determinism** | Highly deterministic | May be non-deterministic (LLM calls) |
| **Domain** | Domain-specific logic | Domain-agnostic capabilities |
| **Reusability** | Moderate (within domain) | High (across domains) |

---

## Execution Patterns

### Pattern 1: Sequential Pipeline

**Intent**: Chain operations where each step depends on the previous result

**Structure**:
```python
class SequentialWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        workflow = (
            Step1Workflow()
            | Step2Workflow()
            | Step3Workflow()
        )
        return workflow.execute(**kwargs)
```

**Real Example**: FactFindingWorkflow
```python
from dana.core.workflow.callable_workflow import CallableWorkflow

class FactFindingWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        workflow = (
            SearchWorkflow()
            | CallableWorkflow(
                _fetcher.fetch_and_extract_single,
                "url=result.results.0.url|url, purpose=query -> fetch_result"
            )
            | CallableWorkflow(
                _extractor.extract_fact,
                "content=fetch_result.content_text, query=query"
            )
            | CallableWorkflow(
                _formatter.format_with_metadata,
                "content=result.fact, metadata=fetch_result.metadata"
            )
        )
        return workflow.execute(**kwargs)
```

**Key Features**:
- Each step receives output from previous step
- Data flows automatically through pipeline
- Use `|` operator for chaining
- Results accumulate in shared context

**When to Use**:
- Clear sequential dependencies
- Each step needs previous results
- Linear data flow

**Data Flow**:
```
kwargs → Step1 → result1 → Step2 → result2 → Step3 → final_result
```

---

### Pattern 2: Parallel Execution

**Intent**: Execute independent operations concurrently for performance

**Structure**:
```python
class ParallelWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        async def parallel_phase():
            results = await asyncio.gather(
                operation1(**kwargs),
                operation2(**kwargs),
                operation3(**kwargs),
            )
            return results

        result1, result2, result3 = asyncio.run(parallel_phase())

        return {
            "result1": result1,
            "result2": result2,
            "result3": result3,
        }
```

**Real Example**: ExpertInterviewWorkflow Phase 1
```python
class ExpertInterviewWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        expert_message = kwargs["expert_message"]
        conversation_history = kwargs.get("conversation_history", [])

        # PHASE 1: Parallel information gathering
        async def phase1():
            """Extract topics and insights in parallel"""
            topic_task = asyncio.create_task(
                self.conversation._extract_topics(
                    message=expert_message,
                    conversation_history=conversation_history,
                    preserve_terminology=True
                )
            )

            insight_task = asyncio.create_task(
                self.insight_analyzer._analyze_insights(
                    message=expert_message,
                    conversation_history=conversation_history,
                    expert_profile=self.expert_profile
                )
            )

            return await asyncio.gather(topic_task, insight_task)

        topics, insights = asyncio.run(phase1())
        # ... continue processing
```

**Key Features**:
- Use `asyncio.gather()` for parallel execution
- Operations must be independent
- Significant performance improvement
- Return tuple/list of results

**When to Use**:
- Operations are independent (no data dependencies)
- Operations are I/O-bound (API calls, LLM calls)
- Want to optimize for speed
- Multiple data sources to gather

**Performance Gain**:
```
Sequential: T1 + T2 + T3 = Total Time
Parallel:   max(T1, T2, T3) = Total Time
```

---

### Pattern 3: Phased Orchestration

**Intent**: Combine parallel gathering with sequential processing

**Structure**:
```python
class PhasedWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Phase 1: Parallel gathering
        async def phase1():
            return await asyncio.gather(
                gather_data1(**kwargs),
                gather_data2(**kwargs),
            )

        data1, data2 = asyncio.run(phase1())

        # Phase 2: Sequential processing (depends on Phase 1)
        processed = process_data(data1, data2)

        # Phase 3: Synthesis (depends on Phase 2)
        final = synthesize_results(processed)

        return final
```

**Real Example**: ResearchSynthesisWorkflow
```python
class ResearchSynthesisWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Pre-processing: Calculate search multiplier
        def adjust_max_results(params):
            params["max_results"] = params.get("max_sources", 5) * 2

        # Compose workflows using direct methods and callables
        workflow = (
            SearchWorkflow(pre_callable=adjust_max_results)
            | _searcher.rank_by_relevance
            | _select_top_urls
            | _fetcher.fetch_and_extract
            | _synthesize
        )

        return workflow.execute(**kwargs)
```

**Key Features**:
- Optimal performance (parallelize what you can)
- Maintain dependencies (sequence what you must)
- Clear phase boundaries
- Mix async/sync as needed

**When to Use**:
- Some operations are independent, others dependent
- Want to optimize performance while respecting dependencies
- Clear logical phases in the process

**Common Phase Patterns**:
```
Phase 1 (Parallel): Data gathering from multiple sources
Phase 2 (Sequential): Processing/analysis of gathered data
Phase 3 (Sequential): Synthesis/output generation
```

---

### Pattern 4: Conditional Branching

**Intent**: Different execution paths based on conditions

**Structure**:
```python
class ConditionalWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        condition = evaluate_condition(**kwargs)

        if condition == "path_a":
            return PathAWorkflow().execute(**kwargs)
        elif condition == "path_b":
            return PathBWorkflow().execute(**kwargs)
        else:
            return DefaultWorkflow().execute(**kwargs)
```

**Real Example**: SummarizeConversationWorkflow
```python
class SummarizeConversationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        conversation_history = kwargs.get("conversation_history", [])

        # Fast path for minimal conversations
        if len(conversation_history) < 2:
            return self.conversation_resource._create_minimal_summary(
                conversation_history,
                current_message
            )

        # Normal path: Full workflow
        workflow = (
            CallableWorkflow(
                self.conversation_resource._format_conversation,
                "conversation_history=conversation_history, current_message=current_message -> conversation_text"
            )
            | CallableWorkflow(
                self.conversation_resource._generate_llm_summary,
                "conversation_text=conversation_text"
            )
            | CallableWorkflow(add_metadata, "key_topics=key_topics, ...")
        )

        return workflow.execute(**kwargs)
```

**Key Features**:
- Fast paths for simple cases
- Different workflows for different conditions
- Explicit decision points
- Performance optimization

**When to Use**:
- Clear decision points
- Different complexity levels
- Optimization opportunities (fast paths)
- Different strategies for different inputs

---

## Composition Patterns

### Pattern 5: Pipe Composition

**Intent**: Chain workflows using the pipe operator

**Syntax**:
```python
workflow = Workflow1() | Workflow2() | Workflow3()
result = workflow.execute(**kwargs)
```

**Data Flow**:
- Output of Workflow1 becomes input to Workflow2
- Results accumulate in shared dictionary
- Access previous results via `result` key or parameter mapping

**Real Example**: GoogleLookupWorkflow
```python
class GoogleLookupWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Use direct method composition - no wrapper workflow needed!
        workflow = SearchWorkflow() | _extractor.extract_answer_from_search
        return workflow.execute(**kwargs)
```

**Key Features**:
- Clean, readable syntax
- Automatic data flow
- Works with workflows AND callables
- Composable with other patterns

---

### Pattern 6: CallableWorkflow Wrapping

**Intent**: Wrap resource methods or functions into workflows for pipeline composition

**Structure**:
```python
from dana.core.workflow.callable_workflow import CallableWorkflow

workflow = (
    SomeWorkflow()
    | CallableWorkflow(resource.method, "param_mapping")
    | CallableWorkflow(helper_function, "param_mapping")
)
```

**Real Example**: FactFindingWorkflow
```python
workflow = (
    SearchWorkflow()
    | CallableWorkflow(
        _fetcher.fetch_and_extract_single,
        "url=result.results.0.url|url, purpose=query -> fetch_result"
    )
    | CallableWorkflow(
        _extractor.extract_fact,
        "content=fetch_result.content_text, query=query"
    )
)
```

**Parameter Mapping Syntax**:
```python
# Format: "target_param=source_path|fallback -> output_name"

# Examples:
"url=result.url"                     # Simple mapping
"url=result.results.0.url"           # Nested access
"url=result.results.0.url|url"       # With fallback
"content=fetch_result.content_text"  # From previous step
"-> fetch_result"                    # Rename output
```

**Key Features**:
- Turn any callable into a workflow
- Declarative parameter mapping
- Automatic resolution from previous results
- Clean pipeline composition

---

### Pattern 7: Pre/Post Callable Hooks

**Intent**: Transform inputs or outputs without modifying workflow logic

**Structure**:
```python
class WorkflowWithHooks(BaseWorkflow):
    def __init__(self, **kwargs):
        def pre_hook(params):
            # Transform params before execution
            params["adjusted_param"] = params.get("param") * 2

        def post_hook(result):
            # Transform result after execution
            result["metadata"] = {"processed": True}

        super().__init__(
            pre_callable=pre_hook,
            post_callable=post_hook,
            **kwargs
        )

    def _do_execute(self, **kwargs):
        # Core logic here
        return {"result": "data"}
```

**Real Example**: ResearchSynthesisWorkflow
```python
class ResearchSynthesisWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Pre-processing: Calculate search multiplier
        def adjust_max_results(params):
            params["max_results"] = params.get("max_sources", 5) * 2

        workflow = (
            SearchWorkflow(pre_callable=adjust_max_results)
            | _searcher.rank_by_relevance
            | _select_top_urls
        )

        return workflow.execute(**kwargs)
```

**When to Use**:
- Need to adjust parameters before execution
- Need to transform results after execution
- Keep core logic clean
- Add metadata or logging

---

## Validation Patterns

### Pattern 8: Input/Output Validation

**Intent**: Enforce contracts and provide clear error messages

**Structure**:
```python
from dana.core.workflow.validation import validate_input, validate_output

class ValidatedWorkflow(BaseWorkflow):
    @validate_input(
        query={"required": True, "type": str, "min_length": 1},
        max_results={"type": int, "min_value": 1, "max_value": 100, "default": 10},
    )
    @validate_output(
        success={"required": True, "type": bool},
        results={"required": True, "type": list},
    )
    def _do_execute(self, **kwargs):
        # Implementation
        pass
```

**Real Example**: SearchWorkflow
```python
class SearchWorkflow(BaseWorkflow):
    @validate_input(
        query={"required": True, "type": str, "min_length": 1},
        max_results={"type": int, "min_value": 1, "max_value": 100, "default": 10},
    )
    @validate_output(
        success={"required": True, "type": bool},
        query={"required": True, "type": str},
        results={"required": True, "type": list},
    )
    def _do_execute(self, **kwargs):
        return _searcher.search_web(
            query=kwargs["query"],
            max_results=kwargs["max_results"]
        )
```

**Validation Options**:
```python
{
    "required": True,           # Must be present
    "type": str,                # Type checking
    "min_length": 1,            # String minimum length
    "max_length": 1000,         # String maximum length
    "min_value": 1,             # Number minimum
    "max_value": 100,           # Number maximum
    "default": 10,              # Default value if missing
    "enum": ["a", "b", "c"],    # Must be one of these
}
```

**Benefits**:
- Clear contracts
- Early error detection
- Automatic defaults
- Self-documenting

---

## Error Handling Patterns

### Pattern 9: Graceful Degradation

**Intent**: Provide fallback behavior when operations fail

**Structure**:
```python
class GracefulWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        try:
            # Primary path
            result = primary_operation(**kwargs)
            return result
        except Exception as e:
            # Fallback path
            return fallback_operation(**kwargs, error=str(e))
```

**Real Example**: SummarizeConversationWorkflow
```python
class SummarizeConversationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        try:
            # Compose the workflow pipeline
            workflow = (
                CallableWorkflow(self.conversation_resource._format_conversation, ...)
                | CallableWorkflow(self.conversation_resource._generate_llm_summary, ...)
                | CallableWorkflow(add_metadata, ...)
            )

            result = workflow.execute(**kwargs)
            return result["result"]

        except Exception as e:
            # Fallback to minimal summary
            return self.conversation_resource._create_fallback_summary(
                conversation_history,
                current_message,
                str(e)
            )
```

**Key Features**:
- Never fail completely
- Degrade gracefully
- Log errors for debugging
- Return partial results when possible

---

### Pattern 10: Custom Validation with Error Response

**Intent**: Validate complex conditions and return structured errors

**Structure**:
```python
class CustomValidationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Custom validation logic
        if not meets_condition(kwargs):
            return {
                "success": False,
                "error": "validation_error",
                "message": "Detailed error message",
                "field": "problematic_field",
            }

        # Normal processing
        return perform_operation(**kwargs)
```

**Real Example**: StructuredDataNavigationWorkflow
```python
class StructuredDataNavigationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        query = kwargs.get("query")
        url = kwargs.get("url")

        # Custom validation: at least one must be provided
        if not query and not url:
            return {
                "success": False,
                "error": "validation_error",
                "message": "Either 'query' or 'url' parameter must be provided",
                "field": "query/url",
                "tables": [],
                "lists": [],
                "statistics": {},
            }

        return _extractor.navigate_and_extract_structured(**kwargs)
```

**Benefits**:
- Clear error messages
- Structured error responses
- Client-friendly errors
- Consistent error format

---

## Resource Integration Patterns

### Pattern 11: Workflow Result Unwrapping

**Intent**: Properly access results when composing workflows

**Problem**: `workflow.execute()` wraps return value in `{"result": {...}}` structure

**Structure**:
```python
class OrchestrationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Execute sub-workflow
        result = SubWorkflow().execute(**kwargs)

        # MUST unwrap the nested result
        inner_result = result.get("result", {})

        # Now access the actual data
        if inner_result.get("success"):
            data = inner_result.get("data", [])
            # Process data...
```

**Real Example**: BatchOrchestrationWorkflow
```python
class BatchOrchestrationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        for province in provinces:
            # Execute discovery workflow
            discovery_result = self.discovery_workflow.execute(province=province)

            # UNWRAP: workflow.execute() returns {"result": {...}}
            inner_result = discovery_result.get("result", {})

            # Access actual result data
            if inner_result.get("success"):
                companies = inner_result.get("companies", [])
                all_discovered.extend(companies)
```

**Key Points**:
- `workflow.execute()` always wraps `_do_execute()` return in `{"result": ...}`
- This enables middleware, logging, and error tracking
- When composing workflows, always unwrap with `.get("result", {})`
- Agent convenience methods should also unwrap before returning to user

**Safe Unwrapping Helper**:
```python
def unwrap_workflow_result(result: dict) -> dict:
    """Safely unwrap the nested result from workflow.execute()."""
    return result.get("result", {})

# Usage:
result = SubWorkflow().execute(**kwargs)
inner = unwrap_workflow_result(result)
```

**When to Use**:
- Always when calling `workflow.execute()` from within another workflow
- In agent convenience methods that wrap workflow execution
- Never needed within `_do_execute()` itself (no wrapping at that level)

---

### Pattern 12: Module-Level Resource Instantiation

**Intent**: Share resource instances across workflows in same module

**Structure**:
```python
# module_workflows.py
from dana.lib.resources import Resource1, Resource2

# Module-level instantiation
_resource1 = Resource1()
_resource2 = Resource2()

class Workflow1(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _resource1.method(**kwargs)

class Workflow2(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _resource2.method(**kwargs)
```

**Real Example**: web_research.py
```python
from dana.lib.resources.web_research import (
    SearchResource,
    FetchResource,
    ExtractResource,
    FormatResource,
    SynthesizeResource
)

# Module-level instantiation
_searcher = SearchResource()
_fetcher = FetchResource()
_extractor = ExtractResource()
_formatter = FormatResource()
_synthesizer = SynthesizeResource()

class SearchWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _searcher.search_web(**kwargs)

class GoogleLookupWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        workflow = SearchWorkflow() | _extractor.extract_answer_from_search
        return workflow.execute(**kwargs)
```

**Benefits**:
- No duplicate instantiation
- Shared resource state (if needed)
- Cleaner workflow code
- Better performance
- Easy to mock for testing

---

### Pattern 13: Instance-Level Resource Ownership

**Intent**: Workflow owns and manages its resources internally

**Structure**:
```python
class ResourceOwningWorkflow(BaseWorkflow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.resource1 = Resource1()
        self.resource2 = Resource2()

    def _do_execute(self, **kwargs):
        data = self.resource1.fetch(**kwargs)
        result = self.resource2.process(data)
        return result
```

**Real Example**: ExpertInterviewWorkflow
```python
class ExpertInterviewWorkflow(BaseWorkflow):
    def __init__(self, reference_materials=None, expert_profile=None, **kwargs):
        super().__init__(workflow_id="expert-interview", **kwargs)

        # Initialize resources
        self.conversation = ConversationResource()
        self.insight_analyzer = ExpertInsightAnalyzer()
        self.gap_detector = KnowledgeGapDetector()

        self.reference_materials = reference_materials or []
        self.expert_profile = expert_profile or {}

    def _do_execute(self, **kwargs):
        # Use self.conversation, self.insight_analyzer, etc.
        pass
```

**When to Use**:
- Workflow needs stateful resources
- Resources need configuration specific to workflow
- Resources not shared with other workflows
- Need clear resource lifecycle

---

## Performance Patterns

### Pattern 14: Fast Path Optimization

**Intent**: Optimize for common, simple cases

**Structure**:
```python
class OptimizedWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Check for fast path condition
        if is_simple_case(**kwargs):
            return fast_path_result(**kwargs)

        # Full processing for complex cases
        return full_processing_workflow().execute(**kwargs)
```

**Real Example**: SummarizeConversationWorkflow
```python
def _do_execute(self, **kwargs):
    conversation_history = kwargs.get("conversation_history", [])

    # Fast path for minimal conversations (no LLM call!)
    if len(conversation_history) < 2:
        return self.conversation_resource._create_minimal_summary(
            conversation_history,
            current_message
        )

    # Full LLM-powered summary for longer conversations
    workflow = (...)
    return workflow.execute(**kwargs)
```

**Performance Impact**:
- Avoid expensive operations (LLM calls) when unnecessary
- Return immediately for simple cases
- Significant latency improvement

---

### Pattern 15: Batch Operations

**Intent**: Process multiple items efficiently

**Structure**:
```python
class BatchWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        items = kwargs["items"]

        # Batch processing
        results = resource.batch_process(items)

        return {"results": results, "count": len(results)}
```

**When to Use**:
- Multiple similar operations
- Resource supports batching
- Want to minimize API calls or overhead

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Workflow Doing Agent Work

**Problem**: Workflow contains decision logic that should be in an agent

**Symptom**:
```python
class BadWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Don't: Complex branching logic based on user intent
        if user_wants_detailed_analysis:
            # 50 lines of logic
        elif user_wants_summary:
            # 50 lines of logic
        else:
            # 50 lines of logic
```

**Solution**: Let agent make the decision, call appropriate workflow
```python
# Agent prompt:
# "If user wants detailed analysis, use DetailedAnalysisWorkflow.
#  If user wants summary, use SummaryWorkflow."
```

---

### Anti-Pattern 2: Sequential When Could Be Parallel

**Problem**: Missing performance optimization opportunity

**Bad**:
```python
def _do_execute(self, **kwargs):
    result1 = fetch_data1(**kwargs)  # Takes 2s
    result2 = fetch_data2(**kwargs)  # Takes 2s
    # Total: 4s
```

**Good**:
```python
def _do_execute(self, **kwargs):
    async def parallel():
        return await asyncio.gather(
            fetch_data1(**kwargs),  # 2s
            fetch_data2(**kwargs),  # 2s
        )
    result1, result2 = asyncio.run(parallel())
    # Total: 2s
```

---

### Anti-Pattern 3: No Validation

**Problem**: Unclear expectations, poor error messages

**Bad**:
```python
def _do_execute(self, **kwargs):
    query = kwargs["query"]  # KeyError if missing!
    return search(query)
```

**Good**:
```python
@validate_input(
    query={"required": True, "type": str, "min_length": 1}
)
def _do_execute(self, **kwargs):
    return search(kwargs["query"])
```

---

### Anti-Pattern 4: Tight Coupling

**Problem**: Workflow tightly coupled to specific resource implementation

**Bad**:
```python
def _do_execute(self, **kwargs):
    # Tightly coupled to GoogleSearchResource
    google = GoogleSearchResource()
    return google.search(kwargs["query"])
```

**Good**:
```python
def __init__(self, search_resource=None, **kwargs):
    super().__init__(**kwargs)
    # Accept any search resource (dependency injection)
    self.search_resource = search_resource or SearchResource()

def _do_execute(self, **kwargs):
    return self.search_resource.search(kwargs["query"])
```

---

## Quick Reference

| Pattern | Use Case | Key Feature |
|---------|----------|-------------|
| Sequential Pipeline | Steps depend on previous results | `|` operator chaining |
| Parallel Execution | Independent operations | `asyncio.gather()` |
| Phased Orchestration | Mix of parallel and sequential | Phases with async/sync |
| Conditional Branching | Different paths based on input | if/elif/else with workflows |
| Pipe Composition | Clean workflow chaining | `Workflow1() \| Workflow2()` |
| CallableWorkflow | Wrap functions/methods | Parameter mapping |
| Pre/Post Hooks | Transform inputs/outputs | `pre_callable`, `post_callable` |
| Input Validation | Enforce contracts | `@validate_input` decorator |
| Graceful Degradation | Handle failures | try/except with fallbacks |
| Custom Validation | Complex conditions | Structured error responses |
| **Result Unwrapping** | **Compose workflows** | **`.get("result", {})`** |
| Module-Level Resources | Share resources | Instantiate at module level |
| Instance-Level Resources | Stateful resources | Store as instance attributes |
| Fast Path | Optimize common cases | Early return for simple cases |
| Batch Operations | Process multiple items | Batch processing |

---

## Examples Reference

- **FactFindingWorkflow**: Sequential pipeline with CallableWorkflow
- **ExpertInterviewWorkflow**: Phased orchestration (parallel → sequential)
- **ResearchSynthesisWorkflow**: Pipeline with pre_callable hook
- **SummarizeConversationWorkflow**: Fast path optimization + graceful degradation
- **SearchWorkflow**: Input/output validation

See the codebase for full implementations:
- `dana/lib/workflows/web_research.py`
- `dana/lib/workflows/conversation.py`
- `contrib/expert_interview/workflows/expert_interview.py`
