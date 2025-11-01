#!/usr/bin/env python3
"""
Configuration classes for HVAC environment simulation.

Centralizes all configuration parameters from ac_test.py and room_feedback.py.
"""

from dataclasses import dataclass
from typing import Literal

Mode = Literal["cool", "heat"]


@dataclass(frozen=True)
class HVACConfig:
    """HVAC system specifications."""

    name: str
    base_capacity_w: float        # Base cooling/heating power (W)
    turbo_capacity_w: float       # Turbo mode power (W)
    turbo_max_minutes: float      # Max turbo duration (minutes)

    @classmethod
    def small_unit(cls) -> "HVACConfig":
        """
        Small HVAC unit from ac_test.py.
        2000W base (~6,800 BTU/hr), suitable for small spaces.
        """
        return cls(
            name="Small Unit (6,800 BTU/hr)",
            base_capacity_w=2000.0,
            turbo_capacity_w=2600.0,
            turbo_max_minutes=30.0
        )

    @classmethod
    def standard_unit(cls) -> "HVACConfig":
        """
        Standard 2-ton HVAC unit from room_feedback.py.
        7000W base (~24,000 BTU/hr), typical residential AC.
        """
        return cls(
            name="Standard 2-Ton (24,000 BTU/hr)",
            base_capacity_w=7000.0,
            turbo_capacity_w=9000.0,
            turbo_max_minutes=30.0
        )


@dataclass(frozen=True)
class ThermalConfig:
    """Building thermal properties."""

    heat_transfer_coeff_w_k: float    # UA (W/K) - heat transfer coefficient
    thermal_mass_j_k: float           # C (J/K) - thermal mass
    internal_heat_w: float            # Q_int (W) - internal heat generation
    fan_boost_multiplier: float       # Fan boost for UA

    @classmethod
    def standard_insulation(cls) -> "ThermalConfig":
        """
        Standard insulation from ac_test.py.
        Higher heat transfer (less insulated), smaller thermal mass.
        """
        return cls(
            heat_transfer_coeff_w_k=150.0,
            thermal_mass_j_k=5e5,
            internal_heat_w=200.0,
            fan_boost_multiplier=1.0
        )

    @classmethod
    def better_insulation(cls) -> "ThermalConfig":
        """
        Better insulation from room_feedback.py.
        Lower heat transfer (better insulated), larger thermal mass.
        """
        return cls(
            heat_transfer_coeff_w_k=85.0,
            thermal_mass_j_k=1.2e6,
            internal_heat_w=100.0,
            fan_boost_multiplier=1.0
        )


@dataclass
class EnvironmentConfig:
    """Complete room configuration combining HVAC and thermal properties."""

    room_name: str
    hvac_config: HVACConfig
    thermal_config: ThermalConfig

    @classmethod
    def ac_test_profile(cls, room_name: str = "Conference Room A") -> "EnvironmentConfig":
        """
        Configuration matching ac_test.py parameters.
        Small HVAC unit with standard insulation.
        """
        return cls(
            room_name=room_name,
            hvac_config=HVACConfig.small_unit(),
            thermal_config=ThermalConfig.standard_insulation()
        )

    @classmethod
    def room_feedback_profile(cls, room_name: str = "Conference Room A") -> "EnvironmentConfig":
        """
        Configuration matching room_feedback.py parameters (DEFAULT).
        Standard 2-ton HVAC with better insulation.
        This is the default profile for backward compatibility.
        """
        return cls(
            room_name=room_name,
            hvac_config=HVACConfig.standard_unit(),
            thermal_config=ThermalConfig.better_insulation()
        )
