"""Simple Q&A example using DXA."""

from typing import Dict, Any
from dxa.agent import Agent
from dxa.execution import WorkflowFactory, WorkflowStrategy, PlanningStrategy, ReasoningStrategy
from dxa.common import DXA_LOGGER


def run_simple_qa():
    """Simple QA workflow with proper signal handling."""
    agent = Agent("qa_agent")
    workflow = WorkflowFactory.create_minimal_workflow(
        "Prove the Fermat's Last Theorem"
    )
    
    result = agent.run(workflow)
    
    # Access response through signal content
    # Dump the result dict
    print(result)
    
def run_prosea():
    """Prosea workflow."""
    agent = Agent("prosea_agent")\
        .with_workflow(WorkflowStrategy.PROSEA)\
        .with_planning(PlanningStrategy.PROSEA)\
        .with_reasoning(ReasoningStrategy.PROSEA)
    
    
    workflow = WorkflowFactory.create_prosea_workflow(
        "Prove the Fermat's Last Theorem"
    )
    return agent.run(workflow)

if __name__ == "__main__":
    DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG)
    # run_simple_qa()
    print(run_prosea())
