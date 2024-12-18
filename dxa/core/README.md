<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Core Modules

Core components that power the DXA agent system. For agent implementation details, see [Agent Documentation](../agent/README.md).

## Modules

### [Planning](planning/README.md)

Strategic layer that manages objectives and generates plans, providing the high-level control for agent behavior.

### [Reasoning](reasoning/README.md)

Tactical layer that implements different thinking patterns (Direct, CoT, OODA, DANA), handling the actual execution of plans.

### [Resource](resource/README.md)

Resource management system that provides access to tools, APIs, and capabilities that agents can use during execution.

### [Capability](capability/README.md)

Pluggable skills and abilities that can be dynamically added to agents to extend their functionality.

### [IO](io/README.md)

Input/Output handlers that manage agent interactions with users, systems, and the environment.

## Integration

These modules work together to create flexible, powerful agents:

- Planning decides what to do
- Reasoning determines how to think
- Resources provide tools to use
- Capabilities define what's possible
- IO manages interactions

See the [Agent Documentation](../agent/README.md) for how these components are integrated into a complete system.

---

<p align="center">
Copyright © 2024 Aitomatic, Inc. All rights reserved.
</p>

<p align="center">
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
