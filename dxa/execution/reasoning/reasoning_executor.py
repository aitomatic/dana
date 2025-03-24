"""Reasoning executor implementation."""

import logging
from typing import List, Optional, Dict, Any

from ..executor import Executor
from ..execution_context import ExecutionContext
from ..execution_graph import ExecutionGraph
from ..execution_types import (
    ExecutionNode, 
    ExecutionSignal, 
    Objective, 
    ExecutionNodeStatus,
    ExecutionSignalType,
)
from ...common.graph import NodeType
from .reasoning_strategy import ReasoningStrategy
from .reasoning import Reasoning

class ReasoningExecutor(Executor[ReasoningStrategy]):
    """Executes reasoning tasks using LLM-based reasoning.
    
    The ReasoningExecutor is responsible for executing reasoning tasks,
    which represent low-level execution steps. It uses LLM-based reasoning
    to perform the actual work.
    """
    
    @property
    def layer(self) -> str:
        """Get the execution layer name."""
        return "reasoning"
    
    @property
    def strategy_class(self) -> type[ReasoningStrategy]:
        """Get the strategy class for this executor."""
        return ReasoningStrategy
    
    @property
    def default_strategy(self) -> ReasoningStrategy:
        """Get the default strategy for this executor."""
        return ReasoningStrategy.DEFAULT
    
    def __init__(
        self, 
        strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT
    ):
        """Initialize reasoning executor.
        
        Args:
            strategy: Reasoning strategy
        """
        super().__init__(depth=2)
        self.strategy = strategy
        self.logger = logging.getLogger(f"dxa.execution.{self.layer}")
        # self.config = ReasoningConfig()
    
    async def execute_node(
        self,
        node: ExecutionNode, 
        context: ExecutionContext,
        prev_signals: Optional[List[ExecutionSignal]] = None,
        upper_signals: Optional[List[ExecutionSignal]] = None,
        lower_signals: Optional[List[ExecutionSignal]] = None
    ) -> List[ExecutionSignal]:
        """Execute a single node in the reasoning layer.
        
        This method handles the execution of a reasoning node by:
        1. Updating the node status
        2. Executing the reasoning task
        3. Processing the results
        
        Args:
            node: Node to execute
            context: Execution context
            prev_signals: Signals from previous nodes
            upper_signals: Signals from upper execution layer
            lower_signals: Signals from lower execution layer
            
        Returns:
            List of execution signals resulting from the node execution
        """
        self.logger.info(f"Executing reasoning node: {node.node_id}")
        
        try:
            # Skip START and END nodes
            if node.node_type in [NodeType.START, NodeType.END]:
                return []
            
            # Update node status to in progress
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.IN_PROGRESS)
            
            # Get the instruction from the node metadata
            instruction = node.metadata.get("instruction", "")
            if not instruction and node.metadata.get("description"):
                instruction = node.metadata.get("description", "")
            
            # If no instruction, use the node ID
            if not instruction:
                instruction = f"Execute task {node.node_id}"
            
            # Get the objective from the graph
            objective = None
            if self.graph and hasattr(self.graph, "objective"):
                objective = self.graph.objective
            
            # Execute the reasoning task
            result = await self._execute_reasoning_task(
                node=node,
                context=context,
                instruction=instruction,
                prev_steps=None,  # TODO: really? We don't have previous steps yet
                objective=objective,
                max_tokens=1000
            )
            
            # Update node status to completed
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.COMPLETED)
            
            # Create result signal
            signal = ExecutionSignal(
                type=ExecutionSignalType.DATA_RESULT,
                content={
                    "node": node.node_id,
                    "result": result
                }
            )
            
            return [signal]
            
        except Exception as e:
            self.logger.error(f"Error executing node {node.node_id}: {str(e)}")
            
            # Update node status to error
            if self.graph:
                self.graph.update_node_status(node.node_id, ExecutionNodeStatus.FAILED)
            
            # Create error signal
            return [self._create_error_signal(node.node_id, str(e))]
    
    def _build_combined_prompt(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        instruction: str,
        prev_steps: Optional[List[str]] = None,
        objective: Optional[Objective] = None
    ) -> str:
        """Build a combined prompt from all layers' context.
        
        Args:
            node: Node to execute
            context: Execution context
            instruction: Base instruction
            prev_steps: Previous steps
            objective: Execution objective
            
        Returns:
            Combined prompt string
        """
        # Get the base prompt template
        prompt_ref = node.metadata.get("prompt", instruction)
        self.logger.debug(f"Prompt reference: {prompt_ref}")
        
        prompt_template = self.config.get_prompt(prompt_ref)
        if not prompt_template:
            prompt_template = instruction
        self.logger.debug(f"Prompt template: {prompt_template}")

        # Build workflow context
        assert context.current_workflow is not None, "Current workflow is required"
        workflow_node = context.current_workflow.get_current_node()
        assert workflow_node is not None, "Current workflow node is required"
        self.logger.debug(f"Workflow node: {workflow_node}")
        workflow_prompt = workflow_node.metadata.get("prompt", "")
        self.logger.debug(f"Workflow prompt: {workflow_prompt}")
        workflow_context = workflow_node.metadata.get("workflow_context", {})
        self.logger.debug(f"Workflow context: {workflow_context}")
        workflow_previous_outputs = workflow_context.get("previous_outputs", {})
        self.logger.debug(f"Workflow previous outputs: {workflow_previous_outputs}")

        # Build planning context
        assert context.current_plan is not None, "Current plan is required"
        plan_node = context.current_plan.get_current_node()
        assert plan_node is not None, "Current plan node is required"
        self.logger.debug(f"Plan node: {plan_node}")
        plan_prompt = plan_node.metadata.get("prompt", "")
        self.logger.debug(f"Plan prompt: {plan_prompt}")
        plan_context = plan_node.metadata.get("plan_context", {})
        self.logger.debug(f"Plan context: {plan_context}")
        plan_previous_outputs = plan_context.get("previous_outputs", {})
        self.logger.debug(f"Plan previous outputs: {plan_previous_outputs}")

        # Format the prompt template with objective and previous outputs
        format_values = {}
        if objective:
            if isinstance(objective, Objective):
                assert objective is not None, "Objective current is required"
                str_objective = objective.current
            else:
                str_objective = str(objective)
            objective_text = getattr(objective, "description", str_objective)
            format_values["objective"] = objective_text
            
        # Add previous outputs to format values
        for node_id, output in workflow_previous_outputs.items():
            # Use node_id as given, without converting to uppercase
            format_values[node_id] = output
            
        for node_id, output in plan_previous_outputs.items():
            # Use node_id as given, without converting to uppercase
            format_values[node_id] = output
            
        self.logger.debug(f"Format values: {format_values}")
        
        try:
            prompt_template = prompt_template.format(**format_values)
            self.logger.debug(f"Formatted prompt template: {prompt_template}")
        except (KeyError, IndexError) as e:
            self.logger.warning(f"Error formatting prompt template: {e}")
            # If there are other format placeholders, append the values instead
            if objective:
                prompt_template = f"{prompt_template}\n\nObjective:\n{objective_text}"
            for node_id, output in workflow_previous_outputs.items():
                prompt_template = f"{prompt_template}\n\n{node_id} Output:\n{output}"
            for node_id, output in plan_previous_outputs.items():
                prompt_template = f"{prompt_template}\n\n{node_id} Output:\n{output}"

        # Build the combined prompt
        combined_prompt = f"""
Workflow Context:
Current Node: {node.node_id}
State: {node.status.name if hasattr(node, 'status') else 'UNKNOWN'}
Previous Outputs: {workflow_context.get('previous_outputs', {})}

Planning Context:
Node: {plan_context.get('node_id', 'UNKNOWN')}
Requirements: {plan_context.get('requirements', [])}
Constraints: {plan_context.get('constraints', [])}

Reasoning Task:
{prompt_template}
"""
        self.logger.debug(f"Combined prompt: {combined_prompt}")

        # Add previous steps if available
        if prev_steps and len(prev_steps) > 0:
            steps_text = "\n".join([f"- {step}" for step in prev_steps])
            combined_prompt = f"{combined_prompt}\n\nPrevious steps:\n{steps_text}"

        return combined_prompt

    async def _execute_reasoning_task(
        self,
        node: ExecutionNode,
        context: ExecutionContext,
        instruction: str,
        prev_steps: Optional[List[str]] = None,
        objective: Optional[Objective] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Execute a reasoning task using LLM.
        
        Args:
            node: Node to execute
            context: Execution context
            instruction: Instruction for the reasoning task
            prev_steps: Previous steps in the reasoning process
            objective: Objective of the reasoning task
            max_tokens: Maximum tokens for the response
            
        Returns:
            Result of the reasoning task
        """
        self.logger.info(f"Executing reasoning task: {instruction}")
        
        # Use the reasoning_llm from context to generate a response
        if context and context.reasoning_llm:
            try:
                # Build the combined prompt
                prompt = self._build_combined_prompt(
                    node=node,
                    context=context,
                    instruction=instruction,
                    prev_steps=prev_steps,
                    objective=objective
                )
                
                # Query the LLM
                response = await context.reasoning_llm.query({
                    "prompt": prompt,
                    "system_prompt": (
                        "You are a helpful AI assistant executing a multi-layer reasoning process, "
                        "comprising Workflow, Planning, and Reasoning layers. Each layer is modeled as a "
                        "graph or flow chart, with nodes representing tasks or conditions. Each node "
                        "from Workflow maps to a graph in the Planning layer, and so on. Fundamentally, "
                        "Workflow represents a human workflow, Planning represents a dynamic plan to accomplish "
                        "each task in the Workflow, while Reasoning represents the thinking or deliberation "
                        "involved in accomplishing each task in the Plan. "
                        "Consider the workflow and planning context carefully when formulating your response."
                    ),
                    "parameters": {
                        "temperature": 0.7,
                        "max_tokens": max_tokens or 1000
                    }
                })
                
                # Extract and return the content
                if response and "content" in response:
                    return response["content"]
                else:
                    self.logger.error("LLM response did not contain content")
                    return "Error: LLM response did not contain content"
                    
            except Exception as e:
                self.logger.error(f"Error executing reasoning task: {str(e)}")
                return f"Error executing reasoning task: {str(e)}"
        else:
            # Fallback to placeholder if no LLM is available
            self.logger.warning("No reasoning LLM available in context, using placeholder")
            return f"Reasoning result for node {node.node_id} using strategy {self.strategy.name}"
    
    def _get_graph_class(self):
        """Get the appropriate graph class for this executor.
        
        Returns:
            Reasoning graph class
        """
        # Import here to avoid circular import
        from .reasoning import Reasoning
        return Reasoning

    def _process_previous_signals(self, signals: List[ExecutionSignal]) -> Dict[str, Any]:
        """Process previous signals to extract outputs.
        
        Args:
            signals: List of previous execution signals
            
        Returns:
            Dictionary mapping node IDs to their outputs
        """
        return {
            str(signal.content.get("node")): signal.content.get("output")
            for signal in signals
            if signal.type == "output"
        }
    
    def _build_layer_context(
        self,
        node: ExecutionNode,
        prev_signals: Optional[List[ExecutionSignal]] = None
    ) -> Dict[str, Any]:
        """Build reasoning context for node execution.
        
        Args:
            node: Node to execute
            prev_signals: Signals from previous node execution
            
        Returns:
            Reasoning context dictionary
        """
        # Get base context from parent
        context = super()._build_layer_context(node, prev_signals)
        
        # Add reasoning-specific context
        if prev_signals:
            context["previous_outputs"] = self._process_previous_signals(prev_signals)
        
        return context
    
    def create_graph_from_node(
        self,
        upper_node: ExecutionNode,
        upper_graph: ExecutionGraph,
        objective: Optional[Objective] = None,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraph:
        """Create a reasoning graph from a node in the plan.
        
        Args:
            upper_node: Node from the plan layer
            upper_graph: Graph from the plan layer
            objective: Execution objective
            context: Execution context
            
        Returns:
            Reasoning graph
        """
        # If we already have a graph, return it
        if self.graph is not None:
            return self.graph
        
        # Get the plan graph
        plan = upper_graph
        if not plan:
            # Create a minimal reasoning if no plan is available
            return Reasoning(
                objective=objective or Objective(f"Execute reasoning for {upper_node.node_id}"),
                name=f"reasoning_for_{upper_node.node_id}"
            )
        
        # Create a reasoning based on the strategy
        if self.strategy == ReasoningStrategy.DEFAULT:
            # Direct execution - create a minimal reasoning
            return self._create_direct_reasoning(plan, objective, upper_node)
        elif self.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            return self._create_chain_of_thought_reasoning(plan, objective, upper_node)
        elif self.strategy == ReasoningStrategy.TREE_OF_THOUGHT:
            return self._create_tree_of_thought_reasoning(plan, objective, upper_node)
        elif self.strategy == ReasoningStrategy.REFLECTION:
            return self._create_reflection_reasoning(plan, objective, upper_node)
        else:
            # Default to direct reasoning
            return self._create_direct_reasoning(plan, objective, upper_node)
    
    def _create_direct_reasoning(
        self, 
        plan: ExecutionGraph, 
        objective: Optional[Objective] = None,
        upper_node: Optional[ExecutionNode] = None
    ) -> Reasoning:
        """Create a direct reasoning from a plan.
        
        A direct reasoning follows the plan structure directly.
        
        Args:
            plan: Plan graph
            objective: Execution objective
            upper_node: Node from the plan layer to create reasoning for
            
        Returns:
            Direct reasoning
        """
        # Create a reasoning that directly follows the plan
        node_id = upper_node.node_id if upper_node else "plan"
        reasoning = Reasoning(
            objective=objective or plan.objective,
            name=f"direct_reasoning_for_{node_id}"
        )
        
        # Create nodes based on plan structure
        for node in plan.nodes.values():
            # Create a copy of the node's metadata
            metadata = node.metadata.copy() if node.metadata else {}
            
            # Ensure prompt is passed through
            if "prompt" in metadata:
                metadata["prompt"] = metadata["prompt"]
            
            reasoning_node = ExecutionNode(
                node_id=node.node_id,
                node_type=node.node_type,
                description=node.description,
                metadata=metadata
            )
            
            # If this is the upper node, add additional metadata
            if upper_node and node.node_id == upper_node.node_id:
                reasoning_node.metadata["is_upper_node"] = True
                reasoning_node.metadata["upper_node_id"] = upper_node.node_id
            
            reasoning.add_node(reasoning_node)
        
        # Create edges based on plan structure
        for edge in plan.edges:
            reasoning.add_edge_between(edge.source, edge.target)
        
        return reasoning
    
    def _create_chain_of_thought_reasoning(
        self, 
        plan: ExecutionGraph, 
        objective: Optional[Objective] = None,
        upper_node: Optional[ExecutionNode] = None
    ) -> Reasoning:
        """Create a chain of thought reasoning from a plan.
        
        Args:
            plan: Plan graph
            objective: Execution objective
            upper_node: Node from the plan layer to create reasoning for
            
        Returns:
            Chain of thought reasoning
        """
        # For now, just create a direct reasoning
        # In the future, this would create a step-by-step reasoning
        return self._create_direct_reasoning(plan, objective, upper_node)
    
    def _create_tree_of_thought_reasoning(
        self, 
        plan: ExecutionGraph, 
        objective: Optional[Objective] = None,
        upper_node: Optional[ExecutionNode] = None
    ) -> Reasoning:
        """Create a tree of thought reasoning from a plan.
        
        Args:
            plan: Plan graph
            objective: Execution objective
            upper_node: Node from the plan layer to create reasoning for
            
        Returns:
            Tree of thought reasoning
        """
        # For now, just create a direct reasoning
        # In the future, this would create a branching reasoning
        return self._create_direct_reasoning(plan, objective, upper_node)
    
    def _create_reflection_reasoning(
        self, 
        plan: ExecutionGraph, 
        objective: Optional[Objective] = None,
        upper_node: Optional[ExecutionNode] = None
    ) -> Reasoning:
        """Create a reflection reasoning from a plan.
        
        Args:
            plan: Plan graph
            objective: Execution objective
            upper_node: Node from the plan layer to create reasoning for
            
        Returns:
            Reflection reasoning
        """
        # For now, just create a direct reasoning
        # In the future, this would create a self-critique reasoning
        return self._create_direct_reasoning(plan, objective, upper_node)
        