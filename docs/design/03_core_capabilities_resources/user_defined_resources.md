| [← Standard System Resources](./system_resources.md) | [Capability Invocation from Dana →](./capability_invocation.md) |
|---|---|

# User-Defined Resources

*(This document is a placeholder. It will explain the process and best practices for developers to create their own custom Resource classes in Python and integrate them into the Dana runtime environment, making new capabilities available to Dana programs.)*

## Key Topics to Cover:

* Motivation: Why create user-defined resources? (e.g., integrating proprietary APIs, specialized hardware, unique data sources, complex business logic).
* Steps to Create a Custom Resource:
 1. **Define the Resource Class**: Inherit from the base `Resource` class (see `resource_model.md`).
 2. **Implement `__init__`**: Handle configuration parameters specific to this resource.
 3. **Implement Lifecycle Methods** (Optional but Recommended): `setup()`, `teardown()`, `health_check()`.
 4. **Define Public Methods**: These are the Python functions that will be exposed as capabilities to Dana.
 * Follow naming conventions.
 * Handle type conversions between Python and Dana (for arguments and return values).
 * Manage errors and exceptions, propagating them appropriately to Dana.
 5. **Documentation**: Clearly document the resource, its capabilities, required configuration, and usage examples.
* Packaging and Distribution (If applicable): How custom resources can be packaged as Python libraries for wider use.
* Registration and Discovery:
 * How the Dana runtime discovers and loads user-defined resources.
 * Mechanisms for programmatic registration or plugin-based loading.
* Configuration for Custom Resources:
 * Extending the system configuration to include settings for user-defined resources.
* Best Practices:
 * Idempotency: Design resource methods to be idempotent where possible.
 * Error Handling: Provide clear and actionable error messages.
 * Security: Consider security implications, especially if the resource interacts with sensitive systems or data. Follow the principle of least privilege.
 * State Management: Be mindful of state within the resource instance and its lifecycle.
 * Testability: Write unit tests for the custom resource.
 * Asynchronous Operations: Implement non-blocking methods for I/O-bound operations if appropriate.
* Example: A Simple Custom Resource
 * Walk through creating a basic resource, e.g., a `WeatherResource` that fetches weather from a public API.
 * Show its Python implementation.
 * Show how it would be configured and called from Dana.
* Advanced Considerations:
 * Resources that manage complex state or long-lived connections.
 * Resources that provide callbacks or emit events.