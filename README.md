<div align="center">
  <img src="docs/.archive/0804/images/dana-logo.jpg" alt="Dana Logo" width="80">
</div>

# Dana: The World’s First Agentic OS  

## Out-of-the-box Expert Agent Development. From idea to deployment. Deterministic and grounded in your domain knowledge.

---

## Why Dana?  

Most frameworks make you choose:  
- **Too rigid** → narrow, specialized agents.  
- **Too generic** → LLM wrappers that fail in production.  
- **Too much glue** → orchestration code everywhere.  

Dana gives you the missing foundation:  
- **Deterministic** → reproducible results you can trust.  
- **Contextual** → memory and knowledge grounding built in.  
- **Concurrent** → parallel by default, no async headaches.  
- **Composed** → workflows as first-class, not bolted on.  
- **Local-first** → runs entirely on your laptop, private and fast.  

---

## Install and launch Dana 

💡 **Tip:** Always activate your virtual environment before running or installing anything for Dana.

```bash
# Activate your virtual environment (recommended)
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

pip install dana
dana studio #Launch Dana Agent Studio
dana repl #Launch Dana Repl
```

- For detailed setup (Python versions, OS quirks, IDE integration), see [Install Guide](docs/install.md).  
- To build from source or set up development, see [Tech Setup](docs/tech-setup.md).  

---

## What’s Included in v0.5  

- **Dana Agent Studio** → Browser app (`dana studio`) to create, test, and deploy agents with visual workflows and a chat UI.  
- **Dana Agent-Native Programming Language** → Python-like `.na` language with built-in runtime for deterministic, concurrent, knowledge-grounded agents.  

Full release notes → [v0.5 Release](docs/releases/v0.5.md)  

---

## First Expert Agent in 4 Steps  

1. **Define an Agent**  
   ```dana
   agent RiskAdvisor
   ```  

2. **Add Resources**  
   ```dana
   resource_financial_docs = get_resources("rag", sources=["10-K.pdf", "Q2.xlsx"])
   ```  

3. **Follow an Expert Workflow**  
   ```dana
   def analyze(...): return ...
   def score(...): return ...  
   def recommend(...): return ...
   
   def wf_risk_check(resources) = analyze | score | recommend

   result = RiskAdvisor.solve("Identify liquidity risks", resources=[resource_financial_docs], workflows=[wf_risk_check])
   
   print(result)
   ```  

4. **Run or Deploy**  
   ```bash
   dana run my_agent.na       # Run locally
   dana deploy my_agent.na    # Deploy as REST API
   ```  

For a full walkthrough → [Quickstart Guide](docs/quickstart.md)  

---

## Learn More  

- [Core Concepts](docs/core-concepts.md) → Agents, Resources, Workflows, Studio.  
- [Cookbook](docs/cookbook/README.md) → Recipes for workflows, pipelines, error recovery, multi-agent chat.  
- [Reference](docs/reference/language.md) → Language syntax and semantics.  
- [Primers](docs/primers/README.md) → Optional deep dives into language design.  

---

## Community  

- 💬 [Discussions](https://github.com/aitomatic/dana/discussions)  
- 🐞 [Issues](https://github.com/aitomatic/dana/issues)  
- 🎙️ [Discord](https://discord.gg/dana)  

Enterprise support → [sales@aitomatic.com](mailto:sales@aitomatic.com)  

---

## License  

Dana is released under the [MIT License](LICENSE.md).  
© 2025 Aitomatic, Inc.  
