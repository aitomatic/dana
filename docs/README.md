<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Documentation

Complete documentation for the DXA framework.

## Structure

- **requirements/**: Domain-specific requirements documentation
- **dxa.html**: API reference HTML documentation

## Documentation

The primary documentation for the DXA framework is contained in README files within each module directory. The code itself is also extensively documented with docstrings.

```bash
# View framework overview
cat dxa/README.md

# View specific component documentation
cat dxa/agent/README.md
cat dxa/execution/workflow/README.md
```

See individual sections for detailed information.

## System Documentation

- [Agent System](../dxa/agent/README.md)
- [Execution System](../dxa/execution/README.md)
  - [Planning System](../dxa/execution/planning/README.md)
  - [Reasoning System](../dxa/execution/reasoning/README.md)
  - [Workflow System](../dxa/execution/workflow/README.md)
  - [Pipeline System](../dxa/execution/pipeline/README.md)
- [Resource System](../dxa/agent/resource/README.md)
- [Capability System](../dxa/agent/capability/README.md)

### Process Automation

The DXA Workflow system provides powerful process automation capabilities:

- Workflow automation
- SOP implementation
- Business process management
- RPA enhancement

See [Workflow Documentation](../dxa/execution/workflow/README.md) for details.
