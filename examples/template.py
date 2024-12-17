"""Template for creating DXA agents."""

from dxa.agent import Agent, AgentFactory
from dxa.core.resource import LLMResource

def create_basic_agent() -> Agent:
    """Create a basic agent with minimal configuration."""
    return Agent("basic")\
        .with_reasoning("direct")\
        .with_resources({
            "llm": LLMResource(model="gpt-4")
        })

def create_advanced_agent() -> Agent:
    """Create an advanced agent using factory configuration."""
    return AgentFactory.from_config({
        "name": "advanced",
        "reasoning": "cot",
        "resources": {
            "llm": LLMResource(model="gpt-4")
        },
        "capabilities": ["memory", "planning"]
    })

async def main():
    """Example usage."""
    # Basic usage - ignore result
    agent = create_basic_agent()
    await agent.run("Simple task")

    # Advanced usage - use result
    async with create_advanced_agent() as agent:
        result = await agent.run({
            "objective": "Complex task",
            "context": {"key": "value"}
        })
        print(f"Task result: {result}")