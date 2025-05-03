"""Reasoning executor for OpenDXA."""

import logging
from typing import List, Optional
from opendxa.base.execution import RuntimeContext
from opendxa.base.execution.execution_types import (
    ExecutionNode,
    ExecutionSignal,
    ExecutionStatus,
    ExecutionEdge,
)
from opendxa.base.execution.base_executor import BaseExecutor
from opendxa.base.resource import LLMResource
from opendxa.execution.reasoning.reasoning import Reasoning
from opendxa.execution.reasoning.reasoning_factory import ReasoningFactory
from opendxa.execution.reasoning.reasoning_strategy import ReasoningStrategy
from opendxa.base.execution.execution_graph import ExecutionGraph
from opendxa.common.graph import NodeType
from opendxa.common.mixins.loggable import Loggable
from opendxa.common.types import BaseRequest


log = logging.getLogger(__name__)

class Reasoner(BaseExecutor[Reasoning], Loggable):
    """Reasoning executor for OpenDXA.
    
    Responsible for executing fine-grained reasoning tasks, typically delegated
    by a Planner. It often interacts with an LLM to perform the reasoning
    based on a specified strategy and contextual information derived from the
    execution hierarchy.

    Initialization (`__init__`):
        - strategy (ReasoningStrategy): Defines the method of reasoning (e.g., 
          Chain-of-Thought). Used for constructing LLM prompts.
        - llm (LLMResource): The language model instance used for reasoning.
        - factory (ReasoningFactory): Used by BaseExecutor for graph creation.

    Execution (`execute_node_core`):
        Receives:
        - node (ExecutionNode): The specific node within the Reasoner's own 
          dynamically created graph. `node.objective` defines the immediate 
          reasoning task, derived from the delegating Planner node's objective.
        - context (RuntimeContext): Passed down the execution chain. Used to access 
          shared state via the StateManager (`context.get`/`set`) and is passed 
          to LLM interaction methods.
        Core Logic:
        - Primarily calls `_execute_with_llm` to perform the task.

    LLM Interaction (`_execute_with_llm`, `_build_user/system_messages`):
        - Builds prompts using information from:
            - The current `node` (objective, description). 
            - The specified `self._strategy`.
            - The execution hierarchy reconstructed by traversing `self.upper_executor` links 
              (accessing `upper_executor.graph.objective` at each level).
            - Potentially other state retrieved via `context.get()`.
        - Queries the `self._llm` resource.
        - Returns the result in an ExecutionSignal.

    Hierarchy Context:
        - Relies on the `self.upper_executor: BaseExecutor` link (set temporarily by the 
          calling Planner) to traverse *up* the execution chain.
        - Accesses `executor.graph.objective` at each level during traversal to 
          understand the broader goals.
        - The Reasoner's own graph objective (`self.graph.objective`) reflects the 
          specific task delegated by the immediate parent node.
    """

    _factory_class = ReasoningFactory

    def __init__(
        self,
        strategy: ReasoningStrategy,
        llm: Optional[LLMResource] = None,
        factory: Optional[ReasoningFactory] = None
    ):
        """Initialize the reasoner.
        
        Args:
            strategy: The reasoning strategy
            llm: Optional LLM resource
            factory: Optional factory for creating graphs
        """
        super().__init__(factory=factory)
        self._strategy = strategy
        self._llm = llm

    async def execute_node_core(
        self,
        node: ExecutionNode,
        context: RuntimeContext
    ) -> ExecutionSignal:
        """Execute the core reasoning node logic."""
        # Removed: current_node_id = context.get('execution.current_node_id')
        # The 'node' parameter passed in *is* the current node.
        
        # Optional: Log context if desired. We can get parent info via upper_executor
        self.info("\nExecuting Reasoning Node:")
        self.info("========================")
        self.info(f"  Node ID: {node.id}")
        self.info(f"  Node Objective: {node.objective}")
        if self.upper_executor and self.upper_executor.current_node:
            upper_node = self.upper_executor.current_node
            self.info(f"  Called by Planner Node: {upper_node.id} ({upper_node.objective})")
        if self.upper_executor and self.upper_executor.graph:
            upper_graph = self.upper_executor.graph
            self.info(f"  Part of Plan Graph: {upper_graph.name or upper_graph.id} ({upper_graph.objective})")
        
        # Execute with LLM
        # This is the main task of the Reasoner node
        self.info(f"Passing node {node.id} to LLM execution.")
        return await self._execute_with_llm(node, context)
        
        # Removed: Check for current_node_id and error branch, 
        # as execute_node_core is always called with a valid node.

    async def _execute_with_llm(
        self,
        node: ExecutionNode,
        context: RuntimeContext
    ) -> ExecutionSignal:
        """Execute node with LLM interaction.
        
        Args:
            node: The node to execute
            context: The runtime context
            
        Returns:
            Execution signal with result
        """
        if not self._llm:
            self.error("Reasoner: No LLM configured for execution.")
            return ExecutionSignal(
                status=ExecutionStatus.FAILED,
                content="No LLM configured"
            )

        # Build messages
        user_messages = self._build_user_messages(node, context)
        system_messages = self._build_system_messages(node, context)
        
        # Create request
        # TODO: Define a proper request structure if BaseRequest is too generic
        request = BaseRequest(arguments={
            "user_messages": user_messages,
            "system_messages": system_messages,
        })
        
        # Query LLM
        self.debug(f"Querying LLM for node {node.node_id}...")
        response = await self._llm.query(request)
        self.debug(f"LLM response received for node {node.node_id}.")
        
        # Return signal
        return ExecutionSignal(
            status=ExecutionStatus.COMPLETED if response.success else ExecutionStatus.FAILED,
            content=response.content
        )

    def _build_user_messages(self, node: ExecutionNode, context: RuntimeContext) -> List[str]:
        """Build user messages for reasoning using executor traversal."""
        user_messages = []
        user_messages.append("EXECUTION HIERARCHY (Parent Objectives):")
        
        hierarchy = []
        executor: Optional[BaseExecutor] = self.upper_executor  # Start traversal from parent
        while executor:
            if executor.graph and executor.graph.objective:
                # Prepend to get top-down order
                hierarchy.insert(0, {
                    'objective': executor.graph.objective,
                    # Could add executor type later if needed: 'type': type(executor).__name__
                })
            # Traverse up the chain
            executor = executor.upper_executor

        if not hierarchy:
            user_messages.append("- Executing at the top level (no parent planners).")
        else:
            for i, frame in enumerate(hierarchy):
                graph_objective = frame.get('objective')
                obj_str = str(graph_objective.current) if hasattr(graph_objective, 'current') else str(graph_objective)
                # executor_type = frame.get('type', 'Unknown') # If type added above
                user_messages.append(f"- Level {i+1}: {obj_str}") 

        user_messages.append("\nCURRENT REASONING TASK:")
        # The current node's objective defines the immediate task
        node_objective_str = str(node.objective.current) if hasattr(node.objective, 'current') else str(node.objective)
        user_messages.append(f"- Objective: {node_objective_str}")
        user_messages.append(f"- Node ID: {node.id}")
        user_messages.append(f"- Description: {node.description}")

        return user_messages

    def _build_system_messages(self, node: ExecutionNode, context: RuntimeContext) -> List[str]:
        """Build system messages for reasoning."""
        system_messages = []
        system_messages.extend([
            "You are executing a reasoning task. Provide clear, logical analysis and reasoning.",
            "You are operating within a two-layer execution hierarchy: Plan -> Reasoning.",
            "The Plan layer is typically generated dynamically to accomplish the objective",
            "The Reasoning layer is typically a choice of several fundamental strategies, e.g., "
            "chain-of-thought, tree-of-thought, reflection, OODA loop, etc.",
            "",
            "You are currently in the Reasoning layer. Execute the reasoning task while keeping in mind:",
            " 1. The specific plan that this reasoning task is part of",
            " 2. The immediate reasoning task requirements",
            "",
        ])

        self.debug(f"Reasoning Strategy: {self._strategy}")
        system_messages.extend(self._build_reasoning_directives(self._strategy))

        # Tell the LLM to call our final_result() function if the task is complete
        system_messages.extend([
            "",
            "When the task is complete, provide your response in JSON format with the following structure:",
            "  {",
            "    'content': The content of the result",
            "    'status': The status of the result, @enum: success, error, partial",
            "    'metadata': Optional metadata about the result",
            "    'error': Optional error message if status is error",
            "  }",
            "If the task is not complete, continue with your analysis.",
        ])

        return system_messages

    def _build_reasoning_directives(self, strategy: ReasoningStrategy) -> List[str]:
        """Build the reasoning strategy section of the prompt."""
        result = []
        
        if strategy == ReasoningStrategy.TREE_OF_THOUGHT:
            result.extend([
                "Reasoning: Following tree-of-thought strategy:",
                "  1. Generate multiple possible solutions",
                "  2. Evaluate each solution branch",
                "  3. Select the most promising branch",
                "  4. Refine the selected solution"
            ])
        elif strategy == ReasoningStrategy.REFLECTION:
            result.extend([
                "Reasoning: Following reflection strategy:",
                "  1. Analyze the current situation",
                "  2. Identify potential improvements",
                "  3. Implement improvements",
                "  4. Verify effectiveness"
            ])
        elif strategy == ReasoningStrategy.OODA:
            result.extend([
                "Reasoning: Following OODA loop strategy:",
                "  1. Observe the current situation",
                "  2. Orient to the context",
                "  3. Decide on a course of action",
                "  4. Act on the decision"
            ])
        elif strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            result.extend([
                "Reasoning: Following chain-of-thought strategy:",
                "  1. Break down the problem into steps",
                "  2. Solve each step sequentially",
                "  3. Combine results to reach conclusion"
            ])
        else:
            result.extend([
                "Reasoning: Following default strategy:",
                "  1. Analyze the problem",
                "  2. Consider possible approaches",
                "  3. Select and implement solution"
            ])
            
        return result

    def create_graph_from_upper_node(
        self, 
        node: ExecutionNode, 
        upper_graph: Optional[ExecutionGraph] = None
    ) -> Optional[Reasoning]:
        """Create a Reasoning graph based on an upper-level node."""
        self.info(f"Creating Reasoning graph for upper node: {node.node_id}")
        
        # Create a new reasoning graph
        reasoning_graph = Reasoning(
            name=f"Reasoning for {node.node_id}",
            objective=node.objective
        )
        
        # TODO: Add logic to populate the reasoning graph based on node and strategy
        # This might involve adding specific nodes (Observe, Orient, Decide, Act for OODA)
        # or setting up the initial state for the chosen reasoning strategy.
        # For now, returning a basic graph structure.
        
        start_node = ExecutionNode(node_id="START", node_type=NodeType.START, objective="Start Reasoning")
        end_node = ExecutionNode(node_id="END", node_type=NodeType.END, objective="End Reasoning")
        reasoning_node = ExecutionNode(
             node_id=f"reasoning_{node.node_id}", 
             node_type=NodeType.TASK, 
             description=f"Perform {self._strategy.name} reasoning for {node.description}",
             objective=node.objective # Explicitly align with description
        )

        reasoning_graph.add_node(start_node)
        reasoning_graph.add_node(reasoning_node)
        reasoning_graph.add_node(end_node)
        
        reasoning_graph.add_edge(ExecutionEdge(source=start_node.node_id, target=reasoning_node.node_id))
        reasoning_graph.add_edge(ExecutionEdge(source=reasoning_node.node_id, target=end_node.node_id))
        
        reasoning_graph.set_start_node_id(start_node.node_id)
        reasoning_graph.set_end_node_id(end_node.node_id)

        return reasoning_graph
