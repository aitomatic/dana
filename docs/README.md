<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# DXA Documentation

Complete documentation for the DXA framework.

## Structure

- **api/**: API reference documentation
- **guides/**: User guides and tutorials
- **examples/**: Code examples and patterns
- **architecture/**: Design documentation

## Building Docs

```bash
# Install doc dependencies
pip install -r docs/requirements.txt

# Build documentation
make html
```

See individual sections for detailed information.

## System Documentation

- [Agent System](../dxa/agent/README.md)
- [Planning System](../dxa/core/planning/README.md)
- [Reasoning System](../dxa/core/reasoning/README.md)
- [Flow System](../dxa/flow/README.md)
- [Resource System](../dxa/core/resource/README.md)

### Process Automation

The DXA Flow system provides powerful process automation capabilities:

- Workflow automation
- SOP implementation
- Business process management
- RPA enhancement

See [Flow Documentation](../dxa/flow/README.md) for details.
