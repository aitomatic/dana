"""Example demonstrating workflow-planning-reasoning expansion and data flow.

This example shows how:
1. A workflow is expanded into planning steps
2. Planning steps are expanded into reasoning steps
3. Data flows between steps and up through the layers
4. Results are propagated back to the workflow level

The example implements a simple data analysis pipeline:
1. Gather data
2. Process data
3. Generate insights
"""

import asyncio
from typing import Dict, Any, Tuple

from dxa.execution import (
    WorkflowExecutor,
    ExecutionContext, Objective, ExecutionNode, ExecutionSignal
)
from dxa.execution.workflow import Workflow
from dxa.common.graph import NodeType
from dxa.agent.resource import LLMResource
from dxa.common.utils.logging import DXA_LOGGER

# Configure logging
DXA_LOGGER.configure(
    level=DXA_LOGGER.DEBUG,
    console=True,
    log_data=True
)
logger = DXA_LOGGER.getLogger(__name__)

async def create_workflow() -> Workflow:
    """Create a workflow with data dependencies."""
    logger.info("Creating workflow with data dependencies")
    
    workflow = Workflow(objective=Objective("Analyze customer feedback data"))
    
    # Add workflow steps
    start_node = ExecutionNode(
        node_id="START",
        node_type=NodeType.START,
        objective="Start analysis"
    )
    workflow.add_node(start_node)
    
    # Step 1: Gather feedback
    gather_node = ExecutionNode(
        node_id="GATHER",
        node_type=NodeType.TASK,
        objective="Gather customer feedback data",
        metadata={
            "output_key": "feedback_data",
            "task_type": "data_collection"
        }
    )
    workflow.add_node(gather_node)
    
    # Step 2: Process data
    process_node = ExecutionNode(
        node_id="PROCESS",
        node_type=NodeType.TASK,
        objective="Process and clean the feedback data",
        metadata={
            "input_key": "feedback_data",
            "output_key": "processed_data",
            "task_type": "data_processing"
        }
    )
    workflow.add_node(process_node)
    
    # Step 3: Generate insights
    analyze_node = ExecutionNode(
        node_id="ANALYZE",
        node_type=NodeType.TASK,
        objective="Analyze processed data and generate insights",
        metadata={
            "input_key": "processed_data",
            "output_key": "insights",
            "task_type": "analysis"
        }
    )
    workflow.add_node(analyze_node)
    
    end_node = ExecutionNode(
        node_id="END",
        node_type=NodeType.END,
        objective="End analysis"
    )
    workflow.add_node(end_node)
    
    # Add edges
    workflow.add_edge_between("START", "GATHER")
    workflow.add_edge_between("GATHER", "PROCESS")
    workflow.add_edge_between("PROCESS", "ANALYZE")
    workflow.add_edge_between("ANALYZE", "END")
    
    logger.info("Workflow created with %d nodes", len(workflow.nodes))
    return workflow

async def setup_execution_context() -> Tuple[ExecutionContext, LLMResource]:
    """Set up the execution context with LLM resources."""
    logger.info("Setting up execution context")
    
    # Create LLM resource
    llm = LLMResource()
    await llm.initialize()
    
    # Create execution context
    context = ExecutionContext(
        reasoning_llm=llm,
        planning_llm=llm,
        workflow_llm=llm
    )
    
    return context, llm

def process_signals(signals: list[ExecutionSignal]) -> Dict[str, Any]:
    """Process execution signals and extract results."""
    logger.info("Processing execution signals")
    
    results = {}
    for signal in signals:
        if hasattr(signal, 'content') and 'result' in signal.content:
            node_name = signal.content.get('node', 'Unknown')
            result = signal.content['result']
            if isinstance(result, dict) and 'content' in result:
                results[node_name] = result['content']
                logger.debug("Extracted result for node %s", node_name)
    
    return results

def display_results(results: Dict[str, Any]) -> None:
    """Display execution results in a structured format."""
    logger.info("Displaying execution results")
    
    print("\nWorkflow Execution Results:")
    print("==========================")
    
    for node_name in ["GATHER", "PROCESS", "ANALYZE"]:
        if node_name in results:
            print(f"\n{node_name} Output:")
            print("-" * (len(node_name) + 8))
            print(results[node_name])
            print()

async def main():
    """Main function to demonstrate workflow-planning-reasoning expansion."""
    try:
        # Create workflow
        workflow = await create_workflow()
        
        # Set up execution context
        context, llm = await setup_execution_context()
        
        # Set up executors
        logger.info("Setting up execution pipeline")
        workflow_executor = WorkflowExecutor()
        
        # Execute workflow
        logger.info("Executing workflow")
        signals = await workflow_executor.execute_workflow(workflow, context)
        
        # Process and display results
        results = process_signals(signals)
        display_results(results)
        
        logger.info("Workflow execution completed successfully")
        return True
        
    except Exception as e:
        logger.error("Error during execution: %s", str(e), exc_info=True)
        return False
        
    finally:
        # Clean up resources
        if 'llm' in locals():
            await llm.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 