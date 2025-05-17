<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

[Project Overview](../README.md)

# DANA Manifesto

---

## A Common Pain Point

**The #1 pain point: Making AI-powered systems accurate, reliable, and easy to manage—without extra complexity.**

How do I get smart automation that gives the right answers, uses context, and doesn't become a complicated, fragile mess?

---

## A Simple DANA Program: Example

Here's a small DANA program. It checks if a machine is too hot and sends an alert if needed. It's short, clear, and does more than just follow rules—it can ask an AI for help.

```python
# Check if a machine is overheating and alert if necessary
if public:sensor.temperature > 100:
    analysis = reason("Is this overheating?", context=public:sensor)
    if analysis == "yes":
        system:alerts.append("Overheat detected on sensor: " + public:sensor.id)
    else:
        log.info("Temperature high, but not overheating.")
else:
    log.info("Temperature normal.")
```

**What this program shows:**
- **Uses context:** It looks at the latest sensor data.
- **Gets help from AI:** It asks, "Is this overheating?" and uses the answer.
- **Keeps things clear:** State and alerts are easy to see and track.
- **Easy to read:** The code is simple and looks like plain logic.

> **Note for AI Engineers:**
> With DANA, you don't need to build big graphs or set up complex tools. Just write what you want to happen, step by step. DANA keeps things simple, but lets you add smart features when you need them.

This example shows how DANA helps you automate smart decisions, using both code and AI, without the usual mess.

---

## Accuracy and Trust: Built In

DANA helps you get more accurate answers from AI, not just by giving you control, but by making many things automatic. DANA keeps track of context, checks confidence, and can retry or correct mistakes on its own. This means fewer "hallucinations" and more reliable results—whether you're answering questions from PDFs, making decisions, or running automations. You don't have to build all this yourself: DANA's runtime is designed to be fault-tolerant and context-aware, so your programs are smarter and safer by default.

---

## Problem

Modern AI systems are brittle, opaque, and fragmented:
- **Prompt chains are fragile** and hard to debug or maintain.
- **Plans are opaque**—difficult to inspect or explain mid-flight.
- **Tool use is scattered**—logic is buried in code, not in declarative, auditable programs.
- **State is implicit**—no shared memory or traceable updates.
- Symbolic systems are structured but inflexible; LLMs are creative but lack transparency.

---

## Vision

To create a universal, interpretable program format and runtime (DANA) that enables both humans and machines to reason, act, and collaborate through structured, auditable, and explainable programs. DANA bridges the gap between natural language objectives and tool-assisted, stateful action—making things "just work" intelligently, safely, and with minimal friction.

---

## Strategy

- **Programs as first-class reasoning artifacts:** DANA programs are concise, auditable, and can be authored by LLMs or domain experts.
- **Shared state containers:** Explicit, auditable memory scopes (`local`, `private`, `public`, `system`).
- **Reusable logic units:** Structured Knowledge Base (KB) for modular, composable logic.
- **Declarative goals, imperative execution:** Allow both high-level intent and precise control.
- **Bidirectional mapping:** Seamless translation between natural language and code.
- **Agentic collaboration:** Agents and tools can emit, interpret, and coordinate DANA programs.

---

## Tactics

- **Context & Intent Inference:** The system infers user intent and context, routing requests to the right agent or function, reducing boilerplate.
- **Fault-Tolerance & Confidence:** Automatic retries, error correction, and confidence assessment; "predict-and-error correct" as a core principle.
- **Agentic Collaboration & Dispatch:** The runtime knows agent capabilities, can parallelize or prioritize dispatch, and manages context.
- **Seamless User Experience:** DANA "just works" for natural language, code, variable/agent resolution, and error handling.
- **Security & Clarity:** Explicit defaults, explainable actions, and modular separation of concerns.
- **Extensibility & Composability:** Easy to extend with new features, tools, and AI models.
- **Human-Centric Design:** Prioritize user intent and control, but provide "magic" where it increases productivity and safety.

---

## Benefits & Implications

### 1. Simplicity and Productivity for the AI Engineer

DANA is designed for familiarity and ease of use, leveraging a Python-like syntax and a sandboxed runtime that manages state, context, and error handling automatically. Engineers benefit from built-in support services such as parsing, error catching, do-what-I-mean (DWIM) intent inference, error correction, and implicit context understanding. This dramatically reduces boilerplate, accelerates prototyping, and empowers engineers to focus on high-level logic rather than low-level plumbing.

### 2. Fault Tolerance AND Determinism—without Ambiguity OR Uncertainty

DANA's neurosymbolic architecture combines the adaptability of LLMs with the structure and determinism of symbolic systems. The runtime provides automatic retries, confidence assessment, and error correction, while maintaining auditable, step-by-step execution. This ensures that programs are both robust to uncertainty and precisely controllable, eliminating ambiguity and making outcomes explainable and repeatable.

### 3. DANA as the Universal Communication Language Between Agents

DANA is not just a tool for individual agents—it's a universal language for agentic collaboration. Agents can not only perform actions for each other, but also transfer knowledge, plans, and workflows in the form of DANA code. This enables agents (human or machine) to share, reuse, and build upon each other's expertise, creating a new paradigm for distributed intelligence and collaborative problem-solving.

## Domain-Aware Neurosymbolic Architecture

DANA brings together the best of two worlds: clear, rule-based logic (symbolic) and flexible, context-aware AI (neural). This means you can write programs that are easy to understand and audit, but also smart enough to handle real-world messiness. DANA lets you mix step-by-step instructions with AI-powered reasoning, so your automations are both accurate and adaptable. This approach helps you get reliable results, even when the task needs both rules and intelligence.

## Not Another Graph or Agent Framework

Many agent and automation platforms use graphs or node editors (like LangGraph), or require you to wire up agents and orchestrators (like Google ADK, Microsoft AutoGen). These can be powerful, but they often add a lot of complexity—even for simple tasks.

**How DANA is different:**
- **Code-first and minimal:** Just write what you want to happen, step by step, in clear code. No need to design or maintain graphs, nodes, or visual pipelines.
- **No extra overhead:** For most use cases, you don't need to learn a new paradigm or set up lots of configuration. DANA is as simple as a script, but can scale up when you need more.
- **Built-in agentic features:** Context, state, and agent collaboration are part of the language—not something you have to bolt on with extra tools or frameworks.
- **Easy to debug and maintain:** Logic and state are right in front of you, not hidden in a visual editor or spread across configs.
- **Grows with you:** Start with a simple automation, and scale up to multi-agent, collaborative workflows—without switching tools or rewriting everything.

DANA lets you focus on what your system should do, not how to wire up agents or manage orchestration. It's simple when you want it, powerful when you need it.

---

## Frequently Asked Questions & Critiques

### On Language and Abstraction

**Why not just natural language?**  
Natural language is powerful for expressing intent, but it is inherently ambiguous, context-dependent, and difficult to execute deterministically. While LLMs can interpret and act on natural language, the lack of structure makes it hard to audit, debug, or guarantee repeatable outcomes—especially in complex or safety-critical workflows. DANA provides a structured, auditable, and executable format that is still LLM-friendly, but removes ambiguity and enables robust automation, collaboration, and compliance. In short: natural language is great for intent, but DANA is needed for precision, safety, and repeatability.

**How is this different from having convenience libraries in Python?**  
While convenience libraries in Python can provide abstractions and helper functions, they are still bound by the semantics, error handling, and state management of general-purpose programming. DANA is a purpose-built language and runtime designed from the ground up for agentic, context-aware, and fault-tolerant execution. It enforces explicit state scopes, supports intent inference, and is designed to be both interpretable by machines and readable by humans/LLMs. The DANA runtime provides built-in mechanisms for context management, error correction, and agent collaboration that go beyond what typical Python libraries offer.

**Why do you need a whole new language?**  
Existing languages are not optimized for agentic reasoning, context inference, or collaborative tool use. DANA is designed to make intent, state, and agent collaboration first-class citizens. By creating a new language, we can enforce best practices, provide built-in support for agentic workflows, and ensure that programs are both interpretable and auditable. This also enables seamless translation between natural language and code, and between agents themselves.

---

### On Agents, Automation, and Collaboration

**What is "agentic" about this?**  
DANA is "agentic" because it is designed for systems (agents) that reason, act, and collaborate autonomously or semi-autonomously. The language and runtime make agent capabilities, state, and collaboration explicit. Agents can emit, interpret, and share DANA programs, enabling them to delegate, coordinate, and transfer knowledge in a way that is transparent and auditable. This is a step beyond simple automation or scripting—DANA is about enabling intelligent, context-aware, and collaborative behaviors among agents (human or machine).

**I don't need an "agent." I just need to automate things and use intelligent/AI services.**  
That's perfectly valid! DANA is designed to be useful even for simple automation and tool orchestration. You don't have to think in terms of "agents" to benefit from DANA's structured, context-aware, and fault-tolerant execution. The language is minimal and familiar, so you can use it for straightforward automation, but it also scales up to more complex, agentic workflows if and when you need them. Think of DANA as a spectrum: it's as simple or as powerful as your use case requires.

**DANA as the universal communication language between agents?**  
DANA enables agents to not only act for each other but also transfer knowledge, plans, and workflows as code—unlocking new forms of distributed intelligence and collaboration. This is a new paradigm: agents (human or machine) can share, reuse, and build upon each other's expertise in a transparent, auditable way.

---

### On Robustness, Overhead, and Suitability

**Is this robust enough for enterprise/industrial needs?**  
DANA is designed with enterprise and industrial robustness in mind. Its explicit state management, auditable execution, and fault-tolerant runtime are well-suited for environments where reliability, traceability, and compliance are critical. The sandboxed execution model ensures security and isolation, while the language's structure supports versioning, testing, and explainability—key requirements for enterprise adoption. Of course, as with any new technology, real-world validation and hardening are ongoing processes.

**Is this overkill for consumer/enterprise needs?**  
It depends on the use case. For very simple tasks, DANA might seem like "more than you need." But as soon as workflows become more complex, require collaboration, or need to be auditable and robust, the benefits of DANA's structure and runtime become clear. For enterprises, the ability to trace, audit, and control intelligent automation is often a necessity, not a luxury. For consumers, DANA's "just works" philosophy aims to make advanced automation accessible without requiring deep technical expertise. The goal is to provide a gentle on-ramp: simple when you want it, powerful when you need it.

**Will this add learning overhead for engineers?**  
There is some initial learning curve, but DANA is intentionally designed to be familiar (Python-like syntax) and minimal. The benefits in productivity, error reduction, and agentic collaboration are intended to outweigh the initial investment in learning the language.

---

### On Architecture and Execution

**Why do you need a whole sandbox?**  
The sandbox is essential for security, isolation, and robust execution. It ensures that code from various sources (including LLMs, users, and other agents) is executed safely, with controlled access to resources and state. The sandbox also provides a unified runtime pipeline for parsing, transforming, type-checking, and interpreting DANA code, enabling features like error correction, retries, and confidence assessment in a controlled environment.

**Isn't this just another layer of abstraction?**  
Yes, DANA is an abstraction—but it's a purposeful one. It abstracts away the boilerplate and complexity of agentic programming, while making intent, state, and collaboration explicit and auditable. The goal is to reduce friction, increase productivity, and enable new forms of agentic collaboration that are difficult to achieve with existing tools.

**How does DANA interoperate with existing tools and languages?**  
DANA is designed to be extensible and composable. It can call out to external tools, libraries, and APIs, and can be generated or consumed by LLMs and other agents. The goal is not to replace existing tools, but to provide a universal, auditable layer for agentic reasoning and collaboration.

---

## Illustrative Examples

### Context & Intent Inference

- `ai.get_time_of_day()`  
  Should just work, whether or not the function exists explicitly. The sandbox can infer intent and find the correct function or agent to call.
- `ai.plan_day_out("tomorrow")`  
  Should just work. The sandbox infers context (location, date, time, user preferences) and routes the request to the right agent or function.
- `some_var = ai.function("some prompt")`  
  Should just work. The sandbox maintains shared state, provides context, rewrites prompts, and ensures fault-tolerance (e.g., verifies up to 3 times, retries automatically until 95% confidence is reached).

### Fault-Tolerance & Confidence

- `while system.confidence < 95%: do()`  
  Should just work. The sandbox automatically prompts for confidence assessment from the LLM based on results and context, and manages retries or escalation as needed.

### Agentic Collaboration & Dispatch

- `with agent_x do: call_x(param_y)`  
  Should just work. The sandbox translates this to an agent call (e.g., `agent_x.call_x(param_y)`), handling context and dispatch.
- `with agent_x, agent_y, agent_z do: call_...`  
  Should just work. The sandbox knows what each agent can do, and can prioritize or parallelize dispatch based on context and agent capabilities.

### Seamless User Experience

- DANA should "just work" for:
  - Natural language prompts and code.
  - Contextual variable and agent resolution.
  - Automatic retries, error correction, and confidence assessment.
  - Shared state and context across statements and agents.

---

## Call to Action

DANA is a living experiment in agentic programming. We invite contributors, users, and AI assistants to help realize this vision—where the boundary between code, intent, and collaboration is as thin as possible, and where "just works" is the default, not the exception.

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p> 