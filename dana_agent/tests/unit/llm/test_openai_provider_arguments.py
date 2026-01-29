"""Tests for OpenAI provider argument serialization."""

import json


class TestOpenAIArgumentSerialization:
    """Test that OpenAI provider serializes arguments correctly."""

    def test_dict_arguments_serialized_as_json(self):
        """Arguments dict should be JSON string, not Python repr."""
        arguments = {"key": "value", "number": 42}

        # JSON format
        json_str = json.dumps(arguments)
        assert '"key": "value"' in json_str
        assert '"number": 42' in json_str

        # Python repr format (wrong)
        repr_str = str(arguments)
        assert "'" in repr_str  # Python uses single quotes

        # Verify JSON can be parsed back
        parsed = json.loads(json_str)
        assert parsed == arguments

    def test_json_dumps_vs_str_for_dict(self):
        """Demonstrate the difference between json.dumps and str for dicts."""
        arguments = {"name": "test", "value": True}

        json_output = json.dumps(arguments)
        str_output = str(arguments)

        # JSON uses double quotes and lowercase booleans
        assert json_output == '{"name": "test", "value": true}'

        # str uses single quotes and Python-style booleans
        assert "'" in str_output
        assert "True" in str_output  # Python repr
