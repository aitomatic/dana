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

                    # Use the new method for iterative tool calling
                    response = await self._query_llm_iterative(
                        llm=context.reasoning_llm,
                        prompt=prompt,
                        system_prompt="You are executing a reasoning task. "
                                      "Provide clear, logical analysis and reasoning.",
                        available_resources=context.resources or {},
                        max_iterations=3,  # Allow up to 3 iterations of tool calling
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

    async def _query_llm_iterative(
        self,
        llm: LLMResource,
        prompt: str,
        system_prompt: Optional[str],
        available_resources: Dict[str, BaseResource],
        max_iterations: int = 3,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Query the LLM with support for iterative resource calling.
        
        This method allows the LLM to request resources, receive their results, and then
        potentially request more resources based on those results, up to a maximum number
        of iterations.
        
        Note: The LLM API uses "tools" terminology, but we translate this to "resources"
        in our internal code. When the LLM requests tools, we treat them as resources.

        Args:
            llm: LLM resource to query
            prompt: The initial prompt to send to the LLM
            system_prompt: System prompt for the LLM
            available_resources: Dictionary of available resources
            max_iterations: Maximum number of resource calling iterations (default: 3)
            max_tokens: Maximum tokens for the response
            temperature: Temperature for LLM generation
            
        Returns:
            Final LLM response with all resource results incorporated
        """
        # Get resource strings for all available resources
        resource_strings: List[Dict[str, Any]] = []
        for resource_id, resource in available_resources.items():
            # Note: get_tool_strings is the API method name
            resource_strings.extend(await resource.get_tool_strings(resource_id))

        # Initialize variables for the loop
        current_prompt = prompt
        all_resource_results = []
        iteration = 0
        
        # Add a system prompt that encourages resource use if not provided
        if not system_prompt:
            system_prompt = (
                "You are a reasoning assistant. Use tools when necessary to complete tasks. "
                "After receiving tool results, you can request additional tools if needed."
            )
        
        # Main loop for iterative resource calling
        while iteration < max_iterations:
            iteration += 1
            self.info(f"Resource calling iteration {iteration}/{max_iterations}")
            
            # Make the LLM query with available resources 
            # (translated to tools in _query_llm_once)
            response = await self._query_llm_once(
                llm=llm,
                prompt=current_prompt,
                system_prompt=system_prompt,
                available_resources=resource_strings,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Check if the LLM requested tools (translated to resources in our code)
            requested_resources = response.get("requested_tools")  # LLM API returns "requested_tools"
            if not requested_resources:
                # No more resources requested, return the final response
                self.info("No more resources requested, returning final response")
                return response
            
            # Execute the requested resources
            self.info(f"Executing {len(requested_resources)} requested resources")
            resource_results = await self._query_requested_resources(requested_resources, available_resources)
            all_resource_results.extend(resource_results)
            
            # Format resource results for the next iteration
            resource_result_text = "\n".join(
                [f"Tool: {result['resource_name']}\nResponse: {result['response']}" for result in resource_results]
            )
            
            # Enhance the prompt with resource results
            current_prompt = f"{current_prompt}\n\n" \
                             f"<tool_calling_results>\n{resource_result_text}\n</tool_calling_results>"
            
            # Add a specific instruction for the next iteration
            current_prompt += (
                "\n\nBased on these tool results, continue your reasoning. "
                "You can request additional tools if needed to complete your task."
            )
        
        # If we've reached the maximum iterations, return the final response
        self.info(f"Reached maximum iterations ({max_iterations}), returning final response")
        return response

    async def _query_llm_once(
        self,
        llm: LLMResource,
        prompt: str,
        system_prompt: Optional[str],
        available_resources: Optional[List[Dict]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Dict:
        """Query the LLM with the given prompt and resources.
        
        This method translates OpenDXA resources to LLM tools in the interface layer.
        Internally, we use "resources" terminology, but the LLM API expects "tools".

        Args:
            llm: LLM resource to query
            prompt: The prompt to send to the LLM
            system_prompt: System prompt for the LLM
            available_resources: Resources available to the LLM (translated to tools in the API call)
            max_tokens: Maximum tokens for the response
            temperature: Temperature for LLM generation

        Returns:
            LLM response with generated text and resource usage info
        """
        # Translate resources to tools for the LLM API
        request = {
            "prompt": prompt,
            "tools": available_resources,  # Resources are passed as tools to the LLM
            "parameters": {"temperature": temperature, "max_tokens": max_tokens or 1000},
        }

        if system_prompt:
            request["system_prompt"] = system_prompt

        return await llm.query(request)

    async def _query_requested_resources(
        self, 
        requested_resources: List[Any], 
        available_resources: Dict[str, BaseResource]
    ) -> List[Dict]:
        """Execute resources using provided resources.
        
        This method processes resources requested by the LLM (which the LLM API calls "tools").
        We maintain the "resources" terminology internally for consistency.

        Args:
            requested_resources: List of resources to execute (from LLM's "requested_tools")
            available_resources: Dictionary of available resources

        Returns:
            List of resource responses
        """
        try:
            resource_responses = []
            for requested_resource in requested_resources:
                function_name = requested_resource.function.name
                try:
                    # Parse the function name to extract resource name and tool name
                    # Format: [resource_name]__query__[tool_name]
                    resource_name, *_, tool_name = function_name.split("__")
                except ValueError:
                    self.warning(
                        f"Invalid function name format: {function_name}, "
                        "expected [resource_name]__query__[tool_name]"
                    )
                    continue

                my_resource = available_resources.get(resource_name)
                if not my_resource:
                    self.warning(f"Resource not found: {resource_name}")
                    continue

                params = requested_resource.function.arguments
                if isinstance(params, str):
                    params = json.loads(params)

                response = await self._query_one_resource(my_resource, tool_name, params)
                resource_responses.append({"resource_name": function_name, "response": response})

            return resource_responses

        except json.JSONDecodeError as e:
            self.error(f"Failed to parse resource arguments as JSON: {e}")
            return []
        except Exception as e:
            self.error(f"Error querying resource: {e}")
            return []

    async def _query_one_resource(self,
                                  resource: BaseResource,
                                  tool_name: Optional[str],
                                  params: Dict[str, Any]) -> Any:
        """Execute a resource with appropriate calling conventions.
        
        This method handles the execution of a resource's functionality (which the LLM API calls a "tool").
        We maintain the "resources" terminology internally for consistency.

        Handles different resource types (MCP, Agent, Base) with their specific
        calling patterns while maintaining a clean interface.

        Args:
            resource: Resource to call
            tool_name: Name of the tool to execute (from LLM's function name)
            params: Dictionary of parameters to pass to the resource

        Returns:
            Resource response
        """
        # For MCP resources, we need to use a specific format
        if isinstance(resource, McpResource):
            return await resource.query({"tool": tool_name, "arguments": params})

        # For other resources, we can pass the parameters directly
        return await resource.query(params)
