"""Simple Q&A example using DXA."""

from dxa.core.agent import Agent

def main():
    """Simple Q&A example."""
    question = "What is quantum computing?"
    print(f"\nQuestion: {question}")
    print(f"Answer: {Agent().ask(question)}")

if __name__ == "__main__":
    main()