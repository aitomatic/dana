import re
from typing import Any, override

from dana.common.schemas.tool_call import MethodSignature, ParameterInfo, ToolCall, ParsedCodecResponse
from dana.core.knowledge.prompts.codecs.abstract_codec import AbstractCodec


class CSXMLCodec(AbstractCodec):

    @classmethod
    def get_instruction(cls) -> str:
        return """
RESPONSE CONTRACT
Output 1-2 blocks per message:

<thinking> (ALWAYS REQUIRED)
Brief analysis (50-150 words):
- What does the user need?
- Do I have sufficient information to answer?
- If yes: What's my answer approach?
- If no: What tool(s) do I need and why?
- Any user confirmation needed?

[Then include the actual response to user:]
Your complete answer, clarification question, or explanation of what tools you're about to call
</thinking>

<function_call>
  <invoke name="ClassName:methodName">
    <parameter name="parameterName">value</parameter>
  </invoke>
</function_call>

RULES:
- <thinking> is always required and contains both reasoning AND user-facing message
- <function_call> only appears when external tools are needed
- Never output function calls without thinking
"""

    @classmethod
    @override
    def construct(cls, signature: MethodSignature) -> str:
        """
        Format a method signature into a Cursor XML format.
        """
        return "\n".join(
            [
                f"### {signature.class_name}:{signature.name}",
                f"Description: {signature.description}",
                "Parameters:",
                cls._parameters_to_str(signature.parameters),
                "Usage:",
                cls._usage_example(signature)
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
    def _usage_example(cls, signature: MethodSignature) -> str:
        text = ""
        text += f"<invoke name=\"{signature.class_name}:{signature.name}\">\n"
        for parameter in signature.parameters:
            text += f"<parameter name=\"{parameter.name}\">{parameter.example if parameter.example else parameter.description}</parameter>\n"
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
        # Extract class_name and method_name from <invoke name="ClassName:methodName">
        invoke_match = re.search(r'<invoke\s+name=["\']([^"\']+):([^"\']+)["\']', xml_string)
        if not invoke_match:
            raise ValueError("Could not find <invoke name=\"ClassName:methodName\"> in XML string")
        
        class_name = invoke_match.group(1)
        method_name = invoke_match.group(2)
        
        # Extract inner content between <invoke> tags
        invoke_content_match = re.search(r'<invoke\s+name=["\'][^"\']+["\']>(.*?)</invoke>', xml_string, re.DOTALL)
        if not invoke_content_match:
            # Try without closing tag (fallback)
            invoke_content_match = re.search(r'<invoke\s+name=["\'][^"\']+["\']>(.*)', xml_string, re.DOTALL)
            if not invoke_content_match:
                return ToolCall(class_name=class_name, name=method_name, parameters={})
            invoke_content = invoke_content_match.group(1)
        else:
            invoke_content = invoke_content_match.group(1)
        
        # Parse parameters using regex approach (primary)
        parameters = cls._parse_parameters_from_xml(xml_string, invoke_content)
        
        return ToolCall(class_name=class_name, name=method_name, parameters=parameters)
    
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
                next_param_match = re.search(r'<parameter', content[start_pos:])
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
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', xml_string, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove XML comments from thinking
            thinking = re.sub(r'<!--.*?-->', '', thinking, flags=re.DOTALL).strip()
        else:
            # No <thinking> tag - extract everything before the first tool call as thinking
            first_function_call_match = re.search(r'<function_call>', xml_string)
            if first_function_call_match:
                thinking = xml_string[:first_function_call_match.start()].strip()
                # Remove XML comments from thinking
                if thinking:
                    thinking = re.sub(r'<!--.*?-->', '', thinking, flags=re.DOTALL).strip()
            else:
                thinking = ""
        
        # Extract all function_call blocks
        function_call_pattern = r'<function_call>(.*?)</function_call>'
        function_call_matches = re.finditer(function_call_pattern, xml_string, re.DOTALL)
        
        tool_calls = []
        for match in function_call_matches:
            function_call_content = match.group(0)  # Get the full <function_call>...</function_call>
            # Skip empty function_call blocks (no <invoke> tag inside)
            if not re.search(r'<invoke\s+name=["\']([^"\']+):([^"\']+)["\']', function_call_content):
                continue
            try:
                tool_call = cls.parse_method_call(function_call_content)
                tool_calls.append(tool_call)
            except ValueError:
                # Skip malformed function_call blocks gracefully
                continue
        
        return ParsedCodecResponse(
            thinking=thinking,
            tool_calls=tool_calls if tool_calls else None
        )

class KLXMLCodec(AbstractCodec):

    @classmethod
    def get_instruction(cls) -> str:
        return """
RESPONSE CONTRACT
Output exactly TWO XML blocks per message:

<thinking>
Intent: [What user wants]
Context: [Current state/findings] 
Decision: [Tool choice + why]
Approval: [If needed, what requires confirmation]
User Message: [What the user needs to understand - acknowledge their request, explain findings in their context, address their concerns]
</thinking>

<tool_name>
  <param>value</param>
</tool_name>
<tool_name>
  <param>value</param>
</tool_name>
"""


    @classmethod
    def _parameters_to_str(cls, parameters: list[ParameterInfo]) -> str:
        text = ""
        for parameter in parameters:
            required = "(required)" if not parameter.has_default else ""
            text += f"- {parameter.name}: {required} {parameter.description}\n"
        return text

    @classmethod
    def _usage_example(cls, signature: MethodSignature) -> str:
        text = ""
        text += f"<{signature.class_name}:{signature.name}>\n"
        for parameter in signature.parameters:
            content = parameter.example if parameter.example else parameter.description
            if len(content) > 200:
                text += f"<{parameter.name}>\n{content}\n</{parameter.name}>\n"
            else:
                text += f"<{parameter.name}>{content}</{parameter.name}>\n"
        text += f"</{signature.class_name}:{signature.name}>\n"
        return text

    @classmethod
    def construct(cls, signature: MethodSignature) -> str:
        """
        Format a method signature into a Kraken XML format.
        """
        return "\n".join(
            [
                f"### {signature.class_name}:{signature.name}",
                f"Description: {signature.description}",
                "Parameters:",
                cls._parameters_to_str(signature.parameters),
                "Usage:",
                cls._usage_example(signature)
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
        # Extract outer tag <ClassName:methodName> to get class_name and method_name
        outer_tag_match = re.search(r'<([^:>]+):([^>]+)>', xml_string)
        if not outer_tag_match:
            raise ValueError("Could not find <ClassName:methodName> tag in XML string")
        
        class_name = outer_tag_match.group(1)
        method_name = outer_tag_match.group(2)
        
        # Extract inner content between opening and closing tags
        outer_tag_pattern = re.escape(f"<{class_name}:{method_name}>")
        closing_tag_pattern = re.escape(f"</{class_name}:{method_name}>")
        
        # Try to find content between tags
        content_match = re.search(f"{outer_tag_pattern}(.*?){closing_tag_pattern}", xml_string, re.DOTALL)
        if not content_match:
            # Try without closing tag (fallback)
            content_match = re.search(f"{outer_tag_pattern}(.*)", xml_string, re.DOTALL)
            if not content_match:
                return ToolCall(class_name=class_name, name=method_name, parameters={})
            content = content_match.group(1)
        else:
            content = content_match.group(1)
        
        # Parse parameters using regex approach (primary)
        parameters = cls._parse_parameters_from_xml(content)
        
        return ToolCall(class_name=class_name, name=method_name, parameters=parameters)
    
    @classmethod
    def _parse_parameters_from_xml(cls, content: str) -> dict[str, Any]:
        """Parse parameters from XML content using regex-based approach."""
        parameters = {}
        
        # Primary approach: extract <param>value</param>
        param_pattern = r'<([^>:]+)>(.*?)</\1>'
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
        tag_pattern = r'<([^/>:]+)>'
        matches = list(re.finditer(tag_pattern, content))
        
        # Build list of tag positions
        tag_positions = []
        for match in matches:
            tag_name = match.group(1)
            # Skip if already captured by primary approach
            if tag_name in captured_tags:
                continue
            # Skip closing tags
            if tag_name.startswith('/'):
                continue
            start_pos = match.end()
            tag_positions.append((tag_name, start_pos))
        
        # Extract values between tags
        for i, (tag_name, start_pos) in enumerate(tag_positions):
            if i + 1 < len(tag_positions):
                # Find the start of the next opening tag
                next_tag_match = re.search(r'<[^/>]', content[start_pos:])
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
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', xml_string, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove XML comments from thinking
            thinking = re.sub(r'<!--.*?-->', '', thinking, flags=re.DOTALL).strip()
        else:
            # No <thinking> tag - extract everything before the first tool call as thinking
            # Pattern to find first <ClassName:methodName> tag
            first_tool_call_match = re.search(r'<([^:>]+):([^>]+)>', xml_string)
            if first_tool_call_match:
                thinking = xml_string[:first_tool_call_match.start()].strip()
                # Remove XML comments from thinking
                if thinking:
                    thinking = re.sub(r'<!--.*?-->', '', thinking, flags=re.DOTALL).strip()
            else:
                thinking = ""
        
        # Extract all KLXML tool call blocks (<ClassName:methodName>...</ClassName:methodName>)
        # Pattern to match <ClassName:methodName>...</ClassName:methodName>
        tool_call_pattern = r'<([^:>]+):([^>]+)>(.*?)</\1:\2>'
        tool_call_matches = list(re.finditer(tool_call_pattern, xml_string, re.DOTALL))
        
        tool_calls = []
        for match in tool_call_matches:
            # Get the full tag with content: <ClassName:methodName>...</ClassName:methodName>
            full_match = match.group(0)
            tool_call = cls.parse_method_call(full_match)
            tool_calls.append(tool_call)
        
        return ParsedCodecResponse(
            thinking=thinking,
            tool_calls=tool_calls if tool_calls else None
        )

if __name__ == "__main__":
    import sys

    from dana.common.utils.misc import Misc
    sys.path.append("examples/agents/financial-analysis/resources")
    from create_file_resource import CreateFileResource
    resource = CreateFileResource()
    
    # Test construct methods
    print("=" * 80)
    print("CSXMLCodec.construct output:")
    print("=" * 80)
    print(CSXMLCodec.construct(Misc.parse_method_signature(resource.create)))
    print("\n")
    
    print("=" * 80)
    print("KLXMLCodec.construct output:")
    print("=" * 80)
    print(KLXMLCodec.construct(Misc.parse_method_signature(resource.create)))
    print("\n")
    
    # Test parse_method_call methods
    print("=" * 80)
    print("Testing KLXMLCodec.parse_method_call:")
    print("=" * 80)
    
    klxml_examples = [
        """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>""",
        """<MyResource:myMethod>
<param1>value1</param1>
<param2>value2</param2>
</MyResource:myMethod>""",
        """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
<another_param>some value</another_param>
</CreateFileResource:create>""",
        """Hello world
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>""",
        """<thinking>
This is my thinking about the task.
</thinking>
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>""",
        """Some text before
<thinking>
This is my thinking about the task.
</thinking>
<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""
    ]
    
    for i, xml_string in enumerate(klxml_examples, 1):
        print(f"\nExample {i}:")
        print(xml_string)
        print("\nParsed result:")
        try:
            result = KLXMLCodec.parse_method_call(xml_string)
            print(f"  class_name: {result.class_name}")
            print(f"  name: {result.name}")
            print(f"  thinking: {repr(result.thinking)}")
            print(f"  parameters: {result.parameters}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("Testing CSXMLCodec.parse_method_call:")
    print("=" * 80)
    
    csxml_examples = [
        """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>""",
        """<function_call>
<invoke name="MyResource:myMethod">
<parameter name="param1">value1</parameter>
<parameter name="param2">value2</parameter>
</invoke>
</function_call>""",
        """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
<parameter name="another_param">some value</parameter>
</invoke>
</function_call>""",
        """Hello world
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>""",
        """<thinking>
This is my thinking about the task.
</thinking>
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>""",
        """Some text before
<thinking>
This is my thinking about the task.
</thinking>
<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""
    ]
    
    for i, xml_string in enumerate(csxml_examples, 1):
        print(f"\nExample {i}:")
        print(xml_string)
        print("\nParsed result:")
        try:
            result = CSXMLCodec.parse_method_call(xml_string)
            print(f"  class_name: {result.class_name}")
            print(f"  name: {result.name}")
            print(f"  thinking: {repr(result.thinking)}")
            print(f"  parameters: {result.parameters}")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # Test round-trip: construct -> parse_method_call
    print("\n" + "=" * 80)
    print("Testing round-trip (construct -> parse_method_call):")
    print("=" * 80)
    
    signature = Misc.parse_method_signature(resource.create)
    
    print("\nKLXMLCodec round-trip:")
    klxml_usage = KLXMLCodec._usage_example(signature)
    print(f"Generated XML:\n{klxml_usage}")
    parsed_kl = KLXMLCodec.parse_method_call(klxml_usage)
    print("\nParsed result:")
    print(f"  class_name: {parsed_kl.class_name}")
    print(f"  name: {parsed_kl.name}")
    print(f"  thinking: {repr(parsed_kl.thinking)}")
    print(f"  parameters: {parsed_kl.parameters}")
    
    print("\nCSXMLCodec round-trip:")
    csxml_usage = CSXMLCodec._usage_example(signature)
    print(f"Generated XML:\n{csxml_usage}")
    parsed_cs = CSXMLCodec.parse_method_call(csxml_usage)
    print("\nParsed result:")
    print(f"  class_name: {parsed_cs.class_name}")
    print(f"  name: {parsed_cs.name}")
    print(f"  thinking: {repr(parsed_cs.thinking)}")
    print(f"  parameters: {parsed_cs.parameters}")