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

    def pretty_print(self) -> str:
        """Generate a human-readable representation of the workflow.
        
        Returns:
            A formatted string representation of the workflow
        """
        output = []
        
        # Basic workflow information
        output.append(f"Workflow Name: {self.name}")
        if self.objective:
            output.append(f"Objective: {self.objective.original}")
        output.append(f"Agent Role: {self.metadata.get('role', 'No role specified')}")
        output.append(f"Number of nodes: {len(self.nodes)}")
        output.append(f"Number of edges: {len(self.edges)}")
        
        # Print detailed node information
        output.append("\nWorkflow Nodes:")
        for node_id, node in self.nodes.items():
            output.append(f"\nNode ID: {node_id}")
            output.append(f"  Type: {node.node_type.name}")
            
            # Print node description (truncated if too long)
            if len(node.description) > 50:
                output.append(f"  Description: {node.description[:50]}...")
            else:
                output.append(f"  Description: {node.description}")
            
            # Print node metadata with special handling for certain fields
            if node.metadata:
                output.append("  Metadata:")
                # First print prompt for emphasis
                if 'prompt' in node.metadata:
                    prompt = node.get_prompt()
                    output.append(f"    prompt: {prompt}")
                
                # Then print planning and reasoning
                if 'planning' in node.metadata:
                    output.append(f"    planning: {node.metadata['planning']}")
                if 'reasoning' in node.metadata:
                    output.append(f"    reasoning: {node.metadata['reasoning']}")
                
                # Then print any other metadata
                for key, value in node.metadata.items():
                    if key not in ['planning', 'reasoning', 'prompt']:  # Skip already printed items
                        if isinstance(value, str) and len(value) > 50:
                            output.append(f"    {key}: {value[:50]}...")
                        else:
                            output.append(f"    {key}: {value}")
        
        # Print edge details
        output.append("\nWorkflow Edges:")
        for edge in self.edges:
            output.append(f"  {edge.source} -> {edge.target}")
            if edge.metadata:
                output.append(f"    Conditions: {edge.metadata.get('condition', 'None')}")
        
        return "\n".join(output)