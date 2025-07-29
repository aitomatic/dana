"""
Plant Growth Simulation

Simulates realistic plant growth and health based on:
- Soil moisture and watering
- Light exposure and intensity
- Temperature and climate
- Nutrient levels
- Growth stage progression
"""

import math
from dataclasses import dataclass, field
from typing import Any

from greenhouse_systems import GreenhouseCommand


@dataclass
class PlantState:
    """Current state of the simulated plants."""

    growth_stage: str = "seedling"  # "seedling", "vegetative", "flowering", "fruiting"
    health_score: float = 80.0  # 0-100
    size: float = 1.0  # Relative size (1.0 = baseline)
    soil_moisture: float = 50.0  # 0-100%
    nutrient_level: float = 60.0  # 0-100%
    stress_level: float = 0.0  # 0-100 (0 = no stress)
    days_in_stage: int = 0  # Days in current growth stage
    total_yield: float = 0.0  # Cumulative harvest


@dataclass
class EnvironmentState:
    """Current greenhouse environment."""

    temperature: float = 70.0  # °F
    humidity: float = 60.0  # %
    light_level: float = 0.0  # 0-100%
    co2_level: float = 400.0  # ppm
    time_of_day: float = 12.0  # 0-24 hours


@dataclass
class PlantMetrics:
    """Historical metrics for plants."""

    health_scores: list[float] = field(default_factory=list)
    growth_rates: list[float] = field(default_factory=list)
    water_usage: list[float] = field(default_factory=list)
    energy_usage: list[float] = field(default_factory=list)
    yields: list[float] = field(default_factory=list)
    timestamps: list[str] = field(default_factory=list)


class GreenhouseSimulator:
    """
    Simulates realistic plant growth in greenhouse conditions.

    Models:
    - Growth stage progression
    - Health response to conditions
    - Resource usage and efficiency
    - Environmental dynamics
    """

    def __init__(self, plant_type: str = "tomato"):
        self.plant_state = PlantState()
        self.environment = EnvironmentState()
        self.metrics = PlantMetrics()

        # Plant characteristics
        self.plant_type = plant_type
        self.growth_rate_base = 0.02  # Base growth per hour
        self.stress_tolerance = 0.3  # Stress threshold

        # Growth stage durations (in simulation days)
        self.stage_durations = {"seedling": 7, "vegetative": 14, "flowering": 10, "fruiting": 21}

        # Optimal conditions by stage
        self.optimal_conditions = {
            "seedling": {"temperature": 72, "humidity": 70, "moisture": 40, "light_hours": 8, "nutrients": 30},
            "vegetative": {"temperature": 74, "humidity": 65, "moisture": 50, "light_hours": 12, "nutrients": 60},
            "flowering": {"temperature": 68, "humidity": 55, "moisture": 45, "light_hours": 10, "nutrients": 40},
            "fruiting": {"temperature": 70, "humidity": 60, "moisture": 55, "light_hours": 10, "nutrients": 80},
        }

        # Resource tracking
        self.total_water_used = 0.0
        self.total_energy_used = 0.0
        self.simulation_hours = 0

    def step(self, command: GreenhouseCommand, duration: float = 1.0) -> dict[str, Any]:
        """
        Advance plant growth simulation by one time step.

        Args:
            command: Greenhouse control output
            duration: Time step in hours

        Returns:
            Updated plant and environment state
        """
        # Update environment based on commands
        self._update_environment(command, duration)

        # Update plant growth and health
        self._update_plant_growth(duration)

        # Calculate resource usage
        water_used = self._calculate_water_usage(command, duration)
        energy_used = self._calculate_energy_usage(command, duration)

        self.total_water_used += water_used
        self.total_energy_used += energy_used
        self.simulation_hours += duration

        # Record metrics
        self._record_metrics(water_used, energy_used)

        return {
            "plant_health": round(self.plant_state.health_score, 1),
            "growth_stage": self.plant_state.growth_stage,
            "size": round(self.plant_state.size, 2),
            "soil_moisture": round(self.plant_state.soil_moisture, 1),
            "temperature": round(self.environment.temperature, 1),
            "humidity": round(self.environment.humidity, 1),
            "light_level": round(self.environment.light_level, 1),
            "water_usage": water_used,
            "energy_usage": energy_used,
            "stress_level": round(self.plant_state.stress_level, 1),
            "total_yield": round(self.plant_state.total_yield, 2),
        }

    def _update_environment(self, command: GreenhouseCommand, duration: float):
        """Update greenhouse environment based on control commands."""
        # Temperature response to heating
        if command.heating_level > 0:
            heat_increase = command.heating_level * 0.1 * duration
            self.environment.temperature += heat_increase

        # Natural temperature drift toward outside temp
        outside_temp = 65 + 10 * math.sin((self.environment.time_of_day - 12) * math.pi / 12)
        temp_drift = (outside_temp - self.environment.temperature) * 0.05 * duration
        self.environment.temperature += temp_drift

        # Humidity response to ventilation
        if command.ventilation_level > 0:
            humidity_decrease = command.ventilation_level * 0.2 * duration
            self.environment.humidity = max(30, self.environment.humidity - humidity_decrease)
        else:
            # Humidity increases naturally
            self.environment.humidity = min(90, self.environment.humidity + 0.5 * duration)

        # Light level from artificial lighting
        self.environment.light_level = command.light_intensity

        # CO2 level
        self.environment.co2_level = min(1200, 400 + command.co2_injection)

        # Advance time
        self.environment.time_of_day += duration
        if self.environment.time_of_day >= 24:
            self.environment.time_of_day -= 24

    def _update_plant_growth(self, duration: float):
        """Update plant growth, health, and stage progression."""
        # Calculate stress factors
        optimal = self.optimal_conditions[self.plant_state.growth_stage]

        temp_stress = abs(self.environment.temperature - optimal["temperature"]) / 10
        humidity_stress = abs(self.environment.humidity - optimal["humidity"]) / 20
        moisture_stress = abs(self.plant_state.soil_moisture - optimal["moisture"]) / 30
        nutrient_stress = max(0, optimal["nutrients"] - self.plant_state.nutrient_level) / 50

        total_stress = temp_stress + humidity_stress + moisture_stress + nutrient_stress
        self.plant_state.stress_level = min(100, total_stress * 20)

        # Health score based on stress
        if self.plant_state.stress_level < self.stress_tolerance * 100:
            health_change = 2 * duration  # Health improves
        else:
            health_change = -self.plant_state.stress_level * 0.1 * duration  # Health declines

        self.plant_state.health_score = max(0, min(100, self.plant_state.health_score + health_change))

        # Growth rate based on health and light
        light_factor = min(1.0, self.environment.light_level / 80)
        health_factor = self.plant_state.health_score / 100
        growth_rate = self.growth_rate_base * light_factor * health_factor * duration

        self.plant_state.size += growth_rate

        # Soil moisture decreases over time
        moisture_loss = 0.5 * duration  # Base evaporation
        if self.environment.temperature > 75:
            moisture_loss *= 1.5  # More loss when hot

        self.plant_state.soil_moisture = max(0, self.plant_state.soil_moisture - moisture_loss)

        # Nutrient depletion
        nutrient_consumption = 0.3 * duration * (self.plant_state.size / 1.0)
        self.plant_state.nutrient_level = max(0, self.plant_state.nutrient_level - nutrient_consumption)

        # Stage progression
        self.plant_state.days_in_stage += duration / 24
        current_duration = self.stage_durations[self.plant_state.growth_stage]

        if self.plant_state.days_in_stage >= current_duration and self.plant_state.health_score > 60:
            self._advance_growth_stage()

    def _advance_growth_stage(self):
        """Advance to next growth stage."""
        stages = ["seedling", "vegetative", "flowering", "fruiting"]
        current_index = stages.index(self.plant_state.growth_stage)

        if current_index < len(stages) - 1:
            self.plant_state.growth_stage = stages[current_index + 1]
            self.plant_state.days_in_stage = 0

        # Yield production in fruiting stage
        if self.plant_state.growth_stage == "fruiting":
            yield_amount = self.plant_state.size * self.plant_state.health_score / 100
            self.plant_state.total_yield += yield_amount * 0.1  # Daily yield

    def _calculate_water_usage(self, command: GreenhouseCommand, duration: float) -> float:
        """Calculate water usage in liters."""
        # Watering system usage
        watering_usage = command.watering_duration * 2.0  # 2 L/minute

        # Humidification (if any)
        humidity_usage = 0.0  # Simplified

        return watering_usage + humidity_usage

    def _calculate_energy_usage(self, command: GreenhouseCommand, duration: float) -> float:
        """Calculate energy usage in kWh."""
        # Lighting energy
        lighting_kw = 0.4 * (command.light_intensity / 100.0)  # 400W LED at full power

        # Heating energy
        heating_kw = 2.0 * (command.heating_level / 100.0)  # 2kW heater

        # Ventilation energy
        ventilation_kw = 0.2 * (command.ventilation_level / 100.0)  # 200W fan

        # Pumps and controls
        pumps_kw = 0.1 if command.watering_duration > 0 else 0.05  # Always some baseline

        total_kw = lighting_kw + heating_kw + ventilation_kw + pumps_kw
        return total_kw * duration

    def _record_metrics(self, water_used: float, energy_used: float):
        """Record historical metrics."""
        self.metrics.health_scores.append(self.plant_state.health_score)
        self.metrics.growth_rates.append(self.plant_state.size)
        self.metrics.water_usage.append(water_used)
        self.metrics.energy_usage.append(energy_used)
        self.metrics.yields.append(self.plant_state.total_yield)

        # Keep only recent history (last 100 points)
        for metric_list in [
            self.metrics.health_scores,
            self.metrics.growth_rates,
            self.metrics.water_usage,
            self.metrics.energy_usage,
            self.metrics.yields,
        ]:
            if len(metric_list) > 100:
                metric_list.pop(0)

    def apply_watering(self, duration: float):
        """Apply watering to increase soil moisture."""
        if duration > 0:
            moisture_increase = duration * 8  # 8% per minute
            self.plant_state.soil_moisture = min(100, self.plant_state.soil_moisture + moisture_increase)

    def apply_nutrients(self, dose: float):
        """Apply nutrients to increase nutrient level."""
        if dose > 0:
            nutrient_increase = dose / 2  # 1ml = 0.5% increase
            self.plant_state.nutrient_level = min(100, self.plant_state.nutrient_level + nutrient_increase)

    def get_growth_stage_progress(self) -> float:
        """Get progress through current growth stage (0-100%)."""
        current_duration = self.stage_durations[self.plant_state.growth_stage]
        return min(100, (self.plant_state.days_in_stage / current_duration) * 100)

    def get_efficiency_metrics(self) -> dict[str, float]:
        """Calculate resource efficiency metrics."""
        if self.simulation_hours <= 0:
            return {"water_efficiency": 0, "energy_efficiency": 0, "yield_per_day": 0}

        days = self.simulation_hours / 24
        yield_per_day = self.plant_state.total_yield / max(days, 0.1)
        water_efficiency = self.plant_state.total_yield / max(self.total_water_used, 0.1)
        energy_efficiency = self.plant_state.total_yield / max(self.total_energy_used, 0.1)

        return {"water_efficiency": water_efficiency, "energy_efficiency": energy_efficiency, "yield_per_day": yield_per_day}

    def reset(self):
        """Reset simulation to initial state."""
        self.plant_state = PlantState()
        self.environment = EnvironmentState()
        self.metrics = PlantMetrics()
        self.total_water_used = 0.0
        self.total_energy_used = 0.0
        self.simulation_hours = 0
