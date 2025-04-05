#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1: Setting up Temperature Sensors

This example demonstrates how to set up mock temperature sensors for a monitoring system.
It covers sensor creation, data source configuration, and data format setup.

Key concepts:
- Mock sensor creation
- Data source configuration
- Data format definition
"""

import asyncio
import random
import logging
from typing import Dict, Any, List
from datetime import datetime

from dxa.common import DXA_LOGGER

# Step 1: Configure logging
DXA_LOGGER.configure(level=logging.INFO)

class TemperatureSensor:
    """Mock temperature sensor that generates random temperature readings."""
    
    def __init__(self, sensor_id: str, location: str, min_temp: float = 15.0, max_temp: float = 30.0):
        """Initialize the temperature sensor.
        
        Args:
            sensor_id: Unique identifier for the sensor
            location: Physical location of the sensor
            min_temp: Minimum temperature the sensor can read
            max_temp: Maximum temperature the sensor can read
        """
        self.sensor_id = sensor_id
        self.location = location
        self.min_temp = min_temp
        self.max_temp = max_temp
        DXA_LOGGER.info(f"Initialized temperature sensor {sensor_id} at {location}")
    
    async def read_temperature(self) -> Dict[str, Any]:
        """Read the current temperature from the sensor.
        
        Returns:
            Dictionary containing sensor data
        """
        # Simulate sensor reading delay
        await asyncio.sleep(0.1)
        
        # Generate random temperature within range
        temperature = random.uniform(self.min_temp, self.max_temp)
        
        # Create sensor reading data
        reading = {
            "sensor_id": self.sensor_id,
            "location": self.location,
            "temperature": round(temperature, 2),
            "timestamp": datetime.now().isoformat(),
            "unit": "celsius"
        }
        
        DXA_LOGGER.debug(f"Sensor {self.sensor_id} reading: {temperature:.2f}°C")
        return reading

class SensorNetwork:
    """Network of temperature sensors."""
    
    def __init__(self):
        """Initialize the sensor network."""
        self.sensors: List[TemperatureSensor] = []
        DXA_LOGGER.info("Initialized sensor network")
    
    def add_sensor(self, sensor: TemperatureSensor) -> None:
        """Add a sensor to the network.
        
        Args:
            sensor: Temperature sensor to add
        """
        self.sensors.append(sensor)
        DXA_LOGGER.info(f"Added sensor {sensor.sensor_id} to the network")
    
    async def read_all_sensors(self) -> List[Dict[str, Any]]:
        """Read data from all sensors in the network.
        
        Returns:
            List of sensor readings
        """
        tasks = [sensor.read_temperature() for sensor in self.sensors]
        readings = await asyncio.gather(*tasks)
        return readings

# Step 2: Create temperature sensors
async def setup_sensors() -> SensorNetwork:
    """Set up a network of temperature sensors.
    
    Returns:
        Configured sensor network
    """
    # Create sensor network
    network = SensorNetwork()
    
    # Add sensors to the network
    network.add_sensor(TemperatureSensor("temp-001", "Server Room", 18.0, 27.0))
    network.add_sensor(TemperatureSensor("temp-002", "Office Area", 20.0, 25.0))
    network.add_sensor(TemperatureSensor("temp-003", "Data Center", 16.0, 22.0))
    
    # Test the network
    readings = await network.read_all_sensors()
    for reading in readings:
        DXA_LOGGER.info(f"Sensor {reading['sensor_id']} at {reading['location']}: {reading['temperature']}°C")
    
    return network

# Step 3: Demonstrate sensor usage
async def main():
    """Main function to demonstrate sensor setup and usage."""
    DXA_LOGGER.info("Setting up temperature monitoring sensors")
    
    # Set up sensor network
    network = await setup_sensors()
    
    # Simulate continuous monitoring for a short period
    DXA_LOGGER.info("Starting continuous monitoring (press Ctrl+C to stop)")
    try:
        for _ in range(5):  # Monitor for 5 cycles
            readings = await network.read_all_sensors()
            # Just print the readings for now
            for reading in readings:
                print(f"{reading['timestamp']}: {reading['location']} - {reading['temperature']}°C")
            await asyncio.sleep(1)  # Wait 1 second between readings
    except KeyboardInterrupt:
        DXA_LOGGER.info("Monitoring stopped by user")
    
    DXA_LOGGER.info("Sensor demonstration completed")

if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())

# Next steps:
# - Proceed to 02_pipeline_creation.py to learn how to create a data processing pipeline
# - Experiment with different sensor configurations and reading frequencies
# - Add error handling and sensor health monitoring 