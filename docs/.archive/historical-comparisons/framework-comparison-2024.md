<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
# OpenDXA Framework Comparison

## Strategic Framework Selection Matrix

OpenDXA provides distinct advantages in several key areas when compared to other agent frameworks:

| Use Case / Feature         | OpenDXA (Dana)         | LangChain / LangGraph      | AutoGPT / BabyAGI         | Google ADK                | Microsoft AutoGen         | CrewAI                    |
|---------------------------|------------------------|----------------------------|---------------------------|---------------------------|---------------------------|---------------------------|
| **Quick Start**           | ✨ Code-first, minimal  | Chain/graph construction   | Command interface         | Agent/workflow setup      | Agent conversation setup  | Crew/team config or YAML  |
| **Simple Tasks**          | ✨ Script-like, direct  | Chain composition          | Command sequences         | Agent definition required | Agent definition required | Crew/team abstraction     |
| **Complex Tasks**         | ✨ Scales up naturally  | Multi-chain/graph          | Command/task recursion    | Hierarchical agents, workflows | Multi-agent orchestration | Crews + Flows, orchestration |
| **Domain Expertise**      | ✨ Built-in, declarative| Tool integration           | Command-based tools       | Tool/connector ecosystem  | Tool integration, custom agents | Role-based agents, tools |
| **Autonomous Operation**  | ✨ Structured autonomy  | Chain/graph automation     | Free-form commands        | Multi-agent, delegation   | Multi-agent, async comms  | Autonomous crews, flows   |
| **Growth Path**           | ✨ Seamless, no rewrite | Chain/graph rebuild        | New commands/tasks        | Add agents, workflows     | Add agents, workflows     | Add agents, crews, flows  |
| **Interface/Abstraction** | ✨ Code, no graphs      | Graphs, nodes, chains      | CLI, config               | Orchestration, config     | Event-driven, agent chat  | YAML, visual builder      |
| **Agentic Features**      | ✨ Built-in, implicit   | Explicit, via chains/graphs| Explicit, via commands    | Explicit, via agent setup | Explicit, via agent setup | Explicit, via crew/team   |

✨ = Optimal choice for category

## Framework Selection Guide

| Need                | Best Choice         | Why |
|---------------------|--------------------|-----|
| Fast Start          | OpenDXA            | Code-first, minimal setup, grows with you |
| Simple Tasks        | OpenDXA            | Direct scripting, no orchestration needed |
| Complex Systems     | OpenDXA/ADK/AutoGen| Scales up to multi-agent, but OpenDXA stays simple |
| Expert Systems      | OpenDXA            | Native expertise, declarative knowledge   |
| Autonomous Agents   | OpenDXA/AutoGen    | Structured autonomy, easy debugging      |

## Implementation Complexity

| Framework           | Initial | Growth | Maintenance |
|---------------------|---------|--------|-------------|
| OpenDXA             | Low     | Linear | Low         |
| LangChain/LangGraph | Low     | Step   | Medium      |
| AutoGPT/BabyAGI     | Low     | Limited| High        |
| Google ADK          | Medium  | Step   | Medium      |
| Microsoft AutoGen   | Medium  | Step   | Medium      |
| CrewAI              | Medium  | Step   | Medium      |

---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
