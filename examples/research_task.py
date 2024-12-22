"""
Multi-step research task demonstrating sequential planning.
Shows how DXA breaks down complex tasks into steps.
"""

from dxa import DXAFactory
from dxa.core.planning import SequentialPlanner
from dxa.core.reasoning import DirectReasoner
from dxa.core.flow.research_flow import ResearchFlow

async def main():
    """Run research task example."""
    
    agent = DXAFactory.create_agent({"name": "researcher"}) \
        .with_llm("gpt-4") \
        .with_planner(SequentialPlanner()) \
        .with_reasoner(DirectReasoner())

    result = await agent.run(
        ResearchFlow("Research quantum computing and summarize its potential impact on cryptography")
    )

    print("\nResearch Results:")
    print(f"Status: {result['status']}")
    print("\nFindings:")
    for step in result["steps"]:
        print(f"\n{step['description']}:")
        print(step['result'])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 