"""Math Solver Example using DANA (Domain-Aware NeuroSymbolic) Reasoning.

This example demonstrates using DANA reasoning for mathematical computation.
DANA combines neural and symbolic approaches, making it ideal for math because:

1. Neural: Understands problem structure and strategy
2. Symbolic: Performs precise calculations
3. Domain-Aware: Applies mathematical rules correctly

Key Components:
-------------
- Reasoning: Uses DANA for hybrid computation
- Resource: LLM for problem understanding
- Problem Structure:
  * Clear mathematical objective
  * Step-by-step solution requirements
  * Precision parameters

Usage:
-----
python examples/math_solver.py

Solution Process:
1. Neural: Understand the problem
2. Symbolic: Apply mathematical operations
3. Neural: Explain results
4. Validate: Check solution correctness
"""

import asyncio
from typing import Dict, Any
from dxa.agent import Agent
from dxa.core.resource import LLMResource
from dxa.common.errors import ConfigurationError

async def main():
    """Run the math solver."""
    try:
        # Create solver agent with DANA reasoning
        agent = Agent("solver")\
            .with_reasoning("dana")  # DANA for hybrid computation
            
        # Add LLM resource
        agent.with_resources({
            "llm": LLMResource(model="gpt-4")
        })
        
        # Math problem
        task = {
            "objective": "Solve optimization problem",
            "command": """
            Find the minimum of the function:
            f(x) = x^2 - 4x + 4
            
            Show:
            1. First derivative
            2. Critical points
            3. Second derivative test
            4. Global minimum
            """,
            "context": {
                "domain": "calculus",
                "precision": "exact",
                "show_work": True
            }
        }
        
        try:
            # Execute calculation
            result = await agent.run(task)
            
            # Display results
            print("\nMath Solution:")
            print("-" * 50)
            print(f"Problem: {task['objective']}")
            print(f"\nSolution:\n{result}")
            
        except Exception as e:
            print(f"Calculation error: {e}")
            
        finally:
            await agent.cleanup()
            
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 