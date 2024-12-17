"""Research assistant example using DXA."""

from dxa.agent import Agent
from dxa.core.resource import LLMResource, SearchResource, DatabaseResource

async def main():
    """Run research assistant."""
    
    # Create research agent with CoT reasoning
    agent = Agent("researcher")\
        .with_reasoning("cot")\  # Better for complex tasks
        .with_resources({
            "llm": LLMResource(model="gpt-4"),
            "search": SearchResource(),
            "db": DatabaseResource()
        })\
        .with_capabilities(["research", "analysis"])

    # Run research task
    async with agent:
        result = await agent.run({
            "objective": "Research quantum computing advances",
            "depth": "technical",
            "format": "structured_report"
        })
        
        print("Research Report:")
        print(result) 