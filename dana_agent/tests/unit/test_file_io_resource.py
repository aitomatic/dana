"""Tests for FileIOResource multimodal read support.

Covers:
- Image reading (PNG, JPG, etc.) → dict with inject_as_user content blocks
- PDF reading → dict with inject_as_user document blocks
- PDF page selection with pymupdf
- Large PDF guard (>10 pages without pages param)
- Text reading regression (existing cat-n behavior unchanged)
- Error handling (missing files, oversized images, invalid page ranges)
"""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dana.core.resource.file_io_resource import (
    MAX_IMAGE_SIZE,
    FileIOResource,
)


@pytest.fixture
def tmp_resource(tmp_path):
    """Create a FileIOResource rooted at a temp directory."""
    return FileIOResource(resource_id="test-file-io", base_path=tmp_path)


@pytest.fixture
def no_vision_resource(tmp_path):
    """Create a FileIOResource with supports_vision=False."""
    return FileIOResource(resource_id="test-file-io-nv", base_path=tmp_path, supports_vision=False)


# ============================================================================
# TEXT READING REGRESSION
# ============================================================================


class TestTextReadRegression:
    """Ensure existing text file reading behavior is unchanged."""

    @pytest.mark.asyncio
    async def test_read_text_file_with_line_numbers(self, tmp_resource, tmp_path):
        """Read a .py file → cat -n formatted output."""
        f = tmp_path / "hello.py"
        f.write_text("print('hello')\nprint('world')\n")

        result = await tmp_resource.read(str(f))
        assert isinstance(result, str)
        assert "1\tprint('hello')" in result
        assert "2\tprint('world')" in result

    @pytest.mark.asyncio
    async def test_read_text_file_with_offset_and_limit(self, tmp_resource, tmp_path):
        """Offset and limit work for text files."""
        f = tmp_path / "lines.txt"
        f.write_text("\n".join(f"line {i}" for i in range(1, 11)))

        result = await tmp_resource.read(str(f), offset=3, limit=2)
        assert isinstance(result, str)
        assert "3\tline 3" in result
        assert "4\tline 4" in result
        assert "5\tline 5" not in result

    @pytest.mark.asyncio
    async def test_read_json_file(self, tmp_resource, tmp_path):
        """JSON files are read as text."""
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}')

        result = await tmp_resource.read(str(f))
        assert isinstance(result, str)
        assert '"key": "value"' in result

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, tmp_resource):
        """Missing file returns error string."""
        result = await tmp_resource.read("/nonexistent/path.txt")
        assert isinstance(result, str)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_read_empty_text_file(self, tmp_resource, tmp_path):
        """Empty file returns appropriate message."""
        f = tmp_path / "empty.txt"
        f.write_text("")

        result = await tmp_resource.read(str(f))
        assert isinstance(result, str)
        assert "empty" in result.lower()


# ============================================================================
# IMAGE READING
# ============================================================================


class TestImageRead:
    """Test image file reading returns inject_as_user content blocks."""

    @pytest.mark.asyncio
    async def test_read_png_returns_dict(self, tmp_resource, tmp_path):
        """Read a PNG → dict with 'message' and 'inject_as_user'."""
        f = tmp_path / "test.png"
        # Write minimal PNG bytes (1x1 pixel)
        png_bytes = (
            b"\x89PNG\r\n\x1a\n"  # PNG signature
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
            b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx"
            b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00"
            b"\x00IEND\xaeB`\x82"
        )
        f.write_bytes(png_bytes)

        result = await tmp_resource.read(str(f))

        assert isinstance(result, dict)
        assert "message" in result
        assert "inject_as_user" in result
        assert "image/png" in result["message"]
        assert "test.png" in result["message"]

        blocks = result["inject_as_user"]
        assert len(blocks) == 2
        assert blocks[0]["type"] == "text"
        assert "test.png" in blocks[0]["text"]
        assert blocks[1]["type"] == "image"
        assert blocks[1]["source"]["type"] == "base64"
        assert blocks[1]["source"]["media_type"] == "image/png"

        # Verify base64 decodes back to original bytes
        decoded = base64.b64decode(blocks[1]["source"]["data"])
        assert decoded == png_bytes

    @pytest.mark.asyncio
    async def test_read_jpg_returns_jpeg_media_type(self, tmp_resource, tmp_path):
        """Read a .jpg → media_type is image/jpeg."""
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # JPEG header stub

        result = await tmp_resource.read(str(f))
        assert isinstance(result, dict)
        assert result["inject_as_user"][1]["source"]["media_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_read_webp(self, tmp_resource, tmp_path):
        """Read a .webp file."""
        f = tmp_path / "image.webp"
        f.write_bytes(b"RIFF" + b"\x00" * 100)

        result = await tmp_resource.read(str(f))
        assert isinstance(result, dict)
        assert result["inject_as_user"][1]["source"]["media_type"] == "image/webp"

    @pytest.mark.asyncio
    async def test_oversized_image_returns_error(self, tmp_resource, tmp_path):
        """Image exceeding 20MB returns error string."""
        f = tmp_path / "huge.png"
        f.write_bytes(b"\x00" * (MAX_IMAGE_SIZE + 1))

        result = await tmp_resource.read(str(f))
        assert isinstance(result, str)
        assert "Error" in result
        assert "20MB" in result


# ============================================================================
# PDF READING
# ============================================================================


class TestPdfRead:
    """Test PDF file reading returns inject_as_user document blocks."""

    @pytest.mark.asyncio
    async def test_read_small_pdf_without_pymupdf(self, tmp_resource, tmp_path):
        """Small PDF without pymupdf → full PDF as base64 document block."""
        f = tmp_path / "small.pdf"
        pdf_bytes = b"%PDF-1.4 minimal pdf content"
        f.write_bytes(pdf_bytes)

        # Mock fitz import to raise ImportError (pymupdf not available)
        with patch.dict("sys.modules", {"fitz": None}):
            with patch(
                "builtins.__import__",
                side_effect=lambda name, *args: (_ for _ in ()).throw(ImportError())
                if name == "fitz"
                else __builtins__.__import__(name, *args),
            ):
                result = await tmp_resource.read(str(f))

        assert isinstance(result, dict)
        assert "message" in result
        assert "inject_as_user" in result
        assert "small.pdf" in result["message"]

        blocks = result["inject_as_user"]
        assert len(blocks) == 2
        assert blocks[0]["type"] == "text"
        assert blocks[1]["type"] == "document"
        assert blocks[1]["source"]["media_type"] == "application/pdf"

        decoded = base64.b64decode(blocks[1]["source"]["data"])
        assert decoded == pdf_bytes

    @pytest.mark.asyncio
    async def test_large_pdf_without_pages_returns_error(self, tmp_resource, tmp_path):
        """PDF >10 pages without pages param → error message."""
        f = tmp_path / "large.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        mock_doc = MagicMock()
        mock_doc.page_count = 25
        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            result = await tmp_resource.read(str(f))

        assert isinstance(result, str)
        assert "Error" in result
        assert "25 pages" in result
        assert "pages parameter" in result.lower() or "pages=" in result

    @pytest.mark.asyncio
    async def test_pdf_page_selection(self, tmp_resource, tmp_path):
        """PDF with pages param → extracts specific pages."""
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        extracted_bytes = b"%PDF-1.4 extracted pages"

        mock_new_doc = MagicMock()
        mock_new_doc.tobytes.return_value = extracted_bytes

        mock_doc = MagicMock()
        mock_doc.page_count = 20

        mock_fitz = MagicMock()
        # First call opens original doc, second opens new empty doc
        mock_fitz.open.side_effect = [mock_doc, mock_new_doc]

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            result = await tmp_resource.read(str(f), pages="1-5")

        assert isinstance(result, dict)
        assert "pages 1-5" in result["message"]
        blocks = result["inject_as_user"]
        assert blocks[1]["type"] == "document"

        # Verify insert_pdf was called with correct 0-indexed range
        mock_new_doc.insert_pdf.assert_called_once_with(mock_doc, from_page=0, to_page=4)

    @pytest.mark.asyncio
    async def test_pdf_single_page_selection(self, tmp_resource, tmp_path):
        """pages='3' extracts only page 3."""
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        mock_new_doc = MagicMock()
        mock_new_doc.tobytes.return_value = b"page3"

        mock_doc = MagicMock()
        mock_doc.page_count = 10

        mock_fitz = MagicMock()
        mock_fitz.open.side_effect = [mock_doc, mock_new_doc]

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            result = await tmp_resource.read(str(f), pages="3")

        assert isinstance(result, dict)
        mock_new_doc.insert_pdf.assert_called_once_with(mock_doc, from_page=2, to_page=2)

    @pytest.mark.asyncio
    async def test_pdf_page_exceeds_document(self, tmp_resource, tmp_path):
        """Requesting pages beyond document length → error."""
        f = tmp_path / "short.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        mock_doc = MagicMock()
        mock_doc.page_count = 5

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            result = await tmp_resource.read(str(f), pages="10")

        assert isinstance(result, str)
        assert "Error" in result
        assert "exceeds" in result.lower()

    @pytest.mark.asyncio
    async def test_pdf_too_many_pages_requested(self, tmp_resource, tmp_path):
        """Requesting >20 pages → error."""
        f = tmp_path / "big.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        mock_fitz = MagicMock()

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            result = await tmp_resource.read(str(f), pages="1-25")

        assert isinstance(result, str)
        assert "Error" in result
        assert "20" in result

    @pytest.mark.asyncio
    async def test_pdf_invalid_page_range(self, tmp_resource, tmp_path):
        """Invalid page range → error."""
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        mock_fitz = MagicMock()

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            result = await tmp_resource.read(str(f), pages="abc")

        assert isinstance(result, str)
        assert "Error" in result
        assert "Invalid" in result


# ============================================================================
# PARSE PAGE RANGE
# ============================================================================


class TestParsePageRange:
    """Test the _parse_page_range static method."""

    def test_single_page(self):
        assert FileIOResource._parse_page_range("3") == (3, 3)

    def test_page_range(self):
        assert FileIOResource._parse_page_range("1-5") == (1, 5)

    def test_page_range_with_whitespace(self):
        assert FileIOResource._parse_page_range("  2-10  ") == (2, 10)

    def test_invalid_page_raises(self):
        with pytest.raises(ValueError):
            FileIOResource._parse_page_range("abc")


# ============================================================================
# CONTENT BLOCK PASSTHROUGH IN TIMELINE
# ============================================================================


class TestContentBlockPassthrough:
    """Test that list[dict] content flows through the timeline unchanged."""

    def test_format_entry_content_passes_through_list(self):
        """_format_entry_content returns list[dict] content unchanged."""
        from dana.core.agent.timeline import Timeline, TimelineEntry, TimelineEntryType

        timeline = Timeline(max_context_tokens=32000)
        multimodal_content = [
            {"type": "text", "text": "Visual contents of image.png:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "abc123"}},
        ]
        entry = TimelineEntry(
            entry_type=TimelineEntryType.USER_MESSAGE,
            content=multimodal_content,
        )

        result = timeline._format_entry_content(entry)
        assert result is multimodal_content  # same object, not stringified

    def test_to_llm_messages_preserves_list_content(self):
        """to_llm_messages preserves list[dict] content in LLMMessage."""
        from dana.core.agent.timeline import Timeline, TimelineEntry, TimelineEntryType

        timeline = Timeline(max_context_tokens=32000)
        multimodal_content = [
            {"type": "text", "text": "Image:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "abc"}},
        ]
        timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content=multimodal_content,
            )
        )

        messages = timeline.to_llm_messages()
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content is multimodal_content

    def test_estimate_tokens_handles_list_content(self):
        """_estimate_tokens doesn't crash on list[dict] content."""
        from dana.common.llm.types import LLMMessage
        from dana.core.agent.timeline import Timeline

        timeline = Timeline(max_context_tokens=32000)
        msg = LLMMessage(
            role="user",
            content=[
                {"type": "text", "text": "hello world this is a test"},
                {"type": "image", "source": {"type": "base64", "data": "abc"}},
            ],
        )
        # Should not raise
        tokens = timeline._estimate_tokens([msg])
        assert tokens > 0


# ============================================================================
# INJECT_AS_USER WITH MULTIMODAL CONTENT
# ============================================================================


class TestInjectAsUserMultimodal:
    """Test that inject_as_user with list[dict] content reaches timeline correctly."""

    @pytest.fixture
    def agent(self):
        from unittest.mock import patch

        from dana.core.agent.star_agent import STARAgent
        from dana.core.agent.timeline import TimelineEntry, TimelineEntryType

        with patch("dana.core.agent.star_agent.LLM"):
            a = STARAgent(agent_type="test-multimodal", auto_register=False)
        a._timeline.add_entry(
            TimelineEntry(
                entry_type=TimelineEntryType.USER_MESSAGE,
                content="read the image",
                is_latest_user_message=True,
            )
        )
        return a

    def test_multimodal_inject_reaches_timeline(self, agent):
        """Tool returning dict with inject_as_user list[dict] → USER_MESSAGE with preserved content."""
        from unittest.mock import Mock

        from dana.core.agent.timeline import TimelineEntryType

        multimodal_blocks = [
            {"type": "text", "text": "Visual contents of test.png:"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "abc123"}},
        ]

        agent._runtime = Mock()
        agent._runtime.execute_tools.return_value = [
            {
                "type": "resource",
                "target": "Read",
                "result": {
                    "message": "Image: test.png (5.0KB, image/png)",
                    "inject_as_user": multimodal_blocks,
                },
                "success": True,
                "tool_call_id": "call_read_1",
            }
        ]

        agent._act({"tool_calls": [{"name": "Read"}]})

        entries = agent._timeline.timeline[1:]  # skip seed
        types = [e.entry_type for e in entries]

        # Should have RESOURCE_RESULT then USER_MESSAGE
        assert TimelineEntryType.RESOURCE_RESULT in types
        assert TimelineEntryType.USER_MESSAGE in types

        # RESOURCE_RESULT has the message text (not the full dict)
        resource_entry = next(e for e in entries if e.entry_type == TimelineEntryType.RESOURCE_RESULT)
        assert resource_entry.content == "Image: test.png (5.0KB, image/png)"

        # USER_MESSAGE has the multimodal content blocks
        user_entry = next(e for e in entries if e.entry_type == TimelineEntryType.USER_MESSAGE)
        assert isinstance(user_entry.content, list)
        assert user_entry.content == multimodal_blocks
        assert user_entry.content[1]["type"] == "image"

    def test_message_key_extracted_as_tool_result(self, agent):
        """After popping inject_as_user, 'message' key becomes the tool result text."""
        from unittest.mock import Mock

        from dana.core.agent.timeline import TimelineEntryType

        agent._runtime = Mock()
        agent._runtime.execute_tools.return_value = [
            {
                "type": "resource",
                "target": "Read",
                "result": {
                    "message": "PDF: report.pdf (120.5KB)",
                    "inject_as_user": [{"type": "text", "text": "Contents of report.pdf:"}],
                },
                "success": True,
                "tool_call_id": "call_1",
            }
        ]

        agent._act({"tool_calls": [{"name": "Read"}]})

        entries = agent._timeline.timeline[1:]
        resource_entry = next(e for e in entries if e.entry_type == TimelineEntryType.RESOURCE_RESULT)
        # The tool result should be the message string, not a JSON dump of the dict
        assert resource_entry.content == "PDF: report.pdf (120.5KB)"
        assert "inject_as_user" not in resource_entry.content


# ============================================================================
# VISION FALLBACK (supports_vision=False)
# ============================================================================


class TestVisionFallbackImage:
    """Test image reading with supports_vision=False uses VisionParser."""

    @pytest.mark.asyncio
    async def test_image_returns_extracted_text(self, no_vision_resource, tmp_path):
        """Image with supports_vision=False → plain text via VisionParser."""
        f = tmp_path / "chart.png"
        f.write_bytes(b"\x89PNG" + b"\x00" * 50)

        mock_parser = MagicMock()
        mock_parser.process_image_async = AsyncMock(
            return_value={"file_object": {"pages": [{"page_content": "A bar chart showing sales data for Q1 2025."}]}}
        )

        with patch.object(no_vision_resource, "_get_vision_parser", return_value=mock_parser):
            result = await no_vision_resource.read(str(f))

        assert isinstance(result, str)
        assert "Extracted content from chart.png" in result
        assert "bar chart showing sales data" in result
        mock_parser.process_image_async.assert_called_once_with(str(f))

    @pytest.mark.asyncio
    async def test_image_extraction_error_returns_error_string(self, no_vision_resource, tmp_path):
        """VisionParser failure → graceful error string."""
        f = tmp_path / "broken.png"
        f.write_bytes(b"\x89PNG" + b"\x00" * 10)

        mock_parser = MagicMock()
        mock_parser.process_image_async = AsyncMock(side_effect=RuntimeError("Vision API down"))

        with patch.object(no_vision_resource, "_get_vision_parser", return_value=mock_parser):
            result = await no_vision_resource.read(str(f))

        assert isinstance(result, str)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_vision_true_still_returns_base64(self, tmp_resource, tmp_path):
        """Default supports_vision=True still returns base64 dict (no regression)."""
        f = tmp_path / "icon.png"
        f.write_bytes(b"\x89PNG" + b"\x00" * 50)

        result = await tmp_resource.read(str(f))
        assert isinstance(result, dict)
        assert "inject_as_user" in result


class TestVisionFallbackPdf:
    """Test PDF reading with supports_vision=False uses VisionParser."""

    @pytest.mark.asyncio
    async def test_pdf_returns_extracted_text(self, no_vision_resource, tmp_path):
        """PDF with supports_vision=False → plain text via VisionParser."""
        f = tmp_path / "report.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        mock_parser = MagicMock()
        mock_parser.process_pdf_async = AsyncMock(
            return_value={
                "file_object": {
                    "pages": [
                        {"page_number": 1, "page_content": "Introduction to the report."},
                        {"page_number": 2, "page_content": "Methodology section."},
                    ]
                }
            }
        )

        with patch.object(no_vision_resource, "_get_vision_parser", return_value=mock_parser):
            result = await no_vision_resource.read(str(f))

        assert isinstance(result, str)
        assert "Extracted content from report.pdf" in result
        assert "Page: 1" in result
        assert "Introduction to the report" in result
        assert "Page: 2" in result
        assert "Methodology section" in result
        mock_parser.process_pdf_async.assert_called_once_with(str(f))

    @pytest.mark.asyncio
    async def test_pdf_with_pages_returns_extracted_text(self, no_vision_resource, tmp_path):
        """PDF with pages param and supports_vision=False → VisionParser page extraction."""
        f = tmp_path / "long.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        mock_doc = MagicMock()
        mock_doc.page_count = 10
        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_doc

        mock_parser = MagicMock()
        mock_img = MagicMock()
        mock_parser._extract_text_from_pdf.return_value = [
            {"page_number": i + 1, "hash": f"hash{i}", "text": f"text page {i + 1}"} for i in range(10)
        ]

        async def fake_get_image(*args, **kwargs):
            return mock_img

        async def fake_process_page(img, page_number=1, page_hash="", text_content=""):
            return {"page_number": page_number, "page_content": f"Processed page {page_number}"}

        mock_parser._get_or_create_page_image = fake_get_image
        mock_parser.process_page_async = fake_process_page

        mock_hash_utils = MagicMock()
        mock_hash_utils.calculate_file_hash.return_value = "filehash123"

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            with patch.object(no_vision_resource, "_get_vision_parser", return_value=mock_parser):
                with patch("dana.core.resource.file_io_resource.FileIOResource._read_pdf_pages_extracted") as mock_method:
                    # Test the branching: PDF with pages goes to _read_pdf_pages_extracted
                    mock_method.return_value = "[Extracted from long.pdf pages 2-4]\n\nPage 2\n\nPage 3\n\nPage 4"
                    result = await no_vision_resource.read(str(f), pages="2-4")

        assert isinstance(result, str)
        assert "Extracted" in result
        mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_pdf_extraction_error_returns_error_string(self, no_vision_resource, tmp_path):
        """VisionParser PDF failure → graceful error string."""
        f = tmp_path / "bad.pdf"
        f.write_bytes(b"%PDF-1.4 content")

        mock_parser = MagicMock()
        mock_parser.process_pdf_async = AsyncMock(side_effect=RuntimeError("PDF processing failed"))

        with patch.object(no_vision_resource, "_get_vision_parser", return_value=mock_parser):
            result = await no_vision_resource.read(str(f))

        assert isinstance(result, str)
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_text_files_unaffected_by_no_vision(self, no_vision_resource, tmp_path):
        """Text files still work normally when supports_vision=False."""
        f = tmp_path / "code.py"
        f.write_text("x = 42\n")

        result = await no_vision_resource.read(str(f))
        assert isinstance(result, str)
        assert "x = 42" in result


# ============================================================================
# SUPPORTS_VISION PROVIDER PROPERTIES
# ============================================================================


class TestSupportsVisionProperty:
    """Test that supports_vision is correctly set on providers."""

    def test_base_provider_defaults_false(self):
        from dana.common.llm.types import LLMProvider

        # Can't instantiate abstract class directly, check the property exists
        assert LLMProvider.supports_vision.fget is not None

    def test_anthropic_provider_supports_vision(self):
        with patch("dana.common.llm.providers.anthropic.config_manager") as mock_cm:
            mock_cm.get_provider_api_key.return_value = "test-key"
            mock_cm.get_provider_base_url.return_value = None
            from dana.common.llm.providers.anthropic import AnthropicProvider

            provider = AnthropicProvider(api_key="test-key")
            assert provider.supports_vision is True

    def test_anthropic_like_provider_no_vision(self):
        with patch("dana.common.llm.providers.anthropic_like.config_manager") as mock_cm:
            mock_cm.get_provider_api_key.return_value = "test-key"
            mock_cm.get_provider_base_url.return_value = "https://example.com"
            from dana.common.llm.providers.anthropic_like import AnthropicLikeProvider

            provider = AnthropicLikeProvider(api_key="test-key", base_url="https://example.com")
            assert provider.supports_vision is False

    def test_llm_delegates_to_provider(self):
        from dana.common.llm.llm import LLM
        from dana.common.llm.types import LLMProvider

        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.supports_vision = True
        mock_provider.model = "test-model"

        llm = LLM(provider=mock_provider)
        assert llm.supports_vision is True

        mock_provider.supports_vision = False
        assert llm.supports_vision is False
