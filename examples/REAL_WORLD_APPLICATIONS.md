# Real-World Applications of DXA

This guide provides a structured learning path for exploring real-world applications of the DXA framework. These examples demonstrate how DXA can be applied to solve domain-specific problems.

## Learning Objectives

By the end of this learning path, you will be able to:
- Apply DXA to domain-specific problems
- Integrate with external systems and data sources
- Create specialized workflows for specific industries
- Build end-to-end applications

## Examples in this Learning Path

### 1. Semiconductor Manufacturing

Start with this example to understand how DXA can be applied to semiconductor manufacturing:

- [fab-roca/rie_monitoring.py](fab-roca/rie_monitoring.py): Semiconductor manufacturing use case
  - Domain-specific workflows
  - Integration with external systems
  - Reactive Ion Etching (RIE) monitoring

### 2. System Health Monitoring

Next, explore system health monitoring:

- [execution/workflow/system_health.py](execution/workflow/system_health.py): System monitoring example
  - Health check workflows
  - Monitoring and alerting patterns
  - System diagnostics

### 3. Temperature Monitoring

Learn about sensor data processing:

- [execution/pipeline/temperature_monitor.py](execution/pipeline/temperature_monitor.py): Data pipeline example
  - Processing streaming data
  - Continuous execution patterns
  - Sensor data analysis

## Suggested Learning Order

1. Start with [execution/pipeline/temperature_monitor.py](execution/pipeline/temperature_monitor.py) for a simple data processing example
2. Move to [execution/workflow/system_health.py](execution/workflow/system_health.py) to learn about system monitoring
3. Explore domain-specific applications with [fab-roca/rie_monitoring.py](fab-roca/rie_monitoring.py)

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

## Next Steps

After completing this learning path, you can:

1. Develop your own domain-specific applications
2. Contribute domain knowledge to the DXA framework
3. Create custom resources for specific industries
4. Build end-to-end solutions using DXA 