"""
Building Management Domain Plugin for POET

Provides domain-specific intelligence for HVAC and building management systems,
including thermal optimization, equipment protection, and energy efficiency.
"""

from typing import Any, Dict, Tuple
from dataclasses import dataclass


@dataclass
class HVACCommand:
    """HVAC control command output."""
    heating_output: float  # 0-100%
    cooling_output: float  # 0-100%
    fan_speed: float      # 0-100%
    status: str           # Status message


class BuildingManagementPlugin:
    """Domain plugin for HVAC and building management systems."""
    
    def __init__(self):
        self.thermal_models = {}
        self.equipment_constraints = {
            "min_temp": 60, "max_temp": 85,
            "min_humidity": 30, "max_humidity": 70,
            "max_temp_change_rate": 2.0  # degrees per hour
        }
        self.energy_optimization_enabled = True
    
    def process_inputs(self, args: Tuple, kwargs: Dict) -> Dict[str, Any]:
        """Process HVAC control inputs with building intelligence."""
        
        # Extract common HVAC parameters
        if len(args) >= 4:
            # Standard HVAC function signature: (current_temp, setpoint, occupancy, outdoor_temp)
            current_temp, setpoint, occupancy, outdoor_temp = args[:4]
        else:
            # Extract from kwargs or use defaults
            current_temp = kwargs.get('current_temp', args[0] if len(args) > 0 else 72.0)
            setpoint = kwargs.get('setpoint', args[1] if len(args) > 1 else 72.0)
            occupancy = kwargs.get('occupancy', args[2] if len(args) > 2 else True)
            outdoor_temp = kwargs.get('outdoor_temp', args[3] if len(args) > 3 else 70.0)
        
        # Apply building management intelligence
        enhanced_inputs = {
            "current_temp": self._validate_temperature(current_temp),
            "setpoint": self._optimize_setpoint(setpoint, occupancy),
            "occupancy": occupancy,
            "outdoor_temp": self._validate_temperature(outdoor_temp),
            "thermal_context": self._get_thermal_context({
                'current_temp': current_temp,
                'setpoint': setpoint,
                'occupancy': occupancy,
                'outdoor_temp': outdoor_temp
            })
        }
        
        return {
            "args": (
                enhanced_inputs["current_temp"],
                enhanced_inputs["setpoint"], 
                enhanced_inputs["occupancy"],
                enhanced_inputs["outdoor_temp"]
            ),
            "kwargs": {}
        }
    
    def validate_output(self, operation_result: Dict, processed_input: Dict) -> Any:
        """Validate HVAC control output for safety and efficiency."""
        
        result = operation_result["result"]
        
        # Validate output is reasonable control command
        if hasattr(result, 'heating_output'):
            if not (0 <= result.heating_output <= 100):
                raise ValueError(f"Invalid heating output: {result.heating_output}%")
                
        if hasattr(result, 'cooling_output'):
            if not (0 <= result.cooling_output <= 100):
                raise ValueError(f"Invalid cooling output: {result.cooling_output}%")
        
        if hasattr(result, 'fan_speed'):
            if not (0 <= result.fan_speed <= 100):
                raise ValueError(f"Invalid fan speed: {result.fan_speed}%")
        
        # Equipment protection: prevent simultaneous heating and cooling
        if (hasattr(result, 'heating_output') and hasattr(result, 'cooling_output') and 
            result.heating_output > 10 and result.cooling_output > 10):
            raise ValueError("Equipment protection: Cannot heat and cool simultaneously")
        
        # Energy efficiency check
        if self.energy_optimization_enabled:
            result = self._apply_energy_optimization(result, processed_input)
        
        return result
    
    def _validate_temperature(self, temp) -> float:
        """Validate and normalize temperature readings."""
        if temp is None:
            return 70.0  # Reasonable default
        
        # Handle various temperature formats
        if isinstance(temp, str):
            try:
                # Handle common formats like "72°F", "72F", "72.5"
                temp = float(temp.replace('°F', '').replace('F', '').strip())
            except:
                return 70.0
        
        # Validate reasonable range (0-120°F)
        if not (0 <= temp <= 120):
            return 70.0
            
        return float(temp)
    
    def _optimize_setpoint(self, setpoint: float, occupancy: bool) -> float:
        """Apply energy-saving setpoint optimization."""
        if setpoint is None:
            return 72.0 if occupancy else 68.0
        
        setpoint = self._validate_temperature(setpoint)
        
        # Energy saving when unoccupied
        if not occupancy and self.energy_optimization_enabled:
            # 3-degree setback when unoccupied
            return max(setpoint - 3, 65)
            
        return setpoint
    
    def _get_thermal_context(self, inputs: Dict) -> Dict[str, Any]:
        """Generate thermal context for enhanced control decisions."""
        current_temp = inputs.get('current_temp', 72)
        setpoint = inputs.get('setpoint', 72)
        outdoor_temp = inputs.get('outdoor_temp', 70)
        occupancy = inputs.get('occupancy', True)
        
        temp_error = current_temp - setpoint
        outdoor_delta = outdoor_temp - current_temp
        
        return {
            "temp_error": temp_error,
            "outdoor_delta": outdoor_delta,
            "heating_load": max(0, -temp_error) if outdoor_temp < current_temp else 0,
            "cooling_load": max(0, temp_error) if outdoor_temp > current_temp else 0,
            "occupancy_factor": 1.0 if occupancy else 0.7,
            "recommended_deadband": 2.0 if not occupancy else 1.0
        }
    
    def _apply_energy_optimization(self, result: Any, processed_input: Dict) -> Any:
        """Apply energy optimization to HVAC commands."""
        
        if not hasattr(result, 'heating_output') and not hasattr(result, 'cooling_output'):
            return result
        
        thermal_context = processed_input.get("kwargs", {}).get("thermal_context", {})
        occupancy_factor = thermal_context.get("occupancy_factor", 1.0)
        
        # Apply occupancy-based energy reduction
        if hasattr(result, 'heating_output'):
            result.heating_output *= occupancy_factor
            
        if hasattr(result, 'cooling_output'):
            result.cooling_output *= occupancy_factor
        
        # Fan speed optimization
        if hasattr(result, 'fan_speed'):
            # Reduce fan speed during low-load conditions
            if result.heating_output < 20 and result.cooling_output < 20:
                result.fan_speed = max(result.fan_speed * 0.8, 20)  # Minimum 20% for air circulation
        
        # Update status to reflect optimization
        if hasattr(result, 'status'):
            if occupancy_factor < 1.0:
                result.status += " (Energy optimized)"
        
        return result