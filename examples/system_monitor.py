"""System Monitor Example using OODA Loop Reasoning.

This example demonstrates using OODA (Observe, Orient, Decide, Act) reasoning
for continuous system monitoring. OODA is ideal for monitoring because it:

1. Continuously observes system state
2. Adapts to changing conditions
3. Makes real-time decisions
4. Takes appropriate actions

Key Components:
-------------
- Reasoning: Uses OODA for adaptive monitoring
- Resource: LLM for analysis and decision making
- Monitoring Parameters:
  * CPU and memory thresholds
  * Error rate limits
  * Monitoring intervals

Usage:
-----
python examples/system_monitor.py

The OODA cycle:
1. OBSERVE: Gather system metrics
2. ORIENT: Analyze current state
3. DECIDE: Choose response if needed
4. ACT: Implement necessary changes
"""

import asyncio
from typing import Dict, Any
from dxa.agent import Agent
from dxa.core.resource import LLMResource
from dxa.common.errors import ConfigurationError

async def main():
    """Run the system monitor."""
    try:
        # Create monitor agent with OODA reasoning
        agent = Agent("monitor")\
            .with_reasoning("ooda")  # OODA for adaptive monitoring
            
        # Add LLM resource
        agent.with_resources({
            "llm": LLMResource(model="gpt-4")
        })
        
        # Monitoring task
        task = {
            "objective": "Monitor system health and respond to issues",
            "command": """
            Monitor these system aspects:
            1. CPU usage
            2. Memory utilization
            3. Network traffic
            4. Error rates
            
            Respond to any anomalies or issues detected.
            """,
            "context": {
                "thresholds": {
                    "cpu_max": 80,
                    "memory_max": 90,
                    "error_rate_max": 0.01
                },
                "monitoring_interval": "5m"
            }
        }
        
        try:
            # Execute monitoring
            result = await agent.run(task)
            
            # Display results
            print("\nMonitoring Results:")
            print("-" * 50)
            print(f"Status: Active")
            print(f"Findings:\n{result}")
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            
        finally:
            await agent.cleanup()
            
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 