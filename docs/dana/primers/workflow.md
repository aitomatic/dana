# Workflow Primer

**What it is**: A workflow combines multiple functions into a single callable pipeline using Dana's `|` operator.

## Core Concept

```dana
# Individual functions
def load_data(source): return load(source)
def analyze_data(data): return analyze(data)
def create_report(analysis): return report(analysis)

# Create workflow
data_pipeline = load_data | analyze_data | create_report

# Call like any function
result = data_pipeline(data_source)
```

## Key Benefits

- **Natural composition**: Use familiar `|` operator
- **Single callable**: Workflow becomes one function
- **Enterprise features**: Add safety, validation, context via WorkflowEngine
- **Deterministic**: Consistent, reproducible results

## Simple Example

```dana
from dana.frameworks.workflow import WorkflowEngine, WorkflowStep

# Create steps with validation
steps = [
    WorkflowStep("extract", extract_text),
    WorkflowStep("analyze", analyze_content),
    WorkflowStep("report", generate_summary)
]

# Execute with orchestration
engine = WorkflowEngine()
result = engine.execute(steps, input_data)
```

**Bottom line**: Workflows turn function sequences into single, reliable, enterprise-ready pipelines. 