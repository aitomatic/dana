"""Dynamic plan executor that leverages RuntimeContext for state management."""

from datetime import datetime
from typing import Any, Dict, List, cast

import yaml

from opendxa.base.execution.base_executor import ExecutionError
from opendxa.base.execution.execution_types import ExecutionNode, ExecutionSignal, ExecutionStatus, NodeType
from opendxa.base.execution.runtime_context import RuntimeContext
from opendxa.execution.planning import Plan, Planner


class DynamicPlanExecutor2(Planner):
    """Executes plans dynamically with robust state management."""

    def _load_plan_config(self, config_path: str) -> Dict[str, Any]:
        with open(config_path) as f:
            return yaml.safe_load(f)

    def _create_plan_from_config(self, config: Dict[str, Any]) -> Plan:
        nodes = []
        for node_config in config["nodes"]:
            node = ExecutionNode(
                node_id=node_config["id"],
                node_type=NodeType[node_config.get("type", "reasoning").upper()],
                next_node_id=node_config.get("next"),
                objective=node_config.get("objective", None),
            )

            if "to_llm" in node_config:
                node.to_llm = node_config["to_llm"]
            if "from_llm" in node_config:
                node.from_llm = node_config["from_llm"]
            nodes.append(node)

        plan = Plan(name=config["name"], objective=config["objective"])
        plan.nodes = nodes
        return plan

    def _replace_prompt_variables(self, prompt: str, node: ExecutionNode, context: RuntimeContext) -> str:
        def replace_variables(text: str) -> str:
            if "{{agent." in text:
                import re

                for match in re.finditer(r"{{agent\.([\w\.]+)}}", text):
                    path = match.group(1)
                    value = context.context_manager.get(path)
                    if value is not None:
                        text = text.replace(match.group(0), str(value))
            return text

        return replace_variables(prompt)

    def _store_llm_response(self, response: Dict[str, Any], node: ExecutionNode, context: RuntimeContext) -> None:
        if not hasattr(node, "from_llm"):
            return
        for key, path in node.from_llm.items():
            if key in response:
                context.context_manager.set(path, response[key])

    def _build_execution_prompt(self, node: ExecutionNode, context: RuntimeContext) -> Dict[str, Any]:
        if not hasattr(node, "to_llm"):
            raise ExecutionError(f"Node {node.node_id} missing to_llm configuration")
        prompt_content = self._replace_prompt_variables(node.to_llm, node, context)
        return {
            "messages": [
                {"role": "system", "content": "You are an AI assistant executing a plan step."},
                {"role": "user", "content": prompt_content},
            ]
        }

    def _parse_execution_response(self, response: Dict[str, Any], node: ExecutionNode, context: RuntimeContext) -> Dict[str, Any]:
        try:
            content = response["choices"][0]["message"]["content"]
            if isinstance(content, str):
                import json

                content = json.loads(content)
            self._store_llm_response(content, node, context)
            return content
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ExecutionError(f"Failed to parse execution response: {str(e)}")

    async def execute(self, graph: Plan, context: RuntimeContext) -> List[ExecutionSignal]:
        self._set_graph(graph)
        self._set_graph_in_context(graph, context)
        self._log_execution_start(graph)

        cursor = graph.start_cursor()
        graph.cursor = cursor
        signals = []

        while True:
            node = cursor.next()
            if node is None:
                break

            if node.node_type in (NodeType.START, NodeType.END):
                continue

            if node.objective:
                node.description = node.objective.current = self._fill_objective_variables(node, graph, context)

            node_signals = await self.execute_node(cast(ExecutionNode, node), context)
            signals.extend(node_signals)
            self._store_node_results(node, node_signals, context)

        return signals

    def _store_node_results(self, node: ExecutionNode, signals: List[ExecutionSignal], context: RuntimeContext) -> None:
        context.context_manager.set("execution.current_node_id", node.node_id)
        results = self._parse_node_signals(signals)
        context.context_manager.set(f"execution.node_results.{node.node_id}", results)

        history = context.context_manager.get("execution.history", [])
        history.append({"node_id": node.node_id, "timestamp": datetime.now(), "results": results})
        context.context_manager.set("execution.history", history)

    def _parse_node_signals(self, node_signals: List[ExecutionSignal]) -> List[str]:
        results = []
        for signal in node_signals:
            for choice in signal.content.get("choices", []):
                content = choice.message.content
                if isinstance(content, dict):
                    content = content.get("output", str(content))
                results.append(content)
        return results

    async def _execute_node_core(self, node: ExecutionNode, context: RuntimeContext) -> List[ExecutionSignal]:
        if self.lower_executor is None:
            raise ExecutionError("No lower executor available")

        if not self.graph:
            raise ExecutionError("No current graph available")

        lower_graph = self.lower_executor.create_graph_from_upper_node(node, self.graph)
        if not lower_graph:
            raise ExecutionError("Failed to create graph for lower layer")

        context.context_manager.set("execution.status", ExecutionStatus.RUNNING)

        try:
            signals = await self.lower_executor.execute(lower_graph, context)
            context.context_manager.set("execution.status", ExecutionStatus.COMPLETED)
            return signals

        except Exception as e:
            context.context_manager.set("execution.status", ExecutionStatus.FAILED)
            context.context_manager.set(
                "execution.last_error",
                {"timestamp": datetime.now(), "error_type": type(e).__name__, "message": str(e), "node_id": node.node_id},
            )
            raise

    def _find_variable_in_text(self, text: str) -> List[tuple[str, str]]:
        import re

        return re.findall(r"({{\s*(\w+)\s*}})", text)

    def _fill_objective_variables(self, node: ExecutionNode, graph: Plan, context: RuntimeContext) -> str:
        current_objective = node.objective.current if node.objective else None
        if current_objective is None:
            raise ExecutionError("No current objective available")

        current_objective_variables = self._find_variable_in_text(current_objective)
        for variable_text, variable_name in current_objective_variables:
            if variable_name == "objective":
                current_objective = current_objective.replace(variable_text, graph.objective.current)
            else:
                value = context.context_manager.get(f"execution.node_results.{variable_name}")
                if value is not None:
                    current_objective = current_objective.replace(variable_text, str(value))
        return current_objective

    async def _create_dynamic_plan_graph(self, node: ExecutionNode, context: RuntimeContext) -> Plan:
        current_objective = node.objective.current if node.objective else None
        if current_objective is None:
            raise ExecutionError("No current objective available")

        current_objective_variables = self._find_variable_in_text(current_objective)
        self.logger.info(f"Found variables in objective: {current_objective_variables}")
        return None
