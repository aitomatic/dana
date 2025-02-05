"""Simple Q&A example using DXA."""

from typing import Dict, Any
from dxa.agent import Agent
from dxa.execution import PlanningStrategy, WorkflowFactory
from dxa.common import DXA_LOGGER

def simple_qa(question: str) -> Dict[str, Any]:
    """Direct question-answer using default agent."""
    return Agent().ask(question)

def workflow_qa(question: str) -> Dict[str, Any]:
    """Question-answer using workflow-is-plan strategy."""
    agent = Agent().with_planning(PlanningStrategy.WORKFLOW_IS_PLAN)
    workflow = WorkflowFactory.create_sequential_workflow(
        objective=question,
        commands=[question]
    )
    return agent.run(workflow)

def two_step_qa(question: str) -> Dict[str, Any]:
    """Two-step summarize-explain using workflow-is-plan strategy."""
    agent = Agent().with_planning(PlanningStrategy.WORKFLOW_IS_PLAN)
    workflow = WorkflowFactory.create_sequential_workflow(
        objective=question,
        commands=[
            f"Summarize: {question}",
            "Explain the summary in detail"
        ]
    )
    return agent.run(workflow)

def run_simple_qa():
    """Simple QA workflow with proper signal handling."""
    agent = Agent("qa_agent")
    workflow = WorkflowFactory.create_minimal_workflow(
        "Explain quantum entanglement in simple terms"
    )
    
    result = agent.run(workflow)
    
    # Access response through signal content
    # Dump the result dict
    print(result)

if __name__ == "__main__":
    DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG)
    run_simple_qa()
