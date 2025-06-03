# OpenDXA - Domain-Expert Agent Framework

> OpenDXA is a comprehensive framework for easily coding and deploying domain-expert multi-agent systems.

> Powered by Dana, a Pythonic agentic programming language and secure sandboxed runtime.
---
## TL;DR - Get Running in 30 Seconds! 🚀
### One-Command Setup
```bash
git clone https://github.com/aitomatic/opendxa.git && cd opendxa && make
```
This installs everything and creates your `.env` file. Then just:
1. Add your API key to `.env` 
2. Run `bin/dana` to start the Dana REPL (interactive shell)

*First time using uv? See [Project Maintenance with uv](#project-maintenance-with-uv) for essential commands.*

---

### Manual Setup (if you prefer)
1. Install [uv](https://astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Setup: `git clone https://github.com/aitomatic/opendxa.git && cd opendxa && uv sync`
3. Configure: `cp .env.example .env` (then add your API keys)
4. Run: `bin/dana` to start the Dana REPL

*New to uv? Check out [Project Maintenance with uv](#project-maintenance-with-uv) for helpful commands.*

---

## 🎯 Choose Your Path

### 🛠️ I want to build with OpenDXA
→ **[For Engineers](docs/for-engineers/README.md)** - Practical guides, recipes, and references  
*Perfect for developers who want to get working quickly*

**What you'll find:**
- 5-minute setup and first agent tutorial
- Complete Dana language reference and REPL guide
- Real-world recipes for chatbots, document processing, and workflows
- Troubleshooting guides and error references

**Start here:** [Quick Start Guide](docs/for-engineers/README.md#quick-start)

---

### 🔍 I'm evaluating OpenDXA for my team
→ **[For Evaluators](docs/for-evaluators/README.md)** - Comparisons, ROI analysis, and proof of concepts  
*Perfect for technical leads and decision makers*

**What you'll find:**
- ROI calculator and competitive analysis
- Risk assessment and technical evaluation frameworks
- Proof of concept guides and adoption strategies
- Decision frameworks and implementation roadmaps

**Start here:** [30-Second Assessment](docs/for-evaluators/README.md#quick-evaluation-framework)

---

### 🏗️ I want to contribute or extend OpenDXA
→ **[For Contributors](docs/for-contributors/README.md)** - Architecture, codebase, and development guides  
*Perfect for developers who want to modify or extend the system*

**What you'll find:**
- Complete architecture deep dive and codebase navigation
- Development environment setup and contribution guidelines
- Extension development for capabilities and resources
- Testing frameworks and documentation standards

**Start here:** [Development Setup](docs/for-contributors/README.md#quick-start-for-contributors)

---

### 🧠 I want to understand the philosophy and theory
→ **[For Researchers](docs/for-researchers/README.md)** - Manifesto, theory, and academic context  
*Perfect for researchers and those interested in the theoretical foundations*

**What you'll find:**
- Dana manifesto and neurosymbolic computing foundations
- Research opportunities and collaboration frameworks
- Theoretical analysis and future research directions
- Academic partnerships and publication opportunities

**Start here:** [Research Overview](docs/for-researchers/README.md#research-overview)

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
- **New to AI development**: [Engineers Quick Start](docs/for-engineers/README.md#quick-start)
- **Experienced with LLMs**: [Migration Guide](docs/for-engineers/setup/migration-guide.md)
- **Need specific examples**: [Recipe Collection](docs/for-engineers/recipes/README.md)
- **Dana language reference**: [Syntax Guide](docs/for-engineers/reference/dana-syntax.md)

### 📊 Business Evaluation
- **ROI Analysis**: [Cost-Benefit Calculator](docs/for-evaluators/roi-analysis/calculator.md)
- **Technical Assessment**: [Architecture Overview](docs/for-evaluators/comparison/technical-overview.md)
- **Proof of Concept**: [Evaluation Guide](docs/for-evaluators/proof-of-concept/evaluation-guide.md)
- **Competitive Analysis**: [Framework Comparison](docs/for-evaluators/comparison/README.md)

### 🔬 Research & Development
- **[DANA: Domain-Aware Neurosymbolic Agents for Consistency and Accuracy](https://arxiv.org/abs/2410.02823)**. *V. Luong, S. Dinh, S. Raghavan, et al.* (arXiv:2410.02823) - This paper introduces DANA (Domain-Aware Neurosymbolic Agent), an architecture that addresses inconsistency and inaccuracy in LLMs by integrating domain-specific knowledge with neurosymbolic approaches. [[DOI](https://doi.org/10.48550/arXiv.2410.02823)]
- **Theoretical Foundations**: [Dana Manifesto](docs/for-researchers/manifesto/vision.md)
- **Neurosymbolic Computing**: [Research Opportunities](docs/for-researchers/README.md#research-opportunities)
- **Academic Collaboration**: [Partnership Programs](docs/for-researchers/README.md#academic-collaboration)
- **Original Documentation**: [Archive](docs/archive/README.md)

### 🛠️ Platform Extension
- **Custom Capabilities**: [Extension Development](docs/for-contributors/extending/extension-development.md)
- **Core Contributions**: [Contribution Guide](docs/for-contributors/development/contribution-guide.md)
- **Architecture Understanding**: [System Design](docs/for-contributors/architecture/system-design.md)
- **Codebase Navigation**: [Code Guide](docs/for-contributors/codebase/README.md)

---

## 🌟 Why OpenDXA?

OpenDXA stands out by enabling truly expert agents grounded in specific domain knowledge:

- **🏢 Leverage Existing Knowledge** - Tap into your company's documents, databases, and expertise
- **🎓 Embed Deep Domain Expertise** - Create reliable agents that understand your specialized processes
- **🔄 Adaptive Knowledge Management** - Manage the full lifecycle as your knowledge evolves
- **🌐 True Interoperability** - Seamlessly connect agents and systems based on different standards

---

## 🛠️ Development Setup

This project uses `uv` for managing dependencies and running development tasks.

### Initial Setup

1.  **Install uv**: If you haven't already, install uv:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
2.  **Clone the repository**:
    ```bash
    git clone https://github.com/aitomatic/opendxa.git
    cd opendxa
    ```
3.  **Sync dependencies**:
    ```bash
    # Install all dependencies, including optional 'dev' and 'docs' groups
    uv sync --extra dev --extra docs
    ```
4.  **Configure environment**:
    ```bash
    cp .env.example .env
    # Then, add your API keys to .env
    ```
5.  **Set up pre-commit hooks**:
    ```bash
    uv run pre-commit install
    ```

### Common Development Tasks

The following `uv run` commands are available for common development workflows. These are direct commands as native task runner support in `uv` is evolving.

#### Testing Workflows
```bash
# Run all tests
uv run pytest tests/

# Fast tests only (excluding 'live' and 'deep' tests)
uv run pytest -m 'not live and not deep' tests/

# Live/integration tests only
uv run pytest -m 'live' tests/

# Run tests with coverage report
uv run pytest --cov=opendxa --cov-report=html tests/
```

#### Code Quality Workflows
```bash
# Lint code
uv run ruff check .

# Lint and auto-fix
uv run ruff check --fix .

# Format code
uv run black .

# Check formatting
uv run black --check .

# Type checking
uv run mypy .
```

#### Documentation Workflows (for DevRel team)
```bash
# Live preview during writing
uv run python -m mkdocs serve

# Live preview (remote accessible)
uv run python -m mkdocs serve --dev-addr=0.0.0.0:8000

# Build docs
uv run python -m mkdocs build

# Build with warnings as errors
uv run python -m mkdocs build --strict
```

#### Deploying to GitHub Pages
To deploy the documentation to GitHub Pages, ensure your `mkdocs.yml` is configured correctly for the GitHub Pages repository and then run:

```bash
# Build and deploy to GitHub Pages
uv run mkdocs gh-deploy --force
```
Make sure you have the necessary permissions to push to the `gh-pages` branch of your repository.

#### Documentation Validation (Catch Staleness)
```bash
# Test code examples in docstrings
uv run pytest --doctest-modules opendxa/

# Check all markdown links (fast async)
uv run python -m linkcheckmd docs/

# Documentation style checking
uv run doc8 docs/

# Validate complete build (same as build --strict)
uv run python -m mkdocs build --strict
```

#### Dana-Specific Commands
```bash
# Run a Dana script
uv run python -m opendxa.dana.exec.dana examples/dana/debug_tests/test_basic.na

# Start the Dana REPL
uv run python -m opendxa.dana.exec.repl.repl
```

---

## 🛠️ Project Maintenance with uv

`uv` is also used for managing project dependencies. Here are some essential commands:

### Environment Management
```bash
# Sync dependencies with pyproject.toml (installs new, removes unused)
uv sync

# Sync with development dependencies
uv sync --extra dev

# Sync with documentation tool dependencies
uv sync --extra docs

# Sync with all optional dependencies
uv sync --extra dev --extra docs

# Add a new production dependency
uv add <package_name>

# Add a new development dependency
uv add --group dev <package_name>

# Remove a dependency
uv remove <package_name>
```
The `pyproject.toml` also mentions `[project.optional-dependencies]` for `dev` and `docs`.
Make sure these are covered when syncing.

---

## 📞 Community & Support

### 💬 Get Help
- **Technical Questions**: [GitHub Discussions](https://github.com/aitomatic/opendxa/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/aitomatic/opendxa/issues)
- **Real-time Chat**: [Discord Community](https://discord.gg/opendxa)

### 🤝 Get Involved
- **Contribute Code**: [Contribution Guidelines](docs/for-contributors/development/contribution-guide.md)
- **Share Examples**: [Community Recipes](docs/for-engineers/recipes/)
- **Research Collaboration**: [Academic Partnerships](docs/for-researchers/README.md#academic-collaboration)

### 🏢 Enterprise Support
- **Business Inquiries**: [Contact Sales](mailto:sales@aitomatic.com)
- **Professional Services**: [Implementation Support](docs/for-evaluators/adoption-guide/professional-services.md)
- **Custom Development**: [Enterprise Solutions](mailto:enterprise@aitomatic.com)

---

## 📄 License

OpenDXA is released under the [MIT License](LICENSE.md).

---

<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>