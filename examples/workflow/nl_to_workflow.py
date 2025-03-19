"""Example demonstrating natural language to workflow conversion."""

import asyncio
from dxa.agent.agent import Agent
from dxa.common.utils.logging.dxa_logger import DXA_LOGGER
from dxa.execution.workflow.workflow_factory import WorkflowFactory


async def run_nl_to_workflow_with_intervention(nl: str):
    """Demonstrate the two-step process with potential for human intervention."""
    print("\n\n==================== Step 1: NL to ONL =====================")
    onl = await WorkflowFactory.nl_to_onl(nl)
    print(f"\nORGANIZED NATURAL LANGUAGE: \n{onl}")
    
    # Here, in a real application, you could allow the user to edit the ONL
    # For example: onl = await get_user_edits(onl)
    
    print("\n\n==================== Step 2: ONL to YAML =====================")
    workflow_yaml = await WorkflowFactory.onl_to_yaml(onl)
    print(f"\nWORKFLOW YAML: \n{workflow_yaml}")
    
    # Here, you could also allow the user to edit the YAML
    # For example: workflow_yaml = await get_user_edits(workflow_yaml)
    
    print("\n\n==================== Step 3: Create and Run Workflow =====================")
    workflow = WorkflowFactory.from_yaml(workflow_yaml)
    agent = Agent("workflow_agent")
    result = await agent.async_run(workflow)
    print(f"\nRESULT: \n{result}")


async def run_nl_to_workflow_direct(nl: str):
    """Demonstrate the direct conversion from natural language to workflow."""
    print("\n\n==================== Direct NL to Workflow =====================")
    workflow = await WorkflowFactory.nl_to_workflow(nl)
    print(f"\nWorkflow created with {len(workflow.nodes)} nodes")
    
    agent = Agent("workflow_agent")
    result = await agent.async_run(workflow)
    print(f"\nRESULT: \n{result}")


if __name__ == "__main__":
    DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, log_data=True)
    
    # Example natural language description of a troubleshooting workflow
    unl = """
        When equipment issues come up in the fab, operators usually start by looking at the basic stuff - 
        you know, power, pressure, those kinds of readings. If anything looks off, they'll want to check 
        the maintenance history and see if someone's worked on it recently. Sometimes the logs will show 
        some warnings that help point to what's wrong. If the basic checks don't show anything obvious, 
        they'll need to dig deeper into the process data and maybe check if sensors are reading correctly. 
        It's important to document everything as you go. If they can't figure it out quickly, they'll need 
        to call in the technical team and maybe shut things down temporarily while they investigate. 
        The key is to be thorough but also work quickly to minimize downtime.
    """

    # Choose which example to run
    asyncio.run(run_nl_to_workflow_with_intervention(unl))
    asyncio.run(run_nl_to_workflow_direct(unl))