"""
Unit tests for LLM types module
"""

import pytest

from dana.common.llm.types import LLMMessage, LLMProvider, LLMResponse


class TestLLMMessage:
    """Unit tests for LLMMessage dataclass"""

    def test_llm_message_creation(self):
        """Test creating an LLMMessage instance"""
        message = LLMMessage(role="user", content="Hello, world!")

        assert message.role == "user"
        assert message.content == "Hello, world!"

    def test_llm_message_different_roles(self):
        """Test creating LLMMessage with different roles"""
        system_msg = LLMMessage(role="system", content="You are a helpful assistant")
        user_msg = LLMMessage(role="user", content="Hello")
        assistant_msg = LLMMessage(role="assistant", content="Hi there!")

        assert system_msg.role == "system"
        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"

    def test_llm_message_empty_content(self):
        """Test creating LLMMessage with empty content"""
        message = LLMMessage(role="user", content="")

        assert message.role == "user"
        assert message.content == ""

    def test_llm_message_equality(self):
        """Test LLMMessage equality"""
        msg1 = LLMMessage(role="user", content="Hello")
        msg2 = LLMMessage(role="user", content="Hello")
        msg3 = LLMMessage(role="user", content="Hi")

        assert msg1 == msg2
        assert msg1 != msg3

    def test_llm_message_repr(self):
        """Test LLMMessage string representation"""
        message = LLMMessage(role="user", content="Hello")
        repr_str = repr(message)

        assert "LLMMessage" in repr_str
        assert "role='user'" in repr_str
        assert "content='Hello'" in repr_str


class TestLLMResponse:
    """Unit tests for LLMResponse dataclass"""

    def test_llm_response_creation(self):
        """Test creating an LLMResponse instance"""
        response = LLMResponse(
            content="Hello, world!", model="gpt-4", usage={"prompt_tokens": 10, "completion_tokens": 5}, finish_reason="stop"
        )

        assert response.content == "Hello, world!"
        assert response.model == "gpt-4"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5}
        assert response.finish_reason == "stop"

    def test_llm_response_minimal(self):
        """Test creating LLMResponse with minimal required fields"""
        response = LLMResponse(content="Hello", model="gpt-3.5-turbo")

        assert response.content == "Hello"
        assert response.model == "gpt-3.5-turbo"
        assert response.usage is None
        assert response.finish_reason is None

    def test_llm_response_optional_fields(self):
        """Test LLMResponse with optional fields set to None"""
        response = LLMResponse(content="Hello", model="gpt-4", usage=None, finish_reason=None)

        assert response.content == "Hello"
        assert response.model == "gpt-4"
        assert response.usage is None
        assert response.finish_reason is None

    def test_llm_response_equality(self):
        """Test LLMResponse equality"""
        resp1 = LLMResponse(content="Hello", model="gpt-4")
        resp2 = LLMResponse(content="Hello", model="gpt-4")
        resp3 = LLMResponse(content="Hi", model="gpt-4")

        assert resp1 == resp2
        assert resp1 != resp3

    def test_llm_response_repr(self):
        """Test LLMResponse string representation"""
        response = LLMResponse(content="Hello", model="gpt-4")
        repr_str = repr(response)

        assert "LLMResponse" in repr_str
        assert "content='Hello'" in repr_str
        assert "model='gpt-4'" in repr_str

    def test_llm_response_with_reasoning_fields(self):
        """Test LLMResponse with reasoning fields for thinking models"""
        response = LLMResponse(
            content="The answer is 42",
            model="gpt-5-thinking-mini",
            reasoning_content="Let me think about this problem step by step...",
            reasoning_tokens=150,
        )

        assert response.content == "The answer is 42"
        assert response.model == "gpt-5-thinking-mini"
        assert response.reasoning_content == "Let me think about this problem step by step..."
        assert response.reasoning_tokens == 150

    def test_llm_response_reasoning_fields_optional(self):
        """Test that reasoning fields default to None for non-thinking models"""
        response = LLMResponse(content="Hello", model="gpt-4")

        assert response.reasoning_content is None
        assert response.reasoning_tokens is None

    def test_llm_response_reasoning_tokens_only(self):
        """Test LLMResponse with only reasoning_tokens (OpenAI thinking models)"""
        # OpenAI thinking models expose token count but not the actual reasoning content
        response = LLMResponse(
            content="The answer is 42",
            model="gpt-5-thinking",
            reasoning_tokens=500,
        )

        assert response.reasoning_content is None  # OpenAI doesn't expose reasoning content
        assert response.reasoning_tokens == 500

    def test_llm_response_reasoning_content_only(self):
        """Test LLMResponse with only reasoning_content (e.g., DeepSeek)"""
        # Some providers expose reasoning content but not token counts
        response = LLMResponse(
            content="The answer is 42",
            model="deepseek-reasoner",
            reasoning_content="Step 1: Consider the question...",
        )

        assert response.reasoning_content == "Step 1: Consider the question..."
        assert response.reasoning_tokens is None


class TestLLMProvider:
    """Unit tests for LLMProvider abstract base class"""

    def test_llm_provider_is_abstract(self):
        """Test that LLMProvider cannot be instantiated directly"""
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore[abstract]

    def test_llm_provider_has_chat_method(self):
        """Test that LLMProvider has the required chat method"""

        # Create a concrete implementation
        class ConcreteProvider(LLMProvider):
            async def chat(self, messages, **kwargs):
                return LLMResponse(content="test", model="test")

        provider = ConcreteProvider()
        assert hasattr(provider, "chat")
        assert callable(provider.chat)

    def test_llm_provider_chat_signature(self):
        """Test that chat method has correct signature"""

        # Create a concrete implementation
        class ConcreteProvider(LLMProvider):
            async def chat(self, messages, **kwargs):
                return LLMResponse(content="test", model="test")

        provider = ConcreteProvider()

        # Check method signature
        import inspect

        sig = inspect.signature(provider.chat)
        assert "messages" in sig.parameters
        assert "kwargs" in sig.parameters

    def test_llm_provider_inheritance(self):
        """Test that a class can inherit from LLMProvider"""

        class TestProvider(LLMProvider):
            async def chat(self, messages, **kwargs):
                return LLMResponse(content="test", model="test")

        provider = TestProvider()
        assert isinstance(provider, LLMProvider)

    def test_llm_provider_missing_chat_method(self):
        """Test that missing chat method raises TypeError"""

        class IncompleteProvider(LLMProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_concrete_provider_usage(self):
        """Test using a concrete provider implementation"""

        class TestProvider(LLMProvider):
            async def chat(self, messages, **kwargs):
                return LLMResponse(
                    content="Test response", model="test-model", usage={"prompt_tokens": 5, "completion_tokens": 3}, finish_reason="stop"
                )

        provider = TestProvider()
        messages = [LLMMessage(role="user", content="Hello")]

        response = await provider.chat(messages)

        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.usage == {"prompt_tokens": 5, "completion_tokens": 3}
        assert response.finish_reason == "stop"
