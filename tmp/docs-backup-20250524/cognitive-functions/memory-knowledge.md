<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)


# Memory and Knowledge in OpenDXA

## Overview

The memory and knowledge systems in OpenDXA enable agents to access, utilize, store, and evolve information and domain expertise. Through integration with Dana programs and state containers, the system is designed to handle both short-term context and long-term structured/unstructured knowledge, making it suitable for enterprise applications.

## Core Concepts

### 1. Knowledge Types
- Technical Knowledge
  - Data processing capabilities
  - Language understanding
  - Pattern recognition
  - Analysis techniques
- Domain Knowledge
  - Industry-specific expertise
  - Process knowledge
  - Best practices
  - Historical data

### 2. Knowledge Operations
- Knowledge storage
- Knowledge retrieval
- Knowledge validation
- Knowledge evolution
- Knowledge sharing

## Architecture

The OpenDXA memory and knowledge architecture consists of several layers that integrate with Dana programs:

1. **Knowledge Sources Layer**: Provides input from experts, documents, historical data, and feedback
2. **Knowledge Storage Layer**: Manages structured and unstructured knowledge
3. **Knowledge Processing Layer**: Handles versioning, quality control, and learning
4. **Knowledge Integration Layer**: Connects knowledge to Dana programs and agent execution
5. **Knowledge Evolution Layer**: Manages continuous improvement of the knowledge base

## Implementation

### 1. Knowledge Base Integration with Dana
```python
from opendxa.dana import run
from opendxa.dana.sandbox.sandbox_context import SandboxContext
from opendxa.common.resource.kb_resource import KBResource

# Create knowledge base resource
kb_resource = KBResource(
    name="semiconductor_kb",
    config={"domain": "semiconductor"}
)

# Define Dana program with knowledge integration
knowledge_program = """
# Initialize knowledge state
agent.query = "semiconductor process control"
temp.kb_params = {"query": agent.query, "limit": 5}

# Query knowledge base
temp.knowledge = use_resource("semiconductor_kb", "query", temp.kb_params)

# Apply knowledge to task
temp.analysis = reason("Using this domain knowledge: {temp.knowledge}, analyze the semiconductor process control challenge")

# Store analysis with attribution
agent.analysis = temp.analysis
agent.knowledge_source = "semiconductor_kb"
"""

# Create context with initial state
context = SandboxContext(
    agent={"name": "knowledge_agent"},
    world={},
    temp={}
)

# Register resource and execute program
agent_runtime = AgentRuntime()
agent_runtime.register_resource(kb_resource)
result = agent_runtime.execute(knowledge_program, context)
```

### 2. Memory Capability in Dana
```python
# Dana program with memory operations
memory_program = """
# Store information in memory
temp.memory_params = {
    "key": "process_control_parameters",
    "value": world.process_parameters,
    "metadata": {
        "source": "sensor_readings",
        "timestamp": current_time(),
        "confidence": 0.95
    }
}
use_capability("memory", "store", temp.memory_params)

# Retrieve from memory
temp.retrieve_params = {"key": "process_control_parameters"}
temp.stored_parameters = use_capability("memory", "retrieve", temp.retrieve_params)

# Compare with current parameters
temp.comparison = reason("Compare these stored parameters: {temp.stored_parameters} with current parameters: {world.current_parameters}")

# Log results
log.info("Parameter comparison: {temp.comparison}")
"""
```

### 3. Knowledge Evolution with Dana
```python
# Dana program for knowledge evolution
knowledge_evolution_program = """
# Get feedback and current knowledge
temp.feedback = world.user_feedback
temp.knowledge_id = "semiconductor_cleaning_process"
temp.retrieve_params = {"id": temp.knowledge_id}
temp.current_knowledge = use_capability("kb", "retrieve", temp.retrieve_params)

# Analyze feedback for potential knowledge updates
temp.update_analysis = reason("Analyze this feedback: {temp.feedback} in relation to current knowledge: {temp.current_knowledge}")

# Determine if update is needed
temp.should_update = reason("Based on the analysis, should the existing knowledge be updated? {temp.update_analysis}")

# If update needed, create update
if "yes" in temp.should_update.lower():
    temp.updated_knowledge = reason("Generate updated knowledge incorporating this feedback: {temp.feedback}")
    temp.update_params = {
        "id": temp.knowledge_id,
        "updates": temp.updated_knowledge,
        "reason": "user_feedback",
        "confidence": 0.9
    }
    use_capability("kb", "update", temp.update_params)
    log.info("Knowledge updated based on feedback")
else:
    log.info("No knowledge update needed")
"""
```

## Dana State Management for Knowledge

The OpenDXA framework uses Dana state containers to manage different types of knowledge:

1. **agent.** container: Stores agent-specific knowledge and memory
   - Personal state
   - Task history
   - Preferences
   - Objectives

2. **world.** container: Stores environmental and domain knowledge
   - External information
   - System state
   - Domain facts
   - Real-world context

3. **temp.** container: Manages transient knowledge processing
   - Intermediate analysis
   - Temporary information
   - Processing results
   - Temporary variables

## Key Differentiators

1. **Dana-Integrated Knowledge**
   - Direct knowledge access in Dana programs
   - State-based knowledge management
   - Reasoning with contextual knowledge
   - Dynamic knowledge application

2. **Domain Expertise Integration**
   - Structured domain knowledge
   - Expert knowledge encoding
   - Process definitions
   - Knowledge validation

3. **Continuous Learning**
   - Feedback integration
   - Knowledge evolution
   - Quality improvement
   - Performance tracking

## Best Practices

1. **Knowledge Organization**
   - Maintain clear structure
   - Use proper categorization
   - Implement version control
   - Manage access appropriately

2. **Knowledge Quality**
   - Validate knowledge
   - Verify accuracy
   - Update regularly
   - Track quality metrics

3. **Knowledge Evolution**
   - Implement learning mechanisms
   - Create feedback loops
   - Track knowledge performance
   - Support continuous improvement

## Common Patterns

1. **Knowledge Access Pattern**
   ```python
   # Dana pattern for knowledge access
   knowledge_access = """
   # Query knowledge
   temp.query_params = {"query": world.user_query, "domain": agent.domain}
   temp.knowledge = use_capability("kb", "query", temp.query_params)
   
   # Apply knowledge
   temp.analysis = reason("Using this domain knowledge: {temp.knowledge}, answer the query: {world.user_query}")
   
   # Store result
   agent.response = temp.analysis
   """
   ```

2. **Memory Storage Pattern**
   ```python
   # Dana pattern for memory operations
   memory_pattern = """
   # Store information with context
   temp.memory_params = {
       "key": "user_preference_" + world.user_id,
       "value": world.user_preference,
       "metadata": {
           "source": "user_input",
           "timestamp": current_time(),
           "context": world.interaction_context
       }
   }
   use_capability("memory", "store", temp.memory_params)
   
   # Acknowledge storage
   log.info("User preference stored successfully")
   """
   ```

3. **Knowledge Evolution Pattern**
   ```python
   # Dana pattern for knowledge evolution
   evolution_pattern = """
   # Track performance
   temp.performance = world.task_performance
   temp.knowledge_id = world.used_knowledge_id
   
   # Analyze performance for knowledge improvement
   temp.analysis = reason("Analyze this performance data: {temp.performance} to identify potential knowledge improvements")
   
   # Update knowledge if needed
   if "improvement" in temp.analysis:
       temp.update_params = {
           "id": temp.knowledge_id,
           "updates": temp.analysis,
           "reason": "performance_based",
           "confidence": 0.85
       }
       use_capability("kb", "update", temp.update_params)
   """
   ```

## Knowledge Examples

1. **Technical Knowledge Application**
   - Data processing techniques
   - Analysis methodologies
   - Pattern recognition approaches
   - Language understanding capabilities

2. **Domain Knowledge Integration**
   - Manufacturing process expertise
   - Financial regulation knowledge
   - Healthcare diagnosis guidelines
   - Supply chain optimization principles

3. **Memory-Based Personalization**
   - User preference tracking
   - Interaction history management
   - Context-aware assistance
   - Personalized recommendations

## Next Steps

- Learn about [Agents](../core-concepts/agent.md)
- Understand [Dana Language](../dana/language.md)
- Explore [Resources](../core-concepts/resources.md)

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>