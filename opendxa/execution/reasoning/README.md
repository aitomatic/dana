<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../../README.md) | [Main Documentation](../../../docs/README.md)

# Reasoning System Module (`opendxa.execution.reasoning`)

This module contains the implementation of the reasoning system, the tactical execution component of OpenDXA's Imperative Aspect.

It implements various **Reasoning Patterns** (e.g., Direct, Chain of Thought, OODA, DANA) that determine how an agent executes individual plan steps and makes decisions.

For detailed explanations of the Reasoning System architecture, concepts, patterns, and usage, please refer to the **[Reasoning System Concepts Documentation](../../../docs/details/reasoning_system.md)**.

## Key Components

- **Reasoning Patterns:** Implementations for different reasoning strategies (e.g., `DirectReasoning`, `ChainOfThoughtReasoning`).
- **Reasoning Factory:** Used to create instances of specific reasoning patterns.
- **Base Classes:** Foundational classes for defining reasoning patterns.

---
<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="../../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
