"""Hello DXA: Introduction to the Distributed eXecution Architecture

This example provides a gentle introduction to the DXA framework and its core concepts.
It demonstrates the most basic usage pattern - creating a simple agent and asking it a question.

Key concepts:
- Basic agent creation
- Simple question answering
- Understanding the DXA architecture

Learning path: Getting Started
Complexity: Beginner

Prerequisites:
- None

Related examples:
- 01_simple_qa.py: Creating a simple question-answering agent
- 02_default_workflow.py: Creating a basic workflow
"""

from opendxa.agent import Agent


def main():
    """Demonstrate the simplest possible DXA usage pattern."""
    print("Welcome to DXA - Distributed eXecution Architecture!")
    print("\nDXA is a framework for building AI agents with:")
    print("- Structured execution patterns")
    print("- Multi-layer processing (Workflow, Planning, Reasoning)")
    print("- Flexible resource integration")
    print("- Robust logging and monitoring")
    
    print("\n=== Creating a Simple Agent ===")
    # Create a basic agent with default settings
    agent = Agent(name="hello_agent")
    print("Agent created successfully!")
    
    print("\n=== Asking a Simple Question ===")
    # The simplest way to use DXA - just ask a question
    question = "What is DXA and why is it useful?"
    print(f"Question: {question}")
    
    # The ask method creates a minimal workflow and executes it
    response = agent.ask(question)
    
    print("\n=== Response ===")
    print(response["result"])
    
    print("\n=== DXA Architecture Overview ===")
    print("What just happened behind the scenes:")
    print("1. The agent created a minimal workflow with your question")
    print("2. The workflow was processed by the planning layer")
    print("3. The planning layer created reasoning tasks")
    print("4. The reasoning layer executed those tasks using LLM resources")
    print("5. The results were returned through the layers back to you")
    
    print("\nCongratulations! You've just used the DXA framework.")
    print("Continue to the next examples to learn more about workflows and advanced features.")


if __name__ == "__main__":
    main() 