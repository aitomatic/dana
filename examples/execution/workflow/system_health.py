"""System health monitoring example."""

import asyncio
from dxa.agent import Agent
from dxa.execution.workflow.workflow_factory import WorkflowFactory
from dxa.execution import PlanStrategy

async def monitor_system():
    """Continuous system monitoring loop."""
    agent = (Agent("sysmon_agent")
             .with_planning(PlanStrategy.DYNAMIC))
    
    # Create monitoring workflow for CPU/Memory
    workflow = WorkflowFactory.create_monitoring_workflow(
        parameters=["cpu_usage", "memory_utilization"],
        description="Monitor system resources"
    )
    
    # Run continuous monitoring
    async with agent:
        while True:
            result = await agent.async_run(workflow)
            handle_monitoring_result(result)
            await asyncio.sleep(60)  # Check every minute

def handle_monitoring_result(signals):
    """Process monitoring signals with severity levels."""
    # If signals is a string, just print it
    if isinstance(signals, str):
        print(f"Result: {signals}")
        return
        
    # Check if signals is None
    if signals is None:
        print("No monitoring results received.")
        return
        
    # Process signals
    try:
        for signal in signals:
            if hasattr(signal, 'type') and signal.type == "parameters_abnormal":
                print(f"ALERT: {signal.content['parameter']} at {signal.content['value']}%")
                # trigger_alert(signal.content)  # Implement actual alerting
    except Exception as e:
        print(f"Error processing monitoring results: {e}")
        print(f"Received: {type(signals)}: {signals}")

if __name__ == "__main__":
    asyncio.run(monitor_system()) 