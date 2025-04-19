"""
Example demonstrating how to run a Default plan using our Plan-Reasoning stack.

This example showcases our architectural changes that formalize the relationship between execution layers:
- Each lower layer creates its graphs from nodes in the upper layer
- Using create_graph_from_upper_node instead of _create_graph throughout the architecture
- Maintaining explicit connections between layers via the upper_node parameter

The example performs a Customer Review Analysis task, walking through:
1. Creating a Default plan with a structured process (Define -> Research -> Strategize -> Execute -> Evaluate)
2. Setting up the two-layer executor hierarchy (Plan -> Reasoning)
3. Running the plan through both layers using our refactored create_graph_from_upper_node pattern
4. Processing and displaying results in a structured format

This demonstrates how our refactoring improves architecture clarity and maintainability
by formalizing the relationship between layers while maintaining the same functionality.
"""

import asyncio
import sys

from opendxa.execution import (
    PlanFactory,
    OptimalPlanExecutor,
    ExecutionContext,
    Objective
)
from opendxa.common import DXA_LOGGER
from opendxa.agent import LLMResource

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
        planning_llm=llm
    )
    
    return llm, context

async def process_results(signals, plan):
    """Process and display plan results."""
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

    # Display results in plan order
    node_order = plan.nodes.keys()
    for node_name in node_order:
        if node_name in results_by_node:
            print(f"\n## {node_name} ##")
            print(results_by_node[node_name])
    
    print("\n========== END OF ANALYSIS ==========")
    print("\nPlan execution completed successfully!")
    print("\nThis demonstrates how our refactored architecture:")
    print("1. Creates a reasoning graph from each plan node")
    print("2. Executes reasoning tasks with the LLM")
    print("3. Returns results through signals back up the stack")

async def main():
    """Run a Default plan to analyze customer reviews and recommend solutions."""
    # Set up logging
    await setup_logging()
    
    print("=================================================================")
    print("EXAMPLE: RUNNING A DEFAULT PLAN WITH OUR REFACTORED P-R STACK")
    print("=================================================================")
    print("\nThis example demonstrates:")
    print("1. Creating a Default plan with a specific objective")
    print("2. Setting up the executor hierarchy with our refactored code")
    print("3. Executing the plan through both layers")
    print("4. Processing and displaying the results in a structured way")
    print("\nStarting Customer Review Analysis plan...")
    
    # Create LLM and context
    llm, context = await create_llm_context()
    
    # Create a Default plan for customer review analysis
    objective = "Analyze customer reviews for a tech company's product, identify key issues, and recommend solutions."
    plan = PlanFactory.create_default_plan(objective=Objective(objective))
    
    # Print plan structure
    print("\nPlan Structure:")
    print(plan.pretty_print())
    print(f"\nCreated plan with {len(plan.nodes)} nodes")
    
    print("Creating PlanExecutor (top layer - orchestrates overall process)")
    plan_executor = OptimalPlanExecutor()
    
    # Execute plan
    print("\nExecuting plan using our refactored create_graph_from_node pattern...")
    print("This will create graphs at each layer derived from nodes in the layer above.")
    try:
        signals = await plan_executor.execute_plan(plan, context)
        await process_results(signals, plan)
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