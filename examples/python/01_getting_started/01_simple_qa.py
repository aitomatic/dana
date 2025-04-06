"""Simple Question Answering with DXA

This example demonstrates how to create a question-answering agent with DXA,
including basic configuration options and execution patterns.

Key concepts:
- Agent creation and configuration
- LLM resource integration
- Simple question answering
- Accessing and interpreting results

Learning path: Getting Started
Complexity: Beginner

Prerequisites:
- None

Related examples:
- 00_hello_dxa.py: Introduction to DXA
- 02_default_workflow.py: Creating a basic workflow
- 03_qa_approaches.py: Different approaches to question answering
"""

from opendxa.agent import Agent
from opendxa.common.resource import LLMResource


def create_basic_agent():
    """Create a basic agent with default settings."""
    # The simplest way to create an agent
    agent = Agent()
    return agent


def create_configured_agent():
    """Create an agent with custom configuration."""
    # Create an agent with a name and custom LLM resource
    agent = Agent(
        name="qa_agent",  # Give your agent a name
    )
    
    # Add an LLM resource to the agent
    # This is where the agent gets its intelligence from
    agent = agent.with_llm(
        LLMResource(
            # You can configure the LLM resource with parameters like:
            # model="gpt-4",
            # temperature=0.7,
            # etc.
        )
    )
    
    return agent


def ask_questions(agent):
    """Ask a series of questions to the agent and display the results."""
    questions = [
        "What is the capital of France?",
        "Explain the concept of machine learning in simple terms.",
        "How does the DXA framework help with building AI applications?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n=== Question {i}: {question} ===")
        
        # The ask method is the simplest way to get an answer
        response = agent.ask(question)
        
        # The response is a dictionary with various fields
        print(f"Answer: {response['result']}")
        
        # You can also access metadata about the execution
        print(f"Execution time: {response.get('execution_time', 'N/A')} seconds")


def main():
    """Demonstrate simple question answering with DXA."""
    print("=== Simple Question Answering with DXA ===\n")
    
    print("Creating a basic agent...")
    basic_agent = create_basic_agent()
    
    print("Creating a configured agent...")
    configured_agent = create_configured_agent()
    
    print("\nUsing the basic agent for a simple question:")
    response = basic_agent.ask("What is DXA?")
    print(f"Answer: {response['result']}")
    
    print("\nUsing the configured agent to answer multiple questions:")
    ask_questions(configured_agent)
    
    print("\n=== Example Complete ===")
    print("Next steps:")
    print("1. Try modifying the questions or adding your own")
    print("2. Experiment with different LLM configurations")
    print("3. Move on to the next example to learn about workflows")


if __name__ == "__main__":
    main() 