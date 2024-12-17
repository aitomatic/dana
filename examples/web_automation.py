"""Web automation example using DXA."""

from dxa.agent import Agent
from dxa.core.resource import LLMResource, BrowserResource, DatabaseResource

async def main():
    """Run web automation task."""
    
    # Create automation agent
    agent = Agent("automator")\
        .with_reasoning("ooda")\  # Good for dynamic web interaction
        .with_resources({
            "llm": LLMResource(model="gpt-4"),
            "browser": BrowserResource(),  # For web interaction
            "db": DatabaseResource()  # For data storage
        })\
        .with_capabilities(["web_automation", "data_extraction"])

    # Run automation task
    async with agent:
        result = await agent.run({
            "type": "web_automation",
            "target_url": "https://example.com",
            "actions": [
                "login",
                "navigate_to_data",
                "extract_information",
                "store_results"
            ],
            "data_schema": {
                "fields": ["title", "price", "availability"]
            }
        })
        
        print("Automation Results:")
        print(result) 