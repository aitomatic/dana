"""
Unit tests for codecs with object_id format support.
"""

from dana.common.schemas.tool_call import MethodSignature, ParameterInfo, ToolCall
from dana.core.knowledge.prompts.codecs.xml_format import CSXMLCodec, KLXMLCodec


class TestCodecWithObjectId:
    """Test codecs with object_id format."""

    def test_csxmlcodec_construct_uses_object_id_when_available(self):
        """Test CSXMLCodec uses object_id in construct when available."""
        param = ParameterInfo(name="query", type="str", description="Search query", has_default=False)
        signature = MethodSignature(
            class_name="SearchResource", object_id="my-search-resource", name="search", description="Search method", parameters=[param]
        )

        result = CSXMLCodec.construct(signature)

        # Should use object_id instead of class_name
        assert "my-search-resource:search" in result
        assert '<invoke name="my-search-resource:search">' in result

    def test_csxmlcodec_construct_falls_back_to_class_name(self):
        """Test CSXMLCodec falls back to class_name when object_id is None."""
        param = ParameterInfo(name="query", type="str", description="Search query", has_default=False)
        signature = MethodSignature(
            class_name="SearchResource", object_id=None, name="search", description="Search method", parameters=[param]
        )

        result = CSXMLCodec.construct(signature)

        # Should use class_name when object_id is None
        assert "SearchResource:search" in result
        assert '<invoke name="SearchResource:search">' in result

    def test_klxmlcodec_construct_uses_object_id_when_available(self):
        """Test KLXMLCodec uses object_id in construct when available."""
        param = ParameterInfo(name="query", type="str", description="Search query", has_default=False)
        signature = MethodSignature(
            class_name="SearchResource", object_id="my-search-resource", name="search", description="Search method", parameters=[param]
        )

        result = KLXMLCodec.construct(signature)

        # Should use object_id instead of class_name
        assert "<my-search-resource:search>" in result
        assert "### my-search-resource:search" in result

    def test_klxmlcodec_construct_falls_back_to_class_name(self):
        """Test KLXMLCodec falls back to class_name when object_id is None."""
        param = ParameterInfo(name="query", type="str", description="Search query", has_default=False)
        signature = MethodSignature(
            class_name="SearchResource", object_id=None, name="search", description="Search method", parameters=[param]
        )

        result = KLXMLCodec.construct(signature)

        # Should use class_name when object_id is None
        assert "<SearchResource:search>" in result
        assert "### SearchResource:search" in result

    def test_csxmlcodec_parse_object_id_format(self):
        """Test CSXMLCodec can parse object_id:method format."""
        xml_string = """<function_call>
<invoke name="my-search-resource:search">
<parameter name="query">test query</parameter>
</invoke>
</function_call>"""

        result = CSXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        # Should parse identifier into object_id (and possibly class_name for compatibility)
        assert result.name == "search"
        assert result.parameters == {"query": "test query"}

    def test_klxmlcodec_parse_object_id_format(self):
        """Test KLXMLCodec can parse object_id:method format."""
        xml_string = """<my-search-resource:search>
<query>test query</query>
</my-search-resource:search>"""

        result = KLXMLCodec.parse_method_call(xml_string)

        assert isinstance(result, ToolCall)
        # Should parse identifier into object_id (and possibly class_name for compatibility)
        assert result.name == "search"
        assert result.parameters == {"query": "test query"}
