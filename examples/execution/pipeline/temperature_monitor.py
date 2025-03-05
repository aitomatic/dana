"""Temperature monitoring pipeline example."""

from typing import Dict, Any
from dxa.execution import Pipeline
from dxa.common import DXA_LOGGER

async def main():
    """Run temperature monitoring pipeline."""
    
    # Enable debug logging with data samples
    DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, log_data=True)

    # Define pipeline steps
    # pylint: disable=unused-argument
    async def read_sensor(data: Dict[str, Any]) -> Dict[str, Any]:
        """Read sensor data."""
        return {"temperature": 25.0}
        
    async def analyze(data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temperature."""
        temp = data["temperature"]
        return {
            "temperature": temp,
            "status": "high" if temp > 30 else "normal"
        }
        
    async def report(data: Dict[str, Any]) -> Dict[str, Any]:
        """Report results."""
        print(f"Temperature: {data['temperature']}°C ({data['status']})")
        return data

    # Execution starts here
    
    # Create pipeline
    pipeline = Pipeline(
        name="temp_monitor",
        steps=[read_sensor, analyze, report]
    )
    
    # Execute pipeline (context will be auto-created if needed)
    await pipeline.execute()
        

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 
