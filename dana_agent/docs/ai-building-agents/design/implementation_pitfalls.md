# Implementation Pitfalls and Fixes

## Overview

This document catalogs common implementation errors encountered when building Dana agents, workflows, and resources. Each pitfall includes the error, the root cause, the fix, and updated best practices.

**Source**: Lessons learned from Vietnam Coffee Research Agent implementation (October 2025)

---

## Import Errors

### Pitfall 1: Validation Decorators from Wrong Module

**Error**:
```python
ImportError: cannot import name 'validate_input' from 'dana.core.workflow.base_workflow'
```

**What We Tried** (❌ Wrong):
```python
from dana.core.workflow.base_workflow import BaseWorkflow, validate_input, validate_output
```

**Root Cause**:
- Validation decorators are in a separate module
- Common assumption: all workflow-related imports come from `base_workflow`

**Fix** (✅ Correct):
```python
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output

class MyWorkflow(BaseWorkflow):
    @validate_input(
        query={"required": True, "type": str, "min_length": 1}
    )
    @validate_output(
        success={"required": True, "type": bool}
    )
    def _do_execute(self, **kwargs):
        # Implementation
        pass
```

**Prevention**:
- ✅ Always import validation decorators from `dana.core.workflow.validation`
- ✅ Use validation decorators on ALL workflows for contract clarity
- ✅ IDE autocomplete may mislead; verify imports in documentation

**Documentation Impact**:
- workflow_design_patterns.md already shows correct import (Pattern 8, line 438)
- ✅ No update needed, but emphasize in quickstart guides

---

### Pitfall 2: Relative Import Failures

**Error**:
```python
ImportError: attempted relative import beyond top-level package
```

**What We Tried** (❌ Wrong):
```python
# In workflows/company_enrichment.py
from ..resources.company_data_structuring import CompanyDataStructuringResource
from ..resources.source_provenance import SourceProvenanceResource
```

**Root Cause**:
- Python relative imports require proper package structure
- Use-case implementations are documentation, not installed packages
- Package hierarchy not configured with `__init__.py` files

**Fix** (✅ Correct):
```python
# Use direct imports instead
from resources.company_data_structuring import CompanyDataStructuringResource
from resources.source_provenance import SourceProvenanceResource
```

**Alternative Fix** (for production packages):
```python
# If properly packaged with __init__.py files:
from vietnam_coffee.resources.company_data_structuring import CompanyDataStructuringResource
```

**Prevention**:
- ✅ For use-case examples: Use direct imports from top-level modules
- ✅ For production packages: Ensure proper `__init__.py` structure
- ✅ Document import patterns in project README

**Best Practice**:
```
# Project structure for use-case examples:
vietnam_coffee/
├── agents/
│   └── vietnam_coffee_research.py  # from resources.X import Y
├── workflows/
│   └── discovery.py                 # from resources.X import Y
├── resources/
│   └── normalization.py
└── examples/
    └── run.py                       # sys.path manipulation if needed
```

---

## API Misunderstandings

### Pitfall 3: Non-Existent execute_workflow() Method

**Error**:
```python
AttributeError: 'VietnamCoffeeResearchAgent' object has no attribute 'execute_workflow'
```

**What We Tried** (❌ Wrong):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def research_companies(self, provinces: list[str], **kwargs):
        # Assuming there's an execute_workflow() method
        result = self.execute_workflow(
            "orchestrate-batches",
            provinces=provinces,
            batch_size=batch_size
        )
        return result
```

**Root Cause**:
- No `execute_workflow()` convenience method exists on STARAgent
- Confusion from agent composition pattern (`with_workflows()`)
- Assumption: "If I compose workflows, there must be a method to execute them"

**Fix** (✅ Correct):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def research_companies(self, provinces: list[str], **kwargs):
        # Directly instantiate and execute the workflow
        from workflows.batch_orchestration import BatchOrchestrationWorkflow

        workflow = BatchOrchestrationWorkflow()
        result = workflow.execute(
            provinces=provinces,
            batch_size=batch_size
        )
        return result.get("result", {})
```

**When to Use Each Approach**:

| Scenario | Approach | Example |
|----------|----------|---------|
| **Agent provides convenience method** | Direct workflow instantiation | `agent.research_companies()` calls workflow |
| **LLM chooses workflow dynamically** | Use `with_workflows()` composition | Agent prompt guides LLM to select workflow |
| **Testing individual workflows** | Direct instantiation | `workflow = SearchWorkflow(); workflow.execute(...)` |

**Prevention**:
- ✅ Workflows composed with `with_workflows()` are for LLM tool selection
- ✅ For programmatic/convenience methods, directly instantiate workflows
- ✅ Don't assume methods exist; check STARAgent API docs

---

### Pitfall 4: Non-Existent get_resource() Method

**Error**:
```python
AttributeError: 'VietnamCoffeeResearchAgent' object has no attribute 'get_resource'
```

**What We Tried** (❌ Wrong):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def get_quality_report(self, company_ids=None):
        # Assuming we can retrieve composed resources
        provenance_resource = self.get_resource("source-tracking")
        return provenance_resource.batch_quality_report(company_ids=company_ids)
```

**Root Cause**:
- Similar to Pitfall 3: no `get_resource()` method exists
- Resources composed via `with_resources()` are for LLM tool use
- Not designed for programmatic access within agent methods

**Fix** (✅ Correct):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def get_quality_report(self, company_ids=None):
        # Directly instantiate the resource
        from resources.source_provenance import SourceProvenanceResource

        provenance_resource = SourceProvenanceResource()
        return provenance_resource.batch_quality_report(company_ids=company_ids)
```

**Alternative Pattern** (for stateful resources):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="...", **kwargs)

        # Store reference if resource maintains state
        from resources.source_provenance import SourceProvenanceResource
        self._provenance = SourceProvenanceResource()

        self.with_resources(
            self._provenance,  # Compose for LLM tool use
            # ... other resources
        )

    def get_quality_report(self, company_ids=None):
        # Use stored reference
        return self._provenance.batch_quality_report(company_ids=company_ids)
```

**Prevention**:
- ✅ `with_resources()` is for LLM tool composition, not programmatic access
- ✅ For convenience methods, instantiate resources directly
- ✅ For stateful resources, store as instance attributes

---

## Result Structure Errors

### Pitfall 5: Workflow Result Unwrapping

**Error**:
```python
# No Python error, but logic error:
# result["success"] always False because accessing wrong level
```

**What We Tried** (❌ Wrong):
```python
class BatchOrchestrationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Execute discovery workflow
        discovery_result = self.discovery_workflow.execute(province=province)

        # Access result directly - WRONG!
        if discovery_result["success"]:
            companies = discovery_result["companies"]
```

**Root Cause**:
- `workflow.execute()` wraps return value in `{"result": {...}}`
- BaseWorkflow automatically wraps `_do_execute()` return value
- Easy to forget unwrapping when composing workflows

**Actual Structure**:
```python
{
    "result": {
        "success": True,
        "companies": [...],
        "total_found": 10
    }
}
```

**Fix** (✅ Correct):
```python
class BatchOrchestrationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Execute discovery workflow
        discovery_result = self.discovery_workflow.execute(province=province)

        # UNWRAP the nested result
        inner_result = discovery_result.get("result", {})

        # Now access the actual result
        if inner_result.get("success"):
            companies = inner_result.get("companies", [])
            all_discovered.extend(companies)
```

**Pattern for Multi-Level Workflow Composition**:
```python
# Level 1: Leaf workflow (no wrapping needed)
class DiscoveryWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return {
            "success": True,
            "companies": [...]
        }

# Level 2: Orchestrator workflow (MUST unwrap)
class BatchOrchestrationWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        result = DiscoveryWorkflow().execute(...)

        # ❌ WRONG: result["success"]
        # ✅ CORRECT: result.get("result", {}).get("success")
        inner = result.get("result", {})
        if inner.get("success"):
            # Process inner["companies"]
            pass

# Level 3: Agent convenience method (MUST unwrap again!)
class MyAgent(STARAgent):
    def my_method(self):
        result = BatchOrchestrationWorkflow().execute(...)
        # Unwrap once more
        return result.get("result", {})
```

**Prevention**:
- ✅ Always unwrap when calling `workflow.execute()` from another workflow
- ✅ Use `.get("result", {})` for safe access
- ✅ Return unwrapped results from agent convenience methods
- ✅ Consider helper function for clarity:
  ```python
  def unwrap_workflow_result(result: dict) -> dict:
      """Unwrap the nested result from workflow.execute()."""
      return result.get("result", {})
  ```

**Why This Happens**:
- BaseWorkflow.execute() wraps `_do_execute()` return in `{"result": ...}`
- This enables middleware, logging, error tracking
- But creates mental overhead when composing workflows

---

## Component Instantiation Patterns

### Pitfall 6: Module-Level vs Instance-Level Resource Instantiation

**Question**: When should resources be instantiated at module level vs instance level?

**Pattern 1: Module-Level (Stateless Resources)**

**Use when**:
- Resource has no state
- Multiple workflows use same resource
- Want to share single instance for performance

**Example** (✅ Correct):
```python
# workflows/company_discovery.py
from dana.lib.resources.web_research.search import SearchResource
from dana.lib.resources.web_research.fetch import FetchResource

# Module-level instantiation
_search_resource = SearchResource()
_fetch_resource = FetchResource()

class CompanyDiscoveryWorkflow(BaseWorkflow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use module-level instances
        self.search_resource = _search_resource
        self.fetch_resource = _fetch_resource
```

**Pattern 2: Instance-Level (Stateful Resources)**

**Use when**:
- Resource maintains state (e.g., database connections, caches)
- Each workflow instance needs isolated state
- Resource configured differently per workflow

**Example** (✅ Correct):
```python
class CompanyEnrichmentWorkflow(BaseWorkflow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Instance-level: each workflow has its own provenance tracker
        from resources.source_provenance import SourceProvenanceResource
        self.provenance = SourceProvenanceResource()
```

**Pattern 3: Direct Instantiation (One-Time Use)**

**Use when**:
- Resource used only once in method
- No need to store reference
- Emphasizes local scope

**Example** (✅ Correct):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def get_quality_report(self, company_ids=None):
        # Direct instantiation for one-time use
        from resources.source_provenance import SourceProvenanceResource
        provenance = SourceProvenanceResource()
        return provenance.batch_quality_report(company_ids=company_ids)
```

**Decision Tree**:
```
Is resource stateless?
├─ Yes: Module-level instantiation
│  └─ Shared across workflows in same file
└─ No: Instance-level or direct instantiation
   ├─ Used multiple times in workflow? → Instance-level (self.resource)
   └─ Used once? → Direct instantiation in method
```

---

### Pitfall 7: Workflow Instantiation in Agent Composition

**Question**: When composing workflows with `with_workflows()`, should I instantiate once or per-use?

**Pattern 1: Agent Composition (for LLM tool use)**

**Use when**:
- Agent prompt guides LLM to select workflows
- Workflows appear as tools to LLM
- Multiple workflows available

**Example** (✅ Correct):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="vietnam-coffee-research", **kwargs)

        # Import at method level to avoid circular imports
        from workflows.company_discovery import CompanyDiscoveryWorkflow
        from workflows.company_enrichment import CompanyEnrichmentWorkflow

        # Compose workflows - instantiated ONCE
        self.with_workflows(
            CompanyDiscoveryWorkflow(workflow_id="discover-companies"),
            CompanyEnrichmentWorkflow(workflow_id="enrich-company"),
        )
```

**Pattern 2: Direct Execution (for programmatic use)**

**Use when**:
- Agent provides convenience method
- Workflow selected programmatically (not by LLM)
- Single-use execution

**Example** (✅ Correct):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def research_companies(self, provinces: list[str], **kwargs):
        # Import locally to avoid loading overhead if method not called
        from workflows.batch_orchestration import BatchOrchestrationWorkflow

        # Instantiate per-use - workflow is stateless
        workflow = BatchOrchestrationWorkflow()
        result = workflow.execute(provinces=provinces, **kwargs)
        return result.get("result", {})
```

**When to Use Each**:
- **Agent composition**: Workflows are tools for LLM-guided execution
- **Direct instantiation**: Workflows are functions for programmatic execution

---

## Import Organization Best Practices

### Pattern: Local Imports for Workflows/Resources

**Recommended** (✅):
```python
class VietnamCoffeeResearchAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="vietnam-coffee-research", **kwargs)

        # Import components locally to avoid circular dependencies
        from resources.company_data_structuring import CompanyDataStructuringResource
        from workflows.batch_orchestration import BatchOrchestrationWorkflow

        self.with_resources(
            CompanyDataStructuringResource(resource_id="company-structure"),
        )

        self.with_workflows(
            BatchOrchestrationWorkflow(workflow_id="orchestrate-batches"),
        )
```

**Why**:
- Avoids circular import issues
- Lazy loading (imports only when agent instantiated)
- Clear component boundaries

**Alternative** (for simple cases):
```python
# Top-level imports if no circular dependencies
from resources.my_resource import MyResource
from workflows.my_workflow import MyWorkflow

class MyAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="my-agent", **kwargs)
        self.with_resources(MyResource())
        self.with_workflows(MyWorkflow())
```

---

## Testing Patterns

### Pattern: Test Workflows Independently First

**Recommended Flow**:
1. ✅ Test resources independently
2. ✅ Test workflows independently
3. ✅ Test agent composition

**Example**:
```python
# Step 1: Test resource
def test_resource():
    resource = MyResource()
    result = resource.my_method(input="test")
    assert result["success"] is True

# Step 2: Test workflow (with resource)
def test_workflow():
    workflow = MyWorkflow()
    result = workflow.execute(input="test")

    # Remember to unwrap!
    inner = result.get("result", {})
    assert inner["success"] is True

# Step 3: Test agent
def test_agent():
    agent = MyAgent()
    result = agent.my_convenience_method(input="test")
    assert result["success"] is True
```

**Benefits**:
- Isolate errors quickly
- Clear failure points
- Easier debugging

---

## Quick Reference Checklist

When implementing a new agent system:

### Imports
- [ ] Import `validate_input`/`validate_output` from `dana.core.workflow.validation`
- [ ] Use direct imports for use-case examples (not relative imports)
- [ ] Import workflows/resources locally in `__init__` to avoid circular deps

### Workflow Composition
- [ ] Use `with_workflows()` for LLM tool composition
- [ ] Use direct instantiation for programmatic execution
- [ ] Always unwrap nested results when calling `workflow.execute()` from another workflow

### Resource Management
- [ ] Module-level for stateless, shared resources
- [ ] Instance-level for stateful resources
- [ ] Direct instantiation for one-time use

### Agent Methods
- [ ] No `execute_workflow()` method exists - instantiate directly
- [ ] No `get_resource()` method exists - instantiate directly or store reference
- [ ] Return unwrapped results from convenience methods

### Testing
- [ ] Test resources → workflows → agent (bottom-up)
- [ ] Remember result unwrapping in tests
- [ ] Verify imports work before testing logic

---

## Documentation Updates Needed

Based on these pitfalls, the following documentation should be enhanced:

1. **agent_team_design_guide.md** (Phase 5: Implementation):
   - Add "Common Implementation Pitfalls" section
   - Reference this document
   - Add import checklist

2. **workflow_design_patterns.md**:
   - ✅ Already covers validation import correctly (Pattern 8)
   - Add explicit note about result unwrapping in Pattern 5-7
   - Add workflow composition result handling example

3. **agent_design_patterns.md**:
   - ✅ Already covers composition patterns well
   - Add note: "`with_workflows()` is for LLM tools, not programmatic access"
   - Add convenience method pattern

4. **New: quickstart_implementation_guide.md**:
   - Step-by-step implementation with all correct imports
   - Common pitfalls inline with code examples
   - Testing strategy

---

## Summary

**Top 5 Mistakes to Avoid**:
1. ❌ Importing validation decorators from `base_workflow`
2. ❌ Using relative imports in use-case examples
3. ❌ Assuming `execute_workflow()` and `get_resource()` methods exist
4. ❌ Forgetting to unwrap `workflow.execute()` results
5. ❌ Mixing up composition patterns (LLM tools vs programmatic use)

**Top 5 Best Practices**:
1. ✅ Import `validate_input`/`validate_output` from `dana.core.workflow.validation`
2. ✅ Use direct imports in use-case examples
3. ✅ Directly instantiate workflows/resources for programmatic use
4. ✅ Always unwrap: `result.get("result", {})` when composing workflows
5. ✅ Test bottom-up: resources → workflows → agent

**When In Doubt**:
- Check existing working examples in `dana/lib/`
- Test components independently before composition
- Use direct instantiation for programmatic access
- Use composition (`with_*`) for LLM tool access
