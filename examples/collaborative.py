"""Collaborative agents example using DXA."""

from dxa.agent import Agent
from dxa.core.resource import LLMResource, AgentResource

async def create_specialist(name: str, expertise: str) -> Agent:
    """Create a specialist agent."""
    return Agent(f"{expertise}_specialist")\
        .with_reasoning("cot")\
        .with_resources({
            "llm": LLMResource(model="gpt-4")
        })\
        .with_capabilities([expertise])

async def main():
    """Run collaborative research task."""
    
    # Create specialist agents
    async with (
        await create_specialist("physics", "quantum") as quantum_agent,
        await create_specialist("cs", "algorithms") as algo_agent
    ):
        # Create coordinator agent
        coordinator = Agent("coordinator")\
            .with_reasoning("ooda")\
            .with_resources({
                "llm": LLMResource(model="gpt-4"),
                "quantum_expert": AgentResource(quantum_agent),
                "algo_expert": AgentResource(algo_agent)
            })
        
        # Run collaborative task
        async with coordinator:
            result = await coordinator.run({
                "objective": "Analyze quantum computing algorithms",
                "aspects": [
                    "quantum_principles",
                    "algorithmic_complexity",
                    "implementation_challenges"
                ]
            })
            
            print("Collaborative Analysis:")
            print(result) 