# OpenDXA for Engineers

## OpenDXA
Get from zero to working agent in 15 minutes.

- [5-Minute Setup](setup/installation.md) - Install and verify OpenDXA
- [Build Your First Agent](recipes/first-agent.md) - Working code in 10 minutes
- [Dana Language Basics](reference/dana-syntax.md) - Essential syntax reference
- [Structs and Methods Guide](reference/structs-and-methods.md) - Complete struct system guide

## 📋 Common Tasks
Jump directly to solutions for typical engineering problems.

- [Build a Chatbot](recipes/chatbot/README.md) - Customer service, FAQ, conversational AI
- 📄 [Process Documents](recipes/document-processor/README.md) - Extract, analyze, transform content
- [Create Workflows](recipes/workflow-agent/README.md) - Multi-step automated processes
- [Integrate APIs](recipes/api-integration/README.md) - Connect external services
- [Struct Patterns Cookbook](recipes/structs-cookbook.md) - Real-world struct patterns and examples
- [Debug Issues](troubleshooting/README.md) - Common problems and solutions

## Reference
Quick lookup for syntax, functions, and commands.

- [Dana Language Reference](reference/dana-syntax.md) - Complete syntax guide
- [Structs and Methods Guide](reference/structs-and-methods.md) - Comprehensive struct system reference
- [API Reference](reference/api/README.md) - All available functions with examples
- [REPL Commands](reference/repl-guide.md) - Interactive development environment
- [Troubleshooting](troubleshooting/README.md) - Common problems and solutions

## By Experience Level
- New to OpenDXA: Start with [Getting Started](#getting-started-paths)
- Experienced Developer: Jump to [Common Tasks](#common-tasks)
- Debugging Issue: Check [Troubleshooting](troubleshooting/README.md)

## What Makes OpenDXA Different

OpenDXA transforms AI development from brittle, unpredictable systems to reliable, auditable automations:

- Transparent: Every step is visible and debuggable
- Reliable: Built-in verification and error correction
- Fast: Dramatically reduced development time
- Collaborative: Share and reuse working solutions

## Core Concepts for Engineers

### Dana Language
Dana is the heart of OpenDXA - a simple, powerful language for AI automation:

```dana
# Load data and analyze
documents = load_documents("contracts/*")
key_points = reason("Extract key terms from {documents}")
summary = reason("Summarize findings: {key_points}")

# Structured data with AI integration
struct Customer:
    name: str
    email: str
    risk_level: str

def assess_risk(customer: Customer) -> str:
    return reason("Assess customer risk level", context=customer)

customer = Customer(name="Alice", email="alice@example.com", risk_level="")
risk = customer.assess_risk()  # Method syntax sugar
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
current_task = "contract_review" # Auto-scoped to local (preferred)
private:analysis_results = review_contract(document) # Agent-specific data
public:completion_status = "ready" # Shared state
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
2. Converting LLM calls to Dana (see recipes)
3. Testing and validation (see troubleshooting)

---

## 📖 Complete Documentation Tree

```
for-engineers/
├── setup/
│ ├── installation.md # Complete installation guide
│ ├── configuration.md # Environment setup
│ ├── verification.md # Test your installation
│ └── migration-guide.md # Migrate from other frameworks
├── recipes/
│ ├── first-agent.md # Your first working agent
│ ├── chatbot/README.md # Build conversational agents
│ ├── document-processor/README.md # Process and analyze documents
│ ├── workflow-agent/README.md # Multi-step automation
│ ├── api-integration/README.md # Connect external services
│ ├── structs-cookbook.md # Real-world struct patterns and examples
│ └── README.md # Recipe guides
├── reference/
│ ├── dana-syntax.md # Complete Dana language reference
│ ├── structs-and-methods.md # Comprehensive struct system guide
│ ├── functions.md # All available functions
│ ├── repl-guide.md # Interactive development
│ ├── agent-api.md # Agent configuration API
│ └── state-management.md # State scopes and management
└── troubleshooting/README.md
 ├── common-issues.md # Frequent problems and solutions
 └── README.md # Troubleshooting guide
```

---

*Ready to build? Start with [Getting Started](#getting-started-paths) or jump to [Common Tasks](#common-tasks)* 

## Quick Examples

### Basic Dana Script
```python
# Simple reasoning and logging
name = "OpenDXA Agent"
analysis = reason("What are the key benefits of this system?", context=specs)
log.info(f"Analysis complete for {name}")

# Load knowledge and process data
use("kb.finance.risk_assessment")
risk_level = reason("Assess portfolio risk", context=portfolio_data)
```

### Object Method Calls & MCP Integration (NEW)
```python
# Connect to MCP services and call methods
websearch = use("mcp", url="http://localhost:8880/websearch")
tools = websearch.list_tools()
results = websearch.search("OpenDXA documentation")

# A2A Agent integration
analyst = use("a2a.research-agent")
market_analysis = analyst.analyze_trends(financial_data)
report = analyst.generate_report(market_analysis)

# Resource management with 'with' statements
with use("mcp.database") as database:
    users = database.query("SELECT * FROM active_users")
    database.update_analytics(users)
```

### Advanced Control Flow
```python
# Process multiple data sources
data_sources = ["api", "database", "files"]

for source in data_sources:
    if source == "api":
        raw_data = fetch_api_data()
    elif source == "database": 
        raw_data = query_database()
    else:
        raw_data = load_file_data()
    
    processed = reason("Clean and validate data", context=raw_data)
    results[source] = processed
```

---

## 🎯 Core Concepts
*Ready to build? Start with [Getting Started](#getting-started-paths) or jump to [Common Tasks](#common-tasks)*

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
