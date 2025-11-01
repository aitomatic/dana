"""
HVAC Environment Simulation - Core Modules

This package contains the core simulation components:
- config: Configuration classes for HVAC and thermal properties
- thermal_physics: Physics engine for HVAC calculations
- environment_generator: Environment state generation
- action_validator: Action plan validation and cost calculation
"""

from .config import (
    Mode,
    HVACConfig,
    ThermalConfig,
    EnvironmentConfig
)

from .thermal_physics import ThermalPhysics
from .environment_generator import EnvironmentGenerator
from .action_validator import ActionValidator

__all__ = [
    # Types
    'Mode',
    # Configuration
    'HVACConfig',
    'ThermalConfig',
    'EnvironmentConfig',
    # Core classes
    'ThermalPhysics',
    'EnvironmentGenerator',
    'ActionValidator',
]

__version__ = '2.0.0'
