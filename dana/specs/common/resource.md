<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

| [← Infrastructure](./infrastructure.md) | [IO System →](./io.md) |
|---|---|

# Base Resource Module (`opendxa.base.resource`)

**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 1.0.0  
**Status:** Implementation

This module provides the foundational `BaseResource` class and potentially other base abstractions for resources within Dana.

Resources represent concrete tools, services, data sources, or interfaces (like LLMs, databases, APIs, human input) that agent capabilities can access.

For detailed explanations of the Resource System architecture, concepts (BaseResource, common types, MCP), design philosophy, and usage, please refer to the **[Resource System Concepts Documentation](../../../docs/details/resource_system.md)**.

## Key Components

- **`BaseResource`**: The abstract base class defining the standard interface for all resources (e.g., `initialize`, `query`, `cleanup`).
- **Specific Resource Implementations**: Concrete resource classes (like `LLMResource`, `HumanResource`, `ToolResource`) are typically found in `opendxa.agent.resource` or potentially other specialized modules.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the [MIT License](../../../LICENSE.md).
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
