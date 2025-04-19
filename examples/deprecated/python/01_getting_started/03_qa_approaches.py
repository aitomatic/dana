"""Question Answering Approaches using DXA.

This example demonstrates different approaches to question answering using the DXA framework,
from simple to complex. It showcases the flexibility of the execution system and how
different strategies can be applied to the same basic task.

Key concepts demonstrated:
1. Direct question answering with minimal plan (using agent.ask)
2. Single-step plan execution (direct reasoning)
3. Multi-step reasoning with custom plan creation (summarize then explain)
4. Complete plan creation and execution process

Use cases:
- Understanding the basic execution flow of DXA
- Learning how to create and run different types of plans
- Seeing how the agent processes natural language questions
- Demonstrating the hierarchical execution model
- Comparing different approaches to the same task
"""

from typing import Dict, Any
from opendxa.agent import Agent
from opendxa.execution import PlanFactory
from opendxa.execution.planning import Plan
from opendxa.base.execution.execution_types import ExecutionNode
from opendxa.common.graph import NodeType
from opendxa.common import DXA_LOGGER

def direct_qa_with_ask(question: str) -> Dict[str, Any]:
    """Direct question-answer using the agent's ask method.
    
    This is the simplest approach, using the agent's built-in 'ask' method
    which creates a minimal plan with a single task node.
    
    Plan Graph Structure:
    - A minimal plan with three nodes:
      START → PERFORM_TASK → END
    - The PERFORM_TASK node contains the question as its description
    - The agent automatically creates this plan internally
    
    Args:
        question: The question to ask
        
    Returns:
        Dictionary containing the response and execution metadata
    """
    return Agent().ask(question)

def single_step_plan(question: str) -> Dict[str, Any]:
    """Single-step question answering using direct plan execution.
    
    This approach explicitly creates a sequential plan and executes it directly.
    This is useful for simple tasks that don't require complex planning.
    
    Plan Graph Structure:
    - A sequential plan with three nodes:
      START → TASK_0 → END
    - The TASK_0 node contains the question as its description
    - This creates a direct execution path: Plan → Reasoning
    
    Args:
        question: The question to ask
        
    Returns:
        Dictionary containing the response and execution metadata
    """
    agent = Agent()
    
    # Create a default plan
    plan = PlanFactory.create_default_plan(objective=question)
    
    return agent.run(plan)

def two_step_summarize_explain(question: str) -> Dict[str, Any]:
    """Two-step summarize-explain using custom plan.
    
    This approach demonstrates a multi-step reasoning process by creating
    a sequential plan with two commands: first summarize, then explain.
    This shows how to chain reasoning steps for more complex tasks.
    
    Plan Graph Structure:
    - A sequential plan with four nodes:
      START → TASK_0 → TASK_1 → END
    - TASK_0 node: "Summarize: {question}"
    - TASK_1 node: "Explain the summary in detail"
    - The output of TASK_0 is implicitly passed to TASK_1 via the execution context
    
    Args:
        question: The question to ask
        
    Returns:
        Dictionary containing the response and execution metadata
    """
    agent = Agent()
    
    # Create a custom plan with two steps
    plan = Plan(objective=question)
    
    # Add nodes
    start_node = ExecutionNode(
        node_id="START",
        node_type=NodeType.START,
        objective="Start of summarize-explain plan"
    )
    plan.add_node(start_node)
    
    summarize_node = ExecutionNode(
        node_id="SUMMARIZE",
        node_type=NodeType.TASK,
        objective=f"Summarize: {question}"
    )
    plan.add_node(summarize_node)
    
    explain_node = ExecutionNode(
        node_id="EXPLAIN",
        node_type=NodeType.TASK,
        objective="Explain the summary in detail"
    )
    plan.add_node(explain_node)
    
    end_node = ExecutionNode(
        node_id="END",
        node_type=NodeType.END,
        objective="End of summarize-explain plan"
    )
    plan.add_node(end_node)
    
    # Add edges
    plan.add_edge_between("START", "SUMMARIZE")
    plan.add_edge_between("SUMMARIZE", "EXPLAIN")
    plan.add_edge_between("EXPLAIN", "END")
    
    return agent.run(plan)

def minimal_plan_example(question: str = "Explain quantum entanglement in simple terms") -> Dict[str, Any]:
    """Demonstrate minimal plan creation and execution.
    
    This example shows how to create and execute a minimal plan with
    a single task node. It's similar to the direct_qa_with_ask approach
    but with explicit plan creation.
    
    Plan Graph Structure:
    - A minimal plan with three nodes:
      START → TASK_0 → END
    - The TASK_0 node contains the question as its description
    
    Args:
        question: The question to ask (default example question)
        
    Returns:
        Dictionary containing the response and execution metadata
    """
    agent = Agent()
    
    # Create a minimal plan
    plan = Plan(objective=question)
    
    # Add nodes
    start_node = ExecutionNode(
        node_id="START",
        node_type=NodeType.START,
        objective="Start of minimal plan"
    )
    plan.add_node(start_node)
    
    task_node = ExecutionNode(
        node_id="TASK_0",
        node_type=NodeType.TASK,
        objective=question
    )
    plan.add_node(task_node)
    
    end_node = ExecutionNode(
        node_id="END",
        node_type=NodeType.END,
        objective="End of minimal plan"
    )
    plan.add_node(end_node)
    
    # Add edges
    plan.add_edge_between("START", "TASK_0")
    plan.add_edge_between("TASK_0", "END")
    
    return agent.run(plan)

def demonstrate_all_approaches():
    """Demonstrate all question answering approaches.
    
    This function runs all the question answering approaches
    with the same example question and prints their results.
    """
    question = "Explain quantum entanglement in simple terms"
    
    DXA_LOGGER.info("1. Direct QA with ask()")
    result = direct_qa_with_ask(question)
    DXA_LOGGER.info(f"Result: {result['content']}\n")
    
    DXA_LOGGER.info("2. Single-step plan")
    result = single_step_plan(question)
    DXA_LOGGER.info(f"Result: {result['content']}\n")
    
    DXA_LOGGER.info("3. Two-step summarize-explain")
    result = two_step_summarize_explain(question)
    DXA_LOGGER.info(f"Result: {result['content']}\n")
    
    DXA_LOGGER.info("4. Minimal plan example")
    result = minimal_plan_example(question)
    DXA_LOGGER.info(f"Result: {result['content']}\n")

if __name__ == "__main__":
    demonstrate_all_approaches()
