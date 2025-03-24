"""Test plan workflow copy strategy."""

import pytest
from typing import List, Optional
from dxa.agent.resource import LLMResource
from dxa.execution.planning.plan_executor import PlanExecutor
from dxa.execution.planning.plan_strategy import PlanStrategy
from dxa.execution.reasoning.reasoning_executor import ReasoningExecutor
from dxa.execution.reasoning.reasoning_strategy import ReasoningStrategy
from dxa.execution.workflow.workflow_executor import WorkflowExecutor
from dxa.execution.workflow.workflow_strategy import WorkflowStrategy
from dxa.execution.workflow.workflow import Workflow
from dxa.execution.execution_context import ExecutionContext
from dxa.execution.execution_types import ExecutionNode, ExecutionSignal, Objective
from dxa.common.graph import NodeType

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
    the_workflow = Workflow(objective=Objective("Test workflow objective"))
    
    # Add START node
    start_node = ExecutionNode(
        node_id="START",
        node_type=NodeType.START,
        description="Start workflow"
    )
    the_workflow.add_node(start_node)
    
    # Add task node
    task_node = ExecutionNode(
        node_id="PERFORM_TASK",
        node_type=NodeType.TASK,
        description="Perform a test task",
        metadata={"test_key": "test_value"}
    )
    the_workflow.add_node(task_node)
    
    # Add END node
    end_node = ExecutionNode(
        node_id="END",
        node_type=NodeType.END,
        description="End workflow"
    )
    the_workflow.add_node(end_node)
    
    # Add edges
    the_workflow.add_edge_between("START", "PERFORM_TASK")
    the_workflow.add_edge_between("PERFORM_TASK", "END")
    
    return the_workflow

@pytest.fixture
def plan_executor():
    """Create a mock plan executor."""
    reasoning_executor = MockReasoningExecutor()
    executor = MockPlanExecutor(strategy=PlanStrategy.DEFAULT)
    executor.lower_executor = reasoning_executor
    return executor

# pylint: disable=redefined-outer-name
@pytest.fixture
def workflow_executor(plan_executor):
    """Workflow executor fixture."""
    executor = MockWorkflowExecutor(
        workflow_strategy=WorkflowStrategy.WORKFLOW_IS_PLAN,
        planning_strategy=PlanStrategy.DEFAULT,
        reasoning_strategy=ReasoningStrategy.DEFAULT
    )
    executor.lower_executor = plan_executor
    return executor
