# OpenDXA and Dana Design Documentation

This directory contains the authoritative design specifications for the OpenDXA framework and the Dana language. These documents define the architecture, implementation details, and design decisions that guide the project.

## Organization

The design documents are organized into the following main sections:

1.  **[00_dana_philosophy/](./00_dana_philosophy/)**: Core vision, goals, and guiding principles behind Dana.
2.  **[01_dana_language_specification/](./01_dana_language_specification/)**: Detailed definition of the Dana language itself – syntax, semantics, data types, functions, state management, etc.
3.  **[02_dana_runtime_and_execution/](./02_dana_runtime_and_execution/)**: How Dana code is executed, including the interpreter, sandbox, REPL, and the IPV architecture.
4.  **[03_dana_tooling_and_processing/](./03_dana_tooling_and_processing/)**: Components involved in processing Dana code, such as the parser, AST, validators, and transcoders.
5.  **[04_opendxa_integration_and_extension/](./04_opendxa_integration_and_extension/)**: How Dana integrates with the broader OpenDXA system, including agents and capabilities.
6.  **[archive/](./archive/)**: Older or superseded design documents.

## Document Status

All documents in this directory (outside of `archive/`) are considered **active design specifications**. They define the current and planned implementation of Dana and its role within OpenDXA. These are the authoritative sources for:

-   Dana language syntax and semantics
-   System architecture decisions related to Dana
-   Implementation patterns and best practices for Dana components
-   Design rationale and trade-offs

## For Contributors

When modifying Dana or its related OpenDXA components:

1.  **Consult relevant design documents** before making changes.
2.  **Update design documents** when making architectural or significant behavioral changes.
3.  **Follow established patterns** and principles documented here.
4.  **Maintain consistency** with the overall design philosophy.

## For Users & Developers

These documents provide deep technical insight into:

-   How Dana language features work internally.
-   The rationale behind specific design decisions.
-   How to extend or integrate with Dana and OpenDXA at a deeper level.
-   Understanding system behavior and limitations.

---

**See Also:**

- User-facing documentation (e.g., in `docs/for-engineers/`, `docs/for-contributors/`) 