<div align="center">
  <img src="https://raw.githubusercontent.com/aitomatic/dana/release/docs/.archive/0804/images/dana-logo.jpg" alt="Dana Logo" width="80">
</div>

# Dana: The Cognitive Ontology Platform

Dana is a **Cognitive Ontology** platform focused on **MapMaking**: capturing, organizing, and continuously improving enterprise knowledge into a living map of how things actually work.

Most AI systems excel at **MapUsing** (See–Think–Act)—navigating existing knowledge to complete tasks. Dana specializes in the harder problem: **Curate–Organize–Reflect**—creating, maintaining, and evolving the map itself.

Dana doesn't replace your existing AI stack—it powers it. We build the cognitive map that other AIs navigate.

> **Why does this matter?** Read the [Manifesto](MANIFESTO.md) for the business case: the $3.1 trillion knowledge problem and how Cognitive Ontology solves it.

---

## What Is Cognitive Ontology?

A **Cognitive Ontology** is a living knowledge graph that captures not just *what* your enterprise knows, but *how* things connect and *why* decisions get made.

Unlike traditional knowledge graphs (which require humans to build and maintain them), a Cognitive Ontology is built and evolved *automatically* by intelligent agents—extracting knowledge from documents, learning from experts, and improving continuously.

**What lives in the ontology:**
- Procedures and the reasoning behind them
- Decisions and their causal links
- Entities, roles, dependencies, and outcomes
- Lessons learned from incidents and operations

It's not just "how to do things"—it's *why*, *where*, *when*, and *what happens next*.

---

## MapMaking vs. MapUsing

This is Dana's core positioning:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   MAPMAKING (Dana)                        MAPUSING (Other AI)               │
│   ────────────────                        ─────────────────                 │
│                                                                             │
│   ┌──────────┐                            ┌──────────┐                      │
│   │  CURATE  │  Extract knowledge         │   SEE    │  Perceive situation  │
│   └────┬─────┘  from docs & experts       └────┬─────┘                      │
│        │                                       │                            │
│        ▼                                       ▼                            │
│   ┌──────────┐                            ┌──────────┐                      │
│   │ ORGANIZE │  Structure into            │  THINK   │  Reason & decide     │
│   └────┬─────┘  causal relationships      └────┬─────┘                      │
│        │                                       │                            │
│        ▼                                       ▼                            │
│   ┌──────────┐                            ┌──────────┐                      │
│   │ REFLECT  │  Learn & improve           │   ACT    │  Execute action      │
│   └──────────┘  the map                   └──────────┘                      │
│                                                                             │
│   Creates the map <─────────────────────────────────▶  Navigates the map    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**MapUsing** is what ChatGPT, copilots, and most AI agents do: they navigate existing knowledge (or hallucinate when the map doesn't exist).

**MapMaking** is the unsolved problem: turning scattered documents, expert judgment, workflows, and operational data into a structured, causal, navigable knowledge graph.

Dana solves MapMaking. Your AI agents handle MapUsing—but now they have a real map to navigate.

---

## COSTAR: The Complete Methodology

The full **COSTAR** lifecycle spans both MapMaking and MapUsing:

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│                       COSTAR: THE COMPLETE CYCLE                       │
│                                                                        │
│  MAPMAKING (Dana)              COGNITIVE              MAPUSING (AI)    │
│  Build the map                 ONTOLOGY               Navigate the map │
│                                                                        │
│  ┌──────────┐           ┌───────────────┐          ┌──────────┐        │
│  │  CURATE  │──────────▶│               │─────────▶│   SEE    │        │
│  └──────────┘  extract  │    Domain     │  context └────┬─────┘        │
│       │       knowledge │   Knowledge   │               │              │
│       ▼                 │     Graph     │               ▼              │
│  ┌──────────┐           │               │          ┌──────────┐        │
│  │ ORGANIZE │──────────▶│  ┌─────────┐  │          │  THINK   │        │
│  └──────────┘ structure │  │ Entity  │  │          └────┬─────┘        │
│       │                 │  ├─────────┤  │               │              │
│       │                 │  │ Entity  │  │               ▼              │
│       │                 │  ├─────────┤  │          ┌──────────┐        │
│       │                 │  │ Entity  │  │◀─────────│   ACT    │        │
│       │                 │  └─────────┘  │  results └────┬─────┘        │
│       │                 │ Causal Links  │               │              │
│       ▼                 └───────────────┘               │              │
│  ┌──────────┐                  ▲                        │              │
│  │ REFLECT  │◀─────────────────┴────────────────────────┘              │
│  └──────────┘                feedback                                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

| Phase | What Happens | The Outcome |
|-------|--------------|-------------|
| **Curate** | Extract knowledge from documents, experts, operations | Expertise that lived in heads becomes accessible |
| **Organize** | Structure into causal and contextual relationships | Agents understand *why*, not just *what* |
| **See** | Perceive situations through accumulated expertise | Anomalies detected that humans would miss |
| **Think** | Reason with domain knowledge, not just patterns | Diagnoses in minutes, not days |
| **Act** | Execute with encoded institutional judgment | Decisions made at 3 AM without waiting for experts |
| **Reflect** | Learn from outcomes, improve the ontology | Every action makes the system smarter |

**Dana's focus:** Curate–Organize–Reflect (MapMaking)

**Your AI agents:** See–Think–Act (MapUsing)

**The result:** A compounding knowledge asset that any downstream system can use.

---

## Architecture

```
dana/
├── dana_lang/      # Language runtime & COSTAR frameworks
├── dana_agent/     # COSTAR agent implementation
├── dana_studio/    # Visual agent builder
├── dana/           # Contrib modules
├── examples/       # Ready-to-run examples
├── tests/          # Test suites
├── docs/           # Documentation
└── bin/            # CLI tools & scripts
```

### Core Components

- **dana_lang** — The language runtime for defining ontology schemas, knowledge extraction rules, and agent behaviors
- **dana_agent** — COSTAR agent implementation for both MapMaking (knowledge agents) and MapUsing (task agents)
- **dana_studio** — Visual builder for designing agents, inspecting the ontology, and monitoring operations

---

## Get Started

### Installation

```bash
pip install dana
```

### Quick Start

```bash
dana studio
```

### Basic Usage

```python
from adana.core.agent import STARAgent

# Create an agent grounded in your domain knowledge
agent = STARAgent(agent_type="operations_expert")

# Point it at your knowledge sources
agent.with_resources(
    rag_resource("./procedures"),
    rag_resource("./incident_reports"),
    rag_resource("./equipment_manuals")
)

# The agent monitors, reasons, and acts autonomously
agent.on_event("sensor_anomaly", handler=lambda e: agent.diagnose_and_respond(e))
```

### What Happens

When furnace #3 shows temperature drift at 2:47 AM:

1. Agent correlates with similar patterns from 2019 incident IR-2019-0847
2. Identifies root cause: failing thermocouple (not heater element)
3. Initiates controlled cooldown per SOP-HT-003 emergency procedures
4. Pages on-call engineer with diagnosis and recommended action
5. Logs decision rationale for continuous learning

**Result:** Problem contained in 4 minutes. Previously took 2+ hours of expert diagnosis—if someone was awake to notice.

---

## Documentation

- [Quick Start Guide](docs/quickstart.md) — Running in 5 minutes
- [Core Concepts](docs/core-concepts.md) — Deep dive into COSTAR and Cognitive Ontology
- [API Reference](docs/api.md) — Complete API documentation
- [Enterprise Deployment](docs/enterprise.md) — Scaling to production

---

## How Dana Compares

| Approach | What It Does | Limitation |
|----------|--------------|------------|
| **RAG** | Retrieves relevant documents | No understanding of relationships or causality |
| **Knowledge Graphs** | Structures entities and relationships | Requires manual construction and maintenance |
| **Fine-tuned LLMs** | Encodes knowledge in weights | Static, expensive to update, not auditable |
| **Agent Frameworks** | Orchestrates LLM actions | Assumes knowledge exists; doesn't create it |
| **Dana** | Automatically builds and evolves a cognitive ontology | — |

Dana is infrastructure, not application. We create the knowledge layer that makes all the above approaches work better.

---

## Community

- [GitHub Issues](https://github.com/aitomatic/dana/issues) — Report bugs, request features
- [Discord](https://discord.gg/dana) — Join the community
- [Contributing](CONTRIBUTING.md) — How to contribute

## Enterprise

Building something mission-critical? [Talk to us](mailto:sales@aitomatic.com).

---

<p align="center">
<strong>Dana: Where Enterprise Knowledge Becomes Immortal</strong>
</p>

<p align="center">
© 2025 Aitomatic, Inc. · <a href="LICENSE.md">MIT License</a>
</p>
