<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)

# State Management

This document describes how OpenDXA manages state across different components of the system.

*Note: For conversation history and LLM interaction context, see [Conversation Context Management](../core-concepts/conversation-context.md).*

## Overview

OpenDXA's state management system is designed to handle different types of variables through blackboards. The main containers are:
- `execution:` - Execution progress and control (via ExecutionState)
- `world:` - Environment and tool state (via WorldState)
- `agent:` - Agent-specific state (via AgentState)
- `plan:` - Direct access to plan object (special container)

*Note: Unlike other containers that access state objects, the `plan:` container provides direct access to the plan object and its properties. This allows for efficient plan manipulation and querying without intermediate state storage.*

The top use cases for state management in agentic systems are:

1. **Execution Control and Progress Tracking** ⭐⭐⭐⭐⭐
   - Current step/phase in execution
   - Task completion status
   - Intermediate results
   - Progress metrics
   - Task dependencies
   
   *Example:*
   ```python
   # Track progress through a multi-step task
   execution_context.set("execution:current.step", "data_processing")
   execution_context.set("execution:progress.items.processed", 42)
   execution_context.set("execution:progress.items.total", 100)

   # Check progress and make decisions
   current_step = execution_context.get("execution:current.step")
   processed = execution_context.get("execution:progress.items.processed")
   total = execution_context.get("execution:progress.items.total")
   if processed >= total:
       execution_context.set("execution:current.step", "complete")
   ```

2. **Plan State Management** ⭐⭐⭐⭐⭐
   - Current plan node
   - Plan execution status
   - Plan modifications
   - Node dependencies
   
   *Example:*
   ```python
   # Direct plan object access (no intermediate state storage)
   execution_context.set("plan:current.node", "process_data")  # Updates plan object directly
   execution_context.set("plan:nodes.process_data.status", "in_progress")  # Modifies node in plan
   execution_context.set("plan:nodes.process_data.dependencies", ["fetch_data", "validate_input"])

   # Get LLM's analysis of plan progress
   llm_resource = LLMResource()
   llm_response = llm_resource.query(
       f"Analyze plan progress. Current node: {execution_context.get('plan:current.node')}, "
       f"Status: {execution_context.get('plan:nodes.process_data.status')}"
   )
   execution_context.set("plan:analysis.last_llm", llm_response)

   # Direct plan queries
   current_node = execution_context.get("plan:current.node")  # Reads from plan object
   dependencies = execution_context.get(f"plan:nodes.{current_node}.dependencies")  # Queries plan structure
   for dep in dependencies:
       dep_status = execution_context.get(f"plan:nodes.{dep}.status")  # Reads node status from plan
       if dep_status != "complete":
           execution_context.set("plan:current.node", dep)  # Updates plan directly
           break
   ```

3. **Environment and Tool State Management** ⭐⭐⭐⭐⭐
   - Tool configurations
   - Connection states
   - Authentication tokens
   - Session data
   - External system states
   
   *Example:*
   ```python
   # Manage tool authentication and session
   execution_context.set("world:api.auth.token", "xyz123")
   execution_context.set("world:api.last_request.time", "2024-03-20T10:00:00")
   execution_context.set("world:api.rate_limit.remaining", 95)

   # Check rate limits before making API calls
   remaining = execution_context.get("world:api.rate_limit.remaining")
   if remaining <= 0:
       next_time = execution_context.get("world:api.rate_limit.reset_time")
       raise RateLimitError(f"Rate limit exceeded. Try again at {next_time}")
   ```

4. **Decision Context and Reasoning State** ⭐⭐⭐⭐
   - Template placeholders and substitutions
   - LLM output parsing rules
   - Decision criteria and context
   - Reasoning chains and justifications
   - Validation results
   
   *Example:*
   ```python
   # Store decision context and LLM interaction state
   execution_context.set("agent:decision.criteria", ["cost", "speed", "reliability"])
   execution_context.set("agent:decision.current.priority", "cost")
   execution_context.set("agent:validation.status", True)

   # Get LLM's decision analysis
   llm_resource = LLMResource()
   criteria = execution_context.get("agent:decision.criteria")
   priority = execution_context.get("agent:decision.current.priority")
   llm_response = llm_resource.query(
       f"Analyze decision criteria: {criteria} with priority: {priority}. "
       "Suggest any adjustments needed."
   )
   execution_context.set("agent:decision.llm_analysis", llm_response)

   # Use decision context for making choices
   if priority in criteria:
       criteria.remove(priority)
       criteria.insert(0, priority)
       execution_context.set("agent:decision.criteria", criteria)
   ```

5. **Error Recovery and Resilience** ⭐⭐⭐⭐
   - Error states and recovery points
   - Retry counts and backoff states
   - Fallback options
   - Error handling strategies
   - System resilience data
   
   *Example:*
   ```python
   # Track error state and recovery attempts
   execution_context.set("execution:error.last.type", "connection_timeout")
   execution_context.set("execution:error.retry.count", 2)
   execution_context.set("execution:error.retry.next_time", "2024-03-20T10:05:00")

   # Get LLM's error analysis and recovery suggestion
   llm_resource = LLMResource()
   error_type = execution_context.get("execution:error.last.type")
   retry_count = execution_context.get("execution:error.retry.count")
   llm_response = llm_resource.query(
       f"Error type: {error_type}, Retry count: {retry_count}. "
       "Suggest recovery strategy and next steps."
   )
   execution_context.set("execution:error.llm_recovery_plan", llm_response)

   # Implement retry logic
   max_retries = execution_context.get("execution:error.retry.max", 3)
   if retry_count >= max_retries:
       raise MaxRetriesExceeded("Maximum retry attempts reached")
   next_time = execution_context.get("execution:error.retry.next_time")
   if datetime.now() < next_time:
       raise RetryNotReady(f"Next retry at {next_time}")
   ```

*Note: Conversation history and LLM interaction context are managed at the Executor (Planner/Reasoner) layer, not within the state management system described here.*

## Additional Information

For more details on state management, please refer to the [State Management](../core-concepts/state-management.md) section in the documentation.
