<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
# OpenDXA Architecture

## Overview

OpenDXA is built on a modular, extensible architecture that enables the creation and deployment of autonomous agents. The system is designed to be flexible, scalable, and maintainable, with clear separation of concerns and well-defined interfaces between components. At its core, OpenDXA leverages Dana, a Domain-Aware NeuroSymbolic Architecture language, for agent reasoning and execution.

## Core Components

| Descriptive Components | Executive Components |
|----------------------|---------------------|
| **Agent**<br>- Autonomous entity<br>- Capability integration<br>- Resource management | **AgentRuntime**<br>- Dana program execution<br>- RuntimeContext management<br>- Resource coordination |
| **Knowledge**<br>- Information storage<br>- Data persistence<br>- Context sharing<br>- CORRAL lifecycle | **RuntimeContext**<br>- State management<br>- Execution tracking<br>- State container coordination |
| **Capabilities**<br>- Core functionalities<br>- Extensible modules<br>- Shared services | **Dana Interpreter**<br>- Program execution<br>- Function management<br>- State updates |
| **Resources**<br>- Tools and utilities<br>- Knowledge bases<br>- External services | **Dana Parser**<br>- Grammar-based parsing<br>- AST generation<br>- Type checking |
| **State**<br>- Agent state<br>- World state<br>- Temp state | **LLMResource**<br>- LLM communication<br>- Model configuration<br>- Response handling |

### CORRAL: Domain Knowledge Lifecycle

OpenDXA's key differentiator is its emphasis on domain knowledge management through the CORRAL lifecycle:

1. **COLLECT**
   - Knowledge acquisition from various sources
   - Initial processing and validation
   - Integration with existing knowledge base

2. **ORGANIZE**
   - Structured storage and categorization
   - Relationship mapping and context linking
   - Metadata management and tagging

3. **RETRIEVE**
   - Context-aware knowledge access
   - Semantic search and relevance ranking
   - Dynamic query optimization

4. **REASON**
   - Inference and contextual reasoning
   - Pattern recognition and hypothesis generation
   - Decision support

5. **ACT**
   - Action planning and execution
   - Applying knowledge to real-world tasks
   - Feedback collection from actions

6. **LEARN**
   - Feedback integration
   - Knowledge refinement
   - Continuous improvement

This lifecycle is implemented through the interaction of various components:
- Knowledge Base for storage and retrieval
- LLMResource for processing and understanding
- Capabilities for specialized knowledge operations
- RuntimeContext for application context
- State for tracking knowledge evolution

## System Architecture

The OpenDXA architecture is organized into layers, with Dana serving as the central execution model:

1. **Application Layer**
   - User Interface components
   - API Gateway for external communication

2. **Agent Layer**
   - Agent configuration and management
   - Capability integration
   - Resource management

3. **Dana Execution Layer**
   - Parser for code interpretation
   - Interpreter for program execution
   - Runtime Context for state management

4. **Resource Layer**
   - LLM integration
   - Knowledge base access
   - External tools and services

## Component Interactions

### 1. Request Flow
1. User request received through API
2. Agent instance created/selected
3. Dana program composed for the task
4. RuntimeContext initialized with state containers
5. Dana Interpreter executes the program
6. LLMResource handles LLM communication
7. Results returned through API

### 2. Agent Initialization
```python
from opendxa.agent import Agent
from opendxa.agent.agent_config import AgentConfig
from opendxa.common.resource import LLMResource

# Create agent with configuration
agent = Agent(name="researcher")
agent_config = AgentConfig(
    model="gpt-4",
    max_tokens=2000,
    temperature=0.7
)

# Configure LLM resource
llm_resource = LLMResource(
    name="agent_llm",
    config={"model": "gpt-4"}
)

# Initialize agent with LLM and capabilities
agent = agent.with_llm(llm_resource)
agent = agent.with_capabilities({
    "memory": MemoryCapability(),
    "domain_expertise": DomainExpertiseCapability()
})
```

### 3. Dana Program Execution
```python
from opendxa.dana import run
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Create sandbox context with state
context = SandboxContext(
    agent={},
    world={},
    temp={}
)

# Define Dana program
dana_program = """
# Set initial state
agent.objective = "Analyze customer feedback"
temp.feedback_data = world.customer_feedback

# Process data
temp.sentiment = reason("Analyze the sentiment in {temp.feedback_data}")
temp.key_issues = reason("Identify key issues in {temp.feedback_data}")

# Generate response
agent.response = reason("Create a summary of sentiment analysis: {temp.sentiment} and key issues: {temp.key_issues}")

# Log results
log.info("Analysis complete. Response: {agent.response}")
"""

# Execute Dana program
result = run(dana_program, context)
```

## Implementation Details

### 1. Agent Runtime
```python
from opendxa.agent.agent_runtime import AgentRuntime
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# AgentRuntime manages Dana program execution with SandboxContext
runtime = AgentRuntime(agent)

# Create and use SandboxContext
context = SandboxContext(
    agent=agent.state,
    world={},
    temp={}
)

# Execute Dana program with context
result = runtime.execute(dana_program, context)
```

### 2. State Management
```python
from opendxa.dana.sandbox.sandbox_context import SandboxContext

# Initialize state containers
context = SandboxContext(
    agent={
        "name": "research_agent",
        "objective": "Analyze data"
    },
    world={
        "data_source": "customer_feedback_db",
        "customer_feedback": [...] 
    },
    temp={}
)

# Access state
objective = context.get("agent.objective")
context.set("temp.analysis_result", analysis_result)
```

### 3. LLM Communication
```python
from opendxa.common.resource import LLMResource

# Create and configure LLM resource
llm_resource = LLMResource(
    name="agent_llm",
    config={
        "model": "gpt-4",
        "max_tokens": 2000,
        "temperature": 0.7
    }
)

# Use LLM resource
response = await llm_resource.query(prompt)
```

## Best Practices

1. **Agent Configuration**
   - Use AgentConfig for consistent settings
   - Configure LLMResource appropriately
   - Manage capabilities efficiently

2. **Dana Program Design**
   - Create clear, modular programs
   - Use proper state scopes (agent, world, temp)
   - Leverage built-in functions like reason() and log()
   - Handle errors gracefully

3. **State Management**
   - Maintain consistent state through SandboxContext
   - Use appropriate state containers
   - Follow proper naming conventions for state variables

## Common Patterns

1. **Agent Creation**
   ```python
   # Create and configure agent
   agent = Agent(name="task_agent")
   agent = agent.with_llm(LLMResource(config))
   agent = agent.with_capabilities(capabilities)
   ```

2. **Dana Program Execution**
   ```python
   # Create context and execute Dana program
   context = SandboxContext(agent={}, world={}, temp={})
   result = run(dana_program, context)
   ```

3. **State Updates**
   ```python
   # Update and access state within Dana programs
   agent.status = "processing"
   temp.result = process_data(world.input_data)
   log.info("Processing complete: {temp.result}")
   ```

## Next Steps

- Learn about [Agents](./agent.md)
- Understand [Capabilities](./capabilities.md)
- Explore [Resources](./resources.md)

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>