"""Question Answering Approaches using DXA.

This example demonstrates different approaches to question answering using the DXA framework,
from simple to complex. It showcases the flexibility of the execution system and how
different strategies can be applied to the same basic task.

Key concepts demonstrated:
1. Direct question answering with minimal workflow (using agent.ask)
2. Single-step workflow with WORKFLOW_IS_PLAN strategy (skipping planning layer)
3. Multi-step reasoning with custom workflow creation (summarize then explain)
4. Complete workflow creation and execution process

Use cases:
- Understanding the basic execution flow of DXA
- Learning how to create and run different types of workflows
- Seeing how the agent processes natural language questions
- Demonstrating the hierarchical execution model
- Comparing different approaches to the same task
"""

from typing import Dict, Any
from dxa.agent import Agent
from dxa.execution import PlanStrategy, WorkflowFactory
from dxa.execution.workflow import Workflow
from dxa.execution.execution_types import ExecutionNode, Objective
from dxa.common.graph import NodeType
from dxa.common import DXA_LOGGER

def direct_qa_with_ask(question: str) -> Dict[str, Any]:
    """Direct question-answer using the agent's ask method.
    
    This is the simplest approach, using the agent's built-in 'ask' method
    which creates a minimal workflow with a single task node.
    
    Workflow Graph Structure:
    - A minimal workflow with three nodes:
      START → PERFORM_TASK → END
    - The PERFORM_TASK node contains the question as its description
    - The agent automatically creates this workflow internally
    
    Args:
        question: The question to ask
        
    Returns:
        Dictionary containing the response and execution metadata
    """
    return Agent().ask(question)

def single_step_workflow_is_plan(question: str) -> Dict[str, Any]:
    """Single-step question answering using workflow-is-plan strategy.
    
    This approach explicitly creates a sequential workflow and uses the
    WORKFLOW_IS_PLAN strategy, which treats the workflow itself as a plan.
    This is useful when you want to skip the planning layer for simple tasks.
    
    Workflow Graph Structure:
    - A sequential workflow with three nodes:
      START → TASK_0 → END
    - The TASK_0 node contains the question as its description
    - With WORKFLOW_IS_PLAN strategy, this workflow is directly used as the plan,
      bypassing the normal workflow-to-plan transformation
    - This creates a more direct execution path: Workflow → Reasoning
    
    Args:
        question: The question to ask
        
    Returns:
        Dictionary containing the response and execution metadata
    """
    agent = Agent().with_planning(PlanStrategy.WORKFLOW_IS_PLAN)
    
    # Create a default workflow instead of using create_minimal_workflow
    workflow = WorkflowFactory.create_default_workflow(objective=question)
    
    return agent.run(workflow)

def two_step_summarize_explain(question: str) -> Dict[str, Any]:
    """Two-step summarize-explain using workflow-is-plan strategy.
    
    This approach demonstrates a multi-step reasoning process by creating
    a sequential workflow with two commands: first summarize, then explain.
    This shows how to chain reasoning steps for more complex tasks.
    
    Workflow Graph Structure:
    - A sequential workflow with four nodes:
      START → TASK_0 → TASK_1 → END
    - TASK_0 node: "Summarize: {question}"
    - TASK_1 node: "Explain the summary in detail"
    - The output of TASK_0 is implicitly passed to TASK_1 via the execution context
    - With WORKFLOW_IS_PLAN strategy, this multi-step workflow becomes the plan
    
    Args:
        question: The question to ask
        
    Returns:
        Dictionary containing the response and execution metadata
    """
    agent = Agent().with_planning(PlanStrategy.WORKFLOW_IS_PLAN)
    
    # Create a custom workflow with two steps
    workflow = Workflow(objective=Objective(question))
    
    # Add START node
    start_node = ExecutionNode(
        node_id="START",
        node_type=NodeType.START,
        objective=Objective("Start workflow")
    )
    workflow.add_node(start_node)
    
    # Add first task node - Summarize
    task1_node = ExecutionNode(
        node_id="TASK_0",
        node_type=NodeType.TASK,
        objective=Objective(f"Summarize: {question}")
    )
    workflow.add_node(task1_node)
    
    # Add second task node - Explain
    task2_node = ExecutionNode(
        node_id="TASK_1",
        node_type=NodeType.TASK,
        objective=Objective("Explain the summary in detail")
    )
    workflow.add_node(task2_node)
    
    # Add END node
    end_node = ExecutionNode(
        node_id="END",
        node_type=NodeType.END,
        objective=Objective("End workflow")
    )
    workflow.add_node(end_node)
    
    # Add edges using add_edge_between which creates ExecutionEdge objects
    workflow.add_edge_between("START", "TASK_0")
    workflow.add_edge_between("TASK_0", "TASK_1")
    workflow.add_edge_between("TASK_1", "END")
    
    return agent.run(workflow)

def minimal_workflow_example(question: str = "Explain quantum entanglement in simple terms") -> Dict[str, Any]:
    """Demonstrate using a minimal workflow with explicit creation.
    
    This function demonstrates the complete execution flow:
    1. Creating an agent with a specific name
    2. Creating a minimal workflow with a specific objective
    3. Running the workflow and getting the result
    
    Workflow Graph Structure:
    - A minimal workflow with three nodes:
      START → PERFORM_TASK → END
    - The START node is the entry point with NodeType.START
    - The PERFORM_TASK node has NodeType.TASK and contains the question
    - The END node is the exit point with NodeType.END
    - Edges connect the nodes in a linear sequence
    
    Args:
        question: The question to ask (defaults to quantum entanglement)
        
    Returns:
        Dictionary containing the response and execution metadata
    """
    agent = Agent("qa_agent")
    workflow = WorkflowFactory.create_default_workflow(objective=question)
    return agent.run(workflow)

def demonstrate_all_approaches():
    """Run all question answering approaches for comparison.
    
    This function demonstrates all four approaches to question answering:
    1. Direct QA with ask method
    2. Single-step workflow with WORKFLOW_IS_PLAN strategy
    3. Two-step summarize-explain workflow
    4. Minimal workflow with explicit creation
    
    Each approach is run with the same question for easy comparison.
    """
    question = "Explain quantum entanglement in simple terms"
    print("\n" + "=" * 80)
    print(f"QUESTION: {question}")
    print("=" * 80)
    
    print("\n1. DIRECT QA WITH ASK METHOD")
    print("-" * 50)
    result = direct_qa_with_ask(question)
    print(f"Result type: {type(result)}")
    print(f"Result keys: {result.keys()}")
    if 'result' in result:
        print(f"Answer: {result['result']}")
    else:
        print(f"Full result: {result}")
    
    print("\n2. SINGLE-STEP WORKFLOW IS PLAN")
    print("-" * 50)
    result = single_step_workflow_is_plan(question)
    print(f"Result type: {type(result)}")
    print(f"Result keys: {result.keys()}")
    if 'result' in result:
        print(f"Answer: {result['result']}")
    else:
        print(f"Full result: {result}")
    
    print("\n3. TWO-STEP SUMMARIZE-EXPLAIN")
    print("-" * 50)
    result = two_step_summarize_explain(question)
    print(f"Result type: {type(result)}")
    print(f"Result keys: {result.keys()}")
    if 'result' in result:
        print(f"Answer: {result['result']}")
    else:
        print(f"Full result: {result}")
    
    print("\n4. MINIMAL WORKFLOW EXAMPLE")
    print("-" * 50)
    result = minimal_workflow_example(question)
    print(f"Result type: {type(result)}")
    print(f"Result keys: {result.keys()}")
    if 'result' in result:
        print(f"Answer: {result['result']}")
    else:
        print(f"Full result: {result}")

if __name__ == "__main__":
    # Configure logging to see detailed execution flow
    DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG)
    demonstrate_all_approaches()
