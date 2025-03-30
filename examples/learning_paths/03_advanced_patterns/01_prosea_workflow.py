"""Example of using the ProSea workflow."""

import asyncio
import os

from dxa.common import DXA_LOGGER
from dxa.execution import WorkflowFactory, WorkflowExecutor
from dxa.execution import ExecutionContext
from dxa.agent.resource import LLMResource

# Configure logging
DXA_LOGGER.basicConfig(
    level=DXA_LOGGER.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Run the example."""
    print("Starting ProSea workflow example...")
    
    # Set up the LLM
    print("Initializing LLM...")
    llm = LLMResource(config={"model": "openai:gpt-3.5-turbo"})
    await llm.initialize()
    
    # Create the execution context
    print("Creating execution context...")
    context = ExecutionContext(reasoning_llm=llm, planning_llm=llm, workflow_llm=llm)
    
    # Create the workflow
    print("Creating ProSea workflow...")
    objective = "Design a simple inventory management system for a small retail store"
    workflow = WorkflowFactory.create_prosea_workflow(
        objective,
        agent_role="Inventory System Designer"
    )
    
    print(f"Created workflow with {len(workflow.nodes)} nodes")
    print(f"Nodes: {', '.join(workflow.nodes.keys())}")
    print(f"Workflow: {workflow.pretty_print()}")
    
    # Set up the execution pipeline
    print("Setting up execution pipeline...")
    workflow_executor = WorkflowExecutor()
    
    # Execute the workflow
    print("\nExecuting workflow...\n")
    try:
        signals = await workflow_executor.execute_workflow(workflow, context)
        
        # Print the results
        print("\nWorkflow execution complete. Results:")
        for signal in signals:
            if 'result' in signal.content:
                print(f"\n--- {signal.content['node']} ---")
                result = signal.content['result'].get('content', '')
                print(result[:500] + "..." if len(result) > 500 else result)
                
        print("\nExecution completed successfully!")
        
        # Clean up resources
        await llm.cleanup()
        return True
    except Exception as e:
        print(f"\nError during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Clean up resources even on error
        await llm.cleanup()
        return False

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Please set the OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY=your-api-key")
        exit(1)
    
    # Run the example
    success = asyncio.run(main())
    
    # Exit with appropriate code
    exit(0 if success else 1) 