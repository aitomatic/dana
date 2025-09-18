#!/usr/bin/env python3
"""
Trip Planner Agent - A2A Protocol Example

Provides itineraries and travel tips for destinations worldwide.
"""

import argparse
import logging

from python_a2a import A2AServer, agent, run_server, skill
from python_a2a.models import TaskState, TaskStatus


@agent(name="Trip Planner Agent", description="Suggests itineraries and travel tips for destinations worldwide", version="1.0.0")
class TripPlannerAgent(A2AServer):
    """
    A2A Trip Planner Agent that provides itineraries and travel tips.
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Trip Planner Agent initialized")

    @skill(name="Get Itinerary", description="Suggest a multi-day itinerary for a location", tags=["trip", "itinerary", "travel"])
    def get_itinerary(self, location: str, days: int = 3) -> str:
        """
        Suggest a multi-day itinerary for a location.
        Args:
            location: The city/location name
            days: Number of days for the itinerary
        Returns:
            Formatted itinerary string
        """
        return (
            f"{days}-day itinerary for {location.title()}:\n"
            f"Day 1: Explore downtown and main attractions.\n"
            f"Day 2: Visit museums and parks.\n"
            f"Day 3: Enjoy local cuisine and shopping."
        )

    @skill(name="Travel Tips", description="Get travel tips for a location", tags=["tips", "travel", "advice"])
    def travel_tips(self, location: str) -> str:
        """
        Get travel tips for a location.
        Args:
            location: The city/location name
        Returns:
            Travel tips string
        """
        return (
            f"Travel tips for {location.title()}:\n"
            f"- Use public transport for convenience.\n"
            f"- Try local food specialties.\n"
            f"- Visit popular landmarks and hidden gems."
        )

    def handle_task(self, task) -> object:
        try:
            message_data = task.message or {}
            content = message_data.get("content", {})
            if isinstance(content, dict):
                text = content.get("text", "")
            elif isinstance(content, str):
                text = content
            else:
                text = str(content)
            text = text.lower().strip()
            self.logger.info(f"Processing trip planner query: {text}")

            # Determine which skill to use
            if any(word in text for word in ["itinerary", "plan", "trip"]):
                location = self._extract_location(text)
                days = self._extract_days(text)
                if not location:
                    task.status = TaskStatus(
                        state=TaskState.INPUT_REQUIRED,
                        message={
                            "role": "agent",
                            "content": {
                                "type": "text",
                                "text": "Please specify a location for the itinerary. For example: 'Plan a 3-day trip to Paris.'",
                            },
                        },
                    )
                    return task
                result = self.get_itinerary(location, days)
            elif any(word in text for word in ["tip", "tips", "advice"]):
                location = self._extract_location(text)
                if not location:
                    task.status = TaskStatus(
                        state=TaskState.INPUT_REQUIRED,
                        message={
                            "role": "agent",
                            "content": {
                                "type": "text",
                                "text": "Please specify a location for travel tips. For example: 'Give me travel tips for Tokyo.'",
                            },
                        },
                    )
                    return task
                result = self.travel_tips(location)
            else:
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Please specify if you want an itinerary or travel tips, and for which location.",
                        },
                    },
                )
                return task
            task.artifacts = [{"parts": [{"type": "text", "text": result}]}]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            self.logger.info("Successfully processed trip planner query.")
        except Exception as e:
            self.logger.error(f"Error processing trip planner task: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {"type": "text", "text": f"Sorry, I encountered an error processing your trip planner request: {str(e)}"},
                },
            )
        return task

    def _extract_location(self, text: str) -> str:
        import re

        # Try to extract location after 'to', 'for', or 'in'
        match = re.search(r"(?:to|for|in) ([a-zA-Z ]+)", text)
        if match:
            return match.group(1).strip()
        # Fallback: last word
        words = text.split()
        if words:
            return words[-1]
        return ""

    def _extract_days(self, text: str) -> int:
        import re

        match = re.search(r"(\d+)\s*-?\s*day", text)
        if match:
            return int(match.group(1))
        return 3


def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trip Planner Agent - A2A Protocol Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python start_planner_agent.py --host localhost --port 5002
    python start_planner_agent.py --debug
    python start_planner_agent.py --port 8082

The agent will be available at http://host:port/a2a
        """,
    )
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind the server to (default: localhost)")
    parser.add_argument("--port", type=int, default=5002, help="Port to bind the server to (default: 5002)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main():
    args = parse_arguments()
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    logger.info("Starting Trip Planner Agent...")
    try:
        agent = TripPlannerAgent()
        logger.info("Trip Planner Agent created successfully")
        logger.info(f"Server will start on {args.host}:{args.port}")
        logger.info(f"Agent endpoint: http://{args.host}:{args.port}/a2a")
        run_server(agent, host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Trip Planner Agent stopped by user")
    except Exception as e:
        logger.error(f"Error starting Trip Planner Agent: {e}")
        raise


if __name__ == "__main__":
    main()
