# Dana Language Specifications

**Author:** Dana Language Team  
**Date:** 2025-01-22  
**Version:** 1.0.0  
**Status:** Complete

This directory contains the authoritative design specifications for the Dana programming language and its ecosystem. It serves as the single source of truth for language features, frameworks, and implementation details.

## Navigation

```
dana/specs/
├── core/          # Language features (syntax, grammar, types)
├── advanced/      # Complex features (methods, composition)
├── agent/         # Agent system and capabilities
│   ├── capabilities.md           # Objective-driven agent design
│   └── agent_keyword.md          # Agent keyword design specification
├── frameworks/    # Language frameworks (POET, KNOWS, Corral)
│   ├── poet_design.md              # POET framework design
│   ├── corral_design.md            # CORRAL framework design
│   ├── knows_proposal.md           # KNOWS framework proposal
│   ├── knows_workflow.md           # KNOWS workflow design
│   ├── knows_retrieval.md          # KNOWS retrieval design
│   ├── knows_ingestion.md          # KNOWS ingestion design
│   ├── corral_curation.md          # CORRAL curation design
│   └── poet_*.md                   # POET examples and use cases
├── runtime/       # Execution engine components
│   ├── concurrency.md              # Concurrent-by-default design
│   ├── interpreter.md              # Interpreter architecture
│   ├── ast.md                      # Abstract syntax tree
│   └── repl.md                     # Read-eval-print loop
├── integrations/  # External system integrations
│   └── vscode.md                   # VS Code language support
├── common/        # Shared infrastructure
│   ├── infrastructure.md           # Common infrastructure design
│   ├── resource.md                 # Resource system design
│   └── io.md                       # IO system design
├── archive/       # Deprecated/historical designs
└── templates/     # Document templates and standards
```

Documents are organized by category in subdirectories. Each document header indicates status: **Complete** (implemented), **Implementation** (in progress), **Design** (proposal), **Example** (use cases), or **Deprecated** (outdated). Look for `*_impl.md` files for implementation details and `*_example.md` files for usage examples. Use `templates/design_document_template.md` for new specifications. 