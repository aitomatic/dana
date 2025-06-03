| [← Resource Abstraction Model](./resource_model.md) | [User-defined Resources →](./user_defined_resources.md) |
|---|---|

# Standard System Resources

*(This document is a placeholder. It will describe the set of standard, built-in resources provided with Dana, such as those for LLM interaction, file system access, network requests, etc. For each resource, it should outline its purpose, key methods/capabilities, and example configuration.)*

## Planned Standard Resources:

*   **`LLMResource` (or specific variants like `OpenAIResource`, `AnthropicResource`)**
    *   Purpose: Interface with Large Language Models.
    *   Capabilities: Text generation, chat completion, embeddings, etc.
    *   Key Methods: `generate_text()`, `chat()`, `get_embedding()`.
    *   Configuration: API keys, model names, default parameters (temperature, max tokens).
    *   Interaction with IPV pattern, especially for `reason()` like functions.

*   **`FileSystemResource`**
    *   Purpose: Interact with the local file system in a controlled manner.
    *   Capabilities: Read file, write file, list directory, check existence.
    *   Key Methods: `read()`, `write()`, `list_dir()`, `exists()`.
    *   Configuration: Base path restrictions (sandboxing), allowed operations.
    *   Security: Emphasize safe and restricted access.

*   **`NetworkResource` (or `HTTPResource`)**
    *   Purpose: Make HTTP requests to external services/APIs.
    *   Capabilities: GET, POST, PUT, DELETE requests.
    *   Key Methods: `get()`, `post()`, `request()`.
    *   Configuration: Allowed domains/IPs, timeout settings, header management.
    *   Security: Considerations for SSRF, data exposure.

*   **`VectorDBResource` (Conceptual - or specific variants for Pinecone, Weaviate, etc.)**
    *   Purpose: Interact with vector databases.
    *   Capabilities: Store vectors, query similar vectors, manage collections.
    *   Key Methods: `upsert()`, `query()`, `delete()`.
    *   Configuration: Connection details, API keys, collection names.

*   **`SQLDatabaseResource` (Conceptual - or specific variants for PostgreSQL, SQLite, etc.)**
    *   Purpose: Execute SQL queries against relational databases.
    *   Capabilities: Execute select, insert, update, delete queries; manage transactions.
    *   Key Methods: `execute_query()`, `execute_statement()`, `begin_transaction()`, `commit()`, `rollback()`.
    *   Configuration: Connection string, credentials.

*   **`ToolResource` (or `FunctionCallingResource`)**
    *   Purpose: A generic way to expose a collection of pre-defined Python tools or functions to Dana, perhaps with schema definition for LLM-based function calling.
    *   Capabilities: List available tools, execute a specific tool by name with arguments.
    *   Key Methods: `list_tools()`, `call_tool(name, **kwargs)`.
    *   Configuration: How tools are registered and described.

*   **`LoggingResource` (Implicit, or an explicit way to configure system logging)**
    *   Purpose: Controls how `log()` statements and system messages are handled.
    *   Capabilities: Set log level, direct logs to different outputs (console, file, external service).
    *   Configuration: Log level, format, output handlers.

*(This list will evolve. Each resource will eventually have its own sub-document or detailed section here.)* 