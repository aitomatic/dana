"""
XML Response Parsing Utilities for Agent Tool Calls

This module provides utilities for parsing XML responses from LLMs
and extracting tool calls in a structured format.
"""

from typing import Any
import xml.etree.ElementTree as ET


def parse_xml_tool_calls(xml_content: str) -> tuple[str, list[dict[str, Any]]]:
    """
    Parse XML response and extract text content and tool calls.
    Handles both single response blocks and multiple response blocks.

    Args:
        xml_content: XML string to parse

    Returns:
        Tuple of (text_content, parsed_tool_calls)
    """
    try:
        # First try to parse as single response
        try:
            root = ET.fromstring(xml_content)
            if root.tag == "response":
                return _parse_single_response(root)
        except ET.ParseError:
            pass

        # If that fails, try to parse multiple response blocks
        # Split by </response> and parse each block
        response_blocks = []
        current_block = ""
        in_response = False

        for line in xml_content.split("\n"):
            if "<response>" in line:
                in_response = True
                current_block = line
            elif "</response>" in line and in_response:
                current_block += "\n" + line
                response_blocks.append(current_block)
                current_block = ""
                in_response = False
            elif in_response:
                current_block += "\n" + line

        if response_blocks:
            all_text_content = []
            all_tool_calls = []

            for block in response_blocks:
                try:
                    root = ET.fromstring(block)
                    if root.tag == "response":
                        text_content, tool_calls = _parse_single_response(root)
                        if text_content:
                            all_text_content.append(text_content)
                        all_tool_calls.extend(tool_calls)
                except ET.ParseError:
                    continue

            return "\n".join(all_text_content), all_tool_calls

        # If no response blocks found, return original content
        return xml_content, []

    except Exception:
        # Not valid XML, return original content
        return xml_content, []


def _parse_single_response(root) -> tuple[str, list[dict[str, Any]]]:
    """Parse a single response element and extract text content and tool calls."""
    # Extract text content
    text_elem = root.find("text")
    text_content = text_elem.text if text_elem is not None and text_elem.text else ""

    # Extract tool calls
    tool_calls = []
    tool_calls_elem = root.find("tool_calls")
    if tool_calls_elem is not None:
        for tool_call in tool_calls_elem:
            try:
                function_elem = tool_call.find("function")
                arguments_elem = tool_call.find("arguments")

                if function_elem is not None and arguments_elem is not None:
                    function_name = function_elem.text
                    if not function_name:
                        continue

                    # Parse arguments based on function type
                    args = {}
                    if function_name == "call_agent":
                        object_id_elem = arguments_elem.find("object_id")
                        message_elem = arguments_elem.find("message")
                        if object_id_elem is not None and message_elem is not None:
                            args["object_id"] = object_id_elem.text or ""
                            args["message"] = message_elem.text or ""

                    elif function_name == "call_resource":
                        resource_id_elem = arguments_elem.find("resource_id")
                        method_elem = arguments_elem.find("method")
                        parameters_elem = arguments_elem.find("parameters")

                        if resource_id_elem is not None and method_elem is not None:
                            args["resource_id"] = resource_id_elem.text or ""
                            args["method"] = method_elem.text or ""

                            # Parse parameters
                            if parameters_elem is not None:
                                params = {}
                                for param in parameters_elem:
                                    if param.text is not None:
                                        params[param.tag] = param.text
                                args["parameters"] = params
                            else:
                                args["parameters"] = {}

                    if args:  # Only add if we have valid arguments
                        tool_calls.append({"function": function_name, "arguments": args})

            except Exception:
                # Skip malformed tool calls
                continue

    return text_content, tool_calls


def has_xml_tool_calls(xml_content: str) -> bool:
    """
    Check if XML content contains tool calls.
    Handles both single response blocks and multiple response blocks.

    Args:
        xml_content: XML string to check

    Returns:
        True if XML contains tool calls
    """
    try:
        # First try to parse as single response
        try:
            root = ET.fromstring(xml_content)
            if root.tag == "response":
                tool_calls_elem = root.find("tool_calls")
                if tool_calls_elem is not None and len(tool_calls_elem) > 0:
                    return True
        except ET.ParseError:
            pass

        # If that fails, try to parse multiple response blocks
        # Split by </response> and check each block
        response_blocks = []
        current_block = ""
        in_response = False

        for line in xml_content.split("\n"):
            if "<response>" in line:
                in_response = True
                current_block = line
            elif "</response>" in line and in_response:
                current_block += "\n" + line
                response_blocks.append(current_block)
                current_block = ""
                in_response = False
            elif in_response:
                current_block += "\n" + line

        if response_blocks:
            for block in response_blocks:
                try:
                    root = ET.fromstring(block)
                    if root.tag == "response":
                        tool_calls_elem = root.find("tool_calls")
                        if tool_calls_elem is not None and len(tool_calls_elem) > 0:
                            return True
                except ET.ParseError:
                    continue

        return False
    except Exception:
        return False


def has_xml_response_format(xml_content: str) -> bool:
    """
    Check if content is in XML response format (regardless of tool calls).

    Args:
        xml_content: XML string to check

    Returns:
        True if content is in XML response format
    """
    try:
        root = ET.fromstring(xml_content)
        return root.tag == "response"
    except ET.ParseError:
        return False
