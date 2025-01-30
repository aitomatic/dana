"""Temperature monitoring pipeline example."""

from typing import Dict, Any
from dxa.core.execution.pipeline import Pipeline, PipelineContext

async def main():
    """Run temperature monitoring pipeline."""
    
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

    # Create pipeline
    pipeline = Pipeline(
        name="temp_monitor",
        steps=[read_sensor, analyze, report]
    )
    
    # Create and setup context
    context = PipelineContext()
    await pipeline.setup(context)
    
    try:
        # Execute pipeline
        await pipeline.execute()
    finally:
        # Clean up
        await pipeline.cleanup(context)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 
