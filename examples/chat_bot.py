"""Interactive chat bot example using DXA."""

from dxa.agent import Agent
from dxa.core.resource import LLMResource, HumanResource

async def main():
    """Run interactive chat bot."""
    
    # Create chat agent
    agent = Agent("chat_bot")\
        .with_reasoning("direct")\  # Simple reasoning for chat
        .with_resources({
            "llm": LLMResource(model="gpt-4"),
            "human": HumanResource()  # For interactive I/O
        })

    # Run chat loop
    async with agent:  # Handles cleanup
        while True:
            user_input = input("> ")
            if user_input.lower() == "exit":
                break
                
            response = await agent.run({
                "type": "chat",
                "input": user_input,
                "context": {"mode": "conversational"}
            })
            print(f"Bot: {response}") 