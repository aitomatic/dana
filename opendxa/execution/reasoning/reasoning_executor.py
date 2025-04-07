"""Reasoning executor implementation."""

import json
from typing import Any, Dict, List, Optional

from ...common.resource import BaseResource, LLMResource, McpResource
from ..execution_context import ExecutionContext
from ..execution_types import ExecutionNode, ExecutionSignal, ExecutionSignalType
from ..executor import Executor
from .reasoning import Reasoning
from .reasoning_factory import ReasoningFactory
from .reasoning_strategy import ReasoningStrategy


class ReasoningExecutor(Executor[ReasoningStrategy, Reasoning, ReasoningFactory]):
    """Executor for reasoning layer tasks.
    This executor handles the reasoning layer of execution, which is
    responsible for executing individual reasoning tasks using LLMs.
    """

    # Required class attributes
    _strategy_type = ReasoningStrategy
    _default_strategy = ReasoningStrategy.DEFAULT
    graph_class = Reasoning
    _factory_class = ReasoningFactory
    _depth = 2

    def __init__(self, strategy: ReasoningStrategy = ReasoningStrategy.DEFAULT):
        """Initialize the reasoning executor.

        Args:
            strategy: Strategy for reasoning execution
        """
        super().__init__(strategy)

    async def _execute_node_core(self, node: ExecutionNode, context: ExecutionContext) -> List[ExecutionSignal]:
        """Execute a reasoning node using LLM.

        This is the bottom layer executor, so it handles the actual execution
        of reasoning tasks using LLMs.

        Args:
            node: The node to execute
            context: The execution context

        Returns:
            List of execution signals
        """
        # Get parent nodes
        workflow_node = context.get_current_workflow_node()
        plan_node = context.get_current_plan_node()

        # Print execution hierarchy with indentation
        self.info("\nExecution Hierarchy:")
        self.info("===================")

        # Workflow node (top level)
        if workflow_node:
            self.info("Workflow Node:")
            self.info(f"  ID: {workflow_node.node_id}")
            self.info(f"  Type: {workflow_node.node_type}")
            self.info(f"  Description: {workflow_node.description}")
            self.info(f"  Status: {workflow_node.status}")
            workflow_obj = context.current_workflow.objective if context.current_workflow else None
            self.info(f"  Workflow Objective: {workflow_obj.current if workflow_obj else 'None'}")
            self.info(f"  Node Objective: {workflow_node.objective.current if workflow_node.objective else 'None'}")

            # Plan node (middle level)
            if plan_node:
                self.info("\n  Plan Node:")
                self.info(f"    ID: {plan_node.node_id}")
                self.info(f"    Type: {plan_node.node_type}")
                self.info(f"    Description: {plan_node.description}")
                self.info(f"    Status: {plan_node.status}")
                plan_obj = context.current_plan.objective if context.current_plan else None
                self.info(f"    Plan Objective: {plan_obj.current if plan_obj else 'None'}")
                self.info(f"    Node Objective: {plan_node.objective.current if plan_node.objective else 'None'}")

                # Reasoning node (bottom level)
                self.info("\n    Reasoning Node:")
                self.info(f"      ID: {node.node_id}")
                self.info(f"      Type: {node.node_type}")
                self.info(f"      Description: {node.description}")
                self.info(f"      Status: {node.status}")
                reasoning_obj = context.current_reasoning.objective if context.current_reasoning else None
                self.info(f"      Reasoning Objective: {reasoning_obj.current if reasoning_obj else 'None'}")
                self.info(f"      Node Objective: {node.objective.current if node.objective else 'None'}")
                self.info(f"      Metadata: {node.metadata}")

                # Make LLM call with the reasoning node's objective
                if context.reasoning_llm and node.objective:
                    prompt = (
                        f"Execute the reasoning task for the following objective hierarchy:\n\n"
                        f"1. Workflow Objective: "
                        f"{workflow_obj.current if workflow_obj else 'None'}\n"
                        f"2. Workflow Node within Workflow: "
                        f"{workflow_node.objective.current if workflow_node.objective else 'None'}\n"
                        f"3. Plan Node under Workflow Node Objective: "
                        f"{plan_node.objective.current if plan_node.objective else 'None'}\n"
                        f"4. Reasoning Node under Plan Node Objective: "
                        f"{node.objective.current}\n\n"
                        f"Reasoning Node Description: {node.description}\n\n"
                        f"Please provide a detailed analysis and reasoning for this task, "
                        f"ensuring your response aligns with all levels of the objective hierarchy."
                    )

                    resource_results = await self._utilize_resources(
                        prompt=prompt,
                        resources=context.resources or {},
                        llm=context.reasoning_llm,
                    )

                    if resource_results:
                        resource_result_text = "\n".join(
                            [f"Tool: {resp['tool_name']}\nResponse: {resp['response']}" for resp in resource_results]
                        )

                        prompt = f"{prompt}\n\n<tool_calling>\n{resource_result_text}\n</tool_calling>"

                    response = await self._llm_query(
                        llm=context.reasoning_llm,
                        prompt=prompt,
                        system_prompt="You are executing a reasoning task. Provide clear, logical analysis and reasoning.",
                        tools=[],
                        max_tokens=1000,
                        temperature=0.7,
                    )

                    if response and "content" in response:
                        self.info("\nReasoning Result:")
                        self.info("================")
                        self.info(response["content"])

                        return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content=response["content"])]

        # If no response was generated, return an empty result
        return [ExecutionSignal(type=ExecutionSignalType.DATA_RESULT, content={})]

    async def _utilize_resources(
        self,
        prompt: str,
        resources: Dict[str, BaseResource],
        llm: LLMResource,
    ) -> List[Dict]:
        """Enhance prompt with tool execution results.

        Args:
            prompt: Original prompt
            resources: Dictionary of available resources
            llm: LLM resource

        Returns:
            Enhanced prompt with tool results
        """
        # Get tools strings
        tool_strings: List[Dict[str, Any]] = []
        for resource_id, resource in resources.items():
            tool_strings.extend(await resource.get_tool_strings(resource_id))

        if not tool_strings:
            return []

        system_prompt = "You are a reasoning assistant. Use tools when necessary to complete tasks."

        # Query LLM with tools
        response = await self._llm_query(llm, prompt, system_prompt, tool_strings)

        if not response.get("tools_used"):
            return []

        # Execute tools and get responses
        return await self._tool_calling(response["tools_used"], resources)

    async def _llm_query(
        self,
        llm: LLMResource,
        prompt: str,
        system_prompt: Optional[str],
        tools: Optional[List[Dict]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Dict:
        """Query the LLM with the given prompt and tools.

        Args:
            llm: LLM resource to query
            prompt: The prompt to send to the LLM
            system_prompt: System prompt for the LLM
            tools: Tools available to the LLM
            max_tokens: Maximum tokens for the response
            temperature: Temperature for LLM generation

        Returns:
            LLM response with generated text and tool usage info
        """
        request = {
            "prompt": prompt,
            "tools": tools,
            "parameters": {"temperature": temperature, "max_tokens": max_tokens or 1000},
        }

        if system_prompt:
            request["system_prompt"] = system_prompt

        return await llm.query(request)

    async def _tool_calling(self, tools_used: List[Any], resources: Dict[str, BaseResource]) -> List[Dict]:
        """Execute tools using provided resources.

        Args:
            tools_used: List of tools to execute
            resources: Dictionary of available resources

        Returns:
            List of tool responses
        """
        try:
            tool_responses = []
            for tool in tools_used:
                function_name = tool.function.name
                try:
                    resource_name, *_, tool_name = function_name.split("__")
                except ValueError:
                    self.warning(f"Invalid function name format: {function_name}, expected [resource_name]__query__[tool_name]")
                    continue

                resource = resources.get(resource_name)
                if not resource:
                    self.warning(f"Resource not found: {resource_name}")
                    continue

                params = tool.function.arguments
                if isinstance(params, str):
                    params = json.loads(params)

                response = await self._call_resource(resource, tool_name, params)
                tool_responses.append({"tool_name": function_name, "response": response})

            return tool_responses

        except json.JSONDecodeError as e:
            self.error(f"Failed to parse tool arguments as JSON: {e}")
            return []
        except Exception as e:
            self.error(f"Error calling tool: {e}")
            return []

    async def _call_resource(self, resource: BaseResource, tool_name: Optional[str], params: Dict[str, Any]) -> Any:
        """Execute a resource with appropriate calling conventions.

        Handles different resource types (MCP, Agent, Base) with their specific
        calling patterns while maintaining a clean interface.

        Args:
            resource: Resource to call
            tool_name: Name of the tool to execute
            params: Dictionary of parameters to pass to the resource

        Returns:
            Resource response
        """

        if isinstance(resource, McpResource):
            return await resource.query({"tool": tool_name, "arguments": params})

        return await resource.query(params)
