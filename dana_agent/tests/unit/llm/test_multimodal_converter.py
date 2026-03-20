"""Tests for multimodal content converter module."""

from dana.common.llm.multimodal_converter import (
    convert_for_anthropic,
    convert_for_openai,
    convert_for_openai_responses,
    is_multimodal_content,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

IMAGE_BLOCK_BASE64 = {
    "type": "image",
    "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo="},
}

IMAGE_BLOCK_URL = {
    "type": "image",
    "source": {"type": "url", "url": "https://example.com/img.png"},
}

AUDIO_BLOCK = {
    "type": "audio",
    "source": {"type": "base64", "media_type": "audio/wav", "data": "UklGR..."},
}

VIDEO_BLOCK = {
    "type": "video",
    "source": {"type": "base64", "media_type": "video/mp4", "data": "AAAA..."},
}

DOCUMENT_BLOCK = {
    "type": "document",
    "source": {"type": "base64", "media_type": "application/pdf", "data": "JVBERi0="},
}

TEXT_BLOCK = {"type": "text", "text": "Describe this image."}


# ---------------------------------------------------------------------------
# is_multimodal_content
# ---------------------------------------------------------------------------


class TestIsMultimodalContent:
    def test_string_content(self):
        assert not is_multimodal_content("hello world")

    def test_text_only_blocks(self):
        assert not is_multimodal_content([TEXT_BLOCK])

    def test_image_blocks(self):
        assert is_multimodal_content([TEXT_BLOCK, IMAGE_BLOCK_BASE64])

    def test_audio_blocks(self):
        assert is_multimodal_content([AUDIO_BLOCK])

    def test_video_blocks(self):
        assert is_multimodal_content([VIDEO_BLOCK])

    def test_document_blocks(self):
        assert is_multimodal_content([DOCUMENT_BLOCK])

    def test_empty_list(self):
        assert not is_multimodal_content([])


# ---------------------------------------------------------------------------
# Anthropic converter
# ---------------------------------------------------------------------------


class TestConvertForAnthropic:
    def test_image_passthrough(self):
        result = convert_for_anthropic([TEXT_BLOCK, IMAGE_BLOCK_BASE64], supports_vision=True)
        assert result[0] == TEXT_BLOCK
        assert result[1] == IMAGE_BLOCK_BASE64

    def test_image_url_passthrough(self):
        result = convert_for_anthropic([IMAGE_BLOCK_URL], supports_vision=True)
        assert result[0] == IMAGE_BLOCK_URL

    def test_document_passthrough(self):
        result = convert_for_anthropic([DOCUMENT_BLOCK], supports_vision=True)
        assert result[0] == DOCUMENT_BLOCK

    def test_audio_unsupported(self):
        result = convert_for_anthropic([AUDIO_BLOCK], supports_audio=False)
        assert result[0]["type"] == "text"
        assert "not supported" in result[0]["text"]

    def test_video_unsupported(self):
        result = convert_for_anthropic([VIDEO_BLOCK], supports_video=False)
        assert result[0]["type"] == "text"
        assert "not supported" in result[0]["text"]

    def test_vision_unsupported_fallback(self):
        result = convert_for_anthropic([IMAGE_BLOCK_BASE64], supports_vision=False)
        assert result[0]["type"] == "text"
        assert "not supported" in result[0]["text"]

    def test_mixed_content(self):
        blocks = [TEXT_BLOCK, IMAGE_BLOCK_BASE64, AUDIO_BLOCK, VIDEO_BLOCK]
        result = convert_for_anthropic(blocks, supports_vision=True, supports_audio=False, supports_video=False)
        assert result[0] == TEXT_BLOCK
        assert result[1] == IMAGE_BLOCK_BASE64  # kept
        assert result[2]["type"] == "text"  # audio placeholder
        assert result[3]["type"] == "text"  # video placeholder


# ---------------------------------------------------------------------------
# OpenAI Chat Completions converter
# ---------------------------------------------------------------------------


class TestConvertForOpenAI:
    def test_image_base64(self):
        result = convert_for_openai([IMAGE_BLOCK_BASE64], supports_vision=True)
        assert result[0]["type"] == "image_url"
        assert result[0]["image_url"]["url"] == "data:image/png;base64,iVBORw0KGgo="
        assert result[0]["image_url"]["detail"] == "auto"

    def test_image_url(self):
        result = convert_for_openai([IMAGE_BLOCK_URL], supports_vision=True)
        assert result[0]["type"] == "image_url"
        assert result[0]["image_url"]["url"] == "https://example.com/img.png"

    def test_audio_supported(self):
        result = convert_for_openai([AUDIO_BLOCK], supports_audio=True)
        assert result[0]["type"] == "input_audio"
        assert result[0]["input_audio"]["format"] == "wav"
        assert result[0]["input_audio"]["data"] == "UklGR..."

    def test_audio_mp3_format(self):
        mp3_block = {
            "type": "audio",
            "source": {"type": "base64", "media_type": "audio/mp3", "data": "data"},
        }
        result = convert_for_openai([mp3_block], supports_audio=True)
        assert result[0]["input_audio"]["format"] == "mp3"

    def test_audio_mpeg_format(self):
        mpeg_block = {
            "type": "audio",
            "source": {"type": "base64", "media_type": "audio/mpeg", "data": "data"},
        }
        result = convert_for_openai([mpeg_block], supports_audio=True)
        assert result[0]["input_audio"]["format"] == "mp3"

    def test_video_always_unsupported(self):
        result = convert_for_openai([VIDEO_BLOCK], supports_video=True)
        assert result[0]["type"] == "text"
        assert "not supported" in result[0]["text"]

    def test_document_supported(self):
        result = convert_for_openai([DOCUMENT_BLOCK], supports_vision=True)
        assert result[0]["type"] == "file"
        assert "base64" in result[0]["file"]["file_data"]

    def test_vision_unsupported_fallback(self):
        result = convert_for_openai([IMAGE_BLOCK_BASE64], supports_vision=False)
        assert result[0]["type"] == "text"
        assert "not supported" in result[0]["text"]

    def test_text_passthrough(self):
        result = convert_for_openai([TEXT_BLOCK])
        assert result[0] == TEXT_BLOCK


# ---------------------------------------------------------------------------
# OpenAI Responses API converter
# ---------------------------------------------------------------------------


class TestConvertForOpenAIResponses:
    def test_text_converted(self):
        result = convert_for_openai_responses([TEXT_BLOCK])
        assert result[0]["type"] == "input_text"
        assert result[0]["text"] == "Describe this image."

    def test_image_base64(self):
        result = convert_for_openai_responses([IMAGE_BLOCK_BASE64], supports_vision=True)
        assert result[0]["type"] == "input_image"
        assert "data:image/png;base64," in result[0]["image_url"]

    def test_image_url(self):
        result = convert_for_openai_responses([IMAGE_BLOCK_URL], supports_vision=True)
        assert result[0]["type"] == "input_image"
        assert result[0]["image_url"] == "https://example.com/img.png"

    def test_vision_unsupported(self):
        result = convert_for_openai_responses([IMAGE_BLOCK_BASE64], supports_vision=False)
        assert result[0]["type"] == "input_text"
        assert "not supported" in result[0]["text"]


# ---------------------------------------------------------------------------
# Placeholder content
# ---------------------------------------------------------------------------


class TestPlaceholder:
    def test_includes_type_and_media(self):
        result = convert_for_anthropic([VIDEO_BLOCK], supports_video=False)
        text = result[0]["text"]
        assert "video" in text
        assert "video/mp4" in text

    def test_audio_placeholder(self):
        result = convert_for_openai([AUDIO_BLOCK], supports_audio=False)
        text = result[0]["text"]
        assert "audio" in text
        assert "audio/wav" in text
