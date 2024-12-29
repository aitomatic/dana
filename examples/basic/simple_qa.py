"""Simple Q&A example using DXA."""

from typing import Dict, Any
from dxa.core.agent import Agent

def main():
    """Simple Q&A example."""
    agent = Agent()
    question = "What is quantum computing?"
    print(f"\nQuestion: {question}")
    answer: Dict[str, Any] = agent.ask(question)
    print(f"Answer: {answer['content']}")

if __name__ == "__main__":
    main()