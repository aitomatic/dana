"""Chat Bot Example using Direct Reasoning.

This example demonstrates using Direct reasoning for conversational interactions.
Direct reasoning is perfect for chat because it:

1. Provides immediate responses
2. Handles simple query-response patterns
3. Maintains conversation flow

Key Components:
-------------
- Reasoning: Uses Direct for simple interactions
- Resource: LLM for response generation
- IO: Console for user interaction
- Context Management:
  * Conversation style
  * Response format
  * User interaction loop

Usage:
-----
python examples/chat_bot.py

Features:
1. Interactive console interface
2. Natural conversation flow
3. Simple command handling
4. Clean exit mechanism

The chat bot will:
1. Accept user input
2. Process using direct reasoning
3. Generate appropriate responses
4. Maintain conversation until exit
"""

import asyncio
from typing import Dict, Any
from dxa.agent import Agent
from dxa.core.resource import LLMResource
from dxa.core.io import ConsoleIO
from dxa.common.errors import ConfigurationError

async def main():
    """Run the chat bot."""
    try:
        # Create chat agent with Direct reasoning
        agent = Agent("chatbot")\
            .with_reasoning("direct")  # Direct for simple interactions
            
        # Add resources
        agent.with_resources({
            "llm": LLMResource(model="gpt-4")
        })
        
        # Add console I/O
        agent.with_io(ConsoleIO())
        
        print("\nChat Bot Started (type 'exit' to quit)")
        print("-" * 50)
        
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'exit':
                break
                
            # Chat task
            task = {
                "objective": "Engage in conversation",
                "command": user_input,
                "context": {
                    "style": "friendly",
                    "format": "chat"
                }
            }
            
            try:
                # Get response
                result = await agent.run(task)
                print(f"\nBot: {result}")
                
            except Exception as e:
                print(f"Chat error: {e}")
                
        # Cleanup
        await agent.cleanup()
            
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 