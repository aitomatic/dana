# Callable Workflow Composition Patterns

## Overview

The new `CallableWorkflow` feature allows you to compose workflows with callables (functions, lambdas, methods) using the `|` operator. This guide shows you the three main patterns and when to use each.

## Pattern 1: Direct Method Composition (Simplest!)

**Use when:** Parameter names match between workflows

**Example:**
```python
from dana.lib.resources.web_research.extract import ExtractResource

_extract_resource = ExtractResource()

# extract_answer_from_search expects 'results' parameter
# Previous workflow returns {'results': [...]}
# Perfect match - use method directly!

workflow = SearchWorkflow() | _extract_resource.extract_answer_from_search
```

**Benefits:**
- ✅ Zero boilerplate
- ✅ Direct, obvious code
- ✅ Automatic parameter extraction via signature inspection

**Before:**
```python
class ExtractAnswerWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _extract_resource.extract_answer_from_search(
            results=kwargs.get("results", [])
        )

workflow = SearchWorkflow() | ExtractAnswerWorkflow()
```

**After:**
```python
workflow = SearchWorkflow() | _extract_resource.extract_answer_from_search
```

**Code reduction:** ~15 lines → 1 line! 📉

---

## Pattern 2: Lambda for Simple Transformations

**Use when:** Need to transform or rename parameters

**Example:**
```python
# Previous workflow returns {'items': [...]}
# Next step needs 'data' parameter

workflow = (
    LoadWorkflow()
    | (lambda items: [x for x in items if x['score'] > 0.5])
    | ProcessWorkflow()
)
```

**Benefits:**
- ✅ Inline transformation
- ✅ No separate function needed
- ✅ Clear data flow

**Common use cases:**
```python
# Filter data
| (lambda results: [r for r in results if r.get('score', 0) > 0.8])

# Extract field
| (lambda items: [item['url'] for item in items])

# Rename parameter
| (lambda fact: {'content': fact, 'metadata': {}})

# Combine fields
| (lambda title, body: {'text': f"{title}\n\n{body}"})
```

---

## Pattern 3: Declarative Mapping (Complex Transformations)

**Use when:** Need complex parameter mapping with fallbacks

### For Regular Workflows:

**Example:**
```python
workflow = (
    SearchWorkflow()
    | FetchWorkflow("url=result.results.0.url|backup_url, purpose=query")
    | ExtractWorkflow("content=result.content_text -> fact")
)
```

### For Callable Workflows (NEW!):

**Example:**
```python
from dana.core.workflow import CallableWorkflow

workflow = (
    SearchWorkflow()
    | FetchWorkflow("url=result.results.0.url|backup_url, purpose=query -> fetch_result")
    | CallableWorkflow(
        _extract_resource.extract_fact,
        args_transform="content=fetch_result.content_text, query=query"
    )
)
```

**Benefits:**
- ✅ Handles nested paths (`result.results.0.url`)
- ✅ Fallback values (`primary|fallback`)
- ✅ Output renaming (`-> new_name`)
- ✅ No code needed, just string syntax
- ✅ Works with any callable (methods, functions, lambdas)

**Syntax:**
```
"param1=source.path|fallback, param2=other.path -> output_name"
```

**Parameter Resolution (NEW!):**

Simple keys (no dots) automatically check `result` first, then top-level:

```python
# "url=url" will check:
# 1. kwargs["result"]["url"]  (priority - previous workflow output)
# 2. kwargs["url"]             (fallback - initial input)

workflow = CallableWorkflow(fetch_data, args_transform="url=url")
```

Explicit paths use exact lookup only:
```python
# "url=result.url" only checks kwargs["result"]["url"]
workflow = CallableWorkflow(fetch_data, args_transform="url=result.url")
```

**Why this matters:**
- ✅ **Less verbose**: Write `url=url` instead of `url=result.url`
- ✅ **More forgiving**: Works whether parameter is in result or top-level
- ✅ **Prioritizes workflow outputs**: Result values take precedence over inputs
- ✅ **Explicit when needed**: Use dots for precise control

**Examples:**
```python
# Simple keys - auto-resolve from result first
CallableWorkflow(process, "url=url, query=query")
# → Tries result.url, result.query first, then top-level

# Mixed simple and explicit
CallableWorkflow(process, "url=url, nested=result.data.nested")
# → url checks result first, nested uses exact path

# Fallback chain respects priority
CallableWorkflow(process, "url=url|backup_url")
# → Tries result.url, then top.url, then result.backup_url, then top.backup_url
```

**Real-World Example:**
```python
# Helper function with custom logic
def format_final_result(content: str, metadata: dict) -> dict:
    from dana.lib.workflows.web_research import _format_resource
    formatted = _format_resource.format_with_metadata(content=content, metadata=metadata)
    return {"formatted_text": formatted}

# Use CallableWorkflow with args_transform to map parameters
workflow = (
    SearchWorkflow()
    | FetchWorkflow("url=result.results.0.url|url, purpose=query -> fetch_result")
    | CallableWorkflow(
        _extract_resource.extract_fact,
        args_transform="content=fetch_result.content_text, query=query"
    )
    | CallableWorkflow(
        format_final_result,
        args_transform="content=result.fact, metadata=fetch_result.metadata"
    )
)
```

**Understanding the Paths:**
- First CallableWorkflow: `fetch_result` is a top-level key (from `-> fetch_result`)
- Second CallableWorkflow: `result.fact` accesses the previous workflow's output; `fetch_result` is still at top-level
- Keys with `->` in args_transform are preserved at the top level for subsequent workflows

---

## Complete Refactoring Example

### Before: Wrapper Classes Everywhere

```python
class RankResultsWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _search_resource.rank_by_relevance(
            query=kwargs.get("query", ""),
            results=kwargs.get("results", []),
            criteria=kwargs.get("criteria", "relevance")
        )

class SelectTopUrlsWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        ranked_results = kwargs.get("ranked_results", [])
        max_sources = kwargs.get("max_sources", 5)
        urls = [r.get("url") for r in ranked_results[:max_sources] if r.get("url")]
        return {"urls": urls}

class FetchMultipleWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _fetch_resource.fetch_and_extract(
            urls=kwargs.get("urls", []),
            max_workers=kwargs.get("max_workers", 3)
        )

# Usage
workflow = (
    SearchWorkflow()
    | RankResultsWorkflow()
    | SelectTopUrlsWorkflow()
    | FetchMultipleWorkflow()
)
```

**Lines of code:** ~50 lines of wrapper classes

### After: Direct Methods + Lambdas

```python
# Helper only for actual transformation logic
def select_top_urls(ranked_results, max_sources=5):
    urls = [r.get("url") for r in ranked_results[:max_sources] if r.get("url")]
    return {"urls": urls}

# Usage - pass methods directly!
workflow = (
    SearchWorkflow()
    | _search_resource.rank_by_relevance  # Direct method!
    | select_top_urls  # Helper for transformation
    | _fetch_resource.fetch_and_extract  # Direct method!
)
```

**Lines of code:** ~5 lines total

**Reduction:** 90% less code! 🎉

---

## Decision Tree

```
Need to call a resource method or function?
│
├─ Do parameter names match? → YES → Use direct method
│  └─ workflow | _resource.method
│  Note: Simple keys auto-resolve from result first!
│
├─ Simple transformation? → YES → Use lambda
│  └─ workflow | (lambda x: transform(x))
│
├─ Complex mapping needed? → YES → Use CallableWorkflow with args_transform
│  └─ workflow | CallableWorkflow(_resource.method, args_transform="param=param")
│  Note: Use "param=param" for simple keys (checks result first),
│         or "param=result.nested.path" for explicit paths
│
└─ Complex mapping + reusable? → YES → Use workflow class with declarative
   └─ workflow | NextWorkflow("param=param|fallback")
```

---

## Real-World Examples

### Example 1: Search → Extract Answer

```python
# ❌ OLD WAY (28 lines)
class ExtractAnswerWorkflow(BaseWorkflow):
    def __init__(self, workflow_id: str | None = None, **kwargs):
        super().__init__(workflow_id=workflow_id or "extract-answer", **kwargs)

    def _do_execute(self, **kwargs) -> DictParams:
        return _extract_resource.extract_answer_from_search(
            results=kwargs.get("results", [])
        )

workflow = SearchWorkflow() | ExtractAnswerWorkflow()

# ✅ NEW WAY (1 line!)
workflow = SearchWorkflow() | _extract_resource.extract_answer_from_search
```

### Example 2: Data Pipeline with Transformation

```python
# Load → Filter → Transform → Save
workflow = (
    DataLoader()
    | (lambda data: [x for x in data if x['valid']])  # Filter
    | _processor.transform_data  # Direct method
    | (lambda transformed: {'output': transformed, 'count': len(transformed)})  # Add metadata
    | SaveWorkflow()
)
```

### Example 3: Multi-Source Research

```python
# ❌ OLD WAY: 3 wrapper classes (~80 lines)
# ✅ NEW WAY: Direct + helpers
workflow = (
    SearchWorkflow()
    | _search_resource.rank_by_relevance  # Direct method
    | select_top_urls  # Helper for URL extraction
    | _fetch_resource.fetch_and_extract  # Direct method
    | SynthesizeWorkflow()
)
```

---

## Advanced: CallableWorkflow with args_transform

The `CallableWorkflow` class now supports the `args_transform` parameter, allowing you to use declarative mapping with any callable. This eliminates the need for many wrapper workflow classes!

### When to Use

Use `CallableWorkflow` with `args_transform` when:
- Parameter names don't match between workflows
- You need to extract nested values (e.g., `result.data.items`)
- You want to combine multiple sources into parameters
- You need a one-off mapping without creating a workflow class

### Syntax Examples

```python
from dana.core.workflow import CallableWorkflow

# Simple parameter mapping
CallableWorkflow(
    my_function,
    args_transform="input=result.data"
)

# Multiple parameters
CallableWorkflow(
    process_data,
    args_transform="content=fetch_result.content_text, query=query"
)

# Nested extraction
CallableWorkflow(
    extract_url,
    args_transform="url=result.results.0.url"
)

# With fallback
CallableWorkflow(
    fetch_content,
    args_transform="url=result.primary_url|result.backup_url"
)

# With output name
CallableWorkflow(
    transform_data,
    args_transform="input=result.data -> transformed"
)
```

### Before/After Comparison

**❌ Before: Wrapper Class**
```python
class ExtractWithMappingWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _extract_resource.extract_fact(
            content=kwargs.get("fetch_result", {}).get("content_text", ""),
            query=kwargs.get("query", "")
        )

workflow = (
    SearchWorkflow()
    | FetchWorkflow()
    | ExtractWithMappingWorkflow()
)
```

**✅ After: CallableWorkflow with args_transform**
```python
workflow = (
    SearchWorkflow()
    | FetchWorkflow("url=result.results.0.url|url, purpose=query -> fetch_result")
    | CallableWorkflow(
        _extract_resource.extract_fact,
        args_transform="content=fetch_result.content_text, query=query"
    )
)
```

**Benefits:**
- 🎯 No workflow class needed
- 📉 ~90% less code
- 🔍 Clear parameter mapping
- 🧪 Works with any callable

---

## Guidelines

### ✅ DO

- Pass resource methods directly when parameter names match
- Use lambdas for simple, inline transformations
- Use helpers for reusable transformation logic
- Keep workflow classes for complex logic with validation
- Use declarative mapping for complex parameter extraction
- Use `CallableWorkflow` with `args_transform` for one-off parameter mappings

### ❌ DON'T

- Create wrapper workflow classes just to call a single method
- Create wrapper functions that just forward parameters unchanged
- Use complex lambdas that are hard to read (make them helpers instead)
- Use `args_transform` with `pre_callable`/`post_callable` (not allowed by design)

---

## Migration Strategy

1. **Identify simple wrappers:** Look for workflows that just call a single resource method
2. **Check parameter matching:** If parameters match, replace with direct method
3. **Extract transformations:** If there's transformation logic, use lambda or helper
4. **Keep complex workflows:** Workflows with validation, multiple steps, or business logic stay as classes

---

## Performance Notes

- **Direct methods:** Same performance as wrapper classes (no overhead)
- **Lambdas:** Slightly faster (less indirection than classes)
- **Signature inspection:** Done once per callable, cached internally
- **Memory:** Reduced memory footprint (fewer class instances)

---

## Summary

| Pattern | Use Case | Code Reduction | Example |
|---------|----------|----------------|---------|
| **Direct Method** | Parameters match | ~90% | `\| _resource.method` (auto-resolves from result) |
| **Lambda** | Simple transform | ~80% | `\| (lambda x: x * 2)` |
| **CallableWorkflow + args_transform** | Complex mapping (one-off) | ~85% | `\| CallableWorkflow(fn, "a=a")` (checks result first!) |
| **Declarative (Workflow)** | Complex mapping (reusable) | ~70% | `\| Workflow("a=a\|fallback")` (checks result first!) |

**Note:** Simple keys (no dots) automatically check `result` first, then top-level. Use explicit paths like `a=result.nested.path` when you need precise control.

The callable workflow feature, especially with `args_transform` support, enables you to write **dramatically simpler** workflow compositions while maintaining all the power and flexibility of the workflow system!
