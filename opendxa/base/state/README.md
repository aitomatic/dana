<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../../README.md) | [Main Documentation](../../../docs/README.md)

# State Management Module (`opendxa.base.state`)

This module provides the foundational classes for state management within OpenDXA, including the `BaseState` model and the `StateManager`.

For detailed explanations of the State Management architecture, concepts (BaseState, StateManager, Blackboard, Artifacts), design principles, and usage, please refer to the **[State Management Concepts Documentation](../../../docs/details/state_management.md)**.

## Key Components

- **`BaseState`**: The core Pydantic model providing blackboard and artifact storage, along with dot-notation access.
- **`StateManager`**: Manages access to different state containers (e.g., `AgentState`, `WorldState`) via prefix-based routing.
- **Specialized State Classes**: (Defined elsewhere, e.g., `AgentState`, `WorldState`, `ExecutionState`) Subclasses of `BaseState` for specific domains.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../../../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 