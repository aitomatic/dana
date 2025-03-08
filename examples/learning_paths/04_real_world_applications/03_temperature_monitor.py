"""Temperature Monitoring Pipeline Example

This example demonstrates how to create and execute a simple data processing pipeline
in the DXA framework. The pipeline reads temperature data from a simulated sensor,
analyzes it, and reports the results.

Key concepts:
- Pipeline creation and configuration
- Asynchronous data processing
- Step-by-step data transformation
- Pipeline execution

Learning path: Core Concepts
Complexity: Intermediate

Prerequisites:
- None

Related examples:
- ../workflow/system_health.py: System monitoring example
- ../../resource/llm_resource.py: Resource integration
"""

from typing import Dict, Any
from dxa.execution import Pipeline
from dxa.common import DXA_LOGGER

async def main():
    """Run a temperature monitoring pipeline.
    
    This function demonstrates:
    1. Creating a pipeline with multiple processing steps
    2. Defining data transformation functions
    3. Executing the pipeline asynchronously
    
    The pipeline consists of three stages:
    - read_sensor: Simulates reading data from a temperature sensor
    - analyze: Processes the temperature data and determines status
    - report: Outputs the results
    
    Returns:
        None: This function executes the pipeline but doesn't return a value
    """
    
    # Enable debug logging with data samples
    # This allows us to see the data flowing through the pipeline
    DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, log_data=True)

    # Define pipeline steps
    # pylint: disable=unused-argument
    async def read_sensor(data: Dict[str, Any]) -> Dict[str, Any]:
        """Read sensor data.
        
        This function simulates reading data from a temperature sensor.
        In a real application, this would connect to an actual sensor.
        
        Args:
            data: Input data (not used in this example)
            
        Returns:
            Dict with temperature reading
        """
        return {"temperature": 25.0}
        
    async def analyze(data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temperature data.
        
        This function processes the temperature reading and determines
        if it's within normal range or high.
        
        Args:
            data: Input data containing temperature reading
            
        Returns:
            Dict with temperature and status information
        """
        temp = data["temperature"]
        return {
            "temperature": temp,
            "status": "high" if temp > 30 else "normal"
        }
        
    async def report(data: Dict[str, Any]) -> Dict[str, Any]:
        """Report analysis results.
        
        This function outputs the temperature and status information.
        In a real application, this might send alerts or update a dashboard.
        
        Args:
            data: Input data containing temperature and status
            
        Returns:
            The same data, passed through
        """
        print(f"Temperature: {data['temperature']}°C ({data['status']})")
        return data

    # Create pipeline with the defined steps
    # Each step will be executed in sequence, with the output of one step
    # becoming the input to the next step
    pipeline = Pipeline(
        name="temp_monitor",
        steps=[read_sensor, analyze, report]
    )
    
    # Execute pipeline (context will be auto-created if needed)
    # This runs the pipeline once; for continuous monitoring, you would
    # typically put this in a loop with a delay
    await pipeline.execute()
        

if __name__ == "__main__":
    # Use asyncio to run the async main function
    import asyncio
    asyncio.run(main()) 
