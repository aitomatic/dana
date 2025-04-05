"""
Example demonstrating how to run a Default workflow using our refactored Workflow-Plan-Reasoning stack.

This example showcases our architectural changes that formalize the relationship between execution layers:
- Each lower layer creates its graphs from nodes in the upper layer
- Using create_graph_from_upper_node instead of _create_graph throughout the architecture
- Maintaining explicit connections between layers via the upper_node parameter

The example performs a Customer Review Analysis task, walking through:
1. Creating a Default workflow with a structured process (Define -> Research -> Strategize -> Execute -> Evaluate)
2. Setting up the three-layer executor hierarchy (Workflow -> Plan -> Reasoning)
3. Running the workflow through all three layers using our refactored create_graph_from_upper_node pattern
4. Processing and displaying results in a structured format

This demonstrates how our refactoring improves architecture clarity and maintainability
by formalizing the relationship between layers while maintaining the same functionality.
"""

import asyncio
import sys

from dxa.execution import (
    WorkflowFactory,
    OptimalWorkflowExecutor,
    ExecutionContext,
    Objective
)
from dxa.common import DXA_LOGGER
from dxa.agent import LLMResource

async def setup_logging():
    """Set up logging configuration."""
    DXA_LOGGER.configure(
        level=DXA_LOGGER.DEBUG,  # Set to DEBUG to see more detailed logs
        console=True,            # Output logs to console
        log_data=True            # Log data payloads
    )

async def create_llm_context():
    """Create LLM resource and execution context."""
    # Create a real LLM resource
    llm = LLMResource()
    await llm.initialize()
    
    # Create an execution context with the LLM resource
    context = ExecutionContext(
        reasoning_llm=llm,
        planning_llm=llm,
        workflow_llm=llm
    )
    
    return llm, context

async def process_results(signals, workflow):
    """Process and display workflow results."""
    print("\n========== CUSTOMER REVIEW ANALYSIS RESULTS ==========")
    
    # Group results by node for organized display
    results_by_node = {}
    for signal in signals:
        if hasattr(signal, 'content') and 'result' in signal.content:
            node_name = signal.content.get('node', 'Unknown')
            result = signal.content['result']
            if isinstance(result, dict) and 'content' in result:
                results_by_node[node_name] = result['content']
            else:
                results_by_node[node_name] = str(result)

    # Display results in workflow order
    node_order = workflow.nodes.keys()
    for node_name in node_order:
        if node_name in results_by_node:
            print(f"\n## {node_name} ##")
            print(results_by_node[node_name])
    
    print("\n========== END OF ANALYSIS ==========")
    print("\nWorkflow execution completed successfully!")
    print("\nThis demonstrates how our refactored architecture:")
    print("1. Creates a plan graph from each workflow node")
    print("2. Creates a reasoning graph from each plan node")
    print("3. Executes reasoning tasks with the LLM")
    print("4. Returns results through signals back up the stack")

async def main():
    """Run a Default workflow to analyze customer reviews and recommend solutions."""
    # Set up logging
    await setup_logging()
    
    print("=================================================================")
    print("EXAMPLE: RUNNING A DEFAULT WORKFLOW WITH OUR REFACTORED W-P-R STACK")
    print("=================================================================")
    print("\nThis example demonstrates:")
    print("1. Creating a Default workflow with a specific objective")
    print("2. Setting up the executor hierarchy with our refactored code")
    print("3. Executing the workflow through all three layers")
    print("4. Processing and displaying the results in a structured way")
    print("\nStarting Customer Review Analysis workflow...")
    
    # Create LLM and context
    llm, context = await create_llm_context()
    
    # Create a Default workflow for customer review analysis
    objective = "Analyze customer reviews for a tech company's product, identify key issues, and recommend solutions."
    workflow = WorkflowFactory.create_default_workflow(objective=Objective(objective))
    
    # Print workflow structure
    print("\nWorkflow Structure:")
    print(workflow.pretty_print())
    print(f"\nCreated workflow with {len(workflow.nodes)} nodes")
    
    print("Creating WorkflowExecutor (top layer - orchestrates overall process)")
    workflow_executor = OptimalWorkflowExecutor()
    
    # Execute workflow
    print("\nExecuting workflow using our refactored create_graph_from_node pattern...")
    print("This will create graphs at each layer derived from nodes in the layer above.")
    try:
        signals = await workflow_executor.execute_workflow(workflow, context)
        await process_results(signals, workflow)
        return True
    except Exception as e:
        print(f"\nError during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await llm.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)