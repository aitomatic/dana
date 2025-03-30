"""Simple Workflow: Creating and Running a Basic Workflow

This example demonstrates how to create and run a basic workflow in DXA.
It shows the workflow creation process and how to execute it through the agent.

Key concepts:
- Workflow creation
- Workflow execution
- Node and edge management
- Execution context

Prerequisites:
- DXA installed: pip install -e .
- OpenAI API key set: export OPENAI_API_KEY=your_key

Related examples:
- 01_hello_dxa.py: Basic agent usage
- 03_qa_approaches.py: Different QA patterns
"""

import asyncio
from dxa.agent import Agent
from dxa.common.utils.logging import DXA_LOGGER
from dxa.agent.resource import LLMResource
from dxa.execution.workflow.workflow_factory import WorkflowFactory

async def main():
    """Demonstrate creating and running a simple workflow."""
    # Configure logging
    DXA_LOGGER.configure(
        level=DXA_LOGGER.INFO,
        console=True
    )
    
    print("=== Creating a Simple Workflow ===")
    print("This example shows how to:")
    print("1. Create a workflow with custom nodes")
    print("2. Set up an agent to execute it")
    print("3. Run the workflow and process results")
    
    # Create a basic workflow
    objective = "Research and summarize the history of artificial intelligence"
    workflow = WorkflowFactory.create_basic_workflow(
        objective=objective,
        commands=[
            "Research early AI developments",
            "Analyze key milestones",
            "Summarize current state"
        ]
    )
    
    print("\nWorkflow Structure:")
    print(workflow.pretty_print())
    
    print("\n=== Setting Up Agent ===")
    # Create and configure agent
    agent = Agent(name="research_agent")
    
    # Initialize LLM resource
    llm = LLMResource()
    await llm.initialize()
    agent.with_llm(llm)
    
    print("\n=== Executing Workflow ===")
    try:
        # Execute the workflow
        result = await agent.run(workflow)
        
        print("\n=== Results ===")
        print("Workflow execution completed successfully!")
        print("\nFinal Summary:")
        print(result["result"])
        
    except Exception as e:
        print(f"\nError during execution: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await llm.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 