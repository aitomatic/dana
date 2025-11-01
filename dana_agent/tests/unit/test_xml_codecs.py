"""
Unit tests for XML codec classes (CSXMLCodec and KLXMLCodec).

This module tests the parse_method_call functionality for both codec classes,
ensuring they can parse XML method call strings back into ToolCall objects.
"""

import pytest

from dana.common.schemas.tool_call import ToolCall, MethodSignature, ParameterInfo
from dana.core.knowledge.prompts.codecs.xml_format import CSXMLCodec, KLXMLCodec


class TestKLXMLCodecParseMethodCall:
    """Test KLXMLCodec.parse_method_call functionality."""

    def test_parse_simple_xml(self):
        """Test parsing simple XML with single parameter."""
        xml_string = """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
</CreateFileResource:create>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "CreateFileResource"
        assert result.name == "create"
        assert result.parameters == {"relative_workspace_path": "dana/hello.py"}

    def test_parse_xml_multiple_parameters(self):
        """Test parsing XML with multiple parameters."""
        xml_string = """<MyResource:myMethod>
<param1>value1</param1>
<param2>value2</param2>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters == {"param1": "value1", "param2": "value2"}

    def test_parse_xml_multiline_content(self):
        """Test parsing XML with multiline content in parameters."""
        xml_string = """<MyResource:myMethod>
<description>This is a
multiline
description</description>
<code>def hello():
    print("world")
</code>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert "This is a\nmultiline\ndescription" in result.parameters["description"]
        assert "def hello():" in result.parameters["code"]

    def test_parse_xml_missing_closing_tags(self):
        """Test parsing XML with missing closing tags using fallback approach."""
        xml_string = """<CreateFileResource:create>
<relative_workspace_path>dana/hello.py</relative_workspace_path>
<another_param>some value"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "CreateFileResource"
        assert result.name == "create"
        assert "relative_workspace_path" in result.parameters
        assert "another_param" in result.parameters

    def test_parse_xml_empty_parameters(self):
        """Test parsing XML with empty parameter tags."""
        xml_string = """<MyResource:myMethod>
<param1></param1>
<param2>value2</param2>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters["param1"] == "" or result.parameters.get("param1") is None
        assert result.parameters["param2"] == "value2"

    def test_parse_xml_no_parameters(self):
        """Test parsing XML with no parameters."""
        xml_string = """<MyResource:myMethod>
</MyResource:myMethod>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters == {}


class TestCSXMLCodecParseMethodCall:
    """Test CSXMLCodec.parse_method_call functionality."""

    def test_parse_full_function_call_format(self):
        """Test parsing full function_call format."""
        xml_string = """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "CreateFileResource"
        assert result.name == "create"
        assert result.parameters == {"relative_workspace_path": "dana/hello.py"}

    def test_parse_invoke_tags_multiple_parameters(self):
        """Test parsing invoke tags with multiple parameters."""
        xml_string = """<function_call>
<invoke name="MyResource:myMethod">
<parameter name="param1">value1</parameter>
<parameter name="param2">value2</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters == {"param1": "value1", "param2": "value2"}

    def test_parse_xml_missing_closing_tags(self):
        """Test parsing XML with missing closing tags."""
        xml_string = """<function_call>
<invoke name="CreateFileResource:create">
<parameter name="relative_workspace_path">dana/hello.py</parameter>
<parameter name="another_param">some value"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "CreateFileResource"
        assert result.name == "create"
        assert "relative_workspace_path" in result.parameters
        assert "another_param" in result.parameters

    def test_parse_xml_empty_parameters(self):
        """Test parsing XML with empty parameter tags."""
        xml_string = """<function_call>
<invoke name="MyResource:myMethod">
<parameter name="param1"></parameter>
<parameter name="param2">value2</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters.get("param1") == "" or result.parameters.get("param1") is None
        assert result.parameters["param2"] == "value2"

    def test_parse_xml_no_parameters(self):
        """Test parsing XML with no parameters."""
        xml_string = """<function_call>
<invoke name="MyResource:myMethod">
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        assert result.class_name == "MyResource"
        assert result.name == "myMethod"
        assert result.parameters == {}


class TestXMLCodecsRoundTrip:
    """Test round-trip conversion: construct → parse_method_call."""

    def test_klxml_round_trip(self):
        """Test KLXMLCodec round-trip conversion."""
        signature = MethodSignature(
            class_name="CreateFileResource",
            name="create",
            description="Create a new file",
            parameters=[
                ParameterInfo(
                    name="relative_workspace_path",
                    type="str",
                    description="Path to file",
                    has_default=False,
                    example="dana/hello.py"
                )
            ]
        )

        # Construct XML
        xml_output = KLXMLCodec.construct(signature)
        
        # Extract just the usage example part (the XML call format)
        # The construct method returns a full description, we need the usage example
        usage_example = KLXMLCodec._usage_example(signature)

        # Parse back
        result = KLXMLCodec.parse_method_call(usage_example)

        assert result.class_name == signature.class_name
        assert result.name == signature.name
        assert result.parameters["relative_workspace_path"] == "dana/hello.py"

    def test_csxml_round_trip(self):
        """Test CSXMLCodec round-trip conversion."""
        signature = MethodSignature(
            class_name="CreateFileResource",
            name="create",
            description="Create a new file",
            parameters=[
                ParameterInfo(
                    name="relative_workspace_path",
                    type="str",
                    description="Path to file",
                    has_default=False,
                    example="dana/hello.py"
                )
            ]
        )

        # Construct XML
        xml_output = CSXMLCodec.construct(signature)
        
        # Extract just the usage example part (the XML call format)
        usage_example = CSXMLCodec._usage_example(signature)

        # Parse back
        result = CSXMLCodec.parse_method_call(usage_example)

        assert result.class_name == signature.class_name
        assert result.name == signature.name
        assert result.parameters["relative_workspace_path"] == "dana/hello.py"

