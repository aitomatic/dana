#!/usr/bin/env python3
"""Single room environment simulator for Honeywell HVAC control."""

import sys
import os
import random
import json

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "dana_agent")
)


class SingleRoomEnvironment:
    """Simulates a single room environment with temperature and occupancy."""

    def __init__(
        self,
        room_name: str = "Conference Room A",
        base_temp: float = 72.0
    ):
        """
        Initialize the room environment.

        Args:
            room_name: Name of the room
            base_temp: Base temperature in Fahrenheit
        """
        self.room_name = room_name
        self.base_temp = base_temp
        self.current_temp = base_temp
        self._cached_meeting_plan = None
        self._cache_date = None

    def get_current_time(self) -> str:
        """
        Get current time in HH:MM format.

        Randomly varies throughout extended hours (08:00-21:59).
        """
        hour = random.randint(8, 21)
        minute = random.randint(0, 59)
        return f"{hour:02d}:{minute:02d}"

    def get_outdoor_temperature(self) -> float:
        """
        Get realistic outdoor temperature based on time of day and season.
        
        Returns:
            Outdoor temperature in Fahrenheit
        """
        current_time = self.get_current_time()
        hour = int(current_time.split(':')[0])
        
        # Simulate daily temperature cycle (realistic outdoor pattern)
        # Peak heat: 14:00-16:00, Coolest: 06:00-08:00
        if 6 <= hour <= 8:
            # Early morning: coolest
            base_outdoor = random.uniform(45, 65)
        elif 9 <= hour <= 11:
            # Morning: warming up
            base_outdoor = random.uniform(55, 75)
        elif 12 <= hour <= 16:
            # Afternoon: hottest
            base_outdoor = random.uniform(70, 95)
        elif 17 <= hour <= 19:
            # Evening: cooling down
            base_outdoor = random.uniform(60, 85)
        else:  # 20-21
            # Night: cooler
            base_outdoor = random.uniform(50, 75)
        
        # Add some random variation
        variation = random.uniform(-3, 3)
        outdoor_temp = base_outdoor + variation
        
        return round(outdoor_temp, 1)

    def get_temperature(self) -> float:
        """
        Get current room temperature with realistic heat transfer from outdoor.
        
        Simulates natural indoor temperature when no AC is running.
        Indoor temp should be very close to outdoor temp.

        Returns:
            Current temperature in Fahrenheit
        """
        outdoor_temp = self.get_outdoor_temperature()
        
        # Without AC, indoor temp should be very close to outdoor temp
        # Small offset for building thermal mass and insulation
        thermal_offset = random.uniform(-2, 2)  # ±2°F difference from outdoor
        
        # Indoor temp = outdoor temp with small thermal offset
        base_indoor = outdoor_temp + thermal_offset
        
        # Add small random variation for realism (±0.5°F)
        variation = random.uniform(-0.5, 0.5)
        self.current_temp = base_indoor + variation
        
        return round(self.current_temp, 1)

    def get_temperature_from_outdoor(self, outdoor_temp: float) -> float:
        """
        Get indoor temperature based on outdoor temperature.
        
        Simulates natural indoor temperature when no AC is running.
        Indoor temp should be very close to outdoor temp.

        Args:
            outdoor_temp: Outdoor temperature in Fahrenheit

        Returns:
            Indoor temperature in Fahrenheit
        """
        # Without AC, indoor temp should be very close to outdoor temp
        # Small offset for building thermal mass and insulation
        thermal_offset = random.uniform(-2, 2)  # ±2°F difference from outdoor
        
        # Indoor temp = outdoor temp with small thermal offset
        base_indoor = outdoor_temp + thermal_offset
        
        # Add small random variation for realism (±0.5°F)
        variation = random.uniform(-0.5, 0.5)
        indoor_temp = base_indoor + variation
        
        return round(indoor_temp, 1)

    def generate_meeting_plan(self, current_time_str: str) -> list[dict]:
        """
        Generate a diverse meeting plan using code for true randomness.

        Args:
            current_time_str: Current time in HH:MM format

        Returns:
            List of meeting dictionaries with start_time and end_time
        """
        # Parse current time
        current_h, current_m = map(int, current_time_str.split(':'))
        current_minutes = current_h * 60 + current_m

        # Extended hours: 08:00 (480 min) to 22:00 (1320 min)
        business_end = 22 * 60   # 22:00

        # Calculate how much time is left
        time_left = business_end - current_minutes

        # If less than 10 minutes left, no meetings possible
        if time_left < 10:
            # Don't cache empty results - try again if time changes
            return []

        # Generate meetings with diverse gaps from current time
        # Ensure earliest meeting is at least 2 hours (120 minutes) from current time
        if time_left < 120:
            # Not enough time for 2-hour gap - no meetings possible
            return []
        else:
            # Normal hours - ensure at least 2 hours gap, up to 3 hours
            min_gap = 120  # 2 hours minimum
            max_gap = min(180, time_left - 30)  # Up to 3 hours, but leave 30 min buffer

        gap = random.randint(min_gap, max(min_gap, max_gap))
        earliest_start = current_minutes + gap

        # Generate random number of meetings (0-5)
        num_meetings = random.randint(1, 5)

        meetings = []
        available_start = earliest_start

        # Possible durations (in minutes) - varied
        # Include short durations for late-day meetings
        if time_left < 60:
            # Short meetings only when time is limited
            durations = [15, 20, 25, 30]
        else:
            durations = [30, 40, 45, 50, 60, 75, 80, 90, 100, 105, 110, 120]

        for _ in range(num_meetings):
            # Check if enough time left for even a short meeting
            remaining = business_end - available_start
            if remaining < 15:
                break

            # Random duration (or shorter if needed)
            duration = random.choice(durations)
            # Ensure duration fits in remaining time
            duration = min(duration, remaining - 5)

            # Ensure meeting ends before extended hours
            latest_start = business_end - duration
            if available_start > latest_start:
                break

            # Random start time (add 0-15 min variation to avoid round hours)
            variation = random.choice([0, 5, 10, 15, 20, 25])
            start_minutes = available_start + variation

            # Ensure we don't go past latest_start
            if start_minutes > latest_start:
                start_minutes = latest_start

            end_minutes = start_minutes + duration

            # Ensure end is before extended hours
            if end_minutes > business_end:
                end_minutes = business_end
                duration = end_minutes - start_minutes
                if duration < 30:  # Skip if too short
                    break

            # Convert to HH:MM format
            start_h, start_m = divmod(start_minutes, 60)
            end_h, end_m = divmod(end_minutes, 60)

            meetings.append({
                "start_time": f"{start_h:02d}:{start_m:02d}",
                "end_time": f"{end_h:02d}:{end_m:02d}"
            })

            # Next meeting starts after current one + gap (30 min to 3 hours)
            gap = random.randint(30, 180)
            available_start = end_minutes + gap

        return meetings

    def get_env(self) -> dict:
        """
        Get complete environment state.

        Returns:
            Dictionary with current_time, temperature, outdoor_temp, and meeting_plan
        """
        # Get current time once and use it consistently
        current_time = self.get_current_time()
        
        # Get outdoor temperature once and use it for both outdoor_temp and indoor temp calculation
        outdoor_temp = self.get_outdoor_temperature()

        return {
            "room_name": self.room_name,
            "current_time": current_time,
            "indoor_temp": self.get_temperature_from_outdoor(outdoor_temp),
            "outdoor_temp": outdoor_temp,
            "meeting_plan": self.generate_meeting_plan(current_time)
        }

    def set_temperature(self, target_temp: float):
        """
        Simulate setting the target temperature.

        Args:
            target_temp: Target temperature in Fahrenheit
        """
        self.base_temp = target_temp
        print(f"Temperature setpoint updated to {target_temp}°F")


def main():
    """Demo the room environment."""
    print("=" * 80)
    print("SINGLE ROOM ENVIRONMENT SIMULATOR")
    print("=" * 80)
    print()

    # Create room environment
    room = SingleRoomEnvironment(
        room_name="Conference Room A",
        base_temp=72.0
    )

    # Get environment state
    print("Getting environment state...")
    env_state = room.get_env()

    # Display in the required format
    output = {
        "current_time": env_state["current_time"],
        "indoor_temp": env_state["indoor_temp"],
        "outdoor_temp": env_state["outdoor_temp"],
        "meeting_plan": env_state["meeting_plan"]
    }

    print()
    print("Environment State:")
    print("-" * 80)
    print(json.dumps(output, indent=2))
    print("-" * 80)
    print()

    # Show room details
    print(f"Room: {env_state['room_name']}")
    print(f"Indoor Temperature: {env_state['indoor_temp']}°F")
    print(f"Outdoor Temperature: {env_state['outdoor_temp']}°F")
    print(f"Number of meetings: {len(env_state['meeting_plan'])}")
    print()


if __name__ == "__main__":
    main()
