"""Temperature Monitoring Pipeline Example

This example demonstrates how to create and execute a simple data processing pipeline
in the DXA framework. The pipeline reads temperature data from a simulated sensor,
analyzes it, and reports the results. It also shows how the pipeline can be used
both as an execution graph and as a discoverable resource.

Key concepts:
- Pipeline creation and configuration
- Pipeline as both execution graph and resource
- Asynchronous data processing
- Step-by-step data transformation
- Pipeline execution and querying

Learning path: Core Concepts
Complexity: Intermediate

Prerequisites:
- None

Related examples:
- ../workflow/system_health.py: System monitoring example
- ../../resource/llm_resource.py: Resource integration
"""

from typing import Dict, Any
from opendxa.execution import Pipeline
from opendxa.common import DXA_LOGGER

async def main():
    """Run a temperature monitoring pipeline.
    
    This function demonstrates:
    1. Creating a pipeline with multiple processing steps
    2. Executing the pipeline as an execution graph
    3. Querying the pipeline as a resource
    
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
    # The pipeline inherits from both ExecutionGraph and BaseResource
    pipeline = Pipeline(
        name="temp_monitor",
        objective="Monitor and analyze temperature data",
        steps=[read_sensor, analyze, report],
        description="Pipeline for monitoring temperature sensor data"
    )
    
    # Step 1: Execute the pipeline as an execution graph
    result = await pipeline.execute()
    print("\nExecution result:", result)
    
    # Step 2: Use the pipeline as a resource
    # Initialize the pipeline resource
    await pipeline.initialize()
    
    # Query the pipeline
    response = await pipeline.query({})
    print("\nQuery result:", response.content)
    
    # Clean up the pipeline resource
    await pipeline.cleanup()
        

if __name__ == "__main__":
    # Use asyncio to run the async main function
    import asyncio
    asyncio.run(main()) 
