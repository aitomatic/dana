"""RIE RF matching monitoring example using DXA."""

import asyncio
import yaml
from pathlib import Path
from dxa.core.agent import Agent
from dxa.core.workflow import WorkflowFactory
from dxa.core.state import WorldState, ExecutionState, AgentState
from dxa.core.execution import ExecutionContext
from dxa.common.graph.traversal import ContinuousTraversal
from resources.mock_fdc import MockFDC

async def load_knowledge():
    """Load monitoring knowledge from YAML files."""
    knowledge_dir = Path(__file__).parent / "knowledge"
    
    # Load parameter definitions
    with open(knowledge_dir / "diagnosis/parameters.yaml") as f:
        parameters = yaml.safe_load(f)
    
    # Load fault patterns
    with open(knowledge_dir / "diagnosis/rf_matching.yaml") as f:
        fault_patterns = yaml.safe_load(f)
        
    # Load monitoring workflow
    with open(knowledge_dir / "workflows/monitoring.yaml") as f:
        workflow = yaml.safe_load(f)
        
    return {
        "parameters": parameters,
        "fault_patterns": fault_patterns,
        "workflow": workflow
    }

async def main():
    """Run the RIE monitoring example."""
    # Load knowledge
    knowledge = await load_knowledge()
    
    # Create mock FDC data source
    fdc = MockFDC()
    
    # Create and configure agent
    agent = Agent("rie_monitor")
    
    # Create workflow from YAML with continuous traversal
    workflow = WorkflowFactory.from_yaml(knowledge["workflow"])
    workflow._default_traversal = ContinuousTraversal()  # Set traversal strategy
    
    # Create execution context
    context = ExecutionContext(
        agent_state=AgentState(),
        world_state=WorldState(),
        execution_state=ExecutionState(),
        parameters=knowledge["parameters"],
        fault_patterns=knowledge["fault_patterns"]
    )
    
    # Execute monitoring loop
    async with agent:
        try:
            async for data in fdc.generate_data():
                # Update context with new data
                context.update_monitoring_data(data)
                
                # Execute workflow cycle
                result = await agent.async_run(workflow, context)
                
                if result:  # We have a diagnosis
                    print(f"Timestamp: {data['timestamp']}")
                    print(f"Values: {data['values']}")
                    print(f"Diagnosis: {result}")
                    print("---")
                    
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

if __name__ == "__main__":
    asyncio.run(main()) 