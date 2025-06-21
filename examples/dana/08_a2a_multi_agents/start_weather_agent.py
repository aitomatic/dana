#!/usr/bin/env python3
"""
Weather Agent - A2A Protocol Example

A simple weather agent that provides weather information and forecasts for various locations.
This agent demonstrates A2A protocol implementation using the python-a2a library.

Usage:
    python start_a2a_agent.py --host localhost --port 5001 --debug

Example queries the agent can handle:
    - "What's the weather in Paris?"
    - "Give me a 3-day forecast for Tokyo"  
    - "Temperature in New York"
    - "Weather forecast for London"

Author: OpenDXA Team
Version: 1.0.0
"""

import argparse
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

try:
    from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
except ImportError:
    print("Error: python-a2a library not found. Please install it with:")
    print("pip install python-a2a")
    exit(1)


# Mock weather data for demonstration
WEATHER_DATA: Dict[str, Dict[str, Any]] = {
    "paris": {
        "temperature": 18,
        "condition": "Partly Cloudy",
        "humidity": 65,
        "wind_speed": 12,
        "unit": "°C"
    },
    "tokyo": {
        "temperature": 22,
        "condition": "Sunny",
        "humidity": 58,
        "wind_speed": 8,
        "unit": "°C"
    },
    "new york": {
        "temperature": 15,
        "condition": "Rainy",
        "humidity": 78,
        "wind_speed": 15,
        "unit": "°C"
    },
    "london": {
        "temperature": 12,
        "condition": "Overcast",
        "humidity": 82,
        "wind_speed": 10,
        "unit": "°C"
    },
    "san francisco": {
        "temperature": 16,
        "condition": "Foggy",
        "humidity": 88,
        "wind_speed": 7,
        "unit": "°C"
    },
    "sydney": {
        "temperature": 25,
        "condition": "Sunny",
        "humidity": 45,
        "wind_speed": 14,
        "unit": "°C"
    },
    "berlin": {
        "temperature": 14,
        "condition": "Cloudy",
        "humidity": 70,
        "wind_speed": 11,
        "unit": "°C"
    }
}

WEATHER_CONDITIONS = ["Sunny", "Partly Cloudy", "Cloudy", "Overcast", "Rainy", "Stormy", "Foggy"]


@agent(
    name="Weather Agent",
    description="Provides weather information and forecasts for locations worldwide",
    version="1.0.0"
)
class WeatherAgent(A2AServer):
    """
    A2A Weather Agent that provides current weather and forecast information.
    
    This agent demonstrates the A2A protocol implementation using python-a2a library.
    It supports weather queries for major cities and provides multi-day forecasts.
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Weather Agent initialized")

    @skill(
        name="Get Current Weather",
        description="Get current weather conditions for a specific location",
        tags=["weather", "current", "temperature"]
    )
    def get_weather(self, location: str) -> str:
        """
        Get current weather for a specific location.
        
        Args:
            location: The city/location name
            
        Returns:
            Formatted weather information string
        """
        location_key = location.lower().strip()
        
        if location_key in WEATHER_DATA:
            data = WEATHER_DATA[location_key]
            return (f"Current weather in {location.title()}:\n"
                   f"Temperature: {data['temperature']}{data['unit']}\n"
                   f"Condition: {data['condition']}\n"
                   f"Humidity: {data['humidity']}%\n"
                   f"Wind Speed: {data['wind_speed']} km/h")
        else:
            # Generate random weather for unknown locations
            temp = random.randint(-10, 35)
            condition = random.choice(WEATHER_CONDITIONS)
            humidity = random.randint(30, 90)
            wind = random.randint(5, 25)
            
            return (f"Current weather in {location.title()}:\n"
                   f"Temperature: {temp}°C\n"
                   f"Condition: {condition}\n"
                   f"Humidity: {humidity}%\n"
                   f"Wind Speed: {wind} km/h")

    @skill(
        name="Get Weather Forecast",
        description="Get multi-day weather forecast for a specific location",
        tags=["weather", "forecast", "multi-day", "prediction"]
    )
    def get_forecast(self, location: str, days: int = 5) -> str:
        """
        Get weather forecast for multiple days.
        
        Args:
            location: The city/location name
            days: Number of days to forecast (1-7)
            
        Returns:
            Formatted forecast string
        """
        if days < 1 or days > 7:
            days = 5
            
        location_key = location.lower().strip()
        base_data = WEATHER_DATA.get(location_key, {
            "temperature": 20,
            "condition": "Partly Cloudy",
            "humidity": 60,
            "wind_speed": 10,
            "unit": "°C"
        })
        
        forecast_lines = [f"{days}-Day Weather Forecast for {location.title()}:\n"]
        
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            day_name = date.strftime("%A")
            date_str = date.strftime("%B %d")
            
            # Vary temperature and conditions for each day
            temp_variation = random.randint(-5, 5)
            temp = base_data["temperature"] + temp_variation
            condition = random.choice(WEATHER_CONDITIONS)
            
            forecast_lines.append(
                f"{day_name}, {date_str}: {temp}°C, {condition}"
            )
        
        return "\n".join(forecast_lines)

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
            
            text = text.lower().strip()
            self.logger.info(f"Processing weather query: {text}")
            
            # Parse weather requests
            location = self._extract_location(text)
            
            if not location:
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Please specify a location for the weather query. For example: 'What's the weather in Paris?' or 'Forecast for Tokyo'"
                        }
                    }
                )
                return task
            
            # Determine if this is a forecast request or current weather
            if any(word in text for word in ["forecast", "prediction", "days", "week"]):
                # Extract number of days if specified
                days = self._extract_days(text)
                weather_info = self.get_forecast(location, days)
            else:
                weather_info = self.get_weather(location)
            
            # Set successful response
            task.artifacts = [{
                "parts": [{"type": "text", "text": weather_info}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            self.logger.info(f"Successfully processed weather query for {location}")
            
        except Exception as e:
            self.logger.error(f"Error processing weather task: {e}")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={
                    "role": "agent", 
                    "content": {
                        "type": "text",
                        "text": f"Sorry, I encountered an error processing your weather request: {str(e)}"
                    }
                }
            )
        
        return task

    def _extract_location(self, text: str) -> str:
        """Extract location from natural language text."""
        # Common patterns for location extraction
        patterns = [
            " in ",
            " for ",
            " at ",
            "weather in ",
            "forecast for ",
            "temperature in "
        ]
        
        for pattern in patterns:
            if pattern in text:
                parts = text.split(pattern, 1)
                if len(parts) > 1:
                    location = parts[1].strip().rstrip("?.,!").strip()
                    # Clean up common suffixes
                    location = location.replace(" please", "").replace(" today", "")
                    return location
        
        # If no pattern found, try to extract city names from known locations
        words = text.split()
        for word in words:
            if word in WEATHER_DATA:
                return word
        
        # Check for multi-word city names
        for city in WEATHER_DATA.keys():
            if city in text:
                return city
        
        return ""

    def _extract_days(self, text: str) -> int:
        """Extract number of days from forecast request."""
        # Look for number patterns
        import re
        
        # Check for explicit day numbers
        day_patterns = [
            r"(\d+)\s*days?",
            r"(\d+)\s*day",
            r"(\d+)-day"
        ]
        
        for pattern in day_patterns:
            match = re.search(pattern, text)
            if match:
                days = int(match.group(1))
                return min(max(days, 1), 7)  # Clamp between 1-7 days
        
        # Default forecast length
        return 5

def setup_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Weather Agent - A2A Protocol Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python start_weather_agent.py --host localhost --port 5001
    python start_weather_agent.py --debug
    python start_weather_agent.py --port 8081

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
        default=5001,
        help="Port to bind the server to (default: 5001)"
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
    logger.info("Starting Weather Agent...")
    try:
        agent = WeatherAgent()
        logger.info(f"Weather Agent created successfully")
        logger.info(f"Server will start on {args.host}:{args.port}")
        logger.info(f"Agent endpoint: http://{args.host}:{args.port}/a2a")
        run_server(agent, host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Weather Agent stopped by user")
    except Exception as e:
        logger.error(f"Error starting Weather Agent: {e}")
        raise


if __name__ == "__main__":
    main()
