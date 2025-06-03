# 03. Core Capabilities and Resources

This section details the core capabilities provided by the Dana platform and the `Resource` abstraction model through which Dana programs interact with both internal and external functionalities.

Capabilities are high-level functionalities that an agent or Dana program can leverage. Resources are concrete implementations, often Python classes, that provide these capabilities to the Dana runtime environment.

## Documents

*   **[Overview of Capabilities and Resources](./capabilities_overview.md)**: Introduces the concepts and their roles in Dana.
*   **[Resource Abstraction Model](./resource_model.md)**: Details the design of the `Resource` class, configuration, and lifecycle.
*   **[Standard System Resources](./system_resources.md)**: Describes built-in resources (e.g., `LLMResource`, `FileSystemResource`, `NetworkResource`).
*   **[User-defined Resources](./user_defined_resources.md)**: Explains how users can create and integrate custom resources.
*   **[Capability Invocation from Dana](./capability_invocation.md)**: How Dana code accesses and uses resources and their methods.

*(More documents to be added as specific capabilities are designed, e.g., for specific LLM interactions, tool usage, data handling, etc.)* 