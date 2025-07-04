<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../../README.md) | [Main Documentation](../../../docs/README.md)

# Base Capability Module (`dana.common.capability`)

This module provides the foundational `BaseCapability` abstract class for defining agent capabilities within Dana.

Capabilities represent higher-level cognitive functions or skills of an agent, bridging the gap between core agent logic (planning/reasoning) and low-level resources.

For detailed explanations of the Capability System architecture, the `BaseCapability` interface, lifecycle, resource integration patterns, and best practices, please refer to the **[Capability System Concepts Documentation](../../../docs/details/capability_system.md)**.

## Key Components

- **`BaseCapability`**: The abstract base class defining the standard interface (`initialize`, `apply`, `cleanup`) for all capabilities.
- **Specific Capability Implementations**: Concrete capabilities (like `MemoryCapability`, `KnowledgeCapability`) are typically found in `dana.frameworks.agent.capability`.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../../../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
