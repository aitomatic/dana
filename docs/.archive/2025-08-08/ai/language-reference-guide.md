# Language Reference Guide

Purpose: A complete, concise reference for Dana syntax and semantics.

Principles:
- Single, comprehensive page preferred; link to primers for deep dives.
- Deterministic structure: grammar → constructs → built-ins → examples.
- Every construct has: syntax, description, constraints, copy-paste example.
- Mark deprecated features and link to migration guides.

Suggested Outline:
1) Version and compatibility badge/comment.
2) Lexical structure (tokens, literals, comments, whitespace).
3) Types and literals.
4) Variables, scope, and assignment.
5) Functions and composition.
6) Structs and methods.
7) Control flow (conditionals, loops, error handling).
8) Concurrency primitives (if public).
9) Built-ins and standard library.
10) Modules/imports.
11) Agents/workflows (public surface only).
12) Annotations/metadata.
13) Deprecations and migrations.

Validation:
- All examples execute with current PyPI.
- No internal or preview-only features.
- Clear links to cookbook recipes for applied patterns.



