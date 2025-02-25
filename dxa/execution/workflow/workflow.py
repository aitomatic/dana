"""Workflow implementation for high-level process."""

from typing import List, Dict, Any, Optional, Union
from dxa.agent.resource.llm_resource import LLMResource

from ..execution_graph import ExecutionGraph
from ..execution_types import ExecutionSignal, Objective

class Workflow(ExecutionGraph):
    """High-level business process (WHY layer)."""

    def __init__(self, objective: Optional[Union[str, Objective]] = None, name: Optional[str] = None):
        super().__init__(objective, name=name)
        self._cursor = None
        self._objective = objective if isinstance(objective, Objective) else Objective(objective)

    def update_from_signal(self, signal: ExecutionSignal) -> None:
        """Update workflow based on signal."""
        pass  # For simple QA, no updates needed

    def process_signal(self, signal: ExecutionSignal) -> List[ExecutionSignal]:
        """Process signal and generate new signals."""
        return []  # For simple QA, no new signals needed

    @classmethod
    async def natural_language_to_yaml(cls, unl: str) -> str:
        """Convert natural language to YAML format.
        
        Args:
            unl: Unstructured natural language text
            
        Returns:
            str: YAML formatted workflow
        """
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
            4. Always start the steps with a verb.
            5. The output should be a valid YAML content only, no other text or comments. And dont put the content in ```yaml``` tags.

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

        unl_to_onl_resource = LLMResource(name="UNL to ONL Resource")
        result = await unl_to_onl_resource.query({"prompt": UNL_TO_ONL_PROMPT.format(unl=unl)})
        onl = result['content']

        onl_to_workflow_resource = LLMResource(name="ONL to Workflow Resource")
        result = await onl_to_workflow_resource.query({"prompt": ONL_TO_WORKFLOW_PROMPT.format(onl=onl)})
        workflow_yaml = result['content']

        # remove the yaml tags if exists
        workflow_yaml = workflow_yaml.replace("```yaml", "").replace("```", "")

        return workflow_yaml

    def update_cursor(self, node_id: str) -> None:
        """Update workflow cursor to specified node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in workflow")
        self._cursor = self.get_a_cursor(self.nodes[node_id])