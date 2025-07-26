#!/usr/bin/env python3
"""
Reasoning Agent - A2A Deployment Script

Deploys the LangGraph Reasoning Agent as an A2A (Agent-to-Agent) service.
This script wraps the existing ReasoningAgent implementation and exposes it
via the python-a2a protocol for inter-agent communication.

Usage:
    python deploy_reasoning_agent_a2a.py --host localhost --port 5002 --debug

Example queries the agent can handle:
    - "What's the weather in Tokyo?"
    - "Explain machine learning concepts"
    - "Analyze renewable energy benefits"
    - "Reason about complex problems"

Author: OpenDXA Team
Version: 1.0.0
"""

import argparse
import asyncio
import logging
import os
from typing import Any

try:
    from python_a2a import A2AServer, TaskState, TaskStatus, agent, run_server, skill
except ImportError:
    print("Error: python-a2a library not found. Please install it with:")
    print("pip install python-a2a")
    exit(1)

# Import the existing ReasoningAgent
from reasoning_agent_langgraph_fixed import AgentConfig, ReasoningAgent


@agent(
    name="LangGraph Reasoning Agent",
    description="Advanced reasoning agent using LangGraph with MCP tool integration for complex problem solving",
    version="1.0.0",
)
class ReasoningAgentA2A(A2AServer):
    """
    A2A wrapper for the LangGraph Reasoning Agent.

    This agent provides advanced reasoning capabilities with MCP tool integration,
    deployed as an A2A service for inter-agent communication.
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing LangGraph Reasoning Agent A2A wrapper")

        # Initialize the underlying reasoning agent
        try:
            config = AgentConfig(
                agent_name="LangGraph Reasoning Agent", agent_description="Advanced reasoning agent with MCP tool integration"
            )
            self.reasoning_agent = ReasoningAgent(config)
            self.logger.info("✅ LangGraph Reasoning Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize LangGraph Reasoning Agent: {e}")
            raise

    @skill(
        name="Advanced Reasoning",
        description="Perform advanced reasoning and problem-solving with MCP tool integration",
        tags=["reasoning", "problem-solving", "analysis", "mcp", "tools"],
    )
    def reason_about_question(self, question: str) -> str:
        """
        Perform advanced reasoning about any question or problem.

        Args:
            question: The question or problem to reason about

        Returns:
            Detailed reasoning response with insights and analysis
        """
        try:
            self.logger.info(f"🤔 Processing reasoning request: {question}")

            # Use the async solve method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.reasoning_agent.solve(question))
                self.logger.info("✅ Successfully processed reasoning request")
                return result
            finally:
                loop.close()

        except Exception as e:
            error_msg = f"Error during reasoning: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return f"I apologize, but I encountered an error while reasoning about your question: {str(e)}"

    @skill(
        name="Weather Analysis",
        description="Get weather information and provide recommendations based on conditions",
        tags=["weather", "analysis", "recommendations", "mcp"],
    )
    def analyze_weather(self, location: str) -> str:
        """
        Get weather information and provide analysis and recommendations.

        Args:
            location: The location to get weather information for

        Returns:
            Weather information with analysis and recommendations
        """
        question = f"What is the weather in {location} and what recommendations do you have?"
        return self.reason_about_question(question)

    @skill(
        name="Concept Explanation",
        description="Explain complex concepts in simple, understandable terms",
        tags=["explanation", "education", "concepts", "analysis"],
    )
    def explain_concept(self, concept: str) -> str:
        """
        Explain complex concepts in simple terms.

        Args:
            concept: The concept to explain

        Returns:
            Clear, detailed explanation of the concept
        """
        question = f"Explain the concept of {concept} in simple, understandable terms"
        return self.reason_about_question(question)

    def handle_task(self, task) -> Any:
        """
        Handle incoming A2A tasks and route them to appropriate skills.

        Args:
            task: The A2A task object containing the message

        Returns:
            Updated task with response
        """
        try:
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})

            # Handle different content types
            if isinstance(content, dict):
                text = content.get("text", "")
            elif isinstance(content, str):
                text = content
            else:
                text = str(content)

            text = text.strip()
            self.logger.info(f"📨 Processing A2A task: {text}")

            if not text:
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Please provide a question or topic for me to reason about. I can help with weather analysis, concept explanations, problem-solving, and general reasoning tasks.",
                        },
                    },
                )
                return task

            # Route to appropriate skill based on content
            try:
                if any(keyword in text.lower() for keyword in ["weather", "temperature", "forecast", "climate"]):
                    # Extract location for weather queries
                    location = self._extract_location(text)
                    if location:
                        response = self.analyze_weather(location)
                    else:
                        response = self.reason_about_question(text)
                elif any(keyword in text.lower() for keyword in ["explain", "what is", "concept", "definition"]):
                    # Extract concept for explanation
                    concept = self._extract_concept(text)
                    if concept:
                        response = self.explain_concept(concept)
                    else:
                        response = self.reason_about_question(text)
                else:
                    # General reasoning
                    response = self.reason_about_question(text)

                # Set successful response
                task.artifacts = [{"parts": [{"type": "text", "text": response}]}]
                task.status = TaskStatus(state=TaskState.COMPLETED)

                self.logger.info("✅ Successfully processed A2A task")

            except Exception as e:
                self.logger.error(f"❌ Error processing reasoning task: {e}")
                task.status = TaskStatus(
                    state=TaskState.FAILED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": f"I apologize, but I encountered an error while processing your request: {str(e)}",
                        },
                    },
                )

        except Exception as e:
            self.logger.error(f"❌ Error handling A2A task: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"role": "agent", "content": {"type": "text", "text": f"I apologize, but I encountered a system error: {str(e)}"}},
            )

        return task

    def _extract_location(self, text: str) -> str:
        """Extract location from natural language text."""
        text_lower = text.lower()

        # Common patterns for location extraction
        patterns = [" in ", " for ", " at ", "weather in ", "weather for ", "temperature in "]

        for pattern in patterns:
            if pattern in text_lower:
                parts = text_lower.split(pattern, 1)
                if len(parts) > 1:
                    location = parts[1].strip().rstrip("?.,!").strip()
                    # Clean up common suffixes
                    location = location.replace(" please", "").replace(" today", "").replace(" now", "")
                    return location.title()

        return ""

    def _extract_concept(self, text: str) -> str:
        """Extract concept from explanation requests."""
        text_lower = text.lower()

        # Patterns for concept extraction
        patterns = ["explain ", "what is ", "what are ", "concept of ", "definition of ", "meaning of "]

        for pattern in patterns:
            if pattern in text_lower:
                parts = text_lower.split(pattern, 1)
                if len(parts) > 1:
                    concept = parts[1].strip().rstrip("?.,!").strip()
                    # Clean up common suffixes
                    concept = concept.replace(" in simple terms", "").replace(" please", "")
                    return concept

        return ""


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="LangGraph Reasoning Agent - A2A Deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python deploy_reasoning_agent_a2a.py --host localhost --port 5002
    python deploy_reasoning_agent_a2a.py --debug
    python deploy_reasoning_agent_a2a.py --port 8082

The agent will be available at http://host:port/a2a

Requirements:
    - OPENAI_API_KEY environment variable must be set
    - MCP server should be running on localhost:8000 (optional)
        """,
    )
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind the server to (default: localhost)")
    parser.add_argument("--port", type=int, default=5002, help="Port to bind the server to (default: 5002)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def check_prerequisites() -> None:
    """Check if all prerequisites are met."""
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        exit(1)

    print("✅ OpenAI API key found")


def main():
    """Main function to deploy the reasoning agent as A2A service."""
    args = parse_arguments()
    setup_logging(args.debug)

    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting LangGraph Reasoning Agent A2A Deployment...")

    try:
        # Check prerequisites
        check_prerequisites()

        # Create and start the A2A agent
        agent = ReasoningAgentA2A()
        logger.info("✅ LangGraph Reasoning Agent A2A wrapper created successfully")
        logger.info(f"🌐 Server will start on {args.host}:{args.port}")
        logger.info(f"🔗 Agent endpoint: http://{args.host}:{args.port}/a2a")
        logger.info("📡 Ready to accept A2A reasoning requests...")

        # Start the server
        run_server(agent, host=args.host, port=args.port)

    except KeyboardInterrupt:
        logger.info("🛑 LangGraph Reasoning Agent A2A stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting LangGraph Reasoning Agent A2A: {e}")
        raise


if __name__ == "__main__":
    main()
