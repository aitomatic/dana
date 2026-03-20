"""Tests for provider prepare_messages() with multimodal content."""

from dana.common.llm.providers.anthropic import prepare_anthropic_messages
from dana.common.llm.types import LLMMessage, LLMProvider
from dana.core.timeline.native_message import NativeMessage


# Canonical test blocks
IMAGE_BLOCK = {
    "type": "image",
    "source": {"type": "base64", "media_type": "image/png", "data": "abc123"},
}
TEXT_BLOCK = {"type": "text", "text": "What is this?"}
MIXED_CONTENT = [TEXT_BLOCK, IMAGE_BLOCK]


# ---------------------------------------------------------------------------
# Anthropic prepare_messages
# ---------------------------------------------------------------------------


class TestAnthropicPrepareMultimodal:
    def test_multimodal_user_message(self):
        msgs = [LLMMessage(role="user", content=MIXED_CONTENT)]
        system, result = prepare_anthropic_messages(msgs)
        assert system is None
        assert len(result) == 1
        assert result[0]["role"] == "user"
        # Content should be list of blocks (Anthropic pass-through)
        content = result[0]["content"]
        assert isinstance(content, list)
        assert content[0] == TEXT_BLOCK
        assert content[1]["type"] == "image"

    def test_plain_text_user_message_unchanged(self):
        msgs = [LLMMessage(role="user", content="Hello")]
        _, result = prepare_anthropic_messages(msgs)
        assert result[0]["content"] == "Hello"


# ---------------------------------------------------------------------------
# OpenAI prepare_messages
# ---------------------------------------------------------------------------


class TestOpenAIPrepareMultimodal:
    def _make_provider(self):
        """Create a minimal OpenAI-compatible provider for testing prepare_messages."""
        from dana.common.llm.providers.openai_compatible_base import OpenAICompatibleProvider

        p = OpenAICompatibleProvider.__new__(OpenAICompatibleProvider)
        p.model = "gpt-4o"
        p.supports_vision = True
        p.supports_audio = False
        p.supports_video = False
        return p

    def test_multimodal_user_message_converts_to_openai_format(self):
        provider = self._make_provider()
        msgs = [LLMMessage(role="user", content=MIXED_CONTENT)]
        _, result = provider.prepare_messages(msgs)
        content = result[0]["content"]
        assert isinstance(content, list)
        # Text block passed through
        assert content[0] == TEXT_BLOCK
        # Image converted to OpenAI format
        assert content[1]["type"] == "image_url"
        assert "data:image/png;base64,abc123" in content[1]["image_url"]["url"]

    def test_plain_text_user_message_unchanged(self):
        provider = self._make_provider()
        msgs = [LLMMessage(role="user", content="Hello")]
        _, result = provider.prepare_messages(msgs)
        assert result[0]["content"] == "Hello"


# ---------------------------------------------------------------------------
# Base LLMProvider fallback
# ---------------------------------------------------------------------------


class TestBaseLLMProviderMultimodalFallback:
    def test_list_content_extracted_as_text(self):
        provider = LLMProvider()
        msgs = [LLMMessage(role="user", content=MIXED_CONTENT)]
        _, result = provider.prepare_messages(msgs)
        # Base class extracts text from blocks
        content = result[0]["content"]
        assert isinstance(content, str)
        assert "What is this?" in content
        assert "[image content]" in content


# ---------------------------------------------------------------------------
# NativeMessage multimodal
# ---------------------------------------------------------------------------


class TestNativeMessageMultimodal:
    def test_list_content_creation(self):
        nm = NativeMessage(role="user", content=MIXED_CONTENT)
        assert isinstance(nm.content, list)
        assert len(nm.content) == 2

    def test_list_content_to_dict(self):
        nm = NativeMessage(role="user", content=MIXED_CONTENT)
        d = nm.to_dict()
        assert d["content"] == MIXED_CONTENT
        assert d["role"] == "user"

    def test_list_content_from_dict(self):
        data = {
            "role": "user",
            "content": MIXED_CONTENT,
            "timestamp": "2026-03-20T15:00:00",
        }
        nm = NativeMessage.from_dict(data)
        assert isinstance(nm.content, list)
        assert nm.content[1]["type"] == "image"

    def test_list_content_to_llm_message(self):
        nm = NativeMessage(role="user", content=MIXED_CONTENT)
        lm = nm.to_llm_message()
        assert isinstance(lm.content, list)
        assert lm.role == "user"

    def test_string_content_still_works(self):
        nm = NativeMessage(role="user", content="hello")
        assert isinstance(nm.content, str)
        d = nm.to_dict()
        assert d["content"] == "hello"
        lm = nm.to_llm_message()
        assert lm.content == "hello"
