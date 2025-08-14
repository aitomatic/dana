"""
Unit tests for Dana TUI input router.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import pytest
import sys
from pathlib import Path

# Add the dana/tui/core directory to path for direct imports
core_path = Path(__file__).parent.parent.parent / "dana" / "tui" / "core"
sys.path.insert(0, str(core_path))

from router import parse, parse_meta_command, validate_agent_name, extract_quoted_string


class TestRouter:
    """Test the input router functionality."""

    def test_parse_agent_declaration(self):
        """Test parsing agent declarations."""
        result = parse("agent Jim")
        assert result.target == "__declare__"
        assert result.payload == "Jim"
        assert not result.is_meta

        result = parse("  agent   researcher  ")
        assert result.target == "__declare__"
        assert result.payload == "researcher"
        assert not result.is_meta

    def test_parse_agent_call(self):
        """Test parsing agent.chat() calls."""
        result = parse('Jim.chat("hello world")')
        assert result.target == "Jim"
        assert result.payload == "hello world"
        assert not result.is_meta

        result = parse("research.chat('find papers on AI')")
        assert result.target == "research"
        assert result.payload == "find papers on AI"
        assert not result.is_meta

    def test_parse_at_routing(self):
        """Test parsing @agent routing."""
        result = parse("@research find papers")
        assert result.target == "research"
        assert result.payload == "find papers"
        assert not result.is_meta

        result = parse("  @coder   build the app  ")
        assert result.target == "coder"
        assert result.payload == "build the app"
        assert not result.is_meta

    def test_parse_meta_commands(self):
        """Test parsing meta commands."""
        result = parse(":help")
        assert result.target is None
        assert result.payload == "help"
        assert result.is_meta

        result = parse(":use researcher")
        assert result.target is None
        assert result.payload == "use researcher"
        assert result.is_meta

        result = parse(":set debug=true")
        assert result.target is None
        assert result.payload == "set debug=true"
        assert result.is_meta

    def test_parse_default_routing(self):
        """Test default routing to focused agent."""
        result = parse("hello there")
        assert result.target is None
        assert result.payload == "hello there"
        assert not result.is_meta

    def test_parse_empty_input(self):
        """Test parsing empty input."""
        result = parse("")
        assert result.target is None
        assert result.payload == ""
        assert not result.is_meta

        result = parse("   ")
        assert result.target is None
        assert result.payload == ""
        assert not result.is_meta


class TestMetaCommand:
    """Test meta command parsing."""

    def test_simple_command(self):
        """Test simple meta commands."""
        cmd = parse_meta_command("help")
        assert cmd.command == "help"
        assert cmd.args == ""
        assert cmd.parsed_args == {}

    def test_command_with_args(self):
        """Test meta commands with arguments."""
        cmd = parse_meta_command("use researcher")
        assert cmd.command == "use"
        assert cmd.args == "researcher"
        assert cmd.parsed_args == {"args": ["researcher"]}

    def test_command_with_key_value(self):
        """Test meta commands with key=value pairs."""
        cmd = parse_meta_command("set debug=true verbose=false")
        assert cmd.command == "set"
        assert cmd.parsed_args == {"debug": "true", "verbose": "false"}

    def test_empty_command(self):
        """Test empty meta command."""
        cmd = parse_meta_command("")
        assert cmd.command == ""
        assert cmd.args == ""
        assert cmd.parsed_args == {}


class TestValidation:
    """Test validation functions."""

    def test_validate_agent_name(self):
        """Test agent name validation."""
        # Valid names
        assert validate_agent_name("agent1")
        assert validate_agent_name("my_agent")
        assert validate_agent_name("_private")
        assert validate_agent_name("CamelCase")
        assert validate_agent_name("a")

        # Invalid names
        assert not validate_agent_name("")
        assert not validate_agent_name("123invalid")
        assert not validate_agent_name("has-dashes")
        assert not validate_agent_name("has spaces")
        assert not validate_agent_name("has.dots")

    def test_extract_quoted_string(self):
        """Test quoted string extraction."""
        # Double quotes
        assert extract_quoted_string('"hello world"') == "hello world"
        assert extract_quoted_string('prefix "hello" suffix') == "hello"

        # Single quotes
        assert extract_quoted_string("'hello world'") == "hello world"
        assert extract_quoted_string("prefix 'hello' suffix") == "hello"

        # No quotes
        assert extract_quoted_string("no quotes here") is None
        assert extract_quoted_string("") is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_malformed_agent_call(self):
        """Test malformed agent.chat() calls."""
        # Missing quotes
        result = parse("Jim.chat(hello)")
        assert result.target is None  # Falls back to default routing
        assert result.payload == "Jim.chat(hello)"

        # Mismatched quotes
        result = parse("Jim.chat(\"hello')")
        assert result.target is None
        assert result.payload == "Jim.chat(\"hello')"

    def test_complex_at_routing(self):
        """Test complex @agent routing scenarios."""
        result = parse("@agent_name complex message with @symbols")
        assert result.target == "agent_name"
        assert result.payload == "complex message with @symbols"

    def test_meta_command_edge_cases(self):
        """Test meta command edge cases."""
        # Malformed meta command
        result = parse(": ")
        assert result.is_meta
        assert result.payload == ""

        # Meta command with colons in args
        result = parse(":set path=/home/user:bin")
        assert result.is_meta
        assert "path=/home/user:bin" in result.payload

    def test_agent_declaration_variations(self):
        """Test agent declaration variations."""
        # Extra whitespace
        result = parse("   agent    test_agent   ")
        assert result.target == "__declare__"
        assert result.payload == "test_agent"

        # Case sensitivity
        result = parse("AGENT myagent")
        assert result.target is None  # Case sensitive, so falls back to default

    def test_unicode_and_special_chars(self):
        """Test unicode and special characters."""
        result = parse("@research find papers on émotions")
        assert result.target == "research"
        assert result.payload == "find papers on émotions"

        result = parse("hello 世界")
        assert result.target is None
        assert result.payload == "hello 世界"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
