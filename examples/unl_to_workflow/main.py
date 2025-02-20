from itertools import tee
from openai import chat
from traitlets import This
from dxa.agent.agent import Agent
from dxa.agent.resource.resource_factory import ResourceFactory
from dxa.common.utils.logging.dxa_logger import DXA_LOGGER
from dxa.execution.workflow.workflow_factory import WorkflowFactory
import yaml

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
    4. The output should be a valid YAML content only, no other text or comments. And dont put the content in ```yaml``` tags.

    Instructions: 
    1. Identify the main procedure name and use it as the root key 
    2. Generate clean, valid YAML that preserves the procedural flow of the original text
    [IMPORTANT] Strictly follow example workflow file with just the essential structure.
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
    onl = result['result']['content']
    print(f"\nRESULT: \n{onl}")

    print("\n\n==================== Translate ONL to workflow =====================")
    agent = Agent("onl_to_workflow_agent")
    result = agent.ask(ONL_TO_WORKFLOW_PROMPT.format(onl=onl))
    workflow_yaml = result['result']['content']
    print(f"\nRESULT: \n{workflow_yaml}")

    workflow = WorkflowFactory.from_yaml(workflow_yaml)
    agent = Agent("workflow_agent")
    result = agent.run(workflow)
    print(f"\nRESULT: \n{result}")

def run_unl_to_workflow_two_agents_with_reasoning_llm(unl: str):
    print("\n\n==================== Translate UNL to ONL =====================")
    config = {
        "name": "unl_to_onl_resource",
        "model": "gpt-4o-mini",
    }
    unl_to_onl_resource = ResourceFactory.create_llm_resource(config=config, system_prompt=UNL_TO_ONL_PROMPT)
    agent = Agent("unl_to_onl_agent").with_reasoning_llm(unl_to_onl_resource) 
    result = agent.ask(unl)
    onl = result['result']['content']
    print(f"\nRESULT: \n{onl}")

    print("\n\n==================== Translate ONL to workflow =====================")
    config = {
        "name": "onl_to_workflow_resource",
        "model": "gpt-4o-mini",
    }
    onl_to_workflow_resource = ResourceFactory.create_llm_resource(config=config, system_prompt=ONL_TO_WORKFLOW_PROMPT)
    agent = Agent("onl_to_workflow_agent").with_reasoning_llm(onl_to_workflow_resource)
    result = agent.ask(onl)
    workflow_yaml = result['result']['content']
    print(f"\nRESULT: \n{workflow_yaml}")

    workflow = WorkflowFactory.from_yaml(workflow_yaml)
    agent = Agent("workflow_agent")
    result = agent.run(workflow)
    print(f"\nRESULT: \n{result}")

def run_unl_to_workflow_in_one_agent(unl: str, onl: str):
    print("\n\n==================== Run workflow =====================")
    agent = Agent("workflow_agent")
    workflow = WorkflowFactory.create_minimal_workflow(workflow)
    result = agent.run(workflow)
    print(f"\nRESULT: \n{result}")


    """Two-step summarize-explain using workflow-is-plan strategy."""
    print("\n\n==================== Translate ONL to workflow =====================")
    workflow = WorkflowFactory.create_sequential_workflow(
        objective="Translate the following unstructured natural language into a workflow",
        commands=[
            UNL_TO_ONL_PROMPT.format(unl=unl),
            ONL_TO_WORKFLOW_PROMPT.format(onl=onl)
        ]
    )
    return agent.run(workflow)

def build_yaml_data(workflow_yaml: str) -> dict:
    """Convert workflow YAML string to dictionary compatible with WorkflowFactory.from_yaml().
    Only extracts leaf nodes (steps) to create a sequential workflow.
    
    Args:
        workflow_yaml (str): YAML content as string containing workflow steps
                           in format:
                           workflow-name:
                             process-name:
                                 - "Step 1"
                                 - "Step 2"
        
    Returns:
        dict: Workflow data with nodes and edges in the format:
        {
            'name': 'workflow_name',
            'description': 'workflow description',
            'nodes': [{id, type, description, metadata}],
            'edges': [{source, target, metadata}]
        }
    """
    if not workflow_yaml or not workflow_yaml.strip():
        raise ValueError("Empty workflow YAML")
        
    raw_data = yaml.safe_load(workflow_yaml)
    if not raw_data or not isinstance(raw_data, dict):
        raise ValueError("Invalid workflow YAML structure")
    
    # Get the workflow name (first key in the YAML)
    try:
        workflow_name = next(iter(raw_data))
        processes = raw_data[workflow_name]
    except (StopIteration, KeyError):
        raise ValueError("Invalid workflow YAML structure")
    
    # Create nodes list starting with START
    nodes = [
        {"id": "START", "type": "START", "description": "Begin workflow"}
    ]
    
    # Extract all steps sequentially
    step_counter = 1
    for process_name, steps in processes.items():
        if isinstance(steps, list):
            for step in steps:
                nodes.append({
                    "id": f"STEP_{step_counter}",
                    "type": "TASK",
                    "description": str(step),
                    "metadata": {"process": process_name}
                })
                step_counter += 1
    
    if len(nodes) == 1:  # Only START node exists
        raise ValueError("No valid steps found in workflow")
    
    # Add END node
    nodes.append({"id": "END", "type": "END", "description": "End workflow"})
    
    # Create sequential edges
    edges = []
    for i in range(len(nodes) - 1):
        edges.append({
            "source": nodes[i]["id"],
            "target": nodes[i + 1]["id"]
        })
    
    return {
        "name": workflow_name,
        "objective": f"Sequential workflow for {workflow_name}",
        "nodes": nodes,
        "edges": edges
    }


if __name__ == "__main__":
    # DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG, log_data=True)
    unl = """
        It is mostly correct. I just had minor adjustment.
        alarm is raised by an statistical measurement and its upper and lower bounds of out of controlled. The measurements in This alarm usually tee common/important parts which easily indicate (and lead to) a significant issue.
        charts: only 2 types of charts. T-chat or time based charts are the raw data from sensors. The sensor data is the continuous measurement on a particular equipment + chamber (one equipment has multiple chambers). Common sensor name: CH3 RF Vpp where CH3 is chamber id. U chart is unit based measurement. A windowed statistical measurement such as MEAN, RANGE, STD, … will be performed in each unit (wafer) throughout the corresponding T-Chart. Each data point is a wafer based measurement, called INDICATOR. For example, MEAN(W1(W0(CH3 RF Vpp))) is indicator.
        Anomaly detection kernel is performed on each sensor/indicator to see any possible abnormality. In this PoC, includes (but not limited to) DROP, SPIKE, FLUCTUATED, LEVEL_SHIFTED. The interpretation of these abnormal patterns depend on physical meaning and expertise.
        other knowledge include maintenance records, part/component lifetime records, shift-handover records.
        Maintenance records contain records for each maintenance, include datetime, equipment, chamber, and related sensors/indicators.
        Part/component lifetime records is the records showing the lifetime for components from first time installed up to current check time. There are an threshold to indicate OLD / (potentially) DEGRADED
        Shift handover may contain notes, images, photo from the real environment that process engineer PE takes notes from their work and transfer to other PE to monitor or further diagnosis.
        If the PE can not identify the root cause and recover the equipment operations, it needs to be shut down and sent to equipment engineers for further diagnosis.
        Besides, documents may include SOP, TROUBLESHOOTING GUIDES, SENSORS DESCRIPTION, etc.
    """

    run_unl_to_workflow_two_agents_with_reasoning_llm(unl)
    # test_build_yaml_data()