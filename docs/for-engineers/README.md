<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../../README.md)

# OpenDXA for Engineers

> **⚠️ IMPORTANT FOR AI CODE GENERATORS:**
> Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
> NEVER use dot notation: `private.x`, `public.x`, etc.
> Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.

## 🚀 Quick Start
Get from zero to working agent in 15 minutes.

- [5-Minute Setup](setup/installation.md) - Install and verify OpenDXA
- [Build Your First Agent](recipes/first-agent.md) - Working code in 10 minutes
- [Dana Language Basics](reference/dana-syntax.md) - Essential syntax reference

## 📋 Common Tasks
Jump directly to solutions for typical engineering problems.

- 🤖 [Build a Chatbot](recipes/chatbot/) - Customer service, FAQ, conversational AI
- 📄 [Process Documents](recipes/document-processor/) - Extract, analyze, transform content
- 🔄 [Create Workflows](recipes/workflow-agent/) - Multi-step automated processes
- 🔗 [Integrate APIs](recipes/api-integration/) - Connect external services
- 🐛 [Debug Issues](troubleshooting/) - Common problems and solutions

## 📚 Reference
Quick lookup for syntax, functions, and commands.

- [Dana Language Reference](reference/dana-syntax.md) - Complete syntax guide
- [Function Catalog](reference/functions.md) - All available functions with examples
- [REPL Commands](reference/repl-guide.md) - Interactive development environment
- [Error Messages](troubleshooting/error-reference.md) - Error codes and fixes

## 🎯 By Experience Level
- **New to OpenDXA**: Start with [Quick Start](#-quick-start)
- **Experienced Developer**: Jump to [Common Tasks](#-common-tasks)
- **Debugging Issue**: Check [Troubleshooting](troubleshooting/)

## 💡 What Makes OpenDXA Different

OpenDXA transforms AI development from brittle, unpredictable systems to reliable, auditable automations:

- **Transparent**: Every step is visible and debuggable
- **Reliable**: Built-in verification and error correction
- **Fast**: Dramatically reduced development time
- **Collaborative**: Share and reuse working solutions

## 🔧 Core Concepts for Engineers

### Dana Language
Dana is the heart of OpenDXA - a simple, powerful language for AI automation:

```python
# Load data and analyze
documents = load_documents("contracts/*")
key_points = reason("Extract key terms from {documents}")
summary = reason("Summarize findings: {key_points}")
```

### Agent Architecture
Build structured agents with clear capabilities:

```python
# Define agent with specific capabilities
agent = Agent("contract_analyzer")
    .with_capabilities(["document_processing", "legal_analysis"])
    .with_resources(["legal_kb", "contract_templates"])
```

### State Management
Clear, scoped state that's always inspectable:

```python
# Organized state scopes
current_task = "contract_review"  # Auto-scoped to local (preferred)
private:analysis_results = review_contract(document)  # Agent-specific data
public:completion_status = "ready"  # Shared state
```

## 🚦 Getting Started Paths

### Path 1: Quick Demo (5 minutes)
```bash
# Install OpenDXA
pip install opendxa

# Run your first agent
opendxa demo chatbot
```

### Path 2: Build from Scratch (15 minutes)
1. [Install OpenDXA](setup/installation.md)
2. [Create your first agent](recipes/first-agent.md)
3. [Test with the REPL](reference/repl-guide.md)

### Path 3: Migrate Existing Code (30 minutes)
1. [Migration Guide](setup/migration-guide.md)
2. [Converting LLM calls to Dana](recipes/migration-patterns.md)
3. [Testing and validation](troubleshooting/migration-issues.md)

---

## 📖 Complete Documentation Tree

```
for-engineers/
├── setup/
│   ├── installation.md           # Complete installation guide
│   ├── configuration.md          # Environment setup
│   ├── verification.md           # Test your installation
│   └── migration-guide.md        # Migrate from other frameworks
├── recipes/
│   ├── first-agent.md            # Your first working agent
│   ├── chatbot/                  # Build conversational agents
│   ├── document-processor/       # Process and analyze documents
│   ├── workflow-agent/           # Multi-step automation
│   ├── api-integration/          # Connect external services
│   └── migration-patterns.md     # Common migration patterns
├── reference/
│   ├── dana-syntax.md            # Complete Dana language reference
│   ├── functions.md              # All available functions
│   ├── repl-guide.md             # Interactive development
│   ├── agent-api.md              # Agent configuration API
│   └── state-management.md       # State scopes and management
└── troubleshooting/
    ├── common-issues.md          # Frequent problems and solutions
    ├── error-reference.md        # Error codes and meanings
    ├── debugging-guide.md        # Debugging techniques
    └── migration-issues.md       # Migration-specific problems
```

---

*Ready to build? Start with [Quick Start](#-quick-start) or jump to [Common Tasks](#-common-tasks)* 


<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>