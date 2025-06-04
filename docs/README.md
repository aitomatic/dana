# OpenDXA Documentation

*Powered by Dana, a Pythonic agentic programming language and secure sandboxed runtime.*

## Choose Your Path

### I want to build with OpenDXA
→ **[For Engineers](for-engineers/README.md)** - Practical guides, recipes, and references
*Perfect for developers who want to get working quickly*

What you'll find:
- 5-minute setup and first agent tutorial
- Complete Dana language reference and REPL guide
- Real-world recipes for chatbots, document processing, and workflows
- Troubleshooting guides and error references

Start here: [Getting Started](for-engineers/README.md#getting-started-paths)

---

### I'm evaluating OpenDXA for my team
→ **[For Evaluators](for-evaluators/README.md)** - Comparisons, ROI analysis, and proof of concepts
*Perfect for technical leads and decision makers*

What you'll find:
- ROI calculator and competitive analysis
- Risk assessment and technical evaluation frameworks
- Proof of concept guides and adoption strategies
- Decision frameworks and implementation roadmaps

Start here: [Evaluation Guide](for-evaluators/README.md)

---

### I want to contribute or extend OpenDXA
→ **[For Contributors](for-contributors/README.md)** - Architecture, codebase, and development guides
*Perfect for developers who want to modify or extend the system*

What you'll find:
- Complete architecture deep dive and codebase navigation
- Development environment setup and contribution guidelines
- Extension development for capabilities and resources
- Testing frameworks and documentation standards

Start here: [Development Setup](for-contributors/README.md)

---

### I want to understand the philosophy and theory
→ **[For Researchers](for-researchers/README.md)** - Manifesto, theory, and academic context
*Perfect for researchers and those interested in the theoretical foundations*

What you'll find:
- Dana manifesto and neurosymbolic computing foundations
- Research opportunities and collaboration frameworks
- Theoretical analysis and future research directions
- Academic partnerships and publication opportunities

Start here: [Research Overview](for-researchers/README.md#research-overview)

---

## What is OpenDXA?

OpenDXA (Domain-eXpert Agent) Framework transforms AI development from brittle, unpredictable systems to reliable, auditable automations. Built on the Dana language - a neurosymbolic programming environment - OpenDXA enables intelligent multi-agent systems with domain expertise.

### ✨ Key Benefits
- Transparent: Every step is visible and debuggable through imperative programming
- 🛡️ Reliable: Built-in verification and error correction with structured state management
- ⚡ Fast: 10x faster development cycles with clear control flow
- 🤝 Collaborative: Share and reuse working solutions across domains
- Domain-Aware: Seamless integration of specialized knowledge and expertise

### Core Innovation: Dana Language & DANKE Engine

Dana (Domain-Aware NeuroSymbolic Architecture) provides an imperative programming model for agent reasoning:

```dana
# Traditional AI: Opaque, brittle
result = llm_call("analyze data", context=data)

# Dana: Transparent, self-correcting with explicit state management
analysis = reason("analyze data", context=data) # Auto-scoped to local (preferred)
while confidence(analysis) < high_confidence:
 analysis = reason("refine analysis", context=[data, analysis])

# Clear state transitions and auditable reasoning
public:result = analysis
use("tools.report.generate", input=public:result)
```

**DANKE** (Domain-Aware NeuroSymbolic Knowledge Engine) implements the CORRAL methodology:
- Collect: Gather and ingest domain knowledge
- Organize: Structure and index knowledge
- Retrieve: Access and search for relevant knowledge
- Reason: Infer, contextualize, and generate insights
- Act: Apply knowledge to take actions and solve problems
- Learn: Integrate feedback and improve knowledge over time

### Architecture Overview

OpenDXA combines declarative knowledge with imperative execution for maintainable, reliable AI systems:

```mermaid
graph TD
    subgraph "Application Layer"
        UI["User Interface & API Gateway"]
        DomainApps["Domain Applications (Manufacturing, Finance, etc.)"]
    end

    subgraph "Agent Workflow Layer"
        AgentMgmt["Agent Management & Planning"]
        Capabilities["Capabilities System (Extensible)"]
        ResourcesMgmt["Resources Management (Tools & LLMs)"]
    end

    subgraph "Dana Execution Layer"
        Parser["Parser (AST) & Grammar Engine"]
        Interpreter["Interpreter (Executor) & Reasoning Integration"]
        StateMgmt["State Management (4-Scope Context: private|public|system|local)"]
    end

    subgraph "DANKE Knowledge Engine"
        CollectLearn["Collect & Learn (CORRAL)"]
        OrganizeStructure["Organize & Structure (Indexing)"]
        RetrieveReasonAct["Retrieve, Reason & Act (Domain Context)"]
    end

    subgraph "Resource & Communication Layer"
        LLMIntegration["LLM Resource Integration (Multi-Model)"]
        KBManagement["Knowledge Base Management"]
        ExternalTools["External Tools & Services (MCP, APIs)"]
    end

    UI --> AgentMgmt
    DomainApps --> AgentMgmt
    AgentMgmt --> Parser
    Capabilities --> Interpreter
    ResourcesMgmt --> Interpreter
    Parser --> Interpreter
    Interpreter --> StateMgmt
    StateMgmt --> CollectLearn
    CollectLearn --> OrganizeStructure
    OrganizeStructure --> RetrieveReasonAct
    RetrieveReasonAct --> LLMIntegration
    RetrieveReasonAct --> KBManagement
    RetrieveReasonAct --> ExternalTools
```

### Execution Flow

```
User Request/Domain Problem
 ↓
Agent Planning Layer → Dana Program Generation
 ↓
Dana Parser → AST Generation
 ↓
Dana Interpreter with 4-Scope State Management
 ↓
Statement Execution + LLM Reasoning Integration
 ↓
DANKE Knowledge Engine → CORRAL Methodology
 ↓
Tool/Resource Access → External System Integration
 ↓
State Updates & Response Generation
 ↓
Auditable Results & Learning Integration
```

---

## Quick Navigation by Use Case

### Building AI Agents
- New to AI development: [Engineers Quick Start](for-engineers/README.md#getting-started-paths)
- Experienced with LLMs: [Migration Guide](for-engineers/setup/migration-guide.md)
- Need specific examples: [Recipe Collection](for-engineers/recipes/README.md)
- Dana language reference: [Syntax Guide](for-engineers/reference/dana-syntax.md)

### 📊 Business Evaluation
- ROI Analysis: [Cost-Benefit Calculator](for-evaluators/roi-analysis/calculator.md)
- Technical Assessment: [Architecture Overview](for-evaluators/comparison/technical-overview.md)
- Proof of Concept: [Evaluation Guide](for-evaluators/proof-of-concept/evaluation-guide.md)
- Competitive Analysis: [Framework Comparison](for-evaluators/comparison/README.md)

### 🔬 Research & Development
- Theoretical Foundations: [Dana Manifesto](for-researchers/manifesto/vision.md)
- Neurosymbolic Computing: [Research Opportunities](for-researchers/README.md#research-opportunities)
- Academic Collaboration: [Partnership Programs](for-researchers/README.md#academic-collaboration)
- Original Documentation: [Archive](https://github.com/aitomatic/opendxa/tree/main/docs/.archive)

### Platform Extension
- Custom Capabilities: [Extension Development](for-contributors/extending/extension-development.md)
- Core Contributions: [Contribution Guide](for-contributors/development/contribution-guide.md)
- Architecture Understanding: [System Design](for-contributors/architecture/system-design.md)
- Codebase Navigation: [Code Guide](for-contributors/codebase/README.md)

---

## 🌟 Success Stories

> *"I used to spend hours debugging prompt chains and patching brittle scripts. Every new document or edge case meant another late night. With Dana, I finally feel in control. My automations are clear, reliable, and easy to improve. What used to take our team weeks now takes days or even hours."*
>
> — Sarah K., Lead AI Engineer at FinTech Solutions

> *"OpenDXA's transparency was a game-changer for our compliance requirements. We can audit every decision, understand every step, and trust our AI systems in production. The ROI was evident within the first month."*
>
> — Michael R., CTO at Healthcare Analytics

---

## 🚦 Getting Started Paths

### ⚡ 5-Minute Demo
```bash
pip install opendxa
opendxa demo chatbot
```
[Try the demo →](for-engineers/README.md#path-1-quick-demo-5-minutes)

### Learn the Concepts
1. [What makes OpenDXA different](for-engineers/README.md#what-makes-opendxa-different)
2. [Dana language basics](for-engineers/reference/dana-syntax.md)
3. [Agent architecture overview](for-contributors/architecture/system-design.md)
4. [DANKE knowledge engine](for-researchers/research/README.md)

### Solve Your Use Case
- [Document Processing](for-engineers/recipes/document-processor/README.md)
- [API Integration](for-engineers/recipes/api-integration/README.md)
- [Workflow Automation](for-engineers/recipes/workflow-agent/README.md)
- [Chatbot Development](for-engineers/recipes/chatbot/README.md)

---

## 📞 Community & Support

### 💬 Get Help
- Technical Questions: [GitHub Discussions](https://github.com/aitomatic/opendxa/discussions)
- Bug Reports: [GitHub Issues](https://github.com/aitomatic/opendxa/issues)
- Real-time Chat: [Discord Community](https://discord.gg/opendxa)

### 🤝 Get Involved
- Contribute Code: [Contribution Guidelines](for-contributors/development/contribution-guide.md)
- Share Examples: [Community Recipes](for-engineers/recipes/README.md)
- Research Collaboration: [Academic Partnerships](for-researchers/README.md#academic-collaboration)

### 🏢 Enterprise Support
- Business Inquiries: [Contact Sales](mailto:sales@aitomatic.com)
- Professional Services: [Implementation Support](for-evaluators/adoption-guide/professional-services.md)
- Custom Development: [Enterprise Solutions](mailto:enterprise@aitomatic.com)

---

## 📖 Documentation Structure

This documentation is organized by audience with cross-references and maintained through structured AI-assisted processes:

```
docs/
├── for-engineers/ # Practical development guides
│ ├── setup/ # Installation and configuration
│ ├── recipes/ # Real-world examples and patterns
│ ├── reference/ # Language and API documentation
│ └── troubleshooting/ # Common issues and solutions
├── for-evaluators/ # Business and technical evaluation
│ ├── comparison/ # Competitive analysis and positioning
│ ├── roi-analysis/ # Cost-benefit and ROI calculations
│ ├── proof-of-concept/ # Evaluation and testing guides
│ └── adoption-guide/ # Implementation and change management
├── for-contributors/ # Development and extension guides
│ ├── architecture/ # System design and implementation
│ ├── codebase/ # Code navigation and understanding
│ ├── extending/ # Building capabilities and resources
│ └── development/ # Contribution and testing guidelines
├── for-researchers/ # Theoretical and academic content
│ ├── manifesto/ # Vision and philosophical foundations
│ ├── neurosymbolic/ # Technical and theoretical analysis
│ ├── research/ # Research opportunities and collaboration
│ └── future-work/ # Roadmap and future directions
├── archive/ # Preserved original documentation
│ ├── original-dana/ # Authoritative Dana language specification
│ ├── original-core-concepts/ # Original architectural concepts
│ └── original-architecture/ # Historical system design
├── internal/ # Internal planning and requirements
└── .ai-only/ # AI assistant structured references
 ├── documentation.md # Documentation maintenance prompts
 ├── documentation-maintenance.md # Structured update procedures
 ├── project.md # Project structure guide
 ├── opendxa.md # System overview and components
 ├── dana.md # Dana language technical reference
 └── functions.md # Function catalog and registry
```

### Documentation Maintenance

This documentation is maintained through structured processes that ensure:
- Function Registry: Automated tracking of new Dana functions and capabilities
- Example Validation: Regular testing of all code examples with current syntax
- Content Gap Analysis: Weekly assessment of documentation coverage
- Cross-Audience Updates: Synchronized updates across all audience trees
- AI-Assisted Quality: Structured prompts for consistent maintenance

The `.ai-only/` directory contains reference materials and maintenance procedures that keep this documentation current and comprehensive.

---

*Ready to transform your AI development? Choose your path above and start building transparent, reliable AI automations with OpenDXA.*

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>