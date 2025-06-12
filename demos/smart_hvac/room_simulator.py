"""
Room Thermal Simulation

Simulates realistic room thermal dynamics including:
- Heat transfer through walls
- Thermal mass effects
- Weather influence
- HVAC system response
"""

import math
import random
from typing import Dict, Any
from dataclasses import dataclass, field
from hvac_systems import HVACCommand


class WeatherService:
    """Shared weather service to ensure consistent outside temperature across all simulators."""

    def __init__(self):
        self.weather_pattern = "mild"  # "hot", "cold", "mild"
        self.time_of_day = 12.0  # 0-24 hours
        self.time_step = 1.0  # minutes
        self.current_outside_temp = 65.0
        self._last_update_time = 0  # Track when we last updated
        self._update_counter = 0  # Counter to track updates

    def update_weather(self, force_update=False):
        """Update weather conditions and time of day."""
        # Only update once per simulation cycle
        current_counter = self._update_counter
        if not force_update and hasattr(self, "_current_cycle_counter") and self._current_cycle_counter == current_counter:
            return  # Already updated this cycle

        self._current_cycle_counter = current_counter

        # Advance time
        self.time_of_day += self.time_step / 60.0
        if self.time_of_day >= 24:
            self.time_of_day = 0

        # Update outside temperature with daily cycle
        if self.weather_pattern == "hot":
            base_temp = 85
            daily_range = 15
        elif self.weather_pattern == "cold":
            base_temp = 35
            daily_range = 20
        else:  # mild
            base_temp = 65
            daily_range = 15

        # Daily temperature cycle (peak at 3 PM)
        daily_factor = math.sin((self.time_of_day - 6) * math.pi / 12)
        self.current_outside_temp = base_temp + daily_range * daily_factor * 0.5

        # Add weather noise (same for all rooms in this cycle)
        weather_noise = random.gauss(0, 2.0)
        self.current_outside_temp += weather_noise

        # Increment counter for next cycle
        self._update_counter += 1

    def get_outside_temp(self) -> float:
        """Get current outside temperature."""
        return self.current_outside_temp

    def get_occupancy_pattern(self) -> bool:
        """Get occupancy based on time of day."""
        if 6 <= self.time_of_day <= 8 or 17 <= self.time_of_day <= 23:
            return True
        else:
            return random.random() > 0.7  # 30% chance when away

    def set_weather_pattern(self, pattern: str):
        """Set weather pattern: 'hot', 'cold', or 'mild'."""
        self.weather_pattern = pattern


# Global weather service instance
_weather_service = WeatherService()


@dataclass
class RoomState:
    """Current state of the simulated room."""

    temperature: float = 72.0  # °F
    thermal_mass: float = 1000.0  # Thermal mass coefficient
    outside_temp: float = 65.0  # °F
    occupancy: bool = True
    heat_gain: float = 0.0  # Internal heat gain (people, equipment)
    humidity: float = 45.0  # %RH (future use)


@dataclass
class RoomMetrics:
    """Historical metrics for the room."""

    temperatures: list = field(default_factory=list)
    energy_usage: list = field(default_factory=list)
    comfort_scores: list = field(default_factory=list)
    hvac_commands: list = field(default_factory=list)
    timestamps: list = field(default_factory=list)


class RoomSimulator:
    """
    Simulates realistic room thermal dynamics.

    Based on simplified building thermal model:
    dT/dt = (Qhvac + Qinternal - Qloss) / (mass * Cp)
    """

    def __init__(self, initial_temp: float = 72.0):
        self.state = RoomState(temperature=initial_temp)
        self.metrics = RoomMetrics()

        # Building characteristics
        self.wall_r_value = 15.0  # Wall R-value (thermal resistance)
        self.wall_area = 400.0  # sq ft
        self.air_changes = 1.0  # Air changes per hour
        self.thermal_capacity = 1000.0  # BTU/°F (thermal mass)

        # Simulation parameters
        self.time_step = 1.0  # minutes
        self.noise_level = 0.1  # Random temperature noise

        # Weather simulation
        self.weather_pattern = "mild"  # "hot", "cold", "mild"
        self.time_of_day = 12.0  # 0-24 hours

    def step(self, hvac_command: HVACCommand, duration: float = 1.0) -> Dict[str, Any]:
        """
        Advance simulation by one time step.

        Args:
            hvac_command: HVAC system output
            duration: Time step in minutes

        Returns:
            Updated room state and metrics
        """
        # Calculate heat flows
        q_hvac = self._calculate_hvac_heat_flow(hvac_command)
        q_internal = self._calculate_internal_heat_gain()
        q_loss = self._calculate_heat_loss()

        # Update temperature based on energy balance
        net_heat_flow = q_hvac + q_internal - q_loss
        temp_change = (net_heat_flow * duration) / self.thermal_capacity

        # Apply temperature change with thermal lag
        thermal_lag = 0.8  # Thermal mass dampening
        self.state.temperature += temp_change * thermal_lag

        # Add realistic noise
        noise = random.gauss(0, self.noise_level)
        self.state.temperature += noise

        # Get weather from shared service (don't update it - that's done centrally)
        self.state.outside_temp = _weather_service.get_outside_temp()
        self.state.occupancy = _weather_service.get_occupancy_pattern()

        # Calculate energy usage
        energy_usage = self._calculate_energy_from_command(hvac_command, duration)

        # Record metrics
        self.metrics.temperatures.append(self.state.temperature)
        self.metrics.energy_usage.append(energy_usage)
        self.metrics.hvac_commands.append(hvac_command)

        # Keep only recent history (last 100 points)
        for metric_list in [self.metrics.temperatures, self.metrics.energy_usage, self.metrics.hvac_commands]:
            if len(metric_list) > 100:
                metric_list.pop(0)

        return {
            "temperature": round(self.state.temperature, 1),
            "outside_temp": round(self.state.outside_temp, 1),
            "occupancy": self.state.occupancy,
            "energy_usage": energy_usage,
            "heat_flows": {"hvac": q_hvac, "internal": q_internal, "loss": q_loss, "net": net_heat_flow},
        }

    def _calculate_hvac_heat_flow(self, command: HVACCommand) -> float:
        """Calculate heat flow from HVAC system (BTU/min)."""
        # HVAC capacity (simplified)
        heating_capacity = 60000  # BTU/hr at 100%
        cooling_capacity = 48000  # BTU/hr at 100%

        heating_btuh = heating_capacity * (command.heating_output / 100.0)
        cooling_btuh = -cooling_capacity * (command.cooling_output / 100.0)  # Negative for cooling

        # Convert to BTU/min
        total_btuh = heating_btuh + cooling_btuh
        return total_btuh / 60.0

    def _calculate_internal_heat_gain(self) -> float:
        """Calculate internal heat gain from people, equipment (BTU/min)."""
        base_gain = 0.0

        if self.state.occupancy:
            # People: ~400 BTU/hr per person (sensible heat)
            people_gain = 400 * 2  # Assume 2 people

            # Equipment: lights, computers, etc.
            equipment_gain = 1000  # BTU/hr

            base_gain = people_gain + equipment_gain
        else:
            # Just equipment standby
            base_gain = 200  # BTU/hr

        # Add time-of-day variation
        time_factor = 1.0 + 0.3 * math.sin((self.time_of_day - 6) * math.pi / 12)

        return (base_gain * time_factor) / 60.0  # Convert to BTU/min

    def _calculate_heat_loss(self) -> float:
        """Calculate heat loss through envelope (BTU/min)."""
        # Heat loss through walls: Q = UA * ΔT
        temp_diff = self.state.temperature - self.state.outside_temp

        # U-value = 1/R-value
        u_value = 1.0 / self.wall_r_value
        wall_loss = u_value * self.wall_area * temp_diff

        # Air infiltration loss
        air_loss = self.air_changes * 1.08 * 1000 * temp_diff  # Simplified

        total_loss = (wall_loss + air_loss) / 60.0  # Convert to BTU/min
        return total_loss

    def _calculate_energy_from_command(self, command: HVACCommand, duration: float) -> float:
        """Calculate energy consumption in kWh."""
        # Electrical power consumption
        heating_kw = 5.0 * (command.heating_output / 100.0)  # 5kW heating
        cooling_kw = 3.5 * (command.cooling_output / 100.0)  # 3.5kW cooling
        fan_kw = 0.5 * (command.fan_speed / 100.0)  # 0.5kW fan

        total_kw = heating_kw + cooling_kw + fan_kw
        return total_kw * (duration / 60.0)  # Convert minutes to hours

    def _update_weather(self):
        """DEPRECATED: Use shared weather service instead."""
        # This method is now handled by the shared WeatherService
        pass

    def set_weather(self, pattern: str):
        """Set weather pattern: 'hot', 'cold', or 'mild'."""
        _weather_service.set_weather_pattern(pattern)

    def set_occupancy(self, occupied: bool):
        """Override occupancy state."""
        self.state.occupancy = occupied

    def get_recent_temps(self, count: int = 10) -> list:
        """Get recent temperature history."""
        return self.metrics.temperatures[-count:] if len(self.metrics.temperatures) >= count else self.metrics.temperatures

    def get_total_energy(self) -> float:
        """Get total energy consumption."""
        return sum(self.metrics.energy_usage)

    def get_avg_energy_rate(self) -> float:
        """Get average energy consumption rate (kW)."""
        if not self.metrics.energy_usage:
            return 0.0

        total_energy = sum(self.metrics.energy_usage)
        total_time_hours = len(self.metrics.energy_usage) * (self.time_step / 60.0)

        return total_energy / max(total_time_hours, 0.001)

    def reset(self, initial_temp: float = 72.0):
        """Reset simulation to initial state."""
        self.state = RoomState(temperature=initial_temp)
        self.metrics = RoomMetrics()
        self.time_of_day = 12.0
