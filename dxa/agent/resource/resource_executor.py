"""Tool execution utilities for DXA."""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from dxa.agent.resource.base_resource import BaseResource
from dxa.agent.resource.llm_resource import LLMResource
from dxa.execution.execution_context import ExecutionContext

logger = logging.getLogger("dxa.common.utils.tool_executor")

class ResourceExecutor:
    """Manages tool execution workflows across executor layers."""

    async def execute_resources(
        self,
        prompt: str,
        context: ExecutionContext,
        layer: str = "reasoning",
    ) -> List[Dict]:
        """Enhance prompt with tool execution results.
        
        Args:
            prompt: Original prompt
            context: Execution context with agent and resources
            layer: Execution layer (workflow, plan, reasoning)
            strategy: Optional specific strategy name
            
        Returns:
            Enhanced prompt with tool results
        """

        # Check if tools are available
        resources = context.resources if hasattr(context, 'resources') else None
        if resources is None:
            return []

        # Get tools and execute LLM query
        tools = await self._get_tool_strings(resources)
        if not tools:
            return []

        system_prompt = self._get_system_prompt(layer)

        # Query LLM with tools
        response = await self._query_llm(
            self._get_llm(context, layer),
            prompt, 
            system_prompt,
            tools
        )

        # If no tools used, return original content
        if not response.get("tools_used"):
            return []

        # Execute tools and get responses
        return await self._execute_tools(response["tools_used"], context.resources)

    async def _get_tool_strings(self, resources: Dict[str, BaseResource]) -> List[Dict]:
        """Get tools from context."""
        tool_formats: List[Dict[str, Any]] = []
        for resource_id, resource in resources.items():
            tool_formats.extend(await resource.get_tool_strings(resource_id))

        return tool_formats

    def _get_llm(self, context: 'ExecutionContext', layer: str) -> LLMResource:
        """Get appropriate LLM for the layer."""
        if layer == "reasoning":
            return context.reasoning_llm
        else:
            return context.planning_llm

    def _get_system_prompt(self, layer: str) -> str:
        """Get system prompt for the specific layer."""
        # Layer-specific system prompts
        prompts = {
            "workflow": """You are a workflow planning assistant. Use tools to gather relevant information.""",
            "plan": """You are a plan execution assistant. Use tools to gather relevant information to create a plan. Especially tool that retrieve the synthesized or heuristic data from the internet.""",
            "reasoning": """You are a reasoning assistant. Use tools when necessary to complete tasks."""
        }
        return prompts.get(layer, prompts["reasoning"])

    def _format_prompt_with_tool_results(self, original_prompt: str, tool_responses: List[Dict]) -> str:
        """Format prompt with tool results."""
        if not tool_responses:
            return original_prompt

        tool_responses_text = "\n".join([
            f"Tool: {resp['tool_name']}\nResponse: {resp['response']}"
            for resp in tool_responses
        ])

        return f"{original_prompt}\n\nRelevant context retrieved from tools:\n{tool_responses_text}"

    async def _query_llm(
        self,
        llm: LLMResource, 
        prompt: str, 
        system_prompt: Optional[str], 
        tools: Optional[List[Dict]], 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
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
            LLM response
        """
        request = {
            "prompt": prompt,
            "tools": tools,
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens or 1000
            }
        }

        if system_prompt:
            request["system_prompt"] = system_prompt

        return await llm.query(request)

    async def _execute_tools(self, tools_used: List[Any], resources: Dict[str, BaseResource]) -> List[Dict]:
        """Execute tools using provided resources.
        
        Args:
            tools_used: List of tools to execute
            resources: Dictionary of available resources
            
        Returns:
            List of tool responses
        """
        tool_responses = []
        for tool in tools_used:
            function_name = tool.function.name
            resource_name, *_, tool_name = function_name.split("__")

            resource = resources.get(resource_name)
            if not resource:
                continue

            params = self._parse_tool_params(tool.function.arguments)

            response = await self._call_resource(resource, tool_name, params)
            tool_responses.append({
                "tool_name": function_name,
                "response": response
            })

        return tool_responses

    def _parse_tool_params(self, params: Union[str, Dict]) -> Dict:
        """Parse tool parameters from string or dict format."""
        if isinstance(params, str):
            try:
                return json.loads(params)
            except json.JSONDecodeError as e:
                logger.info(f"Failed to parse tool arguments as JSON: {e}")
                return {}
        return params

    async def _call_resource(self, resource: BaseResource, tool_name: Optional[str], params: Dict) -> Any:
        """Execute a resource with appropriate calling conventions.
        
        Handles different resource types (MCP, Agent, Base) with their specific
        calling patterns while maintaining a clean interface.
        """
        resource_type = resource.__class__.__name__

        print(f"resource_type: {resource_type}")

        if resource_type in ('McpLocalResource', 'McpRemoteResource'):
            return await resource.query({'tool': tool_name, 'arguments': params})

        if resource_type == 'AgentResource':
            return await resource.query({"agent_id": tool_name, "query": params})
       
        return await resource.query(**params) if isinstance(params, dict) else await resource.query(params)
    