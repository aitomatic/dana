"""Example of using a local workflow configuration file."""

import asyncio
import os
from pathlib import Path

from dxa.execution import WorkflowFactory, WorkflowExecutor, PlanExecutor, ReasoningExecutor
from dxa.execution import ExecutionContext
from dxa.llm import OpenAILLM

async def main():
    """Run the example."""
    # Set up the LLM
    llm = OpenAILLM(model="gpt-3.5-turbo")
    
    # Create the execution context
    context = ExecutionContext(reasoning_llm=llm)
    
    # Path to the local config directory
    # This example assumes you have a 'configs' directory in the same folder as this script
    config_dir = Path(__file__).parent / "configs"
    
    # Create the directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    # Create a sample config file if it doesn't exist
    sample_config_path = config_dir / "custom_workflow.yaml"
    if not sample_config_path.exists():
        with open(sample_config_path, "w") as f:
            f.write("""
name: "Custom Workflow"
description: "A custom workflow example"
version: 1.0
role: "Custom Workflow Agent"
type: SEQUENTIAL

nodes:
  - id: ANALYZE
    description: "Analyze the problem in detail"
    
  - id: SOLVE
    description: "Solve the problem based on the analysis"
    
  - id: REVIEW
    description: "Review the solution for correctness"

prompts:
  ANALYZE: |
    Please analyze the following problem:
    
    {objective}
    
    Provide a detailed analysis including:
    1. Key aspects of the problem
    2. Potential challenges
    3. Resources needed
    
  SOLVE: |
    Based on your analysis, solve the following problem:
    
    {objective}
    
    Provide a step-by-step solution.
    
  REVIEW: |
    Review your solution to:
    
    {objective}
    
    Ensure it's correct, complete, and addresses all aspects of the problem.
""")
    
    # Create the workflow using the local config
    objective = "Design a simple inventory management system for a small retail store"
    workflow = WorkflowFactory.create_from_config(
        "custom_workflow",
        objective,
        role="Inventory System Designer",
        config_dir=config_dir
    )
    
    print(f"Created workflow: {workflow.name}")
    print(f"Objective: {workflow.objective.original}")
    print(f"Role: {workflow.metadata.get('role')}")
    print(f"Nodes: {', '.join(workflow.nodes.keys())}")
    
    # Set up the execution pipeline
    reasoning_executor = ReasoningExecutor()
    plan_executor = PlanExecutor(reasoning_executor=reasoning_executor)
    workflow_executor = WorkflowExecutor(plan_executor=plan_executor)
    
    # Execute the workflow
    print("\nExecuting workflow...\n")
    signals = await workflow_executor.execute_workflow(workflow, context)
    
    # Print the results
    print("\nWorkflow execution complete. Results:")
    for signal in signals:
        if 'result' in signal.content:
            node_id = signal.source_id
            result = signal.content['result'].get('content', '')
            print(f"\n--- {node_id} ---")
            print(result[:500] + "..." if len(result) > 500 else result)

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Please set the OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY=your-api-key")
        exit(1)
        
    asyncio.run(main()) 