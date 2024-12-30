"""Simple Q&A example using DXA."""

from typing import Dict, Any
from dxa.core.agent import Agent
from dxa.core.planning import PlanningStrategy

def main():
    """Simple Q&A example."""
    # agent = Agent().with_planning(PlanningStrategy.WORKFLOW_IS_PLAN)
    agent = Agent()
    question = "What is quantum computing?"
    print(f"\nQuestion: {question}")
    answer: Dict[str, Any] = agent.ask(question)
    print(f"Answer: {answer['content']}")

if __name__ == "__main__":
    main()