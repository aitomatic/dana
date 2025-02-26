# examples/basic/workflow/custom_define_workflow.py

"""
Example demonstrating how to customize a single prompt in the default workflow.

This example shows how to:
1. Create a default workflow with a custom "define_problem" prompt
2. Execute the workflow to see the customized output
"""

from dxa.execution import WorkflowFactory, WorkflowExecutor, PlanExecutor, ExecutionContext
from dxa.llm import LLMFactory
import asyncio

async def main():
    """Create and execute a default workflow with a custom define_problem prompt."""
    
    # Define the objective
    objective = "Design a mobile app for tracking personal fitness goals"
    
    # Define a custom prompt just for the problem definition step
    custom_prompts = {
        "default.define_problem": """
        Define the scope and objectives for a fitness tracking mobile app:
        
        {objective}
        
        Your definition should include:
        1. Primary user personas (e.g., casual exercisers, serious athletes)
        2. Core features the app must include
        3. Key differentiators from existing fitness apps
        4. Technical constraints to consider
        5. Success metrics for the app (user engagement, retention, etc.)
        6. Potential monetization strategies
        
        Be specific and actionable in your definition to guide the rest of the development process.
        """
    }
    
    # Create the workflow with the custom prompt
    workflow = WorkflowFactory.create_workflow_by_name(
        "default",
        objective=objective,
        agent_role="Product Manager",
        custom_prompts=custom_prompts
    )
    
    print(f"Created workflow: {workflow.name}")
    print(f"Objective: {workflow.objective.original}")
    print(f"Number of nodes: {len(workflow.nodes)}")
    
    # Print the customized prompt
    define_node = workflow.get_node_by_id("DEFINE")
    if define_node:
        print("\nCustomized DEFINE node:")
        print(f"Description: {define_node.description}")
        print(f"Prompt reference: {define_node.metadata.get('prompt')}")
    
    # Set up execution components
    llm = LLMFactory.create_llm("openai")
    plan_executor = PlanExecutor()
    workflow_executor = WorkflowExecutor(plan_executor=plan_executor)
    
    # Create execution context
    context = ExecutionContext()
    context.reasoning_llm = llm
    
    print("\nExecuting workflow...")
    
    # Execute the workflow
    result = await workflow_executor.execute(workflow, context)
    
    # Print just the DEFINE step result to see the effect of our custom prompt
    for signal in result:
        if signal.source == "DEFINE" and "result" in signal.content:
            content = signal.content["result"]["content"]
            print("\n=== DEFINE Step Result (Using Custom Prompt) ===\n")
            print(content)
            break
    
    print("\nWorkflow execution completed!")

if __name__ == "__main__":
    asyncio.run(main())