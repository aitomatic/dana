"""Research Assistant Example using Chain of Thought Reasoning.

This example demonstrates using Chain of Thought (CoT) reasoning for structured
research tasks. CoT is particularly suited for research because it:

1. Breaks down complex topics systematically
2. Maintains clear reasoning paths
3. Synthesizes information coherently

Key Components:
-------------
- Reasoning: Uses CoT for structured analysis
- Resource: LLM for information processing
- Task Structure: 
  * Clear objective
  * Specific research points
  * Context parameters

Usage:
-----
python examples/research_assistant.py

The agent will:
1. Understand the research objective
2. Break down the topic
3. Analyze each component
4. Synthesize findings
5. Present structured results
"""

import asyncio
from typing import Dict, Any
from dxa.agent import Agent
from dxa.core.resource import LLMResource
from dxa.common.errors import ConfigurationError

async def main():
    """Run the research assistant."""
    try:
        # Create research agent with CoT reasoning
        agent = Agent("researcher")\
            .with_reasoning("cot")  # CoT for structured analysis
            
        # Add LLM resource
        agent.with_resources({
            "llm": LLMResource(model="gpt-4")
        })
        
        # Research task
        task = {
            "objective": "Research and summarize quantum computing",
            "command": """
            Provide a comprehensive overview of quantum computing:
            1. Basic principles
            2. Current state of technology
            3. Major challenges
            4. Future implications
            """,
            "context": {
                "depth": "technical",
                "audience": "computer science students"
            }
        }
        
        try:
            # Execute research
            result = await agent.run(task)
            
            # Display results
            print("\nResearch Results:")
            print("-" * 50)
            print(f"Topic: {task['objective']}")
            print(f"\nFindings:\n{result}")
            
        except Exception as e:
            print(f"Research error: {e}")
            
        finally:
            await agent.cleanup()
            
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 