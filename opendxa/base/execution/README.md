<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../../README.md) | [Main Documentation](../../../docs/README.md)

# Base Execution Module (`opendxa.base.execution`)

This module provides the foundational abstract classes and interfaces for the execution framework within OpenDXA.

It defines the core concepts like `BaseExecutor`, `ExecutionContext`, `ExecutionGraph`, and `ExecutionSignal` that are used and extended by concrete execution implementations (like Planning, Reasoning, Pipelines).

For detailed explanations of the Base Execution Framework concepts, interfaces, and patterns, please refer to the **[Base Execution Framework Concepts Documentation](../../../docs/details/base_execution.md)**.

## Key Components

- **`BaseExecutor`**: Abstract base class for all execution components.
- **`ExecutionContext`**: Holds state and resources during an execution run.
- **`ExecutionGraph`**: Base structure for defining execution flows.
- **`ExecutionSignal`**: Standardized structure for communication during execution.
- **Supporting Types**: Enums and dataclasses for nodes, edges, results, etc.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 