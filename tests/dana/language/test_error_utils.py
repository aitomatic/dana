"""Tests for error utilities."""

from opendxa.dana.common.error_utils import ErrorUtils
from opendxa.dana.common.exceptions import ParseError


class TestErrorUtils:
    """Test suite for ErrorUtils class."""

    def test_create_error_message_basic(self):
        """Test basic error message creation."""
        error_text = "Test error"
        line = 1
        column = 5
        source_line = "x = 10"
        expected = "Test error\nx = 10\n     ^"
        result = ErrorUtils.create_error_message(error_text, line, column, source_line)
        assert result == expected

    def test_create_error_message_with_adjustment(self):
        """Test error message creation with adjustment."""
        error_text = "Test error"
        line = 1
        column = 5
        source_line = "x = 10"
        adjustment = "Missing value"
        expected = "Test error\nx = 10\n     ^ Missing value"
        result = ErrorUtils.create_error_message(error_text, line, column, source_line, adjustment)
        assert result == expected

    def test_create_error_message_unexpected_token(self):
        """Test error message creation for unexpected token."""
        error_text = "Unexpected token Token('SEMICOLON', ';')"
        line = 1
        column = 5
        source_line = "x = 10;"
        expected = "Unexpected input: Token('SEMICOLON', ';')\nx = 10;\n     ^"
        result = ErrorUtils.create_error_message(error_text, line, column, source_line)
        assert result == expected

    def test_create_error_message_expected_tokens(self):
        """Test error message creation for expected tokens."""
        error_text = "Expected one of:\n\t* NUMBER\n\t* IDENTIFIER"
        line = 1
        column = 5
        source_line = "x = "
        expected = "Invalid syntax\nExpected: NUMBER, IDENTIFIER\nx = \n     ^"
        result = ErrorUtils.create_error_message(error_text, line, column, source_line)
        assert result == expected

    def test_handle_parse_error_with_position(self):
        """Test handling parse error with position information."""

        class MockError(Exception):
            def __init__(self):
                self.line = 1
                self.column = 5
                self.message = "Test error"

            def __str__(self):
                return self.message

        error = MockError()
        program_text = "x = 10"
        error, is_passthrough = ErrorUtils.handle_parse_error(error, program_text, "parsing")

        assert isinstance(error, ParseError)
        assert not is_passthrough
        assert error.line == 1
        assert "Test error" in str(error)

    def test_handle_parse_error_without_position(self):
        """Test handling parse error without position information."""
        error = Exception("Generic error")
        program_text = "x = 10"
        error, is_passthrough = ErrorUtils.handle_parse_error(error, program_text, "parsing")

        assert isinstance(error, ParseError)
        assert not is_passthrough
        assert error.line == 0
        assert "Generic error" in str(error)

    def test_handle_parse_error_assignment(self):
        """Test handling parse error for assignment."""

        class MockError(Exception):
            def __init__(self):
                self.line = 1
                self.column = 5

        error = MockError()
        program_text = "x = # comment"
        error, is_passthrough = ErrorUtils.handle_parse_error(error, program_text, "parsing")

        assert isinstance(error, ParseError)
        assert not is_passthrough
        assert "Missing expression after equals sign" in str(error)
