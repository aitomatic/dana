"""Simple Q&A example using DXA."""

from typing import Dict, Any
from dxa.agent import Agent
from dxa.execution import PlanningStrategy, WorkflowFactory

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

def main():
    """Simple Q&A example."""
    question = "What is quantum computing?"
    print(f"\nQuestion: {question}")
    
    # print("\nSimple QA:")
    # print(simple_qa(question)['content'])
    
    # print("\nWorkflow QA:")
    # print(workflow_qa(question)['content'])
    
    print("\nTwo-step QA:")
    print(two_step_qa(question)['content'])

if __name__ == "__main__":
    main()