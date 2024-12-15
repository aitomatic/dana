"""Example template for DXA agents.

This template demonstrates how to create a new agent with:
1. Specific reasoning pattern
2. Required resources
3. Error handling
4. Proper cleanup
"""

import asyncio
from typing import Dict, Any
from dxa.agent import Agent
from dxa.core.resource import LLMResource
from dxa.common.errors import ConfigurationError

async def main():
    """Run the example agent."""
    try:
        # 1. Create agent with specific reasoning
        agent = Agent("example_agent")\
            .with_reasoning("cot")  # Choose: direct, cot, ooda, or dana
            
        # 2. Add required resources
        agent.with_resources({
            "llm": LLMResource(model="gpt-4")
        })
        
        # 3. Define task
        task = {
            "objective": "What we want to achieve",
            "command": "Specific instruction or query",
            "context": {
                "key": "Additional context if needed"
            }
        }
        
        # 4. Execute task
        try:
            result = await agent.run(task)
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"Execution error: {e}")
            
        # 5. Cleanup
        finally:
            await agent.cleanup()
            
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 