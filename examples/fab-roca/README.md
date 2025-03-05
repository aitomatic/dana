# Fab-ROCA Examples

This directory contains domain-specific examples demonstrating the application of DXA to semiconductor manufacturing use cases, specifically for Fab Remote Operations and Control Automation (ROCA).

## Learning Paths

### Real-World Applications [Advanced]

These examples demonstrate advanced, domain-specific applications:

- [rie_monitoring.py](rie_monitoring.py): Semiconductor manufacturing use case
  - Domain-specific workflows
  - Integration with external systems
  - Reactive Ion Etching (RIE) monitoring

## Subdirectories

- [knowledge/](knowledge/): Domain knowledge and configuration
  - Diagnosis parameters
  - Workflow definitions
- [resources/](resources/): Domain-specific resources
  - Mock FDC (Fault Detection and Classification) system

## Key Concepts

### Domain Knowledge Integration

```python
import yaml
from pathlib import Path

# Load domain knowledge
knowledge_dir = Path(__file__).parent / "knowledge"
with open(knowledge_dir / "diagnosis/parameters.yaml") as f:
    parameters = yaml.safe_load(f)
```

### Specialized Workflows

```python
from dxa.core.workflow import WorkflowFactory

# Create a domain-specific workflow
workflow = WorkflowFactory.create_from_config(
    "rie_monitoring",
    config_path=knowledge_dir / "workflows/monitoring.yaml"
)
```

### External System Integration

```python
from resources.mock_fdc import MockFDC

# Create and configure domain resource
fdc = MockFDC(config={
    "data_path": "path/to/data",
    "sampling_rate": 1.0
})

# Add to agent
agent.with_resources({"fdc": fdc})
```

## Related Concepts

- [Workflow Examples](../execution/workflow/): General workflow patterns
- [Resource Examples](../resource/): Resource management and integration

## Next Steps

After exploring these examples, consider:

1. Adapting the patterns to other domains
2. Extending the monitoring capabilities
3. Implementing more sophisticated diagnosis algorithms
4. Creating real-time visualization of monitoring data 