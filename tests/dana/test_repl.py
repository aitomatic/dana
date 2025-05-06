"""Unit tests for the DANA REPL."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.dana.exceptions import DanaError
from opendxa.dana.language.parser import ParseError, ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.runtime.interpreter import Interpreter, LogLevel
from opendxa.dana.runtime.repl import REPL
from opendxa.dana.transcoder.transcoder import TranscoderError


class TestREPL:
    """Test the REPL class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.llm = AsyncMock(spec=LLMResource)
        self.repl = REPL(self.llm)
        # Mock the interpreter
        self.repl.interpreter = AsyncMock(spec=Interpreter)

    @pytest.mark.asyncio
    async def test_execute_valid_code(self):
        """Test executing valid DANA code."""
        # Valid DANA code
        code = 'private.x = 42\nlog("Value: {private.x}")'

        # Mock transcoder and interpreter
        parse_result = ParseResult(program=MagicMock(), errors=[])
        with patch("opendxa.dana.transcoder.transcoder.FaultTolerantTranscoder.transcode", return_value=(parse_result, None)):
            self.repl.interpreter.execute_program.return_value = None

            await self.repl.execute(code)
            self.repl.interpreter.execute_program.assert_called_once_with(parse_result)

    @pytest.mark.asyncio
    async def test_execute_with_initial_context(self):
        """Test executing DANA code with initial context."""
        # DANA code using initial context
        code = 'log("Location: {system.location}")'
        initial_context = {"system.location": "San Francisco"}

        # Mock transcoder and interpreter
        parse_result = ParseResult(program=MagicMock(), errors=[])
        with patch("opendxa.dana.transcoder.transcoder.FaultTolerantTranscoder.transcode", return_value=(parse_result, None)):
            self.repl.interpreter.execute_program.return_value = None

            await self.repl.execute(code, initial_context)
            self.repl.interpreter.execute_program.assert_called_once_with(parse_result)

    @pytest.mark.asyncio
    async def test_execute_with_transcoder_error(self):
        """Test handling transcoder errors when parsing also fails.

        NOTE: Due to exception subclassing (TranscoderError is a DanaError),
        pytest.raises(DanaError) catches the initial TranscoderError here.
        We assert that this initial error is caught.
        """
        # Invalid DANA code
        code = "x = 42  # Missing scope"
        initial_transcoder_error_msg = "Failed to transcode"

        # Patch the transcode method directly to raise TranscoderError
        with patch.object(
            self.repl.transcoder, "transcode", side_effect=TranscoderError(initial_transcoder_error_msg, code, "")
        ) as mock_transcode:
            # Mock parse to also fail (although the ParseError itself won't be the final caught exception)
            with patch("opendxa.dana.language.parser.parse", side_effect=ParseError("Invalid syntax")):
                # Expect the *initial* TranscoderError because pytest.raises catches the subclass first.
                with pytest.raises(TranscoderError, match=initial_transcoder_error_msg):
                    await self.repl.execute(code)

                # Ensure the transcode mock was awaited, verifying the initial step
                mock_transcode.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_with_interpreter_error(self):
        """Test handling interpreter errors."""
        # Mock interpreter to raise error
        self.repl.interpreter.execute_program.side_effect = RuntimeError("Runtime error")

        # Expect the wrapped DanaError from the final exception handler
        with pytest.raises(DanaError, match=r"Program execution failed: Runtime error"):
            await self.repl.execute("private.x = 42")

    @pytest.mark.asyncio
    async def test_set_log_level(self):
        """Test setting log level."""
        level = LogLevel.DEBUG
        self.repl.set_log_level(level)
        self.repl.interpreter.set_log_level.assert_called_with(level)

    @pytest.mark.asyncio
    async def test_get_context(self):
        """Test getting runtime context."""
        mock_context = RuntimeContext()
        # Create a new interpreter with the mock context
        self.repl.interpreter = Interpreter(mock_context)

        context = self.repl.get_context()
        # Compare state dictionaries, ignoring execution ID
        context_state = context._state.copy()
        mock_state = mock_context._state.copy()
        # Remove execution ID and log level from comparison
        context_state["system"].pop("id", None)
        mock_state["system"].pop("id", None)
        context_state["system"].pop("log_level", None)
        mock_state["system"].pop("log_level", None)
        assert context_state == mock_state
        assert context._resources.list() == mock_context._resources.list()
