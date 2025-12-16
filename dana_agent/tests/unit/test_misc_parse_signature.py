"""
Unit tests for Misc.parse_method_signature with object_id support.
"""

from dana.common.schemas.tool_call import MethodSignature
from dana.common.utils.misc import Misc


class TestParseMethodSignature:
    """Test parse_method_signature with object_id parameter."""

    def test_parse_method_signature_with_object_id(self):
        """Test parse_method_signature accepts object_id parameter."""

        def test_method(self, query: str) -> str:
            """Test method for parsing.

            Args:
                query: Search query string
            """
            return query

        signature = Misc.parse_method_signature(test_method, object_id="my-resource-id")

        assert isinstance(signature, MethodSignature)
        assert signature.object_id == "my-resource-id"
        assert signature.name == "test_method"
        assert len(signature.parameters) == 1
        assert signature.parameters[0].name == "query"

    def test_parse_method_signature_without_object_id(self):
        """Test parse_method_signature backward compatibility - works without object_id."""

        def test_method(self, query: str) -> str:
            """Test method for parsing.

            Args:
                query: Search query string
            """
            return query

        signature = Misc.parse_method_signature(test_method)

        assert isinstance(signature, MethodSignature)
        assert signature.object_id is None
        assert signature.name == "test_method"

    def test_parse_method_signature_object_id_overrides_class_name(self):
        """Test that object_id is set independently of class_name."""

        class TestResource:
            def search(self, query: str) -> str:
                """Search method.

                Args:
                    query: Search query
                """
                return query

        resource = TestResource()
        signature = Misc.parse_method_signature(resource.search, object_id="my-resource-id")

        assert signature.object_id == "my-resource-id"
        assert signature.class_name == "TestResource"  # Still extracted from method
        assert signature.name == "search"
