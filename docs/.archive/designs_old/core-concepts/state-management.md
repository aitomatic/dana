<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
# State Management

This document describes how OpenDXA manages state across different components of the system using Dana's state scopes.

*Note: For conversation history and LLM interaction context, see [Conversation Context Management](../core-concepts/conversation-context.md).*

## Overview

OpenDXA's state management system is designed to handle different types of variables through specific state scopes. The main state containers are:

- `agent.` - Agent-specific state (via AgentState)
- `world.` - Environment and tool state (via WorldState)
- `temp.` - Temporary computation state (via TempState)

Each scope provides separation and organization for different types of variables in Dana programs.

The top use cases for state management in agentic systems are:

1. **Execution Control and Progress Tracking** ⭐⭐⭐⭐⭐
   - Current step/phase in execution
   - Task completion status
   - Intermediate results
   - Progress metrics
   - Task dependencies

   *Example (Dana):*
   ```python
   # Track progress through a multi-step task
   agent.current_step = "data_processing"
   agent.progress_items_processed = 42
   agent.progress_items_total = 100

   # Check progress and make decisions
   if agent.progress_items_processed >= agent.progress_items_total:
       agent.current_step = "complete"
   ```

2. **Environment and Tool State Management** ⭐⭐⭐⭐⭐
   - Tool configurations
   - Connection states
   - Authentication tokens
   - Session data
   - External system states

   *Example (Dana):*
   ```python
   # Manage tool authentication and session
   world.api_auth_token = "xyz123"
   world.api_last_request_time = "2024-03-20T10:00:00"
   world.api_rate_limit_remaining = 95

   # Check rate limits before making API calls
   if world.api_rate_limit_remaining <= 0:
       log.error("Rate limit exceeded. Try again at {world.api_rate_limit_reset_time}")
   else:
       temp.api_response = call_api(world.api_endpoint, world.api_auth_token)
   ```

3. **Decision Context and Reasoning State** ⭐⭐⭐⭐
   - Template placeholders and substitutions
   - LLM output parsing rules
   - Decision criteria and context
   - Reasoning chains and justifications
   - Validation results

   *Example (Dana):*
   ```python
   # Store decision context and LLM interaction state
   agent.decision_criteria = ["cost", "speed", "reliability"]
   agent.decision_current_priority = "cost"
   agent.validation_status = True

   # Get LLM's decision analysis
   temp.llm_response = reason("Analyze decision criteria: {agent.decision_criteria} 
                               with priority: {agent.decision_current_priority}. 
                               Suggest any adjustments needed.")
   agent.decision_llm_analysis = temp.llm_response

   # Use decision context for making choices
   if agent.decision_current_priority in agent.decision_criteria:
       # Update priority in criteria list
       temp.criteria = agent.decision_criteria
       temp.criteria.remove(agent.decision_current_priority)
       temp.criteria.insert(0, agent.decision_current_priority)
       agent.decision_criteria = temp.criteria
   ```

4. **Error Recovery and Resilience** ⭐⭐⭐⭐
   - Error states and recovery points
   - Retry counts and backoff states
   - Fallback options
   - Error handling strategies
   - System resilience data

   *Example (Dana):*
   ```python
   # Track error state and recovery attempts
   agent.error_last_type = "connection_timeout"
   agent.error_retry_count = 2
   agent.error_retry_next_time = "2024-03-20T10:05:00"

   # Get LLM's error analysis and recovery suggestion
   temp.llm_response = reason("Error type: {agent.error_last_type}, 
                               Retry count: {agent.error_retry_count}. 
                               Suggest recovery strategy and next steps.")
   agent.error_llm_recovery_plan = temp.llm_response

   # Implement retry logic
   agent.error_retry_max = agent.error_retry_max if hasattr(agent, "error_retry_max") else 3
   if agent.error_retry_count >= agent.error_retry_max:
       log.error("Maximum retry attempts reached")
   elif current_time() < agent.error_retry_next_time:
       log.info("Next retry at {agent.error_retry_next_time}")
   else:
       # Attempt retry
       agent.error_retry_count += 1
       temp.retry_result = retry_operation()
   ```

5. **Temporary Computation State** ⭐⭐⭐⭐
   - Intermediate calculation results
   - Temporary variables
   - Processing buffers
   - Local function state
   - Short-lived data

   *Example (Dana):*
   ```python
   # Use temp scope for intermediate calculations
   temp.data = world.input_data
   temp.processed_items = []
   
   # Process each item
   for item in temp.data:
       temp.current_item = item
       temp.analysis_result = reason("Analyze this item: {temp.current_item}")
       temp.processed_items.append(temp.analysis_result)
   
   # Store final results in agent state
   agent.processed_results = temp.processed_items
   agent.analysis_complete = True
   ```

*Note: Conversation history and LLM interaction context are managed separately through the LLMResource, not within the state management system described here.*

## SandboxContext API

The SandboxContext class provides an API for interacting with Dana state containers programmatically:

```python
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create context with initial state
context = SandboxContext(
    agent={"name": "analyst", "objective": "Process data"},
    world={"data_source": "customer_feedback.csv"},
    temp={}
)

# Access state programmatically 
agent_name = context.get("agent.name")
context.set("temp.processing_started", True)

# Execute Dana program with context
from opendxa.dana import run

dana_program = """
# Access existing state
log.info("Processing data for agent: {agent.name}")
log.info("Data source: {world.data_source}")

# Create new state
temp.results = []
agent.status = "processing"
"""

run(dana_program, context)
```

## Best Practices

1. **State Organization**
   - Use `agent.` for persistent agent-specific state
   - Use `world.` for environment and external system state
   - Use `temp.` for intermediate calculations and temporary data
   - Follow consistent naming conventions

2. **State Access Patterns**
   - Access state directly via dot notation in Dana
   - Use clear, descriptive variable names
   - Validate state before use with conditional checks
   - Use default values or hasattr for optional state

3. **State Updates**
   - Use explicit assignments for state updates
   - Maintain proper scoping for state variables
   - Consider state persistence when needed
   - Clean up temporary state when no longer needed

## Additional Information

For more details on Dana state management, please refer to the [Dana Language](../dana/language.md) documentation.