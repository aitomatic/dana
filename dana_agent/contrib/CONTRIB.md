# Dana Contrib Applications

This directory contains contributed applications built on top of Dana framework resources and workflows.

## Purpose

Contrib apps demonstrate:
- How to build real applications using Dana resources/workflows
- Best practices for composition and extension
- Domain-specific use cases
- Integration patterns

## Apps

### Expert Interview (`expert_interview/`)

**Domain-agnostic expert interview application with knowledge extraction.**

**Built on:**
- `ConversationResource` (detect_intent, extract_topics)
- `SummarizeConversationWorkflow`
- Custom resources: `ExpertInsightAnalyzer`, `KnowledgeGapDetector`
- Custom workflow: `ExpertInterviewWorkflow`

**LOC:** ~900 lines

**Comparison:**
- Original bs-live-interview: ~10,000 LOC
- This implementation: ~900 LOC (90% reduction)
- Fully domain-agnostic
- Composable and extensible

**See:** [expert_interview/README.md](expert_interview/README.md)

---

## Guidelines for Contrib Apps

### Structure
```
contrib/
├── CONTRIB.md              # This file
└── your_app/
    ├── README.md           # App documentation
    ├── __init__.py         # Package exports
    ├── resources/          # App-specific resources
    ├── workflows/          # App-specific workflows
    └── examples/           # Usage examples
```

### Best Practices

1. **Build on library components** - Reuse Dana's resources/workflows
2. **Domain-agnostic when possible** - Make it reusable
3. **Document well** - README with architecture, usage, examples
4. **Keep it simple** - Focus on demonstrating patterns
5. **Test imports** - Ensure everything loads correctly

### What Makes a Good Contrib App?

✅ **Demonstrates patterns** - Shows how to compose Dana components
✅ **Solves real problems** - Addresses actual use cases
✅ **Well documented** - Clear README with examples
✅ **Minimal dependencies** - Primarily uses Dana library
✅ **Extensible** - Easy to customize and extend

## Contributing

Want to add a contrib app?

1. Create directory under `contrib/`
2. Follow the structure above
3. Write comprehensive README
4. Test imports and basic functionality
5. Submit PR

## License

Same as Dana framework.
