"""
Mock agents for Dana TUI testing and demonstration.

These agents implement the Agent interface and provide realistic responses
for testing the TUI without requiring actual LLM resources.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import asyncio
from collections.abc import AsyncIterator

from .events import AgentEvent, Done, Error, FinalResult, Status, Token
from .runtime import Agent


class MockAgent(Agent):
    """Base mock agent with configurable responses."""

    def __init__(self, name: str, response_text: str = "Hello from mock agent!", delay: float = 0.1):
        super().__init__(name)
        self.response_text = response_text
        self.delay = delay
        self.chat_calls = []

    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """Mock chat implementation."""
        self.chat_calls.append(message)

        # Update metrics
        self.update_metric("is_running", True)
        self.update_metric("current_step", "processing")

        # Status update
        yield Status("thinking", f"Processing: {message}")

        # Simulate processing delay
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        # Generate response tokens
        for char in self.response_text:
            yield Token(char)
            if self.delay > 0:
                await asyncio.sleep(self.delay / len(self.response_text))

        # Final result
        yield FinalResult({"response": self.response_text, "message": message, "agent": self.name})

        # Update metrics
        self.update_metric("is_running", False)
        self.update_metric("current_step", "idle")

        yield Done()


class ResearchAgent(Agent):
    """Mock research agent that simulates finding papers and information."""

    def __init__(self):
        super().__init__("research")
        self.research_topics = {
            "ai": "Found 15 papers on AI: 'Deep Learning Advances' (2024), 'Neural Networks in Practice' (2023), 'Machine Learning Fundamentals' (2022)...",
            "machine learning": "Discovered 23 papers on machine learning including recent breakthroughs in transformer architectures and reinforcement learning applications.",
            "python": "Located 8 papers on Python programming: 'Modern Python Development' (2024), 'Python for Data Science' (2023)...",
            "dana": "Found 3 papers mentioning Dana language: 'Programming Language Design' (2024), 'AI-Assisted Development' (2023)...",
        }

    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """Simulate research agent responses."""
        self.update_metric("is_running", True)
        self.update_metric("current_step", "searching")

        yield Status("searching", f"Searching for: {message}")
        await asyncio.sleep(0.2)

        # Find relevant research
        response = "I couldn't find specific research on that topic."
        for topic, result in self.research_topics.items():
            if topic.lower() in message.lower():
                response = result
                break

        yield Status("analyzing", "Analyzing search results...")
        await asyncio.sleep(0.1)

        # Stream the response in word chunks for better readability
        words = response.split(" ")
        for i, word in enumerate(words):
            if i > 0:
                yield Token(" ")  # Add space between words
            yield Token(word)
            await asyncio.sleep(0.05)  # Slower word-by-word streaming

        yield FinalResult(
            {
                "papers_found": len([t for t in self.research_topics.keys() if t.lower() in message.lower()]),
                "response": response,
                "query": message,
            }
        )

        self.update_metric("is_running", False)
        self.update_metric("current_step", "idle")
        yield Done()


class CoderAgent(Agent):
    """Mock coding agent that simulates code generation and analysis."""

    def __init__(self):
        super().__init__("coder")
        self.code_templates = {
            "python": "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
            "function": "def process_data(data):\n    result = []\n    for item in data:\n        result.append(item * 2)\n    return result",
            "class": "class MyClass:\n    def __init__(self, name):\n        self.name = name\n    \n    def greet(self):\n        return f'Hello, {self.name}!'",
            "api": "from flask import Flask\n\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return 'Hello, World!'\n\nif __name__ == '__main__':\n    app.run()",
        }

    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """Simulate coding agent responses."""
        self.update_metric("is_running", True)
        self.update_metric("current_step", "coding")

        yield Status("analyzing", f"Analyzing request: {message}")
        await asyncio.sleep(0.2)

        # Generate code based on request
        response = "I can help you write code. What specific functionality do you need?"
        if "python" in message.lower():
            response = f"Here's a Python example:\n\n```python\n{self.code_templates['python']}\n```"
        elif "function" in message.lower():
            response = f"Here's a function example:\n\n```python\n{self.code_templates['function']}\n```"
        elif "class" in message.lower():
            response = f"Here's a class example:\n\n```python\n{self.code_templates['class']}\n```"
        elif "api" in message.lower() or "web" in message.lower():
            response = f"Here's a simple API example:\n\n```python\n{self.code_templates['api']}\n```"

        yield Status("generating", "Generating code...")
        await asyncio.sleep(0.1)

        # Stream the response in word chunks for better readability
        words = response.split(" ")
        for i, word in enumerate(words):
            if i > 0:
                yield Token(" ")  # Add space between words
            yield Token(word)
            await asyncio.sleep(0.05)  # Slower word-by-word streaming

        yield FinalResult(
            {
                "code_generated": "python" in message.lower() or "function" in message.lower() or "class" in message.lower(),
                "response": response,
                "language": "python",
            }
        )

        self.update_metric("is_running", False)
        self.update_metric("current_step", "idle")
        yield Done()


class PlannerAgent(Agent):
    """Mock planning agent that simulates project planning and task breakdown."""

    def __init__(self):
        super().__init__("planner")
        self.plan_templates = {
            "project": "1. Define requirements\n2. Create architecture\n3. Implement core features\n4. Testing and validation\n5. Deployment",
            "feature": "1. Research existing solutions\n2. Design the feature\n3. Implement prototype\n4. Get feedback\n5. Refine and deploy",
            "bugfix": "1. Reproduce the issue\n2. Identify root cause\n3. Create fix\n4. Test thoroughly\n5. Deploy and monitor",
        }

    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """Simulate planning agent responses."""
        self.update_metric("is_running", True)
        self.update_metric("current_step", "planning")

        yield Status("analyzing", f"Analyzing planning request: {message}")
        await asyncio.sleep(0.2)

        # Generate plan based on request
        response = "I can help you create a plan. What type of planning do you need?"
        if "project" in message.lower():
            response = f"Here's a project plan:\n\n{self.plan_templates['project']}"
        elif "feature" in message.lower():
            response = f"Here's a feature development plan:\n\n{self.plan_templates['feature']}"
        elif "bug" in message.lower() or "fix" in message.lower():
            response = f"Here's a bug fix plan:\n\n{self.plan_templates['bugfix']}"

        yield Status("planning", "Creating detailed plan...")
        await asyncio.sleep(0.1)

        # Stream the response in word chunks for better readability
        words = response.split(" ")
        for i, word in enumerate(words):
            if i > 0:
                yield Token(" ")  # Add space between words
            yield Token(word)
            await asyncio.sleep(0.05)  # Slower word-by-word streaming

        yield FinalResult(
            {
                "plan_created": any(word in message.lower() for word in ["project", "feature", "bug", "fix"]),
                "response": response,
                "plan_type": "project"
                if "project" in message.lower()
                else "feature"
                if "feature" in message.lower()
                else "bugfix"
                if "bug" in message.lower() or "fix" in message.lower()
                else "general",
            }
        )

        self.update_metric("is_running", False)
        self.update_metric("current_step", "idle")
        yield Done()


class ErrorAgent(Agent):
    """Mock agent that simulates errors for testing error handling."""

    def __init__(self, name: str = "error_agent"):
        super().__init__(name)
        self.error_count = 0

    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """Simulate agent that sometimes fails."""
        self.error_count += 1

        yield Status("processing", f"Processing: {message}")
        await asyncio.sleep(0.1)

        # Simulate occasional errors
        if self.error_count % 3 == 0:
            yield Error("Simulated error for testing purposes")
            return

        yield Token("Successfully processed: ")
        yield Token(message)
        yield Done()


class SlowAgent(Agent):
    """Mock agent that takes a long time to respond for testing timeouts."""

    def __init__(self, name: str = "slow_agent", delay: float = 2.0):
        super().__init__(name)
        self.delay = delay

    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """Simulate slow agent responses."""
        yield Status("thinking", f"Taking my time to process: {message}")

        # Long delay
        await asyncio.sleep(self.delay)

        yield Status("responding", "Finally ready to respond...")
        yield Token("This took a while, but here's my response: ")
        yield Token(message.upper())
        yield Done()
