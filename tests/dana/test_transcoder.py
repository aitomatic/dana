"""Unit tests for the DANA transcoder."""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseResponse
from opendxa.dana.language.parser import ParseError, ParseResult
from opendxa.dana.runtime.context import RuntimeContext
from opendxa.dana.transcoder.transcoder import FaultTolerantTranscoder, TranscoderError


@pytest.mark.asyncio
class TestFaultTolerantTranscoder(IsolatedAsyncioTestCase):
    """Tests for the FaultTolerantTranscoder."""

    async def asyncSetUp(self):
        """Set up async test environment."""
        self.llm = AsyncMock(spec=LLMResource)
        # Mock the query method which is actually used
        self.llm.query = AsyncMock()
        self.context = MagicMock(spec=RuntimeContext)
        self.transcoder = FaultTolerantTranscoder(self.llm)

    async def test_direct_parsing_success(self):
        """Test successful direct parsing when LLM is not available."""
        transcoder = FaultTolerantTranscoder(None)  # type: ignore No LLM
        code = "private.x = 10"
        # Mock parse to succeed directly
        mock_program = MagicMock()
        with patch("opendxa.dana.transcoder.transcoder.parse", return_value=ParseResult(program=mock_program, errors=[])):
            result, cleaned_code = await transcoder.transcode(code, self.context)
            self.assertTrue(result.is_valid)
            self.assertIsNotNone(result.program)
            self.assertEqual(result.program, mock_program)
            self.assertIsNone(cleaned_code)  # No LLM cleaning was performed

    async def test_llm_query_failure(self):
        """Test when the initial parse fails and the LLM query itself fails."""
        code = "invalid code"
        # Mock initial parse to fail
        with patch("opendxa.dana.transcoder.transcoder.parse", side_effect=ParseError("Initial Parse Error")) as mock_initial_parse:
            # Mock LLM query to return a failed response
            failed_response = BaseResponse(success=False, error="LLM Query Failed")
            self.llm.query.return_value = failed_response

            with self.assertRaises(TranscoderError) as cm:
                await self.transcoder.transcode(code, self.context)

            self.assertIn("Failed to clean code with LLM", str(cm.exception))
            mock_initial_parse.assert_called_once_with(code)
            self.llm.query.assert_awaited_once()

    async def test_llm_cleaning_and_final_parse_failure(self):
        """Test when LLM cleaning succeeds but the final parse still fails."""
        original_code = "invalid code"
        cleaned_code = "still invalid code"

        # Mock parse: first call fails, second call (with cleaned code) also fails
        parse_side_effects = [ParseError("Initial Parse Error"), ParseError("Final Parse Error")]
        with patch("opendxa.dana.transcoder.transcoder.parse", side_effect=parse_side_effects) as mock_parse:
            # Mock LLM query to return cleaned code
            mock_choice = MagicMock()
            mock_choice.message.content = cleaned_code
            llm_success_response = BaseResponse(success=True, content={"choices": [mock_choice]})
            self.llm.query.return_value = llm_success_response

            with self.assertRaises(TranscoderError) as cm:
                await self.transcoder.transcode(original_code, self.context)

            self.assertIn("Failed to transcode input after cleaning: Final Parse Error", str(cm.exception))
            # Check parse was called twice
            self.assertEqual(mock_parse.call_count, 2)
            mock_parse.assert_any_call(original_code)
            mock_parse.assert_any_call(cleaned_code)
            # Check LLM query was called
            self.llm.query.assert_awaited_once()

    async def test_llm_cleaning_success(self):
        """Test successful LLM cleaning after initial parse failure."""
        original_code = 'log "hello world'  # Missing closing quote
        cleaned_code = 'log "hello world"'
        mock_program = MagicMock()

        # Mock parse: first call fails, second call (with cleaned code) succeeds
        parse_side_effects = [ParseError("Initial Parse Error"), ParseResult(program=mock_program, errors=[])]
        with patch("opendxa.dana.transcoder.transcoder.parse", side_effect=parse_side_effects) as mock_parse:
            # Mock LLM query to return cleaned code
            mock_choice = MagicMock()
            mock_choice.message.content = cleaned_code
            llm_success_response = BaseResponse(success=True, content={"choices": [mock_choice]})
            self.llm.query.return_value = llm_success_response

            result, cleaned_code_returned = await self.transcoder.transcode(original_code, self.context)

            self.assertTrue(result.is_valid)
            self.assertEqual(result.program, mock_program)
            self.assertEqual(cleaned_code_returned, cleaned_code)  # Check that the cleaned code is returned
            # Check parse was called twice
            self.assertEqual(mock_parse.call_count, 2)
            mock_parse.assert_any_call(original_code)
            mock_parse.assert_any_call(cleaned_code)
            # Check LLM query was called
            self.llm.query.assert_awaited_once()

    async def test_validation(self):
        """Test the validation mechanism."""
        # This test assumes validation logic exists within the transcoder or its components
        # Add specific validation tests if needed
        pass

    async def test_validation_failure(self):
        """Test handling of validation failures."""
        # Mock validation failure if applicable
        pass


if __name__ == "__main__":
    pytest.main()
