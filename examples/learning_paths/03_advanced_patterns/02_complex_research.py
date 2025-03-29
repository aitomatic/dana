"""Complex research workflow example."""

import asyncio
from dxa.agent import Agent
from dxa.execution.workflow.workflow_factory import WorkflowFactory
from dxa.execution import WorkflowStrategy, ReasoningStrategy

def create_research_workflow():
    """Create predefined research steps."""
    return WorkflowFactory.create_basic_workflow(
        objective="Research AI safety",
        commands=[
            "Identify key AI safety organizations",
            "Analyze their research focus areas",
            "Compare approaches to value alignment",
            "Generate summary report"
        ]
    )

async def execute_research_step(agent, step):
    """Execute individual research step with enhanced logging."""
    print(f"Executing step: {step.description}")
    result = await agent.runtime.execute_step(step)
    print(f"Step completed: {step.description[:50]}...")
    return result

async def run_research():
    """Main research execution flow."""
    agent = (Agent("research_agent")
             .with_reasoning(ReasoningStrategy.CHAIN_OF_THOUGHT)
             .with_workflow(WorkflowStrategy.SEQUENTIAL))
    
    workflow = create_research_workflow()
    results = []
    
    async with agent:
        for step in workflow.nodes.values():
            if step.node_type == "TASK":
                results.append(await execute_research_step(agent, step))
                
    print("\nFinal Research Summary:")
    for i, result in enumerate(results, 1):
        print(f"Step {i}: {result['content'][:100]}...")

if __name__ == "__main__":
    asyncio.run(run_research()) 