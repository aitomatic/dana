"""Unit tests for the DANA transcoder."""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opendxa.common.resource.llm_resource import LLMResource
from opendxa.common.types import BaseResponse
from opendxa.dana.language.ast import Program
from opendxa.dana.language.parser import ParseError, ParseResult
from opendxa.dana.transcoder.transcoder import Transcoder, TranscoderError


@pytest.mark.asyncio
class TestTranscoder(IsolatedAsyncioTestCase):
    """Tests for the Transcoder."""

    async def asyncSetUp(self):
        """Set up async test environment."""
        self.llm = AsyncMock(spec=LLMResource)
        self.llm.query = AsyncMock()
        self.transcoder = Transcoder(self.llm)

    async def test_to_dana_success(self):
        """Test successful translation from natural language to DANA code."""
        natural_language = "add 5 and 10"
        dana_code = "private.result = 5 + 10"
        mock_program = MagicMock(spec=Program)

        # Mock LLM response
        llm_response = BaseResponse(success=True, content=dana_code)
        self.llm.query.return_value = llm_response

        # Mock parse to succeed
        with patch("opendxa.dana.transcoder.transcoder.parse", return_value=ParseResult(program=mock_program, errors=[])):
            result, code = await self.transcoder.to_dana(natural_language)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.program, mock_program)
            self.assertEqual(code, dana_code)

    async def test_to_dana_llm_failure(self):
        """Test when LLM query fails."""
        natural_language = "add 5 and 10"
        failed_response = BaseResponse(success=False, error="LLM Query Failed")
        self.llm.query.return_value = failed_response

        with self.assertRaises(TranscoderError) as cm:
            await self.transcoder.to_dana(natural_language)
        self.assertIn("Failed to translate to DANA", str(cm.exception))

    async def test_to_dana_parse_failure(self):
        """Test when LLM returns invalid DANA code."""
        natural_language = "add 5 and 10"
        invalid_code = "invalid dana code"

        # Mock LLM response with invalid code
        llm_response = BaseResponse(success=True, content=invalid_code)
        self.llm.query.return_value = llm_response

        # Mock parse to fail
        with patch(
            "opendxa.dana.transcoder.transcoder.parse", return_value=ParseResult(program=Program([]), errors=[ParseError("Invalid syntax")])
        ):
            with self.assertRaises(TranscoderError) as cm:
                await self.transcoder.to_dana(natural_language)
            self.assertIn("Invalid syntax", str(cm.exception))

    async def test_to_natural_language_success(self):
        """Test successful translation from DANA code to natural language."""
        dana_code = "private.result = 5 + 10"
        natural_language = "Add 5 and 10"

        # Mock LLM response
        llm_response = BaseResponse(success=True, content=natural_language)
        self.llm.query.return_value = llm_response

        result = await self.transcoder.to_natural_language(dana_code)
        self.assertEqual(result, natural_language)

    async def test_to_natural_language_llm_failure(self):
        """Test when LLM query fails during natural language translation."""
        dana_code = "private.result = 5 + 10"
        failed_response = BaseResponse(success=False, error="LLM Query Failed")
        self.llm.query.return_value = failed_response

        with self.assertRaises(TranscoderError) as cm:
            await self.transcoder.to_natural_language(dana_code)
        self.assertIn("Failed to translate to natural language", str(cm.exception))

    async def test_llm_response_formats(self):
        """Test handling of different LLM response formats."""
        dana_code = "private.result = 5 + 10"
        expected_nl = "Add 5 and 10"

        # Test direct content format
        llm_response = BaseResponse(success=True, content=expected_nl)
        self.llm.query.return_value = llm_response
        result = await self.transcoder.to_natural_language(dana_code)
        self.assertEqual(result, expected_nl)

        # Test string format
        llm_response = BaseResponse(success=True, content=str(expected_nl))
        self.llm.query.return_value = llm_response
        result = await self.transcoder.to_natural_language(dana_code)
        self.assertEqual(result, expected_nl)


if __name__ == "__main__":
    pytest.main()
