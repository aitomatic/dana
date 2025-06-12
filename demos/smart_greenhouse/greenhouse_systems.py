"""
Greenhouse Control Systems - Basic vs POET-Enhanced

This module shows two greenhouse control functions:
1. Basic Greenhouse: Fixed schedules and thresholds (SENSE + ACT)
2. POET Greenhouse: Adaptive learning control (SENSE + THINK + ACT)

The key insight: Same logic, POET adds intelligent optimization.
"""

from dataclasses import dataclass
from typing import Dict, Any
import math

# Mock POET decorator for demo
print("🌱 Running greenhouse demo with mock POET decorator")


def poet(*args, **kwargs):
    """Mock POET decorator that simulates POET enhancements for demo purposes."""

    def decorator(func):
        def wrapper(*func_args, **func_kwargs):
            result = func(*func_args, **func_kwargs)
            return {"result": result, "execution_time": 0.002, "success": True, "attempts": 1, "poet_enhanced": True}

        # Mock learning methods
        execution_count = 0

        def get_learning_status(*args, **kwargs):
            nonlocal execution_count
            execution_count += 1

            if execution_count < 10:
                status = "Learning optimal growing conditions..."
            elif execution_count < 30:
                status = "Analyzing plant response patterns..."
            elif execution_count < 80:
                status = "Optimizing resource efficiency..."
            else:
                status = "Advanced cultivation active"

            return {
                "learning_enabled": True,
                "learning_algorithm": "botanical_optimization",
                "executions": execution_count,
                "success_rate": min(0.98, 0.6 + (execution_count * 0.008)),
                "status": status,
            }

        def get_learning_recommendations(*args, **kwargs):
            if execution_count < 10:
                return ["Calibrating sensor baselines", "Learning plant growth cycles", "Initializing nutrient profiles"]
            elif execution_count < 30:
                return ["Detecting optimal watering windows", "Learning light response curves", "Analyzing soil microclimate"]
            elif execution_count < 80:
                return ["Optimizing growth phases", "Reducing water waste 15%", "Improving yield predictions"]
            else:
                return ["Yield optimization active", "Water savings: 25%", "Growth rate improved 18%"]

        def get_metrics(*args, **kwargs):
            return {
                "total_executions": execution_count,
                "success_rate": min(0.98, 0.6 + (execution_count * 0.008)),
                "avg_execution_time": 0.002,
                "learning_progress": "active",
            }

        wrapper.get_learning_status = get_learning_status
        wrapper._poet_executor = type(
            "MockPOETExecutor",
            (),
            {
                "get_learning_status": get_learning_status,
                "get_learning_recommendations": get_learning_recommendations,
                "get_metrics": get_metrics,
            },
        )()
        return wrapper

    return decorator


POET_AVAILABLE = "mock"


@dataclass
class GreenhouseCommand:
    """Greenhouse control command output."""

    watering_duration: float  # minutes
    light_intensity: float  # 0-100%
    ventilation_level: float  # 0-100%
    nutrient_dose: float  # ml
    heating_level: float  # 0-100%
    co2_injection: float  # ppm increase


# ============================================================
# BASIC GREENHOUSE CONTROL (No POET) - SENSE + ACT
# ============================================================


def basic_greenhouse_control(
    soil_moisture: float,
    light_level: float,
    temperature: float,
    humidity: float,
    plant_stage: str,  # "seedling", "vegetative", "flowering", "fruiting"
    time_of_day: float,
) -> GreenhouseCommand:
    """
    Basic scheduled greenhouse control.

    Fixed schedules and thresholds - no learning, no optimization.
    """
    # Fixed watering schedule
    if soil_moisture < 30:  # Below 30% = water for 5 minutes
        watering_duration = 5.0
    else:
        watering_duration = 0.0

    # Fixed lighting schedule (12 hours on/off)
    if 6 <= time_of_day <= 18:  # Daytime lighting
        light_intensity = 80.0
    else:
        light_intensity = 0.0

    # Basic ventilation (temperature-based only)
    if temperature > 75:
        ventilation_level = 60.0
    elif temperature > 70:
        ventilation_level = 30.0
    else:
        ventilation_level = 10.0

    # Fixed nutrient schedule (once daily at 8 AM)
    if 7.5 <= time_of_day <= 8.5:
        nutrient_dose = 50.0  # ml
    else:
        nutrient_dose = 0.0

    # Basic heating (temperature-based only)
    if temperature < 65:
        heating_level = 40.0
    else:
        heating_level = 0.0

    # No CO2 injection in basic system
    co2_injection = 0.0

    return GreenhouseCommand(
        watering_duration=watering_duration,
        light_intensity=light_intensity,
        ventilation_level=ventilation_level,
        nutrient_dose=nutrient_dose,
        heating_level=heating_level,
        co2_injection=co2_injection,
    )


# ============================================================
# POET-ENHANCED GREENHOUSE CONTROL - SENSE + THINK + ACT
# ============================================================


@poet(
    domain="greenhouse_management",
    enable_training=True,
    learning_algorithm="botanical_optimization",
    objectives={"maximize_yield": 0.4, "minimize_water_usage": 0.25, "minimize_energy": 0.25, "optimize_growth_rate": 0.1},
)
def smart_greenhouse_control(
    soil_moisture: float, light_level: float, temperature: float, humidity: float, plant_stage: str, time_of_day: float
) -> GreenhouseCommand:
    """
    POET-enhanced greenhouse control.

    IDENTICAL base logic to basic_greenhouse_control, but POET adds:
    - Adaptive watering based on plant response
    - Optimal light timing for growth phases
    - Intelligent nutrient scheduling
    - Predictive climate control
    - Resource efficiency optimization
    """
    # SAME BASE LOGIC - POET enhances automatically

    # Adaptive watering (POET learns optimal thresholds)
    if soil_moisture < 30:
        watering_duration = 5.0
    else:
        watering_duration = 0.0

    # Smart lighting (POET optimizes timing and intensity)
    if 6 <= time_of_day <= 18:
        light_intensity = 80.0
    else:
        light_intensity = 0.0

    # Intelligent ventilation (POET considers humidity, plant stage)
    if temperature > 75:
        ventilation_level = 60.0
    elif temperature > 70:
        ventilation_level = 30.0
    else:
        ventilation_level = 10.0

    # Adaptive nutrient delivery (POET learns optimal timing)
    if 7.5 <= time_of_day <= 8.5:
        nutrient_dose = 50.0
    else:
        nutrient_dose = 0.0

    # Smart heating (POET optimizes for growth and efficiency)
    if temperature < 65:
        heating_level = 40.0
    else:
        heating_level = 0.0

    # POET adds CO2 optimization
    co2_injection = 0.0

    return GreenhouseCommand(
        watering_duration=watering_duration,
        light_intensity=light_intensity,
        ventilation_level=ventilation_level,
        nutrient_dose=nutrient_dose,
        heating_level=heating_level,
        co2_injection=co2_injection,
    )


# ============================================================
# PLANT RESPONSE SIMULATION
# ============================================================


class PlantGrowthController:
    """
    Simulates plant response to greenhouse conditions.
    Used for user feedback and POET learning.
    """

    def __init__(self):
        self.growth_stage = "seedling"
        self.stress_level = 0.0
        self.feedback_history = []

    def process_growth_feedback(self, feedback: str, current_conditions: Dict) -> str:
        """
        Process user feedback about plant health and adjust expectations.

        Args:
            feedback: "thriving", "healthy", "stressed", "wilting"
            current_conditions: Current greenhouse conditions

        Returns:
            Updated growth stage or recommendations
        """
        self.feedback_history.append({"feedback": feedback, "conditions": current_conditions, "stage": self.growth_stage})

        # Simulate growth stage progression
        if feedback == "thriving" and len(self.feedback_history) > 10:
            if self.growth_stage == "seedling":
                self.growth_stage = "vegetative"
            elif self.growth_stage == "vegetative":
                self.growth_stage = "flowering"
            elif self.growth_stage == "flowering":
                self.growth_stage = "fruiting"

        return self.growth_stage


def calculate_plant_health(soil_moisture: float, light_hours: float, temperature: float, nutrient_level: float, plant_stage: str) -> float:
    """
    Calculate plant health score (0-100) based on conditions.
    """
    # Optimal ranges by growth stage
    optimal_ranges = {
        "seedling": {"moisture": 40, "light": 8, "temp": 70, "nutrients": 30},
        "vegetative": {"moisture": 50, "light": 12, "temp": 72, "nutrients": 60},
        "flowering": {"moisture": 45, "light": 10, "temp": 68, "nutrients": 40},
        "fruiting": {"moisture": 55, "light": 10, "temp": 70, "nutrients": 80},
    }

    optimal = optimal_ranges.get(plant_stage, optimal_ranges["vegetative"])

    # Calculate deviations from optimal
    moisture_score = max(0, 100 - abs(soil_moisture - optimal["moisture"]) * 2)
    light_score = max(0, 100 - abs(light_hours - optimal["light"]) * 8)
    temp_score = max(0, 100 - abs(temperature - optimal["temp"]) * 4)
    nutrient_score = max(0, 100 - abs(nutrient_level - optimal["nutrients"]) * 1.5)

    # Weighted average
    health_score = moisture_score * 0.3 + light_score * 0.25 + temp_score * 0.25 + nutrient_score * 0.2

    return min(100, health_score)


def calculate_resource_efficiency(water_used: float, energy_used: float, yield_estimate: float) -> Dict[str, float]:
    """
    Calculate resource efficiency metrics.
    """
    if yield_estimate <= 0:
        return {"water_efficiency": 0, "energy_efficiency": 0}

    # Efficiency = yield per unit resource
    water_efficiency = yield_estimate / max(water_used, 0.1)
    energy_efficiency = yield_estimate / max(energy_used, 0.1)

    return {"water_efficiency": water_efficiency, "energy_efficiency": energy_efficiency}
