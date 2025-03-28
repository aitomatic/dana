#!/usr/bin/env python3
"""Example script to run a simple DXA workflow."""

import asyncio

from dxa.agent.resource import LLMResource
from dxa.agent.state import AgentState, WorldState, ExecutionState
from dxa.execution.workflow.workflow_factory import WorkflowFactory
from dxa.execution.workflow.workflow_executor import WorkflowExecutor
from dxa.execution import ExecutionContext
from dxa.execution.execution_types import ExecutionSignalType, Objective

async def main():
    """Run a simple DXA workflow."""
    # Create LLM resource
    llm = LLMResource(name="simple_workflow_llm")
    
    # Create a simple workflow with three steps
    workflow = WorkflowFactory.create_sequential_workflow(
        objective=Objective("Demonstrate basic workflow execution"),
        commands=[
            "Step 1: Initialize",
            "Step 2: Process",
            "Step 3: Finalize"
        ]
    )
    
    # Create execution context
    context = ExecutionContext(
        agent_state=AgentState(),
        world_state=WorldState(),
        execution_state=ExecutionState(),
        workflow_llm=llm,
        planning_llm=llm,
        reasoning_llm=llm
    )
    
    # Create workflow executor
    executor = WorkflowExecutor()
    
    # Execute workflow
    signals = await executor.execute_workflow(workflow, context)

    # Print results
    print("\nWorkflow Results:")
    for signal in signals:
        if signal.type == ExecutionSignalType.DATA_RESULT:
            node_id = signal.content.get("node")
            result = signal.content.get("result")
            print(f"\nNode: {node_id}")
            print(f"Result: {result}")
    
    # Cleanup
    await llm.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 