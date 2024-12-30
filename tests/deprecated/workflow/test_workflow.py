"""Tests for workflow creation and manipulation."""

from typing import List, cast
import time
import pytest
import yaml
from dxa.core.execution.execution_graph import ExecutionNodeType, ExecutionNode, ExecutionEdge
from dxa.core.workflow import (
    create_from_command,
    create_from_steps,
    create_from_natural_language,
    Workflow,
    create_from_yaml
)

@pytest.fixture
def simple_command() -> str:
    """Single task workflow text."""
    return "Download the data."

@pytest.fixture
def sequential_steps() -> List[str]:
    """Sequential steps workflow text."""
    return [
        "Load the dataset",
        "Clean the data",
        "Save results",
    ]

@pytest.fixture
def natural_language_workflow() -> str:
    """Complex workflow with decisions text."""
    return """
    First check if we have the latest data.
    If the data is outdated, download new data and verify its format.
    Otherwise, proceed with analysis.
    
    For the analysis:
    - Calculate basic statistics
    - Look for anomalies
    - Generate visualizations
    
    Finally, compile everything into a report.
    """

# pylint: disable=redefined-outer-name
def test_single_command(simple_command):
    """Test converting a single command to workflow."""
    start_time = time.time()
    
    workflow = create_from_command(simple_command)
    assert isinstance(workflow, Workflow)
    assert len(workflow.nodes) == 3  # START, task, END
    assert len(workflow.edges) == 2  # START->task->END

    # Validate YAML
    try:
        Workflow.validate_yaml(yaml_text=workflow.to_yaml())
    # pylint: disable=broad-exception-caught
    except Exception as e:
        pytest.fail(f"Workflow YAML validation raised an error: {e}")

    yaml_str = workflow.to_yaml()
    assert yaml_str is not None
    data = yaml.safe_load(yaml_str)
    assert data["nodes"]["start"]["type"] == "START"
    assert data["nodes"]["task_1"]["type"] == "TASK"
    assert data["nodes"]["end"]["type"] == "END"
    assert len(data["edges"]) == 2  # START->task->END
    
    # Verify execution time
    execution_time = time.time() - start_time
    assert execution_time < 1.0, f"Test took {execution_time:.2f} seconds, should be < 1 second"

def test_sequential_steps(sequential_steps):
    """Same as test_single_command, but with sequential steps."""
    start_time = time.time()

    num_steps = len(sequential_steps)
    workflow = create_from_steps(sequential_steps)
    assert isinstance(workflow, Workflow)
    assert len(workflow.nodes) == num_steps + 2  # START, tasks, END
    assert len(workflow.edges) == num_steps + 1  # START->task_1->task_2->...->END

    # Validate YAML
    try:
        Workflow.validate_yaml(yaml_text=workflow.to_yaml())
    # pylint: disable=broad-exception-caught
    except Exception as e:
        pytest.fail(f"Workflow YAML validation raised an error: {e}")

    yaml_str = workflow.to_yaml()
    assert yaml_str is not None
    data = yaml.safe_load(yaml_str)
    assert data["nodes"]["start"]["type"] == "START"
    assert data["nodes"]["task_1"]["type"] == "TASK"
    assert data["nodes"]["end"]["type"] == "END"
    assert len(data["edges"]) == num_steps + 1  # START->task_1->task_2->...->END

    # Verify execution time
    execution_time = time.time() - start_time
    assert execution_time < 1.0, f"Test took {execution_time:.2f} seconds, should be < 1 second"

@pytest.fixture
def mock_llm(monkeypatch):
    """Mock LLM responses for testing."""
    def mock_do_query(_self, query):
        """Mock LLM query."""
        if "latest data" in query["prompt"]:
            return {"content": """```yaml
nodes:
  start:
    type: START
    description: "Begin workflow"
  condition_1:
    type: CONDITION
    description: "Check if data is latest"
  task_1:
    type: TASK
    description: "Download new data"
  task_2:
    type: TASK
    description: "Analyze data"
  end:
    type: END
    description: "End workflow"
edges:
  - from: start
    to: condition_1
  - from: condition_1
    to: task_1
    condition: "data is outdated"
  - from: condition_1
    to: task_2
    condition: "data is latest"
  - from: task_1
    to: task_2
  - from: task_2
    to: end
```"""}
        elif "Download the data" in query["prompt"]:
            return {"content": """```yaml
nodes:
  start:
    type: START
    description: "Begin workflow"
  task_1:
    type: TASK
    description: "Download the data"
  end:
    type: END
    description: "End workflow"
edges:
  - from: start
    to: task_1
  - from: task_1
    to: end
```"""}
        return {"content": ""}

    # pylint: disable=import-outside-toplevel
    from dxa.core.resource import LLMResource
    monkeypatch.setattr(LLMResource, "do_query", mock_do_query)

# pylint: disable=unused-argument
def test_natural_language_workflow(natural_language_workflow, mock_llm):
    """Test converting complex natural language to workflow."""
    start_time = time.time()
    
    workflow = create_from_natural_language(natural_language_workflow)
    assert isinstance(workflow, Workflow)

    # assert that this does not raise error
    try:
        Workflow.validate_yaml(yaml_text=workflow.to_yaml())
    # pylint: disable=broad-exception-caught
    except Exception as e:
        pytest.fail(f"Workflow YAML validation raised an error: {e}")

    assert len(workflow.nodes) == 5  # START, 3 tasks, END
    assert len(workflow.edges) == 5  # START->1->2->3->END plus 1->3
    
    # Validate basic structure
    assert any(n.type == ExecutionNodeType.CONDITION for n in workflow.nodes.values())
    condition_nodes = [n for n in workflow.nodes.values() if n.type == ExecutionNodeType.CONDITION]
    assert len(condition_nodes) == 1
    
    # Validate condition paths
    condition = condition_nodes[0]
    outgoing = workflow.get_edges_from(condition.node_id)
    assert len(outgoing) == 2
    
    # Verify conditions on condition edges
    conditions = [e.condition for e in outgoing]
    assert "data is outdated" in conditions
    assert "data is latest" in conditions
    
    # Verify execution time (should be fast with mock)
    execution_time = time.time() - start_time
    assert execution_time < 1.0, f"Test took {execution_time:.2f} seconds, should be < 1 second"

def test_create_from_yaml():
    """Test creating workflow from YAML string."""
    yaml_str = """
nodes:
  start:
    type: START
    description: "Begin workflow"
  task_1:
    type: TASK
    description: "Process data"
    requires:
      input_data: str
    provides:
      output_data: str
  task_2:
    type: TASK
    description: "Generate report"
    requires:
      output_data: str
  end:
    type: END
    description: "End workflow"
edges:
  - from: start
    to: task_1
  - from: task_1
    to: task_2
    state_updates:
      data_processed: true
  - from: task_2
    to: end
"""
    start_time = time.time()
    
    workflow = create_from_yaml(yaml_str)
    assert isinstance(workflow, Workflow)
    assert len(workflow.nodes) == 4  # START, 2 tasks, END
    assert len(workflow.edges) == 3  # START->task_1->task_2->END

    # Validate node details
    task1 = cast(ExecutionNode, workflow.nodes["task_1"])
    assert task1.type == ExecutionNodeType.TASK
    assert task1.requires == {"input_data": "str"}
    assert task1.provides == {"output_data": "str"}

    # Validate edge details
    task1_to_task2 = next(e for e in cast(List[ExecutionEdge], workflow.edges)
                          if e.source == "task_1" and e.target == "task_2")
    assert task1_to_task2.state_updates == {"data_processed": True}

    # Verify execution time
    execution_time = time.time() - start_time
    assert execution_time < 1.0, f"Test took {execution_time:.2f} seconds, should be < 1 second"
