# Pipeline Examples

This directory contains examples demonstrating data pipeline and continuous execution patterns in the DXA framework.

## Learning Paths

### Core Concepts [Intermediate]

These examples demonstrate key pipeline concepts:

- [temperature_monitor.py](temperature_monitor.py): Data pipeline example
  - Processing streaming data
  - Continuous execution patterns
  - Sensor data analysis

## Key Concepts

### Pipeline Creation

```python
from dxa.execution.pipeline import Pipeline

# Create a pipeline
pipeline = Pipeline(name="data_processing")

# Add stages
pipeline.add_stage("read", read_function)
pipeline.add_stage("process", process_function)
pipeline.add_stage("store", store_function)
```

### Continuous Execution

```python
import asyncio
from dxa.common.graph.traversal import ContinuousTraversal

# Create a continuous traversal strategy
strategy = ContinuousTraversal(interval_seconds=5)

# Execute continuously
async def run_continuous():
    while True:
        await pipeline.execute(strategy=strategy)
        await asyncio.sleep(1)
```

### Data Transformation

```python
async def transform_data(data):
    # Process the data
    result = {
        "processed": data["raw"] * 2,
        "timestamp": data["timestamp"]
    }
    return result
```

## Related Concepts

- [Workflow Examples](../workflow/): How workflows can be used in pipelines
- [Resource Examples](../../resource/): Integrating external resources in pipelines

## Next Steps

After exploring these examples, consider:

1. Creating more complex data pipelines
2. Implementing error handling in pipelines
3. Exploring parallel data processing
4. Developing real-time monitoring systems 