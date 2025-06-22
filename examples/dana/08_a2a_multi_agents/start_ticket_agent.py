#!/usr/bin/env python3
"""
Ticket Agent - A2A Protocol Example

Finds and books tickets for events and transportation.
"""
import argparse
import logging

from python_a2a import A2AServer, agent, run_server, skill
from python_a2a.models import TaskState, TaskStatus


@agent(
    name="Ticket Agent",
    description="Finds and books tickets for events and transportation",
    version="1.0.0"
)
class TicketAgent(A2AServer):
    """
    A2A Ticket Agent that finds and books tickets for events and transport.
    """
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Ticket Agent initialized")

    @skill(
        name="Find Event Tickets",
        description="Find tickets for events in a location",
        tags=["tickets", "events", "booking"]
    )
    def find_event_tickets(self, location: str, event: str = "concert") -> str:
        """
        Find tickets for events in a location.
        Args:
            location: The city/location name
            event: The event type (default: concert)
        Returns:
            Ticket availability string
        """
        return (f"Tickets for {event.title()} in {location.title()}: Available - $50 each.")

    @skill(
        name="Book Transport Ticket",
        description="Book a transport ticket (train, bus, etc.) in a location",
        tags=["tickets", "transport", "booking"]
    )
    def book_transport_ticket(self, location: str, transport: str = "train") -> str:
        """
        Book a transport ticket in a location.
        Args:
            location: The city/location name
            transport: The transport type (default: train)
        Returns:
            Booking confirmation string
        """
        return (f"{transport.title()} ticket to {location.title()} booked successfully! Reference: ABC123")

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
            self.logger.info(f"Processing ticket agent query: {text}")

            # Determine which skill to use
            if any(word in text for word in ["event", "concert", "show", "ticket", "find"]):
                location = self._extract_location(text)
                event = self._extract_event(text)
                if not location:
                    task.status = TaskStatus(
                        state=TaskState.INPUT_REQUIRED,
                        message={
                            "role": "agent",
                            "content": {
                                "type": "text",
                                "text": "Please specify a location for the event tickets. For example: 'Find concert tickets in Berlin.'"
                            }
                        }
                    )
                    return task
                result = self.find_event_tickets(location, event)
            elif any(word in text for word in ["book", "bus", "train", "transport"]):
                location = self._extract_location(text)
                transport = self._extract_transport(text)
                if not location:
                    task.status = TaskStatus(
                        state=TaskState.INPUT_REQUIRED,
                        message={
                            "role": "agent",
                            "content": {
                                "type": "text",
                                "text": "Please specify a location for the transport ticket. For example: 'Book a train ticket to Paris.'"
                            }
                        }
                    )
                    return task
                result = self.book_transport_ticket(location, transport)
            else:
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Please specify if you want event tickets or to book transport, and for which location."
                        }
                    }
                )
                return task
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            self.logger.info("Successfully processed ticket agent query.")
        except Exception as e:
            self.logger.error(f"Error processing ticket agent task: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text",
                        "text": f"Sorry, I encountered an error processing your ticket agent request: {str(e)}"
                    }
                }
            )
        return task

    def _extract_location(self, text: str) -> str:
        import re
        # Try to extract location after 'to', 'for', 'in'
        match = re.search(r'(?:to|for|in) ([a-zA-Z ]+)', text)
        if match:
            return match.group(1).strip()
        # Fallback: last word
        words = text.split()
        if words:
            return words[-1]
        return ""

    def _extract_event(self, text: str) -> str:
        import re
        match = re.search(r'(concert|show|event|festival|play)', text)
        if match:
            return match.group(1)
        return "concert"

    def _extract_transport(self, text: str) -> str:
        import re
        match = re.search(r'(bus|train|flight|plane|transport)', text)
        if match:
            return match.group(1)
        return "train"

def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ticket Agent - A2A Protocol Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python start_ticket_agent.py --host localhost --port 5003
    python start_ticket_agent.py --debug
    python start_ticket_agent.py --port 8083

The agent will be available at http://host:port/a2a
        """
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind the server to (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5003,
        help="Port to bind the server to (default: 5003)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    logger.info("Starting Ticket Agent...")
    try:
        agent = TicketAgent()
        logger.info("Ticket Agent created successfully")
        logger.info(f"Server will start on {args.host}:{args.port}")
        logger.info(f"Agent endpoint: http://{args.host}:{args.port}/a2a")
        run_server(agent, host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Ticket Agent stopped by user")
    except Exception as e:
        logger.error(f"Error starting Ticket Agent: {e}")
        raise

if __name__ == "__main__":
    main() 