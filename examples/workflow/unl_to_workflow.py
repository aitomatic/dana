from dxa.agent.agent import Agent
from dxa.common.utils.logging.dxa_logger import DXA_LOGGER
from dxa.execution.workflow.workflow import Workflow
from dxa.execution.workflow.workflow_factory import WorkflowFactory
import asyncio

UNL_TO_ONL_PROMPT = """
    You are an expert in translating unstructured natural language into organized natural language. 
    
    Your task is to: 
    1. Convert a multi-level troubleshooting procedure into a organized natural language format that can describe a work flow.
    2. Maintain the essential content while improving organization.

    Instructions: 
    1. Identify the main procedure name and use it as the root.
    2. Identify the main process name and use it under the root limit it under 10 main processes.
    3. Indentfy the steps for each process and list them in sequence.
    4. Generate clean, valid preserves the procedural flow of the original text
    5. The output should be plain text with no formatting.

    The original text is: ```{unl}```
"""

ONL_TO_WORKFLOW_PROMPT = """
    You are an expert in transforming unstructured text into organized YAML format

    Your task is to: 
    1. Convert a multi-level troubleshooting procedure into a structured YAML format that can describe a work flow, which can covert to a dict[str, list[str]] in python, where * key is a short name for a certain process, * each key is then mapped to a list of steps (in sequence) that should be followed.
    2. Maintain the essential content while improving organization 
    3. Use consistent YAML syntax including proper indentation and list markers.
    4. THIS IS VERY IMPORTANT: The output should be a valid YAML content only, no other text or comments. And dont put the content in ```yaml``` tags.

    Instructions: 
    1. Identify the main procedure name and use it as the root key 
    2. Generate clean, valid YAML that preserves the procedural flow of the original text
    [THIS IS VERY IMPORTANT] Strictly follow example workflow file with just the essential structure.
    ```
    workflow-name: 
        process-name:
            - "Step 1" 
            - "Step 2"
    ```
    The original text is: ```{onl}```
"""

def run_unl_to_workflow_two_agents(unl: str):
    print("\n\n==================== Translate UNL to ONL =====================")
    agent = Agent("unl_to_onl_agent")
    result = agent.ask(UNL_TO_ONL_PROMPT.format(unl=unl))
    onl = result['result']
    print(f"\nRESULT: \n{onl}")

    print("\n\n==================== Translate ONL to workflow =====================")
    agent = Agent("onl_to_workflow_agent")
    result = agent.ask(ONL_TO_WORKFLOW_PROMPT.format(onl=onl))
    workflow_yaml = result['result']
    print(f"\nRESULT: \n{workflow_yaml}")

    # remove the yaml tags if exists
    workflow_yaml = workflow_yaml.replace("```yaml", "").replace("```", "")

    workflow = WorkflowFactory.from_yaml(workflow_yaml)
    agent = Agent("workflow_agent")
    result = agent.run(workflow)
    print(f"\nRESULT: \n{result}")

async def run_unl_to_workflow(unl: str):
    print("\n\n==================== Translate UNL to workflow =====================")
    workflow_yaml = await Workflow.natural_language_to_yaml(unl)
    print(f"\nRESULT: \n{workflow_yaml}")

    workflow = WorkflowFactory.from_yaml(workflow_yaml)
    agent = Agent("workflow_agent")
    result = await agent.async_run(workflow)
    print(f"\nRESULT: \n{result}")


if __name__ == "__main__":
    DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, log_data=True)
    unl = """
        When equipment issues come up in the fab, operators usually start by looking at the basic stuff - you know, power, pressure, those kinds of readings. If anything looks off, they'll want to check the maintenance history and see if someone's worked on it recently. Sometimes the logs will show some warnings that help point to what's wrong. If the basic checks don't show anything obvious, they'll need to dig deeper into the process data and maybe check if sensors are reading correctly. It's important to document everything as you go. If they can't figure it out quickly, they'll need to call in the technical team and maybe shut things down temporarily while they investigate. The key is to be thorough but also work quickly to minimize downtime.
    """

    asyncio.run(run_unl_to_workflow(unl))

    # run_unl_to_workflow_two_agents(unl)