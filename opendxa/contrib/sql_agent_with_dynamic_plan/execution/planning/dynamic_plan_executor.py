"""
Dynamic Plan Executor

This is a customized Planner that can create a dynamic plan graph for a given node.

"""
from typing import Any, Dict, List, Optional, cast
from opendxa.execution.planning import Planner
from opendxa.execution.planning import Plan
from opendxa.base.execution.runtime_context import RuntimeContext
from opendxa.base.execution.base_executor import BaseExecutor, ExecutionError
from opendxa.base.execution.execution_types import ExecutionNode, ExecutionSignal, NodeType, ExecutionStatus


class DynamicPlanExecutor(Planner):
    """Dynamic Plan Executor."""

    async def execute(
        self,
        graph: Plan,
        context: RuntimeContext
    ) -> List[ExecutionSignal]:
        """Execute a graph using common execution logic."""
        # Set current graph
        self._set_graph(graph)
        
        # Set graph in context
        self._set_graph_in_context(graph, context)
        
        # Log execution start
        self._log_execution_start(graph)
        
        # Create cursor starting at START node
        cursor = graph.start_cursor()
        graph.cursor = cursor
        
        # Execute nodes in sequence
        signals = []
        
        # Traverse graph using cursor
        while True:
            node = cursor.next()
            if node is None:
                break

            if node.node_type in (NodeType.START, NodeType.END):  # Skip start and end nodes
                continue

            if node.objective:
                node.description = node.objective.current = self._fill_objective_variables(node, graph, context)
                
            # Execute current node
            node_signals = await self.execute_node(
                cast(ExecutionNode, node),
                context
            )
            signals.extend(node_signals)
            context.context_manager.set(f"execution.{node.node_id}", self._parse_node_signals(node_signals))
            # context.global_context[node.node_id] = self._parse_node_signals(node_signals)
        
        return signals
    
    def _parse_node_signals(self, node_signals: List[ExecutionSignal]) -> list[str]:
        """Parse node signals and return a dictionary of results."""
        results = []
        for signal in node_signals:
            for choice in signal.content.get('choices', []):
                results.append(choice.message.content)
        return results
        
    async def _execute_node_core(self, node: ExecutionNode, context: RuntimeContext) -> List[ExecutionSignal]:
        if self.lower_executor is None:
            raise ExecutionError("No lower executor available")
        
        if not self.graph:
            raise ExecutionError("No current graph available")
        
        # if "DYNAMIC" in node.node_id:
        #     lower_graph = await self._create_dynamic_plan_graph(node, context)
        # else:
        lower_graph = self.lower_executor.create_graph_from_upper_node(node, self.graph)
            
        if not lower_graph:
            raise ExecutionError("Failed to create graph for lower layer")
        
        return await self.lower_executor.execute(lower_graph, context)

    def _find_variable_in_text(self, text: str):
        """Find all variables in the text."""
        import re
        return re.findall(r'({{\s*(\w+)\s*}})', text)

    def _fill_objective_variables(self, node: ExecutionNode, graph: Plan, context: RuntimeContext) -> str:
        """Fill the objective variables in the text."""
        current_objective = node.objective.current if node.objective else None
        if current_objective is None:
            raise ExecutionError("No current objective available")
        current_objective_variables = self._find_variable_in_text(current_objective)
        for variable_text, variable_name in current_objective_variables:
            if variable_name == "objective":
                current_objective = current_objective.replace(variable_text, graph.objective.current)
            elif variable_name in context.global_context:
                current_objective = current_objective.replace(variable_text, str(context.global_context[variable_name]))
        return current_objective

    async def _create_dynamic_plan_graph(self, node: ExecutionNode, context: RuntimeContext) -> Plan:
        """Create a dynamic plan graph for a given node.""" 
        # TODO : Implement this later
        current_objective = node.objective.current if node.objective else None
        if current_objective is None:
            raise ExecutionError("No current objective available")
        current_objective_variables = self._find_variable_in_text(current_objective)
        print(current_objective_variables)
        return None