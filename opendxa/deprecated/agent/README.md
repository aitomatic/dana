<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md) | [Main Documentation](../../docs/README.md)

# Agent System Module (`opendxa.agent`)

This module provides the core components for creating and managing OpenDXA agents, including the `Agent` class (often used via `AgentFactory`), and submodules for specific agent aspects like `capability` and `resource` implementations.

For detailed explanations of the Agent System architecture, core concepts (Agents, Capabilities, Resources), design philosophy, and usage, please refer to the **[Agent System Concepts Documentation](../../docs/details/agent_system.md)**.

## Key Submodules / Components

- **`Agent` / `AgentFactory`**: Core classes for creating and configuring agents.
- **`capability/`**: Contains specific capability implementations (e.g., `MemoryCapability`, `KnowledgeCapability`). See also [Base Capability Documentation](../../docs/details/capability_system.md).
- **`resource/`**: Contains specific resource implementations (e.g., `LLMResource`, `HumanResource`). See also [Base Resource Documentation](../../docs/details/resource_system.md).
- **`io/`**: (Placeholder) Intended for agent input/output handling. See [IO System Documentation](../../common/io/README.md).

## Related Documentation

- [Execution System Concepts](../../docs/details/base_execution.md)
- [State Management Concepts](../../docs/details/state_management.md)
- [Examples](../../examples/README.md)

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
