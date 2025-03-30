<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>
<!-- markdownlint-enable MD033 -->

# DXA Documentation

Complete documentation for the DXA framework.

## Structure

- **requirements/**: Domain-specific requirements documentation
- **dxa.html**: API reference HTML documentation
- **README.md**: Framework overview and getting started guide

## Documentation

The primary documentation for the DXA framework is organized in several layers:

1. **Framework Overview**
   - Main README.md - High-level overview and getting started
   - dxa/README.md - Detailed system architecture
   - examples/README.md - Usage patterns and tutorials

2. **Component Documentation**
   - Each module has its own README.md
   - Code is documented with comprehensive docstrings
   - Examples demonstrate usage patterns

3. **API Reference**
   - Generated HTML documentation (dxa.html)
   - Type hints and docstrings
   - Usage examples

```bash
# View framework overview
cat README.md

# View system architecture
cat dxa/README.md

# View component documentation
cat dxa/agent/README.md
cat dxa/execution/workflow/README.md
```

## System Documentation

- [Agent System](../dxa/agent/README.md)
  - [Core Components](../dxa/agent/README.md#core-components)
  - [Capabilities](../dxa/agent/capability/README.md)
  - [Resources](../dxa/agent/resource/README.md)
  - [IO System](../dxa/agent/io/README.md)
  - [State System](../dxa/agent/state/README.md)

- [Execution System](../dxa/execution/README.md)
  - [Workflow Layer](../dxa/execution/workflow/README.md)
  - [Planning Layer](../dxa/execution/planning/README.md)
  - [Reasoning Layer](../dxa/execution/reasoning/README.md)
  - [Pipeline Layer](../dxa/execution/pipeline/README.md)

- [Common Utilities](../dxa/common/README.md)
  - [Logging](../dxa/common/utils/logging.py)
  - [Graph Utilities](../dxa/common/graph.py)

### Process Automation

The DXA Workflow system provides powerful process automation capabilities:

1. **Workflow Management**
   - Define complex workflows
   - Manage dependencies
   - Handle data flow
   - Track execution state

2. **Planning and Reasoning**
   - Strategic decomposition
   - Tactical execution
   - Dynamic adaptation
   - Progress monitoring

3. **Integration Features**
   - External system integration
   - Resource management
   - State persistence
   - Error handling

See [Workflow Documentation](../dxa/execution/workflow/README.md) for details.
