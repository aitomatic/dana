"""RIE RF matching monitoring example using DXA.

This example demonstrates how to use DXA for real-time monitoring of RIE RF matching,
using a mock FDC (Fault Detection and Classification) data source.

Key concepts:
- Loading knowledge from YAML files
- Creating and configuring an agent
- Setting up continuous monitoring
- Handling real-time data updates
- Using execution context for state management
"""

import asyncio
from pathlib import Path
import yaml
from dxa.agent import Agent
from dxa.execution.workflow import WorkflowFactory
from dxa.common.state import AgentState, WorldState, ExecutionState
from dxa.execution.execution_context import ExecutionContext
from dxa.common.graph.traversal import ContinuousTraversal
from resources.mock_fdc import MockFDC

async def load_knowledge():
    """Load monitoring knowledge from YAML files."""
    knowledge_dir = Path(__file__).parent / "knowledge"
    
    # Load parameter definitions
    with open(knowledge_dir / "diagnosis/parameters.yaml", encoding='utf-8') as f:
        parameters = yaml.safe_load(f)
    
    # Load fault patterns
    with open(knowledge_dir / "diagnosis/rf_matching.yaml", encoding='utf-8') as f:
        fault_patterns = yaml.safe_load(f)
        
    # Load monitoring workflow
    with open(knowledge_dir / "workflows/monitoring.yaml", encoding='utf-8') as f:
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
    start_node = workflow.get_start_node()
    if start_node:
        workflow.get_a_cursor(start_node, ContinuousTraversal())
    
    # Create execution context with global context
    context = ExecutionContext(
        agent_state=AgentState(),
        world_state=WorldState(),
        execution_state=ExecutionState(),
        workflow_llm=agent.workflow_llm,
        planning_llm=agent.planning_llm,
        reasoning_llm=agent.reasoning_llm,
        global_context={
            "parameters": knowledge["parameters"],
            "fault_patterns": knowledge["fault_patterns"]
        }
    )
    
    # Execute monitoring loop
    async with agent:
        try:
            async for data in fdc.generate_data():
                # Update world state with new data
                if context.world_state:
                    context.world_state.update({"monitoring_data": data})
                
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