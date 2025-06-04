<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
# Agents in OpenDXA

## Overview

Agents in OpenDXA are autonomous entities that can perceive their environment, make decisions, and take actions to achieve specific goals. They combine capabilities, resources, and Dana programs to perform complex tasks effectively. At their core, they leverage the Domain-Aware NeuroSymbolic Architecture (Dana) to integrate domain knowledge with LLM reasoning capabilities.

## Core Concepts

### 1. Agent Components
- Core System
  - Agent configuration
  - Dana runtime
  - State management
  - Resource coordination
- Capabilities
  - Memory
  - Domain Expertise
  - Learning
- Resources
  - LLMs
  - Knowledge bases
  - External tools
  - Services

### 2. Agent Operations
- Environment perception
- [State management](./state-management.md)
- Decision making with Dana
- Action execution
- Learning and adaptation

## Architecture

The OpenDXA agent architecture is organized around the Dana language as the central execution model:

1. **Agent Layer**
   - Agent configuration and instantiation
   - Capability and resource management
   - Runtime environment setup

2. **Dana Execution Layer**
   - Program parsing and interpretation
   - State management and access
   - Function registry and execution
   - Error handling and recovery

3. **Resource Layer**
   - LLM integration and communication
   - Tool access and orchestration
   - Knowledge base connectivity
   - External service integration

## Implementation

### 1. Basic Agent
```python
from opendxa.agent import Agent
from opendxa.agent.agent_config import AgentConfig
from opendxa.agent.capability.memory_capability import MemoryCapability

# Create agent with configuration
config = AgentConfig(
    id="research_agent",
    name="Research Assistant",
    description="Assists with research tasks"
)
agent = Agent(config)

# Add capability
memory = MemoryCapability()
agent.add_capability(memory)

# Initialize
await agent.initialize()
```

### 2. Resource Integration
```python
from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.resource.kb_resource import KBResource

# Add resources
llm_resource = LLMResource(
    name="agent_llm",
    config={"model": "gpt-4", "temperature": 0.7}
)
kb_resource = KBResource(
    name="knowledge_base",
    config={"source": "research_data.json"}
)

agent.add_resource(llm_resource)
agent.add_resource(kb_resource)
```

### 3. Dana Program Execution
```python
from opendxa.dana import run
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create initial state
context = SandboxContext(
    agent={"name": agent.config.name},
    world={"query": "latest AI research trends"},
    temp={}
)

# Define Dana program
dana_program = """
# Record the query
agent.current_query = world.query
log.info("Processing query: {world.query}")

# Search knowledge base
temp.search_params = {"query": world.query, "limit": 5}
temp.search_results = use_capability("kb", "search", temp.search_params)

# Analyze results
temp.analysis = reason("Analyze these research trends: {temp.search_results}")

# Generate response
agent.response = reason("Create a summary of the latest AI research trends based on this analysis: {temp.analysis}")

# Log completion
log.info("Query processing complete")
"""

# Execute program
result = agent.runtime.execute(dana_program, context)
```

## Key Differentiators

1. **Dana-Powered Decision Making**
   - Imperative programming model
   - Explicit state management
   - Direct integration with reasoning
   - Seamless LLM interactions

2. **Capability Integration**
   - Modular functionality
   - Domain expertise encapsulation
   - Function registration in Dana
   - Specialized operations

3. **Resource Orchestration**
   - Efficient resource management
   - State-aware resource access
   - Error handling and recovery
   - Dynamic resource selection

## Best Practices

1. **Agent Design**
   - Clear purpose and responsibilities
   - Appropriate capabilities
   - Efficient resource utilization
   - Proper state management

2. **Dana Program Design**
   - Modular program structure
   - Clear state organization
   - Proper error handling
   - Performance considerations

3. **Resource Management**
   - Proper configuration
   - Efficient resource sharing
   - Error recovery strategies
   - Resource cleanup

## Common Patterns

1. **Data Processing Agent**
   ```python
   # Dana program for data processing
   dana_program = """
   # Configure processing
   agent.processing_method = "sentiment_analysis"
   temp.data = world.input_data
   
   # Process each item
   temp.results = []
   for item in temp.data:
       temp.analysis = reason("Analyze sentiment in: {item}")
       temp.results.append(temp.analysis)
   
   # Summarize results
   agent.summary = reason("Summarize sentiment analysis results: {temp.results}")
   log.info("Processing complete with summary: {agent.summary}")
   """
   ```

2. **Decision Making Agent**
   ```python
   # Dana program for decision making
   dana_program = """
   # Gather information
   temp.situation = world.current_situation
   temp.options = world.available_options
   temp.criteria = world.decision_criteria
   
   # Analyze options
   temp.analyses = []
   for option in temp.options:
       temp.option_analysis = reason("Analyze option {option} according to criteria {temp.criteria} in situation {temp.situation}")
       temp.analyses.append(temp.option_analysis)
   
   # Make decision
   agent.decision = reason("Select the best option based on these analyses: {temp.analyses}")
   agent.justification = reason("Provide a justification for selecting {agent.decision}")
   
   # Log decision
   log.info("Decision made: {agent.decision} with justification: {agent.justification}")
   """
   ```

3. **Interactive Assistant Agent**
   ```python
   # Dana program for interactive assistance
   dana_program = """
   # Process user query
   temp.query = world.user_query
   temp.history = world.conversation_history
   
   # Generate response
   temp.context_analysis = reason("Analyze this conversation context: {temp.history}")
   agent.response = reason("Generate a helpful response to '{temp.query}' considering this context: {temp.context_analysis}")
   
   # Update memory
   temp.memory_params = {
       "key": "conversation_" + current_time(),
       "value": {
           "query": temp.query,
           "response": agent.response,
           "context": temp.context_analysis
       }
   }
   use_capability("memory", "store", temp.memory_params)
   
   # Log interaction
   log.info("Responded to user query: {temp.query}")
   """
   ```

## Application Examples

1. **Research Assistant Agent**
   - Literature search and analysis
   - Information synthesis
   - Summary generation
   - Knowledge management

2. **Process Automation Agent**
   - Task execution and monitoring
   - Resource management
   - Exception handling
   - Progress reporting

3. **Customer Support Agent**
   - Query understanding
   - Knowledge retrieval
   - Response generation
   - Issue escalation

## Next Steps

- Learn about [Capabilities](./capabilities.md)
- Understand [Resources](./resources.md)
- Explore [Dana Language](../dana/language.md)

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>