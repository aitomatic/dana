"""Test plan workflow copy strategy."""

import pytest
from dxa.agent.resource import LLMResource
from dxa.execution.planning.plan_executor import PlanExecutor
from dxa.execution.planning.plan_strategy import PlanStrategy
from dxa.execution.reasoning.reasoning_executor import ReasoningExecutor
from dxa.execution.workflow.workflow_executor import WorkflowExecutor
from dxa.execution.workflow.workflow_strategy import WorkflowStrategy
from dxa.execution.workflow.workflow import Workflow
from dxa.execution.execution_context import ExecutionContext
from dxa.execution.execution_types import ExecutionNode, ExecutionSignal, Objective
from dxa.common.graph import NodeType
from typing import List, Optional

# Mock implementations for testing
class MockReasoningExecutor(ReasoningExecutor):
    """Mock reasoning executor for testing."""
    
    async def execute_node(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Mock implementation."""
        return []
    
    async def _execute_task(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Mock implementation."""
        return []
    
    def create_graph_from_node(
        self, 
        upper_node=None,
        upper_graph=None, 
        objective=None, 
        context=None
    ):
        """Mock implementation."""
        return upper_graph

class MockPlanExecutor(PlanExecutor):
    """Mock plan executor for testing."""
    
    async def execute_node(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Mock implementation."""
        return []
    
    async def _execute_task(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Mock implementation."""
        return []
    
    def create_graph_from_node(
        self, 
        upper_node=None,
        upper_graph=None, 
        objective=None, 
        context=None
    ):
        """Mock implementation."""
        return upper_graph

class MockWorkflowExecutor(WorkflowExecutor):
    """Mock workflow executor for testing."""
    
    async def execute_node(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Mock implementation."""
        return []
    
    async def _execute_task(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Mock implementation."""
        return []
    
    def create_graph_from_node(
        self, 
        upper_node=None,
        upper_graph=None, 
        objective=None, 
        context=None
    ):
        """Mock implementation."""
        return upper_graph

class MockLLM(LLMResource):
    """Mock LLM for testing."""
    async def query(self, request: dict) -> dict:
        """Mock LLM query."""
        return {"content": f"Mock response for: {request['prompt']}"}

@pytest.fixture
def workflow():
    """Create a test workflow."""
    workflow = Workflow(objective=Objective("Test workflow objective"))
    
    # Add START node
    start_node = ExecutionNode(
        node_id="START",
        node_type=NodeType.START,
        description="Start workflow"
    )
    workflow.add_node(start_node)
    
    # Add task node
    task_node = ExecutionNode(
        node_id="PERFORM_TASK",
        node_type=NodeType.TASK,
        description="Perform a test task",
        metadata={"test_key": "test_value"}
    )
    workflow.add_node(task_node)
    
    # Add END node
    end_node = ExecutionNode(
        node_id="END",
        node_type=NodeType.END,
        description="End workflow"
    )
    workflow.add_node(end_node)
    
    # Add edges
    workflow.add_edge_between("START", "PERFORM_TASK")
    workflow.add_edge_between("PERFORM_TASK", "END")
    
    return workflow

@pytest.fixture
def plan_executor():
    """Create a mock plan executor."""
    reasoning_executor = MockReasoningExecutor()
    executor = MockPlanExecutor(
        reasoning_executor=reasoning_executor,
        strategy=PlanStrategy.DEFAULT
    )
    return executor

@pytest.fixture
def workflow_executor(plan_executor):
    """Workflow executor fixture."""
    return MockWorkflowExecutor(
        plan_executor=plan_executor,
        strategy=WorkflowStrategy.WORKFLOW_IS_PLAN
    )

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_workflow_copy_creation(workflow, workflow_executor):
    """Test creation of plan as exact copy of workflow."""
    # pylint: disable=protected-access
    plan = workflow_executor._create_pass_through_plan(workflow.nodes["PERFORM_TASK"])

    # Verify structure
    assert len(plan.nodes) == 3  # START, task node, END
    assert len(plan.edges) == 2  # START->task, task->END
    
    # Verify node preservation
    assert "PERFORM_TASK" in plan.nodes
    assert plan.nodes["PERFORM_TASK"].metadata.get("is_pass_through") is True

@pytest.mark.asyncio
# pylint: disable=redefined-outer-name
async def test_plan_execution_updates_workflow_cursor(workflow, workflow_executor, plan_executor):
    """Test that plan execution updates workflow cursor."""
    # pylint: disable=protected-access
    plan = workflow_executor._create_pass_through_plan(workflow.nodes["PERFORM_TASK"])
    context = ExecutionContext(
        current_workflow=workflow,
        current_plan=plan,
        workflow_llm=MockLLM(),
        planning_llm=MockLLM(),
        reasoning_llm=MockLLM()
    )
    
    # Set the current node in the workflow
    workflow.update_cursor("PERFORM_TASK")
    
    try:
        await plan_executor.execute_node(plan.nodes["PERFORM_TASK"], context, None, None)
    except ValueError as e:
        assert str(e) == "No reasoning LLM configured in context"

    assert workflow.get_current_node().node_id == "PERFORM_TASK" 
