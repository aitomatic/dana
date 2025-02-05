"""System health monitoring example."""

import asyncio
from dxa.agent import Agent
from dxa.execution.workflow.workflow_factory import WorkflowFactory
from dxa.execution import WorkflowStrategy, PlanningStrategy

async def monitor_system():
    """Continuous system monitoring loop."""
    agent = (Agent("sysmon_agent")
             .with_workflow(WorkflowStrategy.CONDITIONAL)
             .with_planning(PlanningStrategy.DYNAMIC))
    
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
    for signal in signals:
        if signal.type == "parameters_abnormal":
            print(f"ALERT: {signal.content['parameter']} at {signal.content['value']}%")
            # trigger_alert(signal.content)  # Implement actual alerting

if __name__ == "__main__":
    asyncio.run(monitor_system()) 