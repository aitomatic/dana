<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
# Conversation Context Management

This document describes how OpenDXA manages conversation history and LLM interaction context at the Executor (Planner/Reasoner) layer.

*Note: For general state management of workflows, execution progress, and component data flow, see [State Management](../core-concepts/state-management.md).*

## Scope and Responsibilities

The conversation context management system is responsible for:

1. **LLM Interaction State**
   - Managing message history and conversation threads
   - Handling context windows and token usage
   - Controlling conversation flow and branching

2. **Prompt Management**
   - Constructing and formatting prompts
   - Managing context injection
   - Handling prompt optimization

3. **LLM-Specific Operations**
   - Token counting and management
   - Context window optimization
   - Message pruning and summarization

*Note: For workflow state, execution progress, and general component data flow, see [State Management](../core-concepts/state-management.md).*

## Overview

Unlike workflow and execution state (which is managed by `ExecutionContext`), conversation context is handled at the Executor layer (Planner and Reasoner). This separation provides several benefits:

1. **Specialized Handling**: Conversation context requires specific management for:
   - Message history
   - Token counting
   - Context window management
   - Conversation threading

2. **Performance Optimization**: Direct management at the Executor layer allows for:
   - Efficient context window management
   - Optimized token usage
   - Better control over conversation flow

3. **Separation of Concerns**: Keeps the state management system focused on workflow and execution state, while conversation management is handled where it's most relevant.

## Implementation Details

The conversation context is managed through a layered approach:

1. **Executor Layer (Planner/Reasoner)**
   - Maintains conversation history and context
   - Controls conversation flow and branching
   - Manages prompt construction and context injection
   - Uses LLMResource for LLM interactions

2. **LLMResource**
   - Handles direct LLM communication
   - Manages token usage and response length
   - Controls model configuration and parameters
   - Processes tool calls and responses

## Relationship with State Management

While conversation context is managed separately from the state management system, there are points of interaction:

1. **Context Injection**
   - Relevant conversation context can be injected into the state management system when needed
   - Example: Extracting key decisions or preferences from conversation history

2. **State Reference**
   - Conversation context may reference or be influenced by state managed by `ExecutionContext`
   - Example: Using workflow state to inform conversation decisions

## Best Practices

1. **Context Management**
   - Keep conversation context focused on the immediate interaction
   - Use summarization for long conversations
   - Implement efficient pruning strategies

2. **State Integration**
   - Only inject relevant conversation context into the state management system
   - Maintain clear boundaries between conversation and workflow state
   - Use appropriate namespaces when storing conversation-derived state

3. **Performance**
   - Monitor token usage
   - Implement efficient context window management
   - Use appropriate summarization strategies

## Conclusion

The separation of conversation context management from the state management system allows for more specialized and efficient handling of LLM interactions while maintaining clear boundaries between different types of state.

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
