"""
Simple Q&A example demonstrating core DXA architecture.
Uses direct planning and reasoning patterns with GPT-4.
"""

from dxa import DXAFactory
from dxa.core.planning import DirectPlanner
from dxa.core.reasoning import DirectReasoner

async def main():
    """Run simple Q&A example."""

    agent = DXAFactory.create_agent({"name": "qa_agent"}) \
        .with_llm("gpt-4") \
        .with_planner(DirectPlanner()) \
        .with_reasoner(DirectReasoner())

    result = await agent.run("What is quantum computing?")

    print("\nQuestion: What is quantum computing?")
    print(f"Answer: {result['result']['answer']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())