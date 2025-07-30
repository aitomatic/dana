| [← README](../README.md) | [Resource Abstraction Model →](./resource_model.md) |
|---|---|

# Overview of Capabilities and Resources

*(This document is a placeholder. It will provide a high-level introduction to the concepts of Capabilities and Resources within the Dana ecosystem, explaining their distinct roles and how they interrelate to provide functionality to Dana programs and agents.)*

## Key Concepts to Cover:

* What is a Capability?
 * Definition: A high-level, abstract description of a function or service an agent can perform (e.g., "understand_image", "summarize_text", "execute_sql_query").
 * Focus on *what* can be done, not *how* it's done.
 * Role in agent planning and reasoning.
* What is a Resource?
 * Definition: A concrete implementation that provides one or more capabilities.
 * Typically a Python class made available to the Dana sandbox environment.
 * Handles the specifics of interacting with underlying systems (LLMs, databases, APIs, file systems).
 * Examples: `OpenAIChatResource` providing "text_generation" capability, `PostgresResource` providing "sql_execution" capability.
* Relationship between Capabilities and Resources:
 * A capability can be fulfilled by multiple different resources.
 * A resource can provide multiple related capabilities.
 * The runtime system (potentially with agent oversight) selects the appropriate resource to fulfill a requested capability based on availability, configuration, or preference.
* Benefits of this Abstraction:
 * Modularity: Separates the definition of what an agent can do from the implementation details.
 * Extensibility: New resources (and thus new ways to achieve capabilities) can be added without changing agent logic that relies on abstract capabilities.
 * Flexibility: Allows for different backends or services to be swapped out (e.g., changing LLM providers).
 * Testability: Resources can be mocked or stubbed for testing agent logic.
* Discovery and Registration: How capabilities and resources are made known to the system.
* Configuration: How resources are configured with necessary parameters (API keys, connection strings, etc.).