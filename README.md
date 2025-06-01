<!--
⚠️ IMPORTANT FOR AI CODE GENERATORS:
Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
NEVER use dot notation: `private.x`, `public.x`, etc.
Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.
-->

<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA - Domain-Expert Agent Framework

> A comprehensive framework for easily coding and deploying smart, multi-agent systems with domain expertise, powered by Dana, a Pythonic agentic programming language and secure sandboxed runtime.

## TL;DR

### Requirements

- [git](https://github.com/git-guides/install-git)
- [uv](https://github.com/astral-sh/uv)

To install uv, run their installation script in your terminal.

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen your terminal, then check that the `uv` command works.

### Steps

```bash
# Clone the repo
git clone https://github.com/aitomatic/opendxa.git

# Go to the folder
cd opendxa

# Set up the virtual environment
uv sync
```

Add your API key of choice to your .env file.

```bash
# Create your .env file
cp .env.example .env

# Open the file to edit it
open .env
```

Now you can start the DANA shell, just like Python!

```bash
uv run bin/dana

# You can also activate the venv beforehand instead of letting uv automatically handle it.
source .venv/bin/activate
bin/dana
```
---

## 🎯 Choose Your Path

### 🛠️ I want to build with OpenDXA
→ **[For Engineers](docs/for-engineers/)** - Practical guides, recipes, and references  
*Perfect for developers who want to get working quickly*

**What you'll find:**
- 5-minute setup and first agent tutorial
- Complete Dana language reference and REPL guide
- Real-world recipes for chatbots, document processing, and workflows
- Troubleshooting guides and error references

**Start here:** [Quick Start Guide](docs/for-engineers/README.md#-quick-start)

---

### 🔍 I'm evaluating OpenDXA for my team
→ **[For Evaluators](docs/for-evaluators/)** - Comparisons, ROI analysis, and proof of concepts  
*Perfect for technical leads and decision makers*

**What you'll find:**
- ROI calculator and competitive analysis
- Risk assessment and technical evaluation frameworks
- Proof of concept guides and adoption strategies
- Decision frameworks and implementation roadmaps

**Start here:** [30-Second Assessment](docs/for-evaluators/README.md#-quick-evaluation-framework)

---

### 🏗️ I want to contribute or extend OpenDXA
→ **[For Contributors](docs/for-contributors/)** - Architecture, codebase, and development guides  
*Perfect for developers who want to modify or extend the system*

**What you'll find:**
- Complete architecture deep dive and codebase navigation
- Development environment setup and contribution guidelines
- Extension development for capabilities and resources
- Testing frameworks and documentation standards

**Start here:** [Development Setup](docs/for-contributors/README.md#-quick-start-for-contributors)

---

### 🧠 I want to understand the philosophy and theory
→ **[For Researchers](docs/for-researchers/)** - Manifesto, theory, and academic context  
*Perfect for researchers and those interested in the theoretical foundations*

**What you'll find:**
- Dana manifesto and neurosymbolic computing foundations
- Research opportunities and collaboration frameworks
- Theoretical analysis and future research directions
- Academic partnerships and publication opportunities

**Start here:** [Research Overview](docs/for-researchers/README.md#-research-overview)

---

## 🚀 What is OpenDXA?

OpenDXA (Domain-eXpert Agent) Framework transforms AI development from brittle, unpredictable systems to reliable, auditable automations. Built on the Dana language - a neurosymbolic programming environment - OpenDXA enables intelligent multi-agent systems with domain expertise.

### ✨ Key Benefits
- **🔍 Transparent**: Every step is visible and debuggable through imperative programming
- **🛡️ Reliable**: Built-in verification and error correction with structured state management
- **⚡ Fast**: 10x faster development cycles with clear control flow
- **🤝 Collaborative**: Share and reuse working solutions across domains
- **🧠 Domain-Aware**: Seamless integration of specialized knowledge and expertise

### 🎯 Core Innovation: Dana Language

Dana (Domain-Aware NeuroSymbolic Architecture) provides an imperative programming model for agent reasoning:

```python
# Traditional AI: Opaque, brittle
result = llm_call("analyze data", context=data)

# Dana: Transparent, self-correcting with explicit state management
analysis = reason("analyze data", context=data)  # Auto-scoped to local (preferred)
while confidence(analysis) < high_confidence:
    analysis = reason("refine analysis", context=[data, analysis])

# Clear state transitions and auditable reasoning
public:result = analysis
use("tools.report.generate", input=public:result)
```

### 🏗️ Core Components

OpenDXA consists of three primary components:

1. **OpenDXA Framework** - Orchestrates Dana and DANKE components, manages agent lifecycle
2. **Dana Language** - Universal program format and runtime for agent reasoning
3. **DANKE Engine** - Knowledge management implementing the CORRAL methodology: Collect, Organize, Retrieve, Reason, Act, Learn

---

## 🎯 Quick Navigation by Use Case

### 🤖 Building AI Agents
- **New to AI development**: [Engineers Quick Start](docs/for-engineers/README.md#-quick-start)
- **Experienced with LLMs**: [Migration Guide](docs/for-engineers/setup/migration-guide.md)
- **Need specific examples**: [Recipe Collection](docs/for-engineers/recipes/)
- **Dana language reference**: [Syntax Guide](docs/for-engineers/reference/dana-syntax.md)

### 📊 Business Evaluation
- **ROI Analysis**: [Cost-Benefit Calculator](docs/for-evaluators/roi-analysis/calculator.md)
- **Technical Assessment**: [Architecture Overview](docs/for-evaluators/comparison/technical-overview.md)
- **Proof of Concept**: [Evaluation Guide](docs/for-evaluators/proof-of-concept/evaluation-guide.md)
- **Competitive Analysis**: [Framework Comparison](docs/for-evaluators/comparison/)

### 🔬 Research & Development
- **Theoretical Foundations**: [Dana Manifesto](docs/for-researchers/manifesto/vision.md)
- **Neurosymbolic Computing**: [Research Opportunities](docs/for-researchers/README.md#-research-opportunities)
- **Academic Collaboration**: [Partnership Programs](docs/for-researchers/README.md#-academic-collaboration)
- **Original Documentation**: [Archive](docs/archive/)

### 🛠️ Platform Extension
- **Custom Capabilities**: [Extension Development](docs/for-contributors/extending/extension-development.md)
- **Core Contributions**: [Contribution Guide](docs/for-contributors/development/contribution-guide.md)
- **Architecture Understanding**: [System Design](docs/for-contributors/architecture/system-design.md)
- **Codebase Navigation**: [Code Guide](docs/for-contributors/codebase/)

---

## 🌟 Why OpenDXA?

OpenDXA stands out by enabling truly expert agents grounded in specific domain knowledge:

- **🏢 Leverage Existing Knowledge** - Tap into your company's documents, databases, and expertise
- **🎓 Embed Deep Domain Expertise** - Create reliable agents that understand your specialized processes
- **🔄 Adaptive Knowledge Management** - Manage the full lifecycle as your knowledge evolves
- **🌐 True Interoperability** - Seamlessly connect agents and systems based on different standards

---

## 🛠️ Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

This ensures code quality checks run automatically on commit, including:
- Code formatting with Ruff
- Linting with Ruff (including undefined attributes/methods)
- Basic file checks (trailing whitespace, merge conflicts, etc.)

---

## 📞 Community & Support

### 💬 Get Help
- **Technical Questions**: [GitHub Discussions](https://github.com/aitomatic/opendxa/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/aitomatic/opendxa/issues)
- **Real-time Chat**: [Discord Community](https://discord.gg/opendxa)

### 🤝 Get Involved
- **Contribute Code**: [Contribution Guidelines](docs/for-contributors/development/contribution-guide.md)
- **Share Examples**: [Community Recipes](docs/for-engineers/recipes/)
- **Research Collaboration**: [Academic Partnerships](docs/for-researchers/README.md#-academic-collaboration)

### 🏢 Enterprise Support
- **Business Inquiries**: [Contact Sales](mailto:sales@aitomatic.com)
- **Professional Services**: [Implementation Support](docs/for-evaluators/adoption-guide/professional-services.md)
- **Custom Development**: [Enterprise Solutions](mailto:enterprise@aitomatic.com)

---

## 📄 License

OpenDXA is released under the [MIT License](LICENSE.md).

---

<p align="center">
Copyright © 2024 Aitomatic, Inc. Licensed under the <a href="LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>