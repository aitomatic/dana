<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# OpenDXA Documentation

*Choose your path to get started with OpenDXA - the transparent, reliable AI automation platform*

---

## 🎯 Choose Your Path

### 🛠️ I want to build with OpenDXA
→ **[For Engineers](for-engineers/)** - Practical guides, recipes, and references  
*Perfect for developers who want to get working quickly*

**What you'll find:**
- 5-minute setup and first agent tutorial
- Complete Dana language reference and REPL guide
- Real-world recipes for chatbots, document processing, and workflows
- Troubleshooting guides and error references

**Start here:** [Quick Start Guide](for-engineers/README.md#-quick-start)

---

### 🔍 I'm evaluating OpenDXA for my team
→ **[For Evaluators](for-evaluators/)** - Comparisons, ROI analysis, and proof of concepts  
*Perfect for technical leads and decision makers*

**What you'll find:**
- ROI calculator and competitive analysis
- Risk assessment and technical evaluation frameworks
- Proof of concept guides and adoption strategies
- Decision frameworks and implementation roadmaps

**Start here:** [30-Second Assessment](for-evaluators/README.md#-quick-evaluation-framework)

---

### 🏗️ I want to contribute or extend OpenDXA
→ **[For Contributors](for-contributors/)** - Architecture, codebase, and development guides  
*Perfect for developers who want to modify or extend the system*

**What you'll find:**
- Complete architecture deep dive and codebase navigation
- Development environment setup and contribution guidelines
- Extension development for capabilities and resources
- Testing frameworks and documentation standards

**Start here:** [Development Setup](for-contributors/README.md#-quick-start-for-contributors)

---

### 🧠 I want to understand the philosophy and theory
→ **[For Researchers](for-researchers/)** - Manifesto, theory, and academic context  
*Perfect for researchers and those interested in the theoretical foundations*

**What you'll find:**
- Dana manifesto and neurosymbolic computing foundations
- Research opportunities and collaboration frameworks
- Theoretical analysis and future research directions
- Academic partnerships and publication opportunities

**Start here:** [Research Overview](for-researchers/README.md#-research-overview)

---

## 🚀 What is OpenDXA?

OpenDXA transforms AI development from brittle, unpredictable systems to reliable, auditable automations. Built on the Dana language - a neurosymbolic programming environment - OpenDXA enables:

### ✨ Key Benefits
- **🔍 Transparent**: Every step is visible and debuggable
- **🛡️ Reliable**: Built-in verification and error correction  
- **⚡ Fast**: 10x faster development cycles
- **🤝 Collaborative**: Share and reuse working solutions

### 🎯 Core Innovation: Dana Language
```python
# Traditional AI: Opaque, brittle
result = llm_call("analyze data", context=data)

# Dana: Transparent, self-correcting
analysis = reason("analyze data", context=data)
while confidence(analysis) < high_confidence:
    analysis = reason("refine analysis", context=[data, analysis])
```

### 🏗️ Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│                      Agent Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Agent     │  │ Capabilities │  │     Resources       │ │
│  │ Management  │  │   System     │  │    Management       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Dana Execution Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    Parser   │  │ Interpreter │  │  Runtime Context    │ │
│  │   (AST)     │  │  (Executor) │  │  (State Manager)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Resource Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ LLM Resource│  │ Knowledge   │  │  External Tools     │ │
│  │ Integration │  │    Base     │  │   & Services        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Quick Navigation by Use Case

### 🤖 Building AI Agents
- **New to AI development**: [Engineers Quick Start](for-engineers/README.md#-quick-start)
- **Experienced with LLMs**: [Migration Guide](for-engineers/setup/migration-guide.md)
- **Need specific examples**: [Recipe Collection](for-engineers/recipes/)

### 📊 Business Evaluation
- **ROI Analysis**: [Cost-Benefit Calculator](for-evaluators/roi-analysis/calculator.md)
- **Technical Assessment**: [Architecture Overview](for-evaluators/comparison/technical-overview.md)
- **Proof of Concept**: [Evaluation Guide](for-evaluators/proof-of-concept/evaluation-guide.md)

### 🔬 Research & Development
- **Theoretical Foundations**: [Dana Manifesto](for-researchers/manifesto/vision.md)
- **Neurosymbolic Computing**: [Research Opportunities](for-researchers/README.md#-research-opportunities)
- **Academic Collaboration**: [Partnership Programs](for-researchers/README.md#-academic-collaboration)

### 🛠️ Platform Extension
- **Custom Capabilities**: [Extension Development](for-contributors/extending/extension-development.md)
- **Core Contributions**: [Contribution Guide](for-contributors/development/contribution-guide.md)
- **Architecture Understanding**: [System Design](for-contributors/architecture/system-design.md)

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

### 📚 Learn the Concepts
1. [What makes OpenDXA different](for-engineers/README.md#-what-makes-opendxa-different)
2. [Dana language basics](for-engineers/reference/dana-syntax.md)
3. [Agent architecture overview](for-contributors/architecture/system-design.md)

### 🎯 Solve Your Use Case
- [Document Processing](for-engineers/recipes/document-processor/)
- [API Integration](for-engineers/recipes/api-integration/)
- [Workflow Automation](for-engineers/recipes/workflow-agent/)
- [Chatbot Development](for-engineers/recipes/chatbot/)

---

## 📞 Community & Support

### 💬 Get Help
- **Technical Questions**: [GitHub Discussions](https://github.com/aitomatic/opendxa/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/aitomatic/opendxa/issues)
- **Real-time Chat**: [Discord Community](https://discord.gg/opendxa)

### 🤝 Get Involved
- **Contribute Code**: [Contribution Guidelines](for-contributors/development/contribution-guide.md)
- **Share Examples**: [Community Recipes](for-engineers/recipes/)
- **Research Collaboration**: [Academic Partnerships](for-researchers/README.md#-academic-collaboration)

### 🏢 Enterprise Support
- **Business Inquiries**: [Contact Sales](mailto:sales@aitomatic.com)
- **Professional Services**: [Implementation Support](for-evaluators/adoption-guide/professional-services.md)
- **Custom Development**: [Enterprise Solutions](mailto:enterprise@aitomatic.com)

---

## 📖 Documentation Structure

```
docs/
├── for-engineers/          # Practical development guides
│   ├── setup/             # Installation and configuration
│   ├── recipes/           # Real-world examples and patterns
│   ├── reference/         # Language and API documentation
│   └── troubleshooting/   # Common issues and solutions
├── for-evaluators/        # Business and technical evaluation
│   ├── comparison/        # Competitive analysis and positioning
│   ├── roi-analysis/      # Cost-benefit and ROI calculations
│   ├── proof-of-concept/  # Evaluation and testing guides
│   └── adoption-guide/    # Implementation and change management
├── for-contributors/      # Development and extension guides
│   ├── architecture/      # System design and implementation
│   ├── codebase/         # Code navigation and understanding
│   ├── extending/        # Building capabilities and resources
│   └── development/      # Contribution and testing guidelines
├── for-researchers/       # Theoretical and academic content
│   ├── manifesto/        # Vision and philosophical foundations
│   ├── neurosymbolic/    # Technical and theoretical analysis
│   ├── research/         # Research opportunities and collaboration
│   └── future-work/      # Roadmap and future directions
├── internal/             # Internal planning and requirements
└── archive/              # Historical documentation and references
```

---

*Ready to transform your AI development? Choose your path above and start building transparent, reliable AI automations with OpenDXA.*
