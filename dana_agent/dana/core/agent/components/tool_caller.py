"""
ToolCaller: Handles tool call execution and orchestration.

This component provides functionality for:
- Tool call execution (agents, resources, workflows)
- Tool call result processing
- Tool call error handling
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import json
import re
import traceback
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dana.common.llm.debug_logger import get_debug_logger
from dana.common.llm.types import LLMResponse
from dana.common.observable import observable
from dana.common.protocols import DictParams
from dana.common.utils.misc import Misc
from dana.core.knowledge.prompts.codecs import AbstractCodec


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent


class WARCaller:
    """Unified caller for Workflows, Agents, and Resources with consistent behavior."""

    def __init__(self, agent: STARAgent, tool_caller: ToolCaller | None = None):
        """Initialize with agent reference."""
        self._agent = agent
        self._llm = agent.llm_client  # TODO: maintain our own LLM (maybe local?)
        self._tool_caller = tool_caller

    def execute_call(self, arguments: dict[str, Any], object_type: str, id_key: str, default_method: str | None = None) -> dict[str, Any]:
        """
        Execute a tool call with unified logic for both resources and workflows.

        Args:
            arguments: Tool call arguments
            object_type: "resource" or "workflow"
            id_key: Key for the object ID ("resource_id" or "workflow_id")
            default_method: Default method name if not provided (e.g., "execute" for workflows)

        Returns:
            Tool call result dictionary
        """
        object_id = arguments.get(id_key)
        method = arguments.get("method", default_method)
        parameters = arguments.get("parameters", {})

        # Validate required parameters
        if not object_id or not method:
            if object_type == "resource":
                return self._create_tool_error(object_type, object_id or "unknown", "Missing resource_id or method for resource call")
            else:
                return self._create_tool_error(object_type, object_id or "unknown", f"Missing {id_key} or method for {object_type} call")

        # Execute call
        try:
            # Parse parameters if they're in string format (XML/JSON)
            if isinstance(parameters, str):
                if self._tool_caller:
                    parsed_parameters = self._tool_caller._convert_function_parameter_value(parameters)
                else:
                    # Fallback: treat as dict if it looks like one, otherwise create a simple dict
                    parsed_parameters = {"data": parameters}
            else:
                parsed_parameters = parameters

            result = self.invoke(object_id, method, parsed_parameters, object_type)
            return self._create_tool_success(object_type, f"{object_id}.{method}", result)
        except Exception as e:
            return self._create_tool_error(
                object_type, f"{object_id}.{method}", f"Error calling {object_type} {object_id}.{method}: {str(e)}"
            )

    @observable
    def invoke(self, object_id: str, method: str, parameters: dict[str, Any], object_type: str) -> str | DictParams:
        """
        Invoke a method on a workflow, resource, or agent with consistent behavior.

        Args:
            object_id: ID of the workflow, resource, or agent
            method: Method name to call
            parameters: Parameters to pass to the method
            object_type: "workflow", "resource", or "agent"

        Returns:
            String or DictParams result of the method call
        """
        # Find the object
        obj = None
        if object_type == "resource":
            for r in self._agent.available_resources:
                if r.object_id == object_id:
                    obj = r
                    break
        elif object_type == "workflow":
            for w in self._agent.available_workflows:
                if w.workflow_id == object_id:
                    obj = w
                    break
        elif object_type == "agent":
            # Handle agent calls with registry management
            self._agent.ensure_registered()
            registry = self._agent._registry

            if self._agent.object_id not in registry._items:
                return "Error: Agent not registered"

            obj = registry.get(object_id)
            if not obj:
                return f"Error: Agent {object_id} not found"

            # Debug logging for agent calls
            debug_logger = get_debug_logger()
            message = parameters.get("message", "") if parameters else ""
            debug_logger.log_agent_interaction(
                agent_id=self._agent.object_id,
                agent_type=self._agent.agent_type,
                interaction_type="agent_call_outgoing",
                content=message,
                target_agent_id=object_id,
                metadata={"target_agent_type": obj.agent_type, "message_length": len(message)},
            )

        if not obj:
            return f"Error: {object_type.title()} {object_id} not found"

        try:
            # Get the method from the object
            if not hasattr(obj, method):
                return f"Error: {object_type.title()} {object_id} does not have method '{method}'"

            obj_method = getattr(obj, method)

            # Call the method with the parsed parameters
            if parameters:
                # Handle case where parameters is a single value that should be passed as the first argument
                if not isinstance(parameters, dict):
                    # Get the method signature to determine the parameter name
                    import inspect

                    sig = inspect.signature(obj_method)
                    param_names = list(sig.parameters.keys())
                    if param_names and param_names[0] != "self":
                        # Pass the parsed value as the first parameter
                        first_param = param_names[0]
                        result = obj_method(**{first_param: parameters})
                    else:
                        # Fallback: try to call with the value directly
                        result = obj_method(parameters)
                else:
                    # Normal dict parameters
                    result = obj_method(**parameters)
            else:
                result = obj_method()

            # Handle async methods (consistent for both workflows and resources)
            if asyncio.iscoroutinefunction(obj_method):
                result = asyncio.run(result)

            # Special handling for agent calls
            if object_type == "agent":
                # Debug logging for agent response
                debug_logger = get_debug_logger()
                if isinstance(result, dict):
                    debug_logger.log_agent_interaction(
                        agent_id=self._agent.object_id,
                        agent_type=self._agent.agent_type,
                        interaction_type="agent_call_response",
                        content=result.get("response", ""),
                        target_agent_id=object_id,
                        metadata={
                            "target_agent_type": obj.agent_type,
                            "response_length": len(result.get("response", "")),
                            "success": result.get("success", False),
                        },
                    )

                    # Process agent response similar to _invoke_agent logic
                    has_success = result.get("success")
                    has_response = result.get("response")
                    has_error = result.get("error")

                    if has_success is True or (has_success is None and has_response and not has_error):
                        return result.get("response", "No response")
                    else:
                        return f"Error: {result.get('error', 'Unknown error')}"

            # Consistent result formatting for workflows and resources
            assert isinstance(result, dict) or isinstance(result, str)
            return result

        except Exception as e:
            # Debug logging for agent errors
            if object_type == "agent":
                debug_logger = get_debug_logger()
                debug_logger.log_agent_interaction(
                    agent_id=self._agent.object_id,
                    agent_type=self._agent.agent_type,
                    interaction_type="agent_call_error",
                    content=str(e),
                    target_agent_id=object_id,
                    metadata={"target_agent_type": obj.agent_type if obj else "unknown", "error_type": type(e).__name__},
                )
            raise Exception(f"Error calling {object_type} {object_id}.{method}: {str(e)}")

    # Utility methods for tool call results
    def _create_tool_success(self, tool_type: str, target: str, result: str) -> dict[str, Any]:
        """Create a successful tool call result."""
        return {"type": tool_type, "target": target, "result": result, "success": True}

    def _create_tool_error(self, tool_type: str, target: str, error_message: str) -> dict[str, Any]:
        """Create a tool call error result."""
        return {"type": tool_type, "target": target, "result": f"Error: {error_message}", "success": False}

    # Convenience methods for specific object types
    def execute_resource_call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a resource tool call."""
        return self.execute_call(arguments, "resource", "resource_id")

    def execute_workflow_call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a workflow tool call."""
        return self.execute_call(arguments, "workflow", "workflow_id", "execute")

    def execute_agent_call(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute an agent tool call."""
        object_id = arguments.get("object_id")
        message = arguments.get("message")

        # Validate required parameters
        if not object_id or not message:
            return self._create_tool_error("agent", object_id or "unknown", "Missing object_id or message for agent call")

        # Execute the call using unified invoke method
        try:
            result = self.invoke(object_id, "query", {"message": message}, "agent")
            return self._create_tool_success("agent", object_id, result)
        except Exception as e:
            return self._create_tool_error("agent", object_id, f"Error calling agent {object_id}: {str(e)}")


class ToolCaller(WARCaller):
    """Component providing tool call execution and orchestration capabilities."""

    def __init__(self, agent: STARAgent):
        """
        Initialize the component with a reference to the agent.

        Args:
            agent: The agent instance this component belongs to
        """
        super().__init__(agent, self)  # Pass self as tool_caller
        self._agent = agent

    # ============================================================================
    # PUBLIC API - TOOL EXECUTION
    # ============================================================================

    def execute_tool_calls(self, parsed_tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute parsed tool calls from LLM response."""
        return [self._execute_single_call(call) for call in parsed_tool_calls]

    # ============================================================================
    # TOOL CALL EXECUTION
    # ============================================================================

    def _execute_single_call(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a single tool call with error handling.

        FAULT-TOLERANCE STRATEGY (Phase 1):
        This method handles multiple tool call format combinations through branching logic:

        1. type + target + method: 'type="agent" id="web-researcher"/' (XML format)
        2. target + method: {"target": "web-researcher", "method": "query"} (explicit target in args)
        3. function-as-target: {"function": "web-researcher", "arguments": {...}} (implicit target)

        Each branch extracts the necessary information (type, target, method, parameters) and
        dispatches to the appropriate execution method.

        FUTURE ENHANCEMENT (Phase 2):
        Consider refactoring to a canonical normalization approach:
        - Extract all format handling into _normalize_tool_call_to_canonical()
        - Normalize all combinations to: {"type": str, "target": str, "method": str, "parameters": dict}
        - Single dispatch based on normalized type
        - Benefits: cleaner separation, easier to extend, better testability
        - Challenges: type inference cost, ambiguity handling if target exists in multiple registries

        Args:
            tool_call: Dictionary with "function" and "arguments" keys

        Returns:
            Tool call result dictionary with type, target, result, and success fields
        """
        try:
            function_name = tool_call.get("function", "")
            arguments = tool_call.get("arguments", {})

            # Handle new target/method format
            if 'type="agent"' in function_name:
                # Extract agent ID from function name like 'type="agent" id="web-research-001"/'
                import re

                id_match = re.search(r'id="([^"]+)"', function_name)
                if id_match:
                    agent_id = id_match.group(1)
                    # Convert to expected format for agent call
                    agent_args = {"object_id": agent_id, "message": arguments.get("message", "")}
                    return self.execute_agent_call(agent_args)
                else:
                    return self._create_tool_error("agent", "unknown", "Could not extract agent ID from target")

            elif 'type="resource"' in function_name:
                # Extract resource ID and handle resource calls
                import re

                id_match = re.search(r'id="([^"]+)"', function_name)
                if id_match:
                    resource_id = id_match.group(1)
                    # Convert to expected format for resource call
                    resource_args = {
                        "resource_id": resource_id,
                        "method": arguments.get("method", "execute"),
                        "parameters": {k: v for k, v in arguments.items() if k != "method"},
                    }
                    return self.execute_resource_call(resource_args)
                else:
                    return self._create_tool_error("resource", "unknown", "Could not extract resource ID from target")

            elif 'type="workflow"' in function_name:
                # Extract workflow ID and handle workflow calls
                import re

                id_match = re.search(r'id="([^"]+)"', function_name)
                if id_match:
                    workflow_id = id_match.group(1)
                    # Convert to expected format for workflow call
                    workflow_args = {
                        "workflow_id": workflow_id,
                        "method": arguments.get("method", "execute"),
                        "parameters": {k: v for k, v in arguments.items() if k != "method"},
                    }
                    return self.execute_workflow_call(workflow_args)
                else:
                    return self._create_tool_error("workflow", "unknown", "Could not extract workflow ID from target")

            else:
                # Check if this is a structured JSON call with target field
                if "target" in arguments:
                    return self._handle_target_based_call(function_name, arguments)

                # Phase 1: Try function_name as implicit target (e.g., "web-researcher")
                # This handles cases where LLM provides function name without explicit target field
                if function_name:
                    pseudo_args = {"target": function_name} | arguments
                    return self._handle_target_based_call(function_name, pseudo_args)

                return self._create_unknown_function_error(function_name or "unknown")

        except Exception as e:
            return self._create_execution_error(tool_call, e)

    # ============================================================================
    # LLM RESPONSE PARSING
    # ============================================================================

    @observable
    def parse_llm_response(self, llm_response: LLMResponse) -> tuple[str | None, str | None, list[DictParams]]:
        """
        Parse LLM response using LLM-assisted parsing.

        This method uses the LLM to recast the response into canonical XML form,
        then parses it symbolically with high confidence.
        """
        return self.parse_llm_response_symbolic(llm_response)

    @observable
    def parse_llm_response_symbolic(self, llm_response: LLMResponse) -> tuple[str | None, str | None, list[DictParams]]:
        """
        Parse LLM response using pure symbolic parsing (original method).

        This method uses only symbolic parsing without LLM assistance.
        It handles both XML content and structured tool calls.

        Args:
            llm_response: The LLM response object containing content and tool calls

        Returns:
            Tuple of (response_text, response_reasoning, tool_calls_list)
        """
        if not llm_response:
            return None, None, []

        # Work with a copy to avoid mutating the input
        content = llm_response.content.strip()

        result_response = None
        result_reasoning = None
        result_tool_calls = []

        try:
            if llm_response.tool_calls:
                if len(llm_response.tool_calls) == 1 and llm_response.tool_calls[0].function.name == "<|constrain|>response":
                    # OMG this is a response being passed back as a tool call (openai/gpt-oss-20b)
                    content = llm_response.tool_calls[0].function.arguments
                    if content:
                        content = content.strip()
                else:
                    # Structured (JSON) tool calls
                    result_tool_calls.extend(self._to_tool_call_dicts(llm_response.tool_calls))

            # Try to extract text content first
            text = self._extract_content_between_xml_tags(content, "content")
            if not text:
                # Fallback: use content between <response> tags
                text = self._extract_content_between_xml_tags(content, "response")

            if not text:
                # Find the first instance of "<response>"
                response_start = content.find("<response>")
                if response_start == -1:
                    text = content
                else:
                    text = content[response_start:]

            result_response = text  # Already stripped
            if not result_response:
                result_response = content

            # Extract tool calls from content
            tool_calls_xml = self._extract_content_between_xml_tags(content, "tool_calls")
            if tool_calls_xml:
                # Use the proper XML parsing method that creates correct structure
                result_tool_calls.extend(self._extract_tool_calls_from_xml(tool_calls_xml))

            result_reasoning = self._extract_content_between_xml_tags(content, "reasoning")
        except Exception as e:
            # Log error but don't crash - return what we have
            # TODO: Replace with proper logging
            print(f"Error parsing LLM response: {e}")
            # Fall back to treating content as plain text
            if not result_response and content:
                result_response = content

        return result_response, result_reasoning, result_tool_calls

    @observable
    def parse_llm_response_assisted(self, llm_response: LLMResponse) -> tuple[str | None, str | None, list[DictParams]]:
        """
        Parse LLM response using LLM-assisted canonical XML conversion.

        This method first uses the LLM to recast the response into canonical XML form,
        then parses it symbolically with high confidence.

        Args:
            llm_response: The LLM response object containing content and tool calls

        Returns:
            Tuple of (response_text, response_reasoning, tool_calls_list)
        """
        if not llm_response:
            return None, None, []

        # Handle structured tool calls from LLM providers (like OpenAI function calling)
        if llm_response.tool_calls:
            if len(llm_response.tool_calls) == 1 and llm_response.tool_calls[0].function.name == "<|constrain|>response":
                # Special case: response passed as tool call (openai/gpt-oss-20b)
                content = llm_response.tool_calls[0].function.arguments
                if content:
                    content = content.strip()
            else:
                # Structured tool calls - convert to our format and return
                structured_tool_calls = self._to_tool_call_dicts(llm_response.tool_calls)
                return llm_response.content, None, structured_tool_calls

        # Work with a copy to avoid mutating the input
        content = llm_response.content.strip()

        try:
            # Step 1: Use LLM to recast the response into canonical XML form
            canonical_xml = self._recast_to_canonical_xml(content)

            # Step 2: Parse the canonical XML symbolically with confidence
            return self._parse_canonical_xml(canonical_xml)

        except Exception as e:
            # Fallback to symbolic parsing method if LLM-assisted parsing fails
            print(f"Error in LLM-assisted parsing, falling back to symbolic method: {e}")
            return self.parse_llm_response_symbolic(llm_response)

    def _recast_to_canonical_xml(self, content: str) -> str:
        """
        Use the LLM to recast the response content into canonical XML form.

        Args:
            content: The original LLM response content

        Returns:
            Canonical XML string with proper structure
        """
        from dana.common.llm.types import LLMMessage

        recast_prompt = f"""
You are a response parser that converts LLM responses into canonical XML format.

Convert the following response into the standard XML format with these sections:
- <response> as the root wrapper
- <content> for the main response text
- <reasoning> for any reasoning or explanation (optional)
- <tool_calls> for any tool calls with proper structure (optional)

Expected XML format:
<response>
<content>Main response text here</content>
<reasoning>Any reasoning or explanation</reasoning>
<tool_calls>
<tool_call>
<target id="target-name"/>
<method>method-name</method>
<arguments>
<param1>value1</param1>
<param2>value2</param2>
</arguments>
</tool_call>
</tool_calls>
</response>

Original response:
{content}

Please provide the canonical XML format:
"""

        try:
            # Use the LLM to recast the content
            messages = [
                LLMMessage(role="system", content="You are a response parser that converts LLM responses into canonical XML format."),
                LLMMessage(role="user", content=recast_prompt),
            ]
            recast_response = self._llm.chat_response_sync(messages)
            return recast_response.content.strip()
        except Exception as e:
            print(f"Error recasting to canonical XML: {e}")
            # Return original content wrapped in basic XML structure
            return f"<content>{content}</content>"

    def _parse_canonical_xml(self, canonical_xml: str) -> tuple[str | None, str | None, list[DictParams]]:
        """
        Parse canonical XML with high confidence using symbolic parsing.

        Args:
            canonical_xml: The canonical XML string to parse

        Returns:
            Tuple of (response_text, response_reasoning, tool_calls_list)
        """
        result_response = None
        result_reasoning = None
        result_tool_calls = []

        try:
            # Extract content section
            content_text = self._extract_content_between_xml_tags(canonical_xml, "content")
            if content_text:
                result_response = content_text.strip()
            else:
                # Fallback: use the entire content if no content tags found
                result_response = canonical_xml.strip()

            # Extract reasoning section
            reasoning_text = self._extract_content_between_xml_tags(canonical_xml, "reasoning")
            if reasoning_text:
                result_reasoning = reasoning_text.strip()

            # Extract tool calls section
            tool_calls_xml = self._extract_content_between_xml_tags(canonical_xml, "tool_calls")
            if tool_calls_xml:
                # Parse tool calls with high confidence since they're in canonical form
                result_tool_calls.extend(self._extract_tool_calls_from_xml(tool_calls_xml))

        except Exception as e:
            print(f"Error parsing canonical XML: {e}")
            # Return what we have so far
            if not result_response:
                result_response = canonical_xml

        return result_response, result_reasoning, result_tool_calls

    def _extract_content_between_xml_tags(self, content: str, tag: str) -> str | None:
        """
        Extract content between tags, handling both balanced and unbalanced cases.

        Args:
            content: The XML content to parse
            tag: The tag name (without < > brackets)

        Returns:
            Content between tags, or None if tag not found
        """
        if not content or not tag:
            return None

        # Escape the tag name to prevent regex injection
        escaped_tag = re.escape(tag)

        # First try to find balanced tags
        match = re.search(r"<" + escaped_tag + r">(.*?)</" + escaped_tag + r">", content, re.DOTALL)
        if match:
            return match.group(1).strip()

        # If no balanced tags found, look for opening tag and return everything until next tag or end
        match = re.search(r"<" + escaped_tag + r">([^<]*)", content, re.DOTALL)
        if match:
            captured = match.group(1).strip()
            # If we captured nothing or only whitespace, try to capture everything
            if not captured:
                match = re.search(r"<" + escaped_tag + r">(.*)", content, re.DOTALL)
                if match:
                    return match.group(1).strip()
            return captured

        return None

    def _parse_xml_attributes(self, attrs_str: str) -> dict[str, str]:
        """
        Parse XML attributes from a string into a dictionary.

        Args:
            attrs_str: String containing XML attributes (e.g., 'id="foo" type="bar"')

        Returns:
            Dictionary of attribute name-value pairs
        """
        attributes = {}
        # Match attribute="value" or attribute='value'
        attr_pattern = r'(\w+)\s*=\s*["\']([^"\']*)["\']'
        for match in re.finditer(attr_pattern, attrs_str):
            attr_name, attr_value = match.groups()
            attributes[attr_name] = attr_value
        return attributes

    def _extract_function_name_from_attributes(self, attrs_str: str) -> str | None:
        """
        Extract function name from XML attributes with preference: id > type.

        Args:
            attrs_str: String containing XML attributes

        Returns:
            Function name (id or type value), or None if neither found
        """
        if not attrs_str or not attrs_str.strip():
            return None

        attributes = self._parse_xml_attributes(attrs_str)

        # Prefer id over type
        return attributes.get("id") or attributes.get("type")

    def _extract_tool_calls_from_xml(self, tool_calls_xml: str) -> list[DictParams]:
        """
        Parse XML tool calls into dictionary format.

        Supports these patterns (with id preferred over type):
        - <tool_call id="xxx"> or <tool_call type="xxx"> or <tool_call id="xxx" type="yyy">
        - <tool_call><target id="xxx"/> or <tool_call><target type="xxx"/> etc.

        Args:
            tool_calls_xml: XML string containing tool calls

        Returns:
            List of tool call dictionaries
        """
        if not tool_calls_xml or not tool_calls_xml.strip():
            return []

        tool_calls = []

        try:
            # Find all tool_call elements using regex (handle attributes on opening tag)
            # Use word boundary \b to avoid matching <tool_calls> as <tool_call>
            matches = re.findall(r"<tool_call\b\s*([^>]*)>(.*?)</tool_call>", tool_calls_xml, re.DOTALL)

            if not matches:
                # Try tolerant parsing for unbalanced tags
                tool_call_content = self._extract_content_between_xml_tags(tool_calls_xml, "tool_call")
                if tool_call_content:
                    matches = [("", tool_call_content)]

            for attrs_str, tool_call_content in matches:
                # Extract function name: try <tool_call> attributes first, then <target> tag
                function_name = None

                # Strategy 1: Extract from <tool_call> tag attributes (id > type)
                if attrs_str:
                    function_name = self._extract_function_name_from_attributes(attrs_str)

                # Strategy 2: Extract from <target> tag attributes (id > type)
                if not function_name:
                    target_match = re.search(r"<target\s+([^>]+)/?>", tool_call_content)
                    if target_match:
                        function_name = self._extract_function_name_from_attributes(target_match.group(1))

                # Skip if no function name found
                if not function_name:
                    continue

                # Extract method
                method = self._extract_content_between_xml_tags(tool_call_content, "method")

                # Extract arguments
                arguments_xml = self._extract_content_between_xml_tags(tool_call_content, "arguments")
                arguments_dict = {}

                if arguments_xml:
                    # Parse individual argument tags - try balanced first, then tolerant
                    arg_matches = re.findall(r"<(\w+)>(.*?)</\1>", arguments_xml, re.DOTALL)
                    for arg_name, arg_value in arg_matches:
                        # Use unified parser to handle XML, JSON, or plain text
                        arguments_dict[arg_name] = self._convert_function_parameter_value(arg_value.strip())

                    # If no XML tags found, try parsing entire content as JSON or other format
                    if not arg_matches:
                        # Try to parse the entire arguments_xml as a value (handles JSON, nested XML, etc.)
                        parsed_value = self._convert_function_parameter_value(arguments_xml)

                        # If it parsed to a dict, merge it into arguments_dict
                        if isinstance(parsed_value, dict):
                            arguments_dict.update(parsed_value)
                        else:
                            # Fall back to tolerant XML parsing for malformed tags
                            arguments_dict = self._parse_tool_call_arguments_with_error_recovery(arguments_xml)

                # Add method to arguments if present
                if method and method.strip():
                    arguments_dict["method"] = method.strip()

                tool_calls.append({"function": function_name, "arguments": arguments_dict})

        except Exception as e:
            # Log error but don't crash - return empty list
            # TODO: Replace with proper logging
            print(f"Error parsing XML tool calls: {e}")
            return []

        return tool_calls

    def _parse_tool_call_arguments_with_error_recovery(self, arguments_xml: str) -> dict[str, str]:
        """
        Parse arguments using tolerant parsing for unbalanced tags.

        Args:
            arguments_xml: XML string containing arguments

        Returns:
            Dictionary of argument name-value pairs
        """
        arguments_dict = {}

        # Find all opening tags and extract content until next tag or end
        tag_pattern = r"<(\w+)>"
        pos = 0

        while True:
            match = re.search(tag_pattern, arguments_xml[pos:])
            if not match:
                break

            tag_name = match.group(1)
            tag_start = pos + match.end()

            # Find next tag or end of string
            next_tag_match = re.search(r"<", arguments_xml[tag_start:])
            if next_tag_match:
                tag_end = tag_start + next_tag_match.start()
            else:
                tag_end = len(arguments_xml)

            arg_value = arguments_xml[tag_start:tag_end].strip()
            if arg_value:
                arguments_dict[tag_name] = arg_value

            pos = tag_start

        return arguments_dict

    def _parse_tool_call_arguments_from_json(self, json_string: str) -> dict[str, Any]:
        """Parse JSON arguments string."""
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            return {}

    def _extract_tool_calls_from_xml_arguments(self, xml_string: str) -> list[dict[str, Any]]:
        """Parse XML arguments string and extract tool calls."""
        try:
            # Look for tool_calls section in the XML
            if "<tool_calls>" in xml_string and "</tool_calls>" in xml_string:
                # Extract the tool_calls section
                start = xml_string.find("<tool_calls>")
                end = xml_string.find("</tool_calls>") + len("</tool_calls>")
                tool_calls_section = xml_string[start:end]

                # Parse the tool calls - this should return a list of tool calls
                tool_calls = self._parse_tool_call_arguments_with_error_recovery(tool_calls_section)
                return tool_calls if isinstance(tool_calls, list) else [tool_calls]
            else:
                # If no tool_calls section, try to parse the entire XML
                result = self._parse_tool_call_arguments_with_error_recovery(xml_string)
                return [result] if isinstance(result, dict) else result
        except Exception as e:
            # If XML parsing fails, return empty list
            print(f"XML parsing failed: {e}")
            return []

    def _filter_valid_tool_calls(self, xml_tool_calls: list) -> list[DictParams]:
        """Process XML tool calls and add valid ones to the result list."""
        valid_tool_calls = []
        for xml_tool_call in xml_tool_calls:
            if isinstance(xml_tool_call, dict) and "function" in xml_tool_call:
                valid_tool_calls.append(xml_tool_call)
        return valid_tool_calls

    def _detect_format_and_extract_tool_calls(self, arguments: str, function_name: str) -> list[DictParams]:
        """Parse arguments based on format detection and return tool calls."""
        if arguments.strip().startswith("{") and arguments.strip().endswith("}"):
            # JSON format
            args = self._parse_tool_call_arguments_from_json(arguments)
            return [{"function": function_name, "arguments": args}]

        elif arguments.strip().startswith("<") and arguments.strip().endswith(">"):
            # XML format - returns list of tool calls
            xml_tool_calls = self._extract_tool_calls_from_xml_arguments(arguments)
            return self._filter_valid_tool_calls(xml_tool_calls)

        else:
            # Fallback: try JSON first, then XML
            try:
                args = self._parse_tool_call_arguments_from_json(arguments)
                return [{"function": function_name, "arguments": args}]
            except Exception as _e:
                xml_tool_calls = self._extract_tool_calls_from_xml_arguments(arguments)
                return self._filter_valid_tool_calls(xml_tool_calls)

    def _to_tool_call_dicts(self, llm_tool_calls: list) -> list[DictParams]:
        """Convert structured function calls to our internal format."""
        tool_call_dicts = []

        for llm_tool_call in llm_tool_calls:
            try:
                function_name = llm_tool_call.function.name
                arguments = llm_tool_call.function.arguments

                if isinstance(arguments, str):
                    # Parse string arguments based on format
                    # Note: For XML format, outer_function_name is ignored and replaced
                    # with function names from nested XML structure
                    parsed_calls = self._detect_format_and_extract_tool_calls(arguments, function_name)
                    tool_call_dicts.extend(parsed_calls)
                else:
                    # Non-string arguments (already parsed) - use outer function name
                    tool_call_dicts.append({"function": function_name, "arguments": arguments})

            except Exception:
                continue

        return tool_call_dicts

    # ============================================================================
    # UNIFIED PARAMETER PARSING
    # ============================================================================

    def _convert_function_parameter_value(self, value: str, method=None) -> Any:
        """
        Parse a parameter value that could be XML, JSON, or plain text.
        Uses smart conventions to determine the appropriate Python type.

        Args:
            value: The parameter value to parse (string)
            method: Optional method object for type hint validation

        Returns:
            Parsed Python object (dict, list, str, int, bool, etc.)
        """
        if not value or not value.strip():
            return None

        value = value.strip()

        # Try JSON first (most explicit)
        if self._detect_json_format(value):
            import json

            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                pass  # Fall through to XML parsing

        # Try XML parsing (our main format)
        if self._detect_xml_format(value):
            return self._convert_xml_to_python_object(value)

        # Try basic type coercion for plain text
        return self._convert_text_to_typed_value(value)

    def _detect_json_format(self, value: str) -> bool:
        """Check if a string looks like JSON."""
        value = value.strip()
        return (value.startswith("{") and value.endswith("}")) or (value.startswith("[") and value.endswith("]"))

    def _detect_xml_format(self, value: str) -> bool:
        """Check if a string looks like XML."""
        value = value.strip()
        return value.startswith("<") and value.endswith(">")

    def _element_to_python(self, element) -> Any:
        """
        Convert an ElementTree Element to a Python object.

        Conventions:
        - Element with only text → typed value (string, int, bool, etc.)
        - Element with children → dict or list
        - Multiple children with same tag → list
        - Mixed children tags → dict

        Args:
            element: xml.etree.ElementTree.Element

        Returns:
            Python object (dict, list, or primitive)
        """
        # If element has no children, return its text content
        if len(element) == 0:
            text = element.text or ""
            return self._convert_text_to_typed_value(text.strip())

        # Group children by tag name
        children_by_tag = {}
        for child in element:
            tag = child.tag
            if tag not in children_by_tag:
                children_by_tag[tag] = []
            children_by_tag[tag].append(child)

        # Single tag type with multiple instances → list
        if len(children_by_tag) == 1:
            tag, children = next(iter(children_by_tag.items()))
            if len(children) > 1:
                return [self._element_to_python(child) for child in children]
            else:
                # Single child - check if parent suggests it should be a list
                # (e.g., <todos><todo>...</todo></todos> should return a list)
                parsed = self._element_to_python(children[0])
                parent_tag = element.tag
                if parent_tag.endswith("s") and not tag.endswith("s"):
                    return [parsed]
                return parsed

        # Multiple tag types → dict
        result = {}
        for tag, children in children_by_tag.items():
            if len(children) > 1:
                result[tag] = [self._element_to_python(child) for child in children]
            else:
                result[tag] = self._element_to_python(children[0])
        return result

    def _convert_xml_to_python_object(self, xml_str: str, parent_tag: str | None = None) -> Any:
        """
        Parse XML string to Python objects using smart conventions.

        Uses hybrid approach:
        1. Try proper XML parser (ElementTree) for well-formed XML
        2. Fall back to regex-based tolerant parsing for malformed XML

        Conventions:
        - Repeated tags → list
        - Tags with children → dict
        - Tags with only text → string (with type coercion)
        - Empty tags → None
        """
        import re
        import xml.etree.ElementTree as ET

        xml_str = xml_str.strip()

        # Strategy 1: Try proper XML parser (best for nested structures)
        try:
            # Wrap in root element if there are multiple root elements
            # or if it's a fragment
            wrapped_xml = f"<root>{xml_str}</root>"
            root = ET.fromstring(wrapped_xml)

            # If root has only one child, unwrap it
            if len(root) == 1:
                return self._element_to_python(root[0])
            elif len(root) > 1:
                # Multiple children at root level
                return self._element_to_python(root)
            else:
                # Root has no children, just text
                text = root.text or ""
                return self._convert_text_to_typed_value(text.strip())

        except ET.ParseError:
            # Fall through to regex-based tolerant parsing
            pass

        # Strategy 2: Regex-based tolerant parsing (for malformed XML)
        # Handle simple single-tag case: <tag>value</tag>
        simple_match = re.match(r"^<(\w+)>(.*?)</\1>$", xml_str, re.DOTALL)
        if simple_match:
            tag_name, content = simple_match.groups()
            content = content.strip()

            # If content has no child tags, it's a simple value
            if not re.search(r"<\w+>", content):
                return self._convert_text_to_typed_value(content)

            # Otherwise parse as complex structure
            return self._convert_xml_structure_to_python(content, parent_tag=tag_name)

        # Handle multiple root elements or complex structure
        return self._convert_xml_structure_to_python(xml_str)

    def _convert_xml_structure_to_python(self, xml_content: str, parent_tag: str | None = None) -> Any:
        """Parse XML content that may contain multiple child elements."""
        import re

        # Find all child elements
        child_matches = re.findall(r"<(\w+)>(.*?)</\1>", xml_content, re.DOTALL)

        if not child_matches:
            # No child elements, return as plain text
            return self._convert_text_to_typed_value(xml_content.strip())

        # Group by tag name to detect lists
        tag_groups = {}
        for tag_name, tag_content in child_matches:
            if tag_name not in tag_groups:
                tag_groups[tag_name] = []
            tag_groups[tag_name].append(tag_content.strip())

        # Convert to appropriate Python structure
        if len(tag_groups) == 1:
            # Single tag type - could be a list
            tag_name, values = next(iter(tag_groups.items()))
            if len(values) > 1:
                # Multiple instances → list
                return [self._convert_xml_to_python_object(f"<{tag_name}>{v}</{tag_name}>") for v in values]
            else:
                # Single instance → parse the content
                parsed_value = self._convert_xml_to_python_object(f"<{tag_name}>{values[0]}</{tag_name}>")
                # Special case: if parent tag is plural (like "todos") and child is singular (like "todo"),
                # wrap single items in a list to maintain consistency
                if parent_tag and parent_tag.endswith("s") and not tag_name.endswith("s"):
                    return [parsed_value]
                return parsed_value
        else:
            # Multiple tag types → dict
            result = {}
            for tag_name, values in tag_groups.items():
                if len(values) > 1:
                    # Multiple values → list
                    result[tag_name] = [self._convert_xml_to_python_object(f"<{tag_name}>{v}</{tag_name}>") for v in values]
                else:
                    # Single value → parse directly
                    result[tag_name] = self._convert_xml_to_python_object(f"<{tag_name}>{values[0]}</{tag_name}>")
            return result

    def _convert_text_to_typed_value(self, text: str) -> Any:
        """Coerce plain text to appropriate Python type."""
        if not text:
            return None

        text = text.strip()

        # Boolean values
        if text.lower() in ("true", "false"):
            return text.lower() == "true"

        # Integer values
        try:
            if "." not in text and text.lstrip("-").isdigit():
                return int(text)
        except ValueError:
            pass

        # Float values
        try:
            if "." in text:
                return float(text)
        except ValueError:
            pass

        # Default to string
        return text

    # ============================================================================
    # RESULT CREATION METHODS
    # ============================================================================

    def _create_unknown_function_error(self, function_name: str) -> dict[str, Any]:
        """Create error result for unknown function."""
        return {
            "type": "unknown",
            "target": function_name or "unknown",
            "result": f"Unknown function: {function_name}",
            "success": False,
        }

    def _create_execution_error(self, tool_call: dict[str, Any], error: Exception) -> dict[str, Any]:
        """Create error result for execution failure."""
        return {
            "type": "error",
            "target": tool_call.get("function", "unknown"),
            "result": f"Error executing tool call: {str(error)}",
            "success": False,
        }

    def _handle_target_based_call(self, function_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Fault-tolerant fallback for malformed structured (JSON) tool calls.

        This method handles cases where the LLM generates simple function names
        instead of properly formatted XML function calls. It uses the target-based
        approach to parse and execute tool calls by looking up the target in
        available workflows, resources, and agents.

        Args:
            function_name: The function name from the tool call (may be malformed)
            arguments: The arguments containing target, method, etc.

        Returns:
            Tool call result dictionary with success/error status
        """
        # Extract target-based parameters
        target = arguments.get("target")
        method = arguments.get("method", "execute")

        # Handle both nested and flat parameter structures:
        # - Nested: arguments = {"target": "x", "method": "y", "arguments": {"param1": "value1"}}
        # - Flat:   arguments = {"target": "x", "method": "y", "param1": "value1"}
        params = arguments.get("arguments", {})
        if not params:
            # Extract all non-reserved keys as parameters (flat structure from XML parsing)
            params = {k: v for k, v in arguments.items() if k not in ["target", "method"]}

        # Try to find target in available objects
        try:
            # Check workflows first
            for workflow in self._agent.available_workflows:
                if workflow.workflow_id == target or workflow.object_id == target:
                    workflow_args = {"workflow_id": target, "method": method, "parameters": params}
                    return self.execute_workflow_call(workflow_args)

            # Check resources
            for resource in self._agent.available_resources:
                if resource.resource_id == target or resource.object_id == target:
                    resource_args = {"resource_id": target, "method": method, "parameters": params}
                    return self.execute_resource_call(resource_args)

            # Check agents (requires registry lookup)
            self._agent.ensure_registered()
            registry = self._agent._registry
            if registry and target in registry._items:
                agent_args = {"object_id": target, "message": params.get("message", "")}
                return self.execute_agent_call(agent_args)

            # Target not found in any registry
            available_targets = []
            for workflow in self._agent.available_workflows:
                available_targets.append(f"workflow:{workflow.workflow_id}")
            for resource in self._agent.available_resources:
                available_targets.append(f"resource:{resource.resource_id}")

            return self._create_tool_error(
                "target_not_found",
                target or "unknown",
                f"Target '{target}' not found in any registry. Available targets: {', '.join(available_targets[:5])}{'...' if len(available_targets) > 5 else ''}",
            )

        except Exception as e:
            return self._create_tool_error("parsing", target or "unknown", f"Fault-tolerant parsing failed: {str(e)}")


class CodecToolCaller(WARCaller):
    def __init__(self, agent: STARAgent, codec: type[AbstractCodec]):
        super().__init__(agent, self)
        self._agent = agent
        self._codec = codec

    @observable
    def parse_llm_response(self, llm_response: LLMResponse) -> tuple[str | None, str | None, list[DictParams]]:
        """
        Parse LLM response using codec-based format.
        """
        return self.parse_llm_response_symbolic(llm_response)

    @observable
    def parse_llm_response_symbolic(self, llm_response: LLMResponse) -> tuple[str | None, str | None, list[DictParams]]:
        """
        Parse LLM response using codec-based format.

        Handles codec format with <thinking> and <function_call> blocks.
        Falls back to parent implementation for old formats.

        Args:
            llm_response: The LLM response object containing content and tool calls

        Returns:
            Tuple of (response_text, response_reasoning, tool_calls_list)
        """
        if not llm_response:
            return None, None, []

        # Work with a copy to avoid mutating the input
        content = llm_response.content.strip()
        try:
            return self._parse_codec_response(llm_response, content)
        except Exception as _:
            return content, None, []

    def _parse_codec_response(self, llm_response: LLMResponse, content: str) -> tuple[str | None, str | None, list[DictParams]]:
        """
        Parse codec-based response format using codec's parse_response method.

        Uses self._codec.parse_response() to parse the content and converts
        the result to the expected format.

        Args:
            llm_response: The LLM response object
            content: The response content string

        Returns:
            Tuple of (response_text, response_reasoning, tool_calls_list)
        """
        # Handle structured tool calls from LLM providers first
        result_tool_calls = []
        if llm_response.tool_calls:
            if len(llm_response.tool_calls) == 1 and llm_response.tool_calls[0].function.name == "<|constrain|>response":
                # Response passed as tool call (openai/gpt-oss-20b)
                content = llm_response.tool_calls[0].function.arguments
                if content:
                    content = content.strip()
            else:
                # Structured (JSON) tool calls
                result_tool_calls.extend(self._to_tool_call_dicts(llm_response.tool_calls))

        # Parse using codec's parse_response method
        parsed_response = self._codec.parse_response(content)

        # Extract thinking as reasoning
        response_reasoning = parsed_response.thinking if parsed_response.thinking else None
        response_text = parsed_response.response if parsed_response.response else None

        if response_reasoning and not (parsed_response.tool_calls or response_text):
            suggestion_message = f"[Error] invalid format, please follow the following instruction.\n{self._codec.get_instruction()}"
            return "No response generated", suggestion_message, []

        if not (response_reasoning or response_text or parsed_response.tool_calls):
            # If no xml tags parsed, likely there is a direct answer
            return llm_response.content, None, []

        if not response_reasoning:
            print(f"Response reasoning: {response_reasoning}")

        # Convert tool calls to DictParams format
        if parsed_response.tool_calls:
            for tool_call in parsed_response.tool_calls:
                function_name = f"{tool_call.class_name}:{tool_call.name}"
                result_tool_calls.append({"function": function_name, "arguments": tool_call.parameters})
            return "No response generated", response_reasoning, result_tool_calls
        else:
            return response_text, response_reasoning, result_tool_calls

    def _to_tool_call_dicts(self, llm_tool_calls: list) -> list[DictParams]:
        """Convert structured function calls to our internal format."""
        tool_call_dicts = []

        for llm_tool_call in llm_tool_calls:
            try:
                function_name = llm_tool_call.function.name
                arguments = llm_tool_call.function.arguments

                # Non-string arguments (already parsed) - use outer function name
                tool_call_dicts.append({"function": function_name, "arguments": arguments})

            except Exception:
                continue

        return tool_call_dicts

    @observable
    def execute_tool_calls(self, parsed_tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self._execute_single_call(call) for call in parsed_tool_calls]

    async def async_execute_tool_calls(self, parsed_tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute tool calls with native async support and parallel execution."""
        return list(await asyncio.gather(*[self._execute_single_call_async(call) for call in parsed_tool_calls]))

    async def _execute_single_call_async(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        """Async version of _execute_single_call with native await for async methods."""
        function_name = tool_call.get("function", "")
        arguments = tool_call.get("arguments", {})
        if ":" not in function_name:
            return self._create_tool_error("codec_format", function_name, "Expected ClassName:methodName format")

        parts = function_name.split(":", 1)
        identifier = parts[0]
        method_name = parts[1]

        # Try object_id lookup first, then fallback to class_name lookup
        obj_info = self._find_object_by_id(identifier)
        if not obj_info:
            obj_info = self._find_object_by_class_name(identifier)

        if not obj_info:
            available_classes = self._get_available_class_names()
            return self._create_tool_error(
                "class_not_found",
                identifier,
                f"Object '{identifier}' not found by object_id or class_name in available agents/resources/workflows. "
                f"Available classes: {', '.join(available_classes[:10])}{'...' if len(available_classes) > 10 else ''}",
            )

        # Method signature validation and conversion to the expected type
        if hasattr(obj_info["object"], method_name):
            method = getattr(obj_info["object"], method_name)
            arguments = self._validate_n_cast_method_arguments(method, arguments)

            try:
                # Set session_id for EventLog if it exists
                if obj_info["type"] == "agent":
                    if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                        session_id = self._agent._event_log._current_session_id
                        if session_id is not None:
                            arguments["session_id"] = session_id
                # Native async execution instead of Misc.safe_asyncio_run
                if asyncio.iscoroutinefunction(method):
                    result = await method(**arguments)
                else:
                    result = method(**arguments)
                return self._create_tool_success(obj_info["type"], f"{identifier}.{method_name}", result)
            except Exception as e:
                return self._create_tool_error(
                    "execution_error",
                    f"{identifier}.{method_name}",
                    f"Error executing call {identifier}.{method_name}: {str(e)}\n{traceback.format_exc()}",
                )
        else:
            return self._create_tool_error(
                "method_not_found",
                f"{identifier}.{method_name}",
                f"Method '{method_name}' not found in object '{identifier}'\n{traceback.format_exc()}",
            )

    def _validate_n_cast_method_arguments(self, method: Callable, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate the arguments of a method."""
        import json
        import types
        from typing import Any as TypingAny
        from typing import Union, get_origin

        signature = Misc.parse_method_signature(method)
        for param in signature.parameters:
            if param.type_object and param.name in arguments:
                # Skip validation for typing.Any - accept any value as-is
                if param.type_object is TypingAny:
                    continue

                # Get origin for generic types (e.g., List[int] -> list)
                origin = get_origin(param.type_object)
                if origin is None:
                    origin = param.type_object

                # Extract types from Union/Optional (handles __args__)
                # Support both typing.Union and types.UnionType (Python 3.10+)
                is_union_type = hasattr(param.type_object, "__args__") and (origin is Union or origin is types.UnionType)
                if is_union_type:
                    # For Union/Optional types, iterate through args
                    hinted_types = param.type_object.__args__
                else:
                    # For non-Union types (including List, Dict), use origin
                    hinted_types = [origin]

                # Process each type in the union or the single type
                for _type in hinted_types:
                    # Skip NoneType in Optional types
                    if _type is type(None):
                        continue

                    # Skip typing.Any in Union types
                    if _type is TypingAny:
                        break

                    # Get origin for this type (handles nested generics)
                    type_origin = get_origin(_type)
                    if type_origin is None:
                        type_origin = _type

                    # Type short-circuit: if already correct type
                    # Skip isinstance check for typing.Any
                    if type_origin is not TypingAny and isinstance(arguments[param.name], type_origin):
                        break

                    # Handle primitive types (str, int, float)
                    if type_origin in (str, int, float):
                        try:
                            arguments[param.name] = type_origin(arguments[param.name])
                            break
                        except Exception:
                            continue

                    # Handle bool with safe string conversion
                    elif type_origin is bool:
                        val = arguments[param.name]
                        if isinstance(val, bool):
                            break
                        elif isinstance(val, str):
                            arguments[param.name] = val.lower() in (
                                "true",
                                "1",
                                "yes",
                                "on",
                            )
                            break
                        else:
                            try:
                                arguments[param.name] = bool(val)
                                break
                            except Exception:
                                continue

                    # Handle list with safe JSON parsing
                    elif type_origin is list:
                        val = arguments[param.name]
                        if isinstance(val, list):
                            break
                        elif isinstance(val, str):
                            try:
                                parsed = json.loads(val)
                                if isinstance(parsed, list):
                                    arguments[param.name] = parsed
                                    break
                            except (json.JSONDecodeError, ValueError):
                                continue
                        else:
                            continue

                    # Handle dict with safe JSON parsing
                    elif type_origin is dict:
                        val = arguments[param.name]
                        if isinstance(val, dict):
                            break
                        elif isinstance(val, str):
                            try:
                                parsed = json.loads(val)
                                if isinstance(parsed, dict):
                                    arguments[param.name] = parsed
                                    break
                            except (json.JSONDecodeError, ValueError):
                                continue
                        else:
                            continue

                    # Handle Pydantic BaseModel with safe issubclass check
                    elif isinstance(_type, type) and issubclass(_type, BaseModel):
                        val = arguments[param.name]
                        if isinstance(val, _type):
                            break
                        elif isinstance(val, str):
                            try:
                                arguments[param.name] = _type.model_validate_json(val)
                                break
                            except Exception:
                                continue

        return arguments

    @observable
    def _execute_single_call(self, tool_call: dict[str, Any]) -> dict[str, Any]:
        function_name = tool_call.get("function", "")
        arguments = tool_call.get("arguments", {})
        if ":" not in function_name:
            return self._create_tool_error("codec_format", function_name, "Expected ClassName:methodName format")

        parts = function_name.split(":", 1)
        identifier = parts[0]
        method_name = parts[1]

        # Try object_id lookup first, then fallback to class_name lookup
        obj_info = self._find_object_by_id(identifier)
        if not obj_info:
            obj_info = self._find_object_by_class_name(identifier)

        if not obj_info:
            available_classes = self._get_available_class_names()
            return self._create_tool_error(
                "class_not_found",
                identifier,
                f"Object '{identifier}' not found by object_id or class_name in available agents/resources/workflows. "
                f"Available classes: {', '.join(available_classes[:10])}{'...' if len(available_classes) > 10 else ''}",
            )

        # Method signature validation and conversion to the expected type
        if hasattr(obj_info["object"], method_name):
            method = getattr(obj_info["object"], method_name)
            arguments = self._validate_n_cast_method_arguments(method, arguments)

            try:
                # Set session_id for EventLog if it exists
                if obj_info["type"] == "agent":
                    if hasattr(self._agent, "_event_log") and self._agent._event_log is not None:
                        session_id = self._agent._event_log._current_session_id
                        if session_id is not None:
                            arguments["session_id"] = session_id
                if asyncio.iscoroutinefunction(method):
                    result = Misc.safe_asyncio_run(method, **arguments)
                else:
                    result = method(**arguments)
                return self._create_tool_success(obj_info["type"], f"{identifier}.{method_name}", result)
            except Exception as e:
                return self._create_tool_error(
                    "execution_error",
                    f"{identifier}.{method_name}",
                    f"Error executing call {identifier}.{method_name}: {str(e)}\n{traceback.format_exc()}",
                )
        else:
            return self._create_tool_error(
                "method_not_found",
                f"{identifier}.{method_name}",
                f"Method '{method_name}' not found in object '{identifier}'\n{traceback.format_exc()}",
            )

    def _find_object_by_id(self, object_id: str) -> dict[str, Any] | None:
        """
        Find an object by its object_id in available agents, resources, and workflows.

        Args:
            object_id: The object_id to search for

        Returns:
            Dictionary with "type" and "object" keys, or None if not found
        """
        # Search in resources (check both object_id and resource_id)
        for resource in self._agent.available_resources:
            if (hasattr(resource, "object_id") and resource.object_id == object_id) or (
                hasattr(resource, "resource_id") and resource.resource_id == object_id
            ):
                return {"type": "resource", "object": resource}

        # Search in workflows (check both object_id and workflow_id)
        for workflow in self._agent.available_workflows:
            if (hasattr(workflow, "object_id") and workflow.object_id == object_id) or (
                hasattr(workflow, "workflow_id") and workflow.workflow_id == object_id
            ):
                return {"type": "workflow", "object": workflow}

        # Search in agents (check object_id via registry)
        self._agent.ensure_registered()
        registry = self._agent._registry
        if registry and object_id in registry._items:
            agent = registry.get(object_id)
            if agent:
                return {"type": "agent", "object": agent}

        return None

    def _find_object_by_class_name(self, class_name: str) -> dict[str, Any] | None:
        """
        Find an object by its class name in available agents, resources, and workflows.

        Note: This matches the first occurrence found. If multiple objects of the
        same class exist, only the first one will be matched, which may cause issues.

        Args:
            class_name: The class name to search for (__class__.__name__)

        Returns:
            Dictionary with "type" and "object" keys, or None if not found
        """
        # Search in agents
        for agent in self._agent.available_agents:
            if agent.__class__.__name__ == class_name:
                return {"type": "agent", "object": agent}

        # Search in resources
        for resource in self._agent.available_resources:
            if resource.__class__.__name__ == class_name:
                return {"type": "resource", "object": resource}

        # Search in workflows
        for workflow in self._agent.available_workflows:
            if workflow.__class__.__name__ == class_name:
                return {"type": "workflow", "object": workflow}

        return None

    def _get_available_class_names(self) -> list[str]:
        """Get list of available class names from all objects."""
        class_names = []
        for agent in self._agent.available_agents:
            class_names.append(agent.__class__.__name__)
        for resource in self._agent.available_resources:
            class_names.append(resource.__class__.__name__)
        for workflow in self._agent.available_workflows:
            class_names.append(workflow.__class__.__name__)
        return sorted(set(class_names))
