"""
ToolCaller: Handles tool call execution and orchestration.

This component provides functionality for:
- Tool call execution (agents, resources, workflows)
- Tool call result processing
- Tool call error handling
"""

import asyncio
import json
import re
from typing import TYPE_CHECKING, Any

from adana.common.llm.debug_logger import get_debug_logger
from adana.common.llm.types import LLMResponse
from adana.common.observable import observable
from adana.common.protocols import DictParams


if TYPE_CHECKING:
    from adana.core.agent.star_agent import STARAgent


class WARCaller:
    """Unified caller for Workflows, Agents, and Resources with consistent behavior."""

    def __init__(self, agent: "STARAgent", tool_caller=None):
        """Initialize with agent reference."""
        self._agent = agent
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

    def __init__(self, agent: "STARAgent"):
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
        """Execute a single tool call with error handling."""
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
                else:
                    return self._create_unknown_function_error(function_name or "unknown")

        except Exception as e:
            return self._create_execution_error(tool_call, e)

    # ============================================================================
    # LLM RESPONSE PARSING
    # ============================================================================

    @observable
    def parse_llm_response(self, llm_response: LLMResponse) -> tuple[str | None, str | None, list[DictParams]]:
        """
        Parse LLM response into response text and tool calls.

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

    def _extract_tool_calls_from_xml(self, tool_calls_xml: str) -> list[DictParams]:
        """
        Parse XML tool calls into dictionary format.

        Args:
            tool_calls_xml: XML string containing tool calls

        Returns:
            List of tool call dictionaries
        """
        if not tool_calls_xml or not tool_calls_xml.strip():
            return []

        tool_calls = []

        try:
            # Find all tool_call elements using regex (since we need to handle multiple)
            matches = re.findall(r"<tool_call>(.*?)</tool_call>", tool_calls_xml, re.DOTALL)

            if not matches:
                # Try tolerant parsing for unbalanced tags
                tool_call_content = self._extract_content_between_xml_tags(tool_calls_xml, "tool_call")
                if tool_call_content:
                    matches = [tool_call_content]

            for tool_call_content in matches:
                # Extract target (function name) - handle self-closing tags
                target_match = re.search(r"<target\s+([^>]+)/?>", tool_call_content)
                if not target_match:
                    continue
                function_name = target_match.group(1).strip()

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

                    # If no balanced arguments found, try tolerant parsing
                    if not arg_matches:
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

    def _convert_xml_to_python_object(self, xml_str: str, parent_tag: str | None = None) -> Any:
        """
        Parse XML string to Python objects using smart conventions:

        1. Repeated tags → list
        2. Tags with children → dict
        3. Tags with only text → string (with type coercion)
        4. Empty tags → None
        """
        import re

        xml_str = xml_str.strip()

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
        params = arguments.get("arguments", {})

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
