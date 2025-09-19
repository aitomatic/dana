<div align="center">
  <img src="https://raw.githubusercontent.com/aitomatic/dana/release/docs/.archive/0804/images/dana-logo.jpg" alt="Dana Logo" width="80">
</div>

# Dana: The World’s First Agentic OS

## Build deterministic expert agent easily with Dana.
 

### A complete Expert Agent Development Toolkit: Agentic out of the box. Grounded in domain expertise.

---

## Why Dana?  

Most frameworks make you choose:  
- **Too rigid** → narrow, specialized agents.  
- **Too generic** → LLM wrappers that fail in production.  
- **Too much glue** → orchestration code everywhere.  

Dana gives you the missing foundation:

- **Deterministic** → flexible on input, consistent on output — reliable results every run.  
- **Contextual** → built-in memory and knowledge grounding let agents recall, adapt, and reason with domain expertise.  
- **Concurrent by default** → non-blocking execution; agents run tasks in parallel without threads or async code.  
- **Composable workflows** → chain simple steps into complex, reproducible processes that capture expert know-how.  
- **Local** → runs on your laptop or secure environments, ensuring privacy, speed, and mission-critical deployment.  
- **Robust** → fault-tolerant by design, agents recover gracefully from errors and edge cases.  
- **Adaptive** → agents learn from feedback and evolving conditions, improving performance over time.
  

---

## Install and Launch Dana 

💡 **Tip:** Always activate your virtual environment before running or installing anything for Dana.

```bash
# Activate your virtual environment (recommended)
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

pip install dana
dana studio # Launch Dana Agent Studio
dana repl # Launch Dana Repl
```

- For detailed setup (Python versions, OS quirks, IDE integration), see [Tech Setup](https://github.com/aitomatic/dana/blob/release/docs/tech-setup.md).

---

## What’s Included in v0.5  

### Agent Studio
Turn a problem statement into a draft expert agent with three parts — agent, resources, workflows. Studio generates a best-match workflow and lets you extend it with resources (documents, generated knowledge, web search) or edit workflows directly.

### Agent-Native Programming Language
A Python-like `.na` language with a built-in runtime that provides agentic behaviors out of the box — concurrency, knowledge grounding, and deterministic execution — so you don’t have to wire these up yourself.

What this means for you: You can build and iterate on expert agents faster, with less setup and more confidence they’ll run reliably in production.

Full release notes → [v0.5 Release](https://github.com/aitomatic/dana/blob/release/docs/releases/v0.5.md).

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

 

---

## Learn More  

- [Core Concepts](https://github.com/aitomatic/dana/blob/release/docs/core-concepts.md) → Agents, Resources, Workflows, Studio.
- [Reference](https://github.com/aitomatic/dana/blob/release/docs/reference/language.md) → Language syntax and semantics.
- [Primers](https://github.com/aitomatic/dana/tree/release/docs/primers) → Deep dives into Dana language design.

---

## Community  
- 🐞 [Issues](https://github.com/aitomatic/dana/issues)  
- 💬 [Discuss on Discord](https://discord.gg/dana)  

## Enterprise support
- [Contact Aitomatic Sales](mailto:sales@aitomatic.com)  

---

## License  

Dana is released under the [MIT License](https://github.com/aitomatic/dana/blob/release/LICENSE.md).  
© 2025 Aitomatic, Inc.  
