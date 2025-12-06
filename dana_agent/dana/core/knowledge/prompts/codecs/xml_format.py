import re
from typing import Any, override

from dana.common.schemas.tool_call import MethodSignature, ParameterInfo, ParsedCodecResponse, ToolCall
from dana.core.knowledge.prompts.codecs.abstract_codec import AbstractCodec


class CSXMLCodec(AbstractCodec):
    @classmethod
    def get_instruction(cls) -> str:
        return """
RESPONSE CONTRACT
PURPOSE: Enforce a clear separation between the assistant’s private reasoning
         and its user-visible output (answer or tool invocation).

── OUTPUT FORMAT ────────────────────────────────────────────
Each assistant reply MUST contain 1-3 XML blocks, in the order shown:
  1. <thinking>  ← MANDATORY, *internal* reasoning only
  2. <response>  ← optional, a direct answer (omit if tool call needed)
  3. <function_call> ← optional, external-tool invocation

<thinking>
/* PRIVATE — NOT SHOWN TO USER
   Brief analysis (≈ 50-150 words):
   • What does the user need?
   • Do I have enough info? → If no, specify the tool(s) required.
   • Planned answer approach or tool workflow.
   • Whether a user confirmation question is needed.
   END PRIVATE */
</thinking>

<!-- BRANCH A: DIRECT ANSWER (no tool call) -->
<response>
  <!-- Visible answer, clarification question, or next-step guidance. -->
</response>

<!-- BRANCH B: TOOL CALL (no <response>) -->
<function_call>
  <invoke name="ClassName:methodName">
    <parameter name="parameterName">value</parameter>
    <!-- Add more <parameter> tags as needed -->
  </invoke>
</function_call>

# RULES
• <thinking> is ALWAYS required; it contains only internal reasoning.
• Exactly one of <response> or <function_call> must appear.
• If <function_call> is present, ignore any <response>.
• Never output a tool call without a preceding <thinking>.
• If you have neither a tool call nor a direct answer, the <thinking> block’s user-visible section becomes the reply.
"""

    @classmethod
    @override
    def construct(cls, signature: MethodSignature) -> str:
        """
        Format a method signature into a Cursor XML format.
        """
        # Use object_id if available, fallback to class_name
        identifier = signature.object_id or signature.class_name
        return "\n".join(
            [
                f"### {identifier}:{signature.name}",
                f"Description: {signature.description}",
                "Parameters:",
                cls._parameters_to_str(signature.parameters),
                "Usage:",
                cls._usage_example(signature, identifier),
            ]
        )

    @classmethod
    def _parameters_to_str(cls, parameters: list[ParameterInfo]) -> str:
        text = ""
        for parameter in parameters:
            required = "(required)" if not parameter.has_default else ""
            text += f"- {parameter.name}: {required} {parameter.description}\n"
        return text

    @classmethod
    def _usage_example(cls, signature: MethodSignature, identifier: str | None = None) -> str:
        # Use provided identifier or fallback to class_name
        if identifier is None:
            identifier = signature.object_id or signature.class_name
        text = ""
        text += f'<invoke name="{identifier}:{signature.name}">\n'
        for parameter in signature.parameters:
            text += f'<parameter name="{parameter.name}">{parameter.example if parameter.example else parameter.description}</parameter>\n'
        text += "</invoke>"
        return f"<function_call>\n{text}\n</function_call>"

    @classmethod
    @override
    def parse_method_call(cls, xml_string: str) -> ToolCall:
        """
        Parse XML method call string back into a ToolCall object.

        Args:
            xml_string: XML string in format: <function_call><invoke name="Class:method">...</invoke></function_call>

        Returns:
            ToolCall object with class_name, name, and parameters
        """
        # Extract identifier and method_name from <invoke name="identifier:methodName">
        # identifier can be object_id or class_name
        invoke_match = re.search(r'<invoke\s+name=["\']([^"\']+):([^"\']+)["\']', xml_string)
        if not invoke_match:
            raise ValueError('Could not find <invoke name="identifier:methodName"> in XML string')

        identifier = invoke_match.group(1)
        method_name = invoke_match.group(2)
        # Store in both object_id and class_name for compatibility
        class_name = identifier

        # Extract inner content between <invoke> tags
        invoke_content_match = re.search(r'<invoke\s+name=["\'][^"\']+["\']>(.*?)</invoke>', xml_string, re.DOTALL)
        if not invoke_content_match:
            # Try without closing tag (fallback)
            invoke_content_match = re.search(r'<invoke\s+name=["\'][^"\']+["\']>(.*)', xml_string, re.DOTALL)
            if not invoke_content_match:
                return ToolCall(class_name=class_name, object_id=identifier, name=method_name, parameters={})
            invoke_content = invoke_content_match.group(1)
        else:
            invoke_content = invoke_content_match.group(1)

        # Parse parameters using regex approach (primary)
        parameters = cls._parse_parameters_from_xml(xml_string, invoke_content)

        return ToolCall(class_name=class_name, object_id=identifier, name=method_name, parameters=parameters)

    @classmethod
    def _parse_parameters_from_xml(cls, xml_string: str, content: str) -> dict[str, Any]:
        """Parse parameters from XML content using regex-based approach."""
        parameters = {}

        # Primary approach: extract <parameter name="param">value</parameter>
        param_pattern = r'<parameter\s+name=["\']([^"\']+)["\'][^>]*>(.*?)</parameter>'
        matches = list(re.finditer(param_pattern, content, re.DOTALL))
        captured_params = set()

        for match in matches:
            param_name = match.group(1)
            param_value = match.group(2).strip()
            parameters[param_name] = param_value
            captured_params.add(param_name)

        # Fallback: handle missing closing tags for parameters not captured by primary approach
        fallback_params = cls._parse_parameters_without_closing_tags(content, captured_params)
        parameters.update(fallback_params)

        return parameters

    @classmethod
    def _parse_parameters_without_closing_tags(cls, content: str, captured_params: set[str] | None = None) -> dict[str, Any]:
        """Parse parameters from XML content that may be missing closing tags."""
        if captured_params is None:
            captured_params = set()

        parameters = {}

        # Find all parameter opening tags
        param_open_pattern = r'<parameter\s+name=["\']([^"\']+)["\'][^>]*>'
        matches = list(re.finditer(param_open_pattern, content))

        param_positions = []
        for match in matches:
            param_name = match.group(1)
            # Skip if already captured by primary approach
            if param_name in captured_params:
                continue
            start_pos = match.end()
            param_positions.append((param_name, start_pos))

        # Extract values between opening tags
        for i, (param_name, start_pos) in enumerate(param_positions):
            if i + 1 < len(param_positions):
                # Find the start of the next parameter tag
                next_param_match = re.search(r"<parameter", content[start_pos:])
                if next_param_match:
                    end_pos = start_pos + next_param_match.start()
                else:
                    end_pos = len(content)
                value = content[start_pos:end_pos].strip()
            else:
                # Last parameter - get everything after it
                value = content[start_pos:].strip()

            parameters[param_name] = value

        return parameters

    @classmethod
    def parse_response(cls, xml_string: str) -> ParsedCodecResponse:
        """
        Parse XML response string with thinking and multiple tool calls.

        Args:
            xml_string: XML string containing <thinking> and <function_call> blocks

        Returns:
            ParsedCodecResponse with thinking content and list of tool calls
        """
        # Extract thinking block if it exists
        thinking_match = re.search(r"<thinking>(.*?)</thinking>", xml_string, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove XML comments from thinking
            thinking = re.sub(r"<!--.*?-->", "", thinking, flags=re.DOTALL).strip()
        else:
            # No <thinking> tag - extract everything before the first tool call as thinking
            first_function_call_match = re.search(r"<function_call>", xml_string)
            if first_function_call_match:
                thinking = xml_string[: first_function_call_match.start()].strip()
                # Remove XML comments from thinking
                if thinking:
                    thinking = re.sub(r"<!--.*?-->", "", thinking, flags=re.DOTALL).strip()
            else:
                thinking = ""

        # Extract all function_call blocks
        function_call_pattern = r"<function_call>(.*?)</function_call>"
        function_call_matches = re.finditer(function_call_pattern, xml_string, re.DOTALL)

        tool_calls = []
        for match in function_call_matches:
            function_call_content = match.group(1)  # Get the inner content of <function_call>
            # Find all <invoke>...</invoke> blocks inside this function_call
            invoke_pattern = r"<invoke\s+name=[\"'][^\"']+:[^\"']+[\"'][^>]*>.*?</invoke>"
            invoke_matches = re.finditer(invoke_pattern, function_call_content, re.DOTALL)

            for invoke_match in invoke_matches:
                invoke_xml = invoke_match.group(0)
                try:
                    tool_call = cls.parse_method_call(invoke_xml)
                    tool_calls.append(tool_call)
                except ValueError:
                    # Skip malformed invoke blocks gracefully
                    continue

        # Extract response tag if it exists
        response_match = re.search(r"<response>(.*?)</response>", xml_string, re.DOTALL)
        response = None
        if response_match:
            response = response_match.group(1).strip()
            # Remove XML comments from response
            response = re.sub(r"<!--.*?-->", "", response, flags=re.DOTALL).strip()

        # Fallback: if thinking is still empty, extract remaining content after removing function_call and response blocks
        if not thinking:
            # Remove all function_call blocks from xml_string
            remaining_content = re.sub(r"<function_call>.*?</function_call>", "", xml_string, flags=re.DOTALL)
            # Remove all response blocks from xml_string
            remaining_content = re.sub(r"<response>.*?</response>", "", remaining_content, flags=re.DOTALL)
            # Remove XML comments and strip whitespace
            remaining_content = re.sub(r"<!--.*?-->", "", remaining_content, flags=re.DOTALL).strip()
            # Use remaining content as thinking if not empty
            if remaining_content:
                thinking = remaining_content

        # Priority: if tool_calls exist, ignore response
        if tool_calls:
            response = None
        # If only thinking exists (no response and no tool_calls), set response = thinking
        elif thinking and not response and not tool_calls:
            response = thinking

        return ParsedCodecResponse(thinking=thinking, tool_calls=tool_calls if tool_calls else None, response=response)


class KLXMLCodec(AbstractCodec):
    @classmethod
    def get_instruction(cls) -> str:
        return """
RESPONSE CONTRACT
PURPOSE: Enforce a clear separation between the assistant’s private reasoning
         and its user-visible output (answer or tool invocation).

── OUTPUT FORMAT ────────────────────────────────────────────
Each assistant reply MUST contain 1-3 XML blocks, in the order shown:
  1. <thinking>  ← MANDATORY, *internal* reasoning only
  2. <response>  ← optional, a direct answer (omit if tool call needed)
  3. <function_call> ← optional, external-tool invocation

<thinking>
/* PRIVATE — NOT SHOWN TO USER
   Brief analysis (≈ 50-150 words):
   • What does the user need?
   • Do I have enough info? → If no, specify the tool(s) required.
   • Planned answer approach or tool workflow.
   • Whether a user confirmation question is needed.
   END PRIVATE */
</thinking>

<!-- BRANCH A: DIRECT ANSWER (no tool call) -->
<response>
  <!-- Visible answer, clarification question, or next-step guidance. -->
</response>

<!-- BRANCH B — ONE OR MORE TOOL CALLS (omit <response>) -->
<ClassName:methodName>
  <param name="parameterName">value</param>
  <!-- Add additional <param> tags as needed -->
</ClassName:methodName>

<!-- Example of a second tool call, if required
<OtherClass:otherMethod>
  <param name="...">...</param>
</OtherClass:otherMethod> -->


# RULES
• <thinking> is ALWAYS required; it contains only internal reasoning.
• Exactly one of <response> or <function_call> must appear.
• If <function_call> is present, ignore any <response>.
• Never output a tool call without a preceding <thinking>.
• If you have neither a tool call nor a direct answer, the <thinking> block’s user-visible section becomes the reply.
"""

    @classmethod
    def _parameters_to_str(cls, parameters: list[ParameterInfo]) -> str:
        text = ""
        for parameter in parameters:
            required = "(required)" if not parameter.has_default else ""
            text += f"- {parameter.name}: {required} {parameter.description}\n"
        return text

    @classmethod
    def _usage_example(cls, signature: MethodSignature, identifier: str | None = None) -> str:
        # Use provided identifier or fallback to class_name
        if identifier is None:
            identifier = signature.object_id or signature.class_name
        text = ""
        text += f"<{identifier}:{signature.name}>\n"
        for parameter in signature.parameters:
            content = parameter.example if parameter.example else parameter.description
            if len(content) > 200:
                text += f"<{parameter.name}>\n{content}\n</{parameter.name}>\n"
            else:
                text += f"<{parameter.name}>{content}</{parameter.name}>\n"
        text += f"</{identifier}:{signature.name}>\n"
        return text

    @classmethod
    def construct(cls, signature: MethodSignature) -> str:
        """
        Format a method signature into a Kraken XML format.
        """
        # Use object_id if available, fallback to class_name
        identifier = signature.object_id or signature.class_name
        return "\n".join(
            [
                f"### {identifier}:{signature.name}",
                f"Description: {signature.description}",
                "Parameters:",
                cls._parameters_to_str(signature.parameters),
                "Usage:",
                cls._usage_example(signature, identifier),
            ]
        )

    @classmethod
    @override
    def parse_method_call(cls, xml_string: str) -> ToolCall:
        """
        Parse XML method call string back into a ToolCall object.

        Args:
            xml_string: XML string in format: <ClassName:methodName><param>value</param></ClassName:methodName>

        Returns:
            ToolCall object with class_name, name, and parameters
        """
        # Extract outer tag <identifier:methodName> to get identifier and method_name
        # identifier can be object_id or class_name
        outer_tag_match = re.search(r"<([^:>]+):([^>]+)>", xml_string)
        if not outer_tag_match:
            raise ValueError("Could not find <identifier:methodName> tag in XML string")

        identifier = outer_tag_match.group(1)
        method_name = outer_tag_match.group(2)
        # Store in both object_id and class_name for compatibility
        class_name = identifier

        # Extract inner content between opening and closing tags
        outer_tag_pattern = re.escape(f"<{class_name}:{method_name}>")
        closing_tag_pattern = re.escape(f"</{class_name}:{method_name}>")

        # Try to find content between tags
        content_match = re.search(f"{outer_tag_pattern}(.*?){closing_tag_pattern}", xml_string, re.DOTALL)
        if not content_match:
            # Try without closing tag (fallback)
            content_match = re.search(f"{outer_tag_pattern}(.*)", xml_string, re.DOTALL)
            if not content_match:
                return ToolCall(class_name=class_name, object_id=identifier, name=method_name, parameters={})
            content = content_match.group(1)
        else:
            content = content_match.group(1)

        # Parse parameters using regex approach (primary)
        parameters = cls._parse_parameters_from_xml(content)

        return ToolCall(class_name=class_name, object_id=identifier, name=method_name, parameters=parameters)

    @classmethod
    def _parse_parameters_from_xml(cls, content: str) -> dict[str, Any]:
        """Parse parameters from XML content using regex-based approach."""
        parameters = {}

        # Primary approach: extract <param>value</param>
        param_pattern = r"<([^>:]+)>(.*?)</\1>"
        matches = list(re.finditer(param_pattern, content, re.DOTALL))
        captured_tags = set()

        for match in matches:
            param_name = match.group(1)
            param_value = match.group(2).strip()
            parameters[param_name] = param_value
            captured_tags.add(param_name)

        # Fallback: handle missing closing tags for tags not captured by primary approach
        fallback_params = cls._parse_parameters_without_closing_tags(content, captured_tags)
        parameters.update(fallback_params)

        return parameters

    @classmethod
    def _parse_parameters_without_closing_tags(cls, content: str, captured_tags: set[str] | None = None) -> dict[str, Any]:
        """Parse parameters from XML content that may be missing closing tags."""
        if captured_tags is None:
            captured_tags = set()

        parameters = {}

        # Find all opening tags (not closing tags - those start with /)
        tag_pattern = r"<([^/>:]+)>"
        matches = list(re.finditer(tag_pattern, content))

        # Build list of tag positions
        tag_positions = []
        for match in matches:
            tag_name = match.group(1)
            # Skip if already captured by primary approach
            if tag_name in captured_tags:
                continue
            # Skip closing tags
            if tag_name.startswith("/"):
                continue
            start_pos = match.end()
            tag_positions.append((tag_name, start_pos))

        # Extract values between tags
        for i, (tag_name, start_pos) in enumerate(tag_positions):
            if i + 1 < len(tag_positions):
                # Find the start of the next opening tag
                next_tag_match = re.search(r"<[^/>]", content[start_pos:])
                if next_tag_match:
                    end_pos = start_pos + next_tag_match.start()
                else:
                    end_pos = len(content)
                value = content[start_pos:end_pos].strip()
            else:
                # Last tag - get everything after it
                value = content[start_pos:].strip()

            parameters[tag_name] = value

        return parameters

    @classmethod
    def parse_response(cls, xml_string: str) -> ParsedCodecResponse:
        """
        Parse XML response string with thinking and multiple tool calls.

        Args:
            xml_string: XML string containing <thinking> and <ClassName:methodName> blocks

        Returns:
            ParsedCodecResponse with thinking content and list of tool calls
        """
        # Extract thinking block if it exists
        thinking_match = re.search(r"<thinking>(.*?)</thinking>", xml_string, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove XML comments from thinking
            thinking = re.sub(r"<!--.*?-->", "", thinking, flags=re.DOTALL).strip()
        else:
            # No <thinking> tag - extract everything before the first tool call as thinking
            # Pattern to find first <ClassName:methodName> tag
            first_tool_call_match = re.search(r"<([^:>]+):([^>]+)>", xml_string)
            if first_tool_call_match:
                thinking = xml_string[: first_tool_call_match.start()].strip()
                # Remove XML comments from thinking
                if thinking:
                    thinking = re.sub(r"<!--.*?-->", "", thinking, flags=re.DOTALL).strip()
            else:
                thinking = ""

        # Extract all KLXML tool call blocks (<ClassName:methodName>...</ClassName:methodName>)
        # Pattern to match <ClassName:methodName>...</ClassName:methodName>
        tool_call_pattern = r"<([^:>]+):([^>]+)>(.*?)</\1:\2>"
        tool_call_matches = list(re.finditer(tool_call_pattern, xml_string, re.DOTALL))

        tool_calls = []
        for match in tool_call_matches:
            # Get the full tag with content: <ClassName:methodName>...</ClassName:methodName>
            full_match = match.group(0)
            tool_call = cls.parse_method_call(full_match)
            tool_calls.append(tool_call)

        # Extract response tag if it exists
        response_match = re.search(r"<response>(.*?)</response>", xml_string, re.DOTALL)
        response = None
        if response_match:
            response = response_match.group(1).strip()
            # Remove XML comments from response
            response = re.sub(r"<!--.*?-->", "", response, flags=re.DOTALL).strip()

        # Fallback: if thinking is still empty, extract remaining content after removing tool call and response blocks
        if not thinking:
            # Remove all tool call blocks (<ClassName:methodName>...</ClassName:methodName>) from xml_string
            remaining_content = re.sub(r"<([^:>]+):([^>]+)>.*?</\1:\2>", "", xml_string, flags=re.DOTALL)
            # Remove all response blocks from xml_string
            remaining_content = re.sub(r"<response>.*?</response>", "", remaining_content, flags=re.DOTALL)
            # Remove XML comments and strip whitespace
            remaining_content = re.sub(r"<!--.*?-->", "", remaining_content, flags=re.DOTALL).strip()
            # Use remaining content as thinking if not empty
            if remaining_content:
                thinking = remaining_content

        # Priority: if tool_calls exist, ignore response
        if tool_calls:
            response = None
        # If only thinking exists (no response and no tool_calls), set response = thinking
        elif thinking and not response and not tool_calls:
            response = thinking

        return ParsedCodecResponse(thinking=thinking, tool_calls=tool_calls if tool_calls else None, response=response)


if __name__ == "__main__":
    csxml_examples = [
        """
<thinking>
/* I have found key ontology nodes: "Monomer" (id:1), "Anion" (id:3), and several related to polymerization process ("Solvent", "SMValue", "Temperature", "ReactionTime", all in polymerization conditions). The "Anion" node's expert insight states: "Only monomers with the same anion are replaceable. Anion compatibility is critical for PAG monomer replacement." This directly supports the user's first request. For the second request, nodes for process parameters and their similarity criteria (e.g., SMValue ±0.5, Temperature ±10°C, Solvent must match) are present. Next, I need to explore the relationships between these nodes, especially how monomers are linked to anions, and how polymers are linked to process conditions and lot numbers. I will get connected nodes and edges for "Monomer", "Anion", and process-related nodes in parallel. */
</thinking>
<function_call>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">1</parameter>
  <parameter name="direction">both</parameter>
</invoke>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">3</parameter>
  <parameter name="direction">both</parameter>
</invoke>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">8</parameter>
  <parameter name="direction">both</parameter>
</invoke>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">10</parameter>
  <parameter name="direction">both</parameter>
</invoke>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">7</parameter>
  <parameter name="direction">both</parameter>
</invoke>
<invoke name="ontology:get_connected_nodes">
  <parameter name="node_id">12</parameter>
  <parameter name="direction">both</parameter>
</invoke>
</function_call>
""",
    ]

    for i, xml_string in enumerate(csxml_examples, 1):
        print(f"\nExample {i}:")
        print(xml_string)
        print("\nParsed result:")
        try:
            result = CSXMLCodec.parse_response(xml_string)
            print(result)
        except Exception as e:
            print(f"  ERROR: {e}")
