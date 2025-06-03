<!--
⚠️ IMPORTANT FOR AI CODE GENERATORS:
Always use colon notation for explicit scopes: `private:x`, `public:x`, `system:x`, `local:x`
NEVER use dot notation: `private.x`, `public.x`, etc.
Prefer using unscoped variables (auto-scoped to local) instead of explicit `private:` scope unless private scope is specifically needed.
-->

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

*First time using uv? See [Project Maintenance with uv](#-project-maintenance-with-uv) for essential commands.*

---

### Manual Setup (if you prefer)
1. Install [uv](https://astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Setup: `git clone https://github.com/aitomatic/opendxa.git && cd opendxa && uv sync`
3. Configure: `cp .env.example .env` (then add your API keys)
4. Run: `bin/dana` to start the Dana REPL

*New to uv? Check out [Project Maintenance with uv](#-project-maintenance-with-uv) for helpful commands.*

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
uv sync --extra dev

# Set up pre-commit hooks  
uv run pre-commit install

# Or use the convenience script
uv run setup-dev
```

### Available Development Scripts

With uv, you can use convenient scripts for common tasks:

```bash
# Testing
uv run test           # Run all tests
uv run test-fast      # Run fast tests only
uv run test-cov       # Run tests with coverage

# Code Quality  
uv run lint           # Check code with ruff
uv run format         # Format code with black
uv run check          # Run all quality checks
uv run fix            # Auto-fix formatting and linting
```

Or use the Makefile for traditional commands:
```bash
make help            # Show all available commands
make dev             # Complete development setup
make test            # Run tests
make check           # Code quality checks
```

This ensures code quality checks run automatically on commit, including:
- Code formatting with Ruff
- Linting with Ruff (including undefined attributes/methods)
- Basic file checks (trailing whitespace, merge conflicts, etc.)

---

## 🔧 Project Maintenance with uv

*New to uv? This section covers essential commands for maintaining the OpenDXA project.*

### 📦 Dependency Management

```bash
# Add a new dependency
uv add package-name                    # Production dependency
uv add --dev package-name             # Development-only dependency
uv add "package-name>=1.0,<2.0"      # With version constraints

# Remove dependencies
uv remove package-name                 # Remove from pyproject.toml and uv.lock
uv remove --dev package-name          # Remove dev dependency

# Update dependencies
uv sync                               # Install/sync to match uv.lock exactly
uv lock --upgrade                     # Update uv.lock to latest versions
uv sync --extra dev                   # Sync with development dependencies
```

### 🐍 Python Environment Management

```bash
# Python version management
uv python install 3.12               # Install Python 3.12
uv python list                       # List available Python versions
uv run python --version              # Check current Python version

# Virtual environment
uv venv                              # Create .venv (done automatically)
uv venv --python 3.12                # Create with specific Python version
source .venv/bin/activate            # Activate manually (rarely needed)
```

### 🏃‍♂️ Running Commands

```bash
# Run commands in the uv environment
uv run python script.py              # Run Python scripts
uv run pytest                       # Run tests
uv run dana                          # Start Dana REPL

# Use predefined scripts (see pyproject.toml [tool.uv.scripts])
uv run test                          # Equivalent to: uv run pytest tests/
uv run lint                          # Equivalent to: uv run ruff check .
uv run format                        # Equivalent to: uv run black .
```

### 🔄 Common Workflows

```bash
# Daily development workflow
uv sync                              # Sync dependencies
uv run test-fast                     # Run quick tests
uv run check                         # Code quality checks

# Adding a new feature
uv add new-package                   # Add new dependency
uv run test                          # Run full test suite
uv run fix                           # Auto-fix code issues

# Updating the project
git pull                             # Get latest changes
uv sync                              # Sync to new dependencies
uv run test-fast                     # Verify everything works
```

### 🆚 uv vs pip/virtualenv Cheat Sheet

| Task | Old Way (pip/venv) | New Way (uv) |
|------|-------------------|-------------|
| Create environment | `python -m venv .venv` | `uv venv` (automatic) |
| Activate environment | `source .venv/bin/activate` | Not needed with `uv run` |
| Install dependencies | `pip install -r requirements.txt` | `uv sync` |
| Add dependency | `pip install package && pip freeze > requirements.txt` | `uv add package` |
| Run script | `python script.py` | `uv run python script.py` |
| Run tests | `pytest` | `uv run pytest` |

### 🚨 Troubleshooting Tips

**"Command not found: uv"**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or: pip install uv
```

**"Python version not found"**
```bash
uv python install 3.12              # Install missing Python version
uv python list                      # Check available versions
```

**"Dependencies out of sync"**
```bash
uv sync --reinstall                 # Reinstall all dependencies
uv lock --upgrade                   # Update lock file
```

**"Can't find module after adding dependency"**
```bash
uv sync                             # Ensure dependencies are installed
uv run python -c "import module"   # Test import with uv run
```

### 💡 Pro Tips

- **Always use `uv run`** for commands instead of activating the virtual environment
- **Use `uv sync`** regularly to stay in sync with `uv.lock`
- **Add dependencies with `uv add`** instead of editing `pyproject.toml` manually
- **Use `make` commands** for complex workflows (they use uv internally)
- **Check `pyproject.toml [tool.uv.scripts]`** for available shortcuts

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
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>