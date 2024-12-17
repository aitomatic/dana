"""System monitoring example using DXA."""

from dxa.agent import Agent
from dxa.core.resource import LLMResource, SystemResource, AlertResource

async def main():
    """Run system monitoring agent."""
    
    # Create monitoring agent with OODA reasoning
    agent = Agent("monitor")\
        .with_reasoning("ooda")\  # Good for continuous monitoring
        .with_resources({
            "llm": LLMResource(model="gpt-4"),
            "system": SystemResource(),  # For metrics collection
            "alerts": AlertResource()    # For notifications
        })\
        .with_capabilities(["monitoring", "analysis"])

    # Run monitoring loop
    async with agent:
        while True:
            result = await agent.run({
                "type": "monitor",
                "metrics": ["cpu", "memory", "disk", "network"],
                "thresholds": {
                    "cpu_percent": 80,
                    "memory_percent": 90,
                    "disk_percent": 95
                }
            })
            
            if result.get("alerts"):
                print("Alerts:", result["alerts"]) 