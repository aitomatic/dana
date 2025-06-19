"""Tests for OpenDXA common exceptions."""

from opendxa.common.exceptions import (
    AgentError,
    CommunicationError,
    ConfigurationError,
    DXAContextError,
    DXAMemoryError,
    DXAValidationError,
    LLMAuthenticationError,
    LLMContextLengthError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponseError,
    NetworkError,
    OpenDXAError,
    ReasoningError,
    ResourceError,
    StateError,
    ValidationError,  # Backward compatibility alias
    WebSocketError,
)


class TestOpenDXAError:
    """Test the base OpenDXAError class."""

    def test_basic_initialization(self):
        """Test basic error initialization."""
        error = OpenDXAError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_inheritance(self):
        """Test that all OpenDXA exceptions inherit from OpenDXAError."""
        exception_classes = [
            ConfigurationError,
            LLMError,
            LLMProviderError,
            LLMRateLimitError,
            LLMAuthenticationError,
            LLMContextLengthError,
            LLMResponseError,
            ResourceError,
            NetworkError,
            WebSocketError,
            ReasoningError,
            AgentError,
            CommunicationError,
            DXAValidationError,
            ValidationError,  # Backward compatibility alias
            StateError,
            DXAMemoryError,
            DXAContextError,
        ]

        for exc_class in exception_classes:
            assert issubclass(exc_class, OpenDXAError)


class TestLLMProviderError:
    """Test LLMProviderError and its subclasses."""

    def test_initialization_with_status_code(self):
        """Test LLMProviderError with status code."""
        error = LLMProviderError("openai", 429, "Rate limit exceeded")
        expected_msg = "openai API error (status 429): Rate limit exceeded"
        assert str(error) == expected_msg
        assert error.provider == "openai"
        assert error.status_code == 429

    def test_initialization_without_status_code(self):
        """Test LLMProviderError without status code."""
        error = LLMProviderError("anthropic", None, "General error")
        expected_msg = "anthropic API error: General error"
        assert str(error) == expected_msg
        assert error.provider == "anthropic"
        assert error.status_code is None

    def test_subclass_inheritance(self):
        """Test that LLM provider error subclasses inherit properly."""
        rate_limit_error = LLMRateLimitError("openai", 429, "Too many requests")
        auth_error = LLMAuthenticationError("openai", 401, "Invalid API key")
        context_error = LLMContextLengthError("openai", 400, "Context too long")

        assert isinstance(rate_limit_error, LLMProviderError)
        assert isinstance(auth_error, LLMProviderError)
        assert isinstance(context_error, LLMProviderError)

        assert isinstance(rate_limit_error, LLMError)
        assert isinstance(auth_error, LLMError)
        assert isinstance(context_error, LLMError)


class TestLLMResponseError:
    """Test LLMResponseError."""

    def test_initialization_with_response(self):
        """Test LLMResponseError with response data."""
        response_data = {"error": "Invalid format", "code": 400}
        error = LLMResponseError("Response parsing failed", response_data)

        assert str(error) == "Response parsing failed"
        assert error.response == response_data

    def test_initialization_without_response(self):
        """Test LLMResponseError without response data."""
        error = LLMResponseError("Response parsing failed")

        assert str(error) == "Response parsing failed"
        assert error.response is None

    def test_inheritance(self):
        """Test LLMResponseError inheritance."""
        error = LLMResponseError("Test error")
        assert isinstance(error, LLMError)
        assert isinstance(error, OpenDXAError)


class TestBasicExceptions:
    """Test basic exception classes."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"
        assert isinstance(error, OpenDXAError)

    def test_resource_error(self):
        """Test ResourceError."""
        error = ResourceError("Resource not found")
        assert str(error) == "Resource not found"
        assert isinstance(error, OpenDXAError)

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, OpenDXAError)

    def test_websocket_error(self):
        """Test WebSocketError."""
        error = WebSocketError("WebSocket connection lost")
        assert str(error) == "WebSocket connection lost"
        assert isinstance(error, OpenDXAError)

    def test_reasoning_error(self):
        """Test ReasoningError."""
        error = ReasoningError("Reasoning failed")
        assert str(error) == "Reasoning failed"
        assert isinstance(error, OpenDXAError)

    def test_agent_error(self):
        """Test AgentError."""
        error = AgentError("Agent initialization failed")
        assert str(error) == "Agent initialization failed"
        assert isinstance(error, OpenDXAError)

    def test_communication_error(self):
        """Test CommunicationError."""
        error = CommunicationError("Communication failed")
        assert str(error) == "Communication failed"
        assert isinstance(error, OpenDXAError)

    def test_dxa_validation_error(self):
        """Test DXAValidationError."""
        error = DXAValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, OpenDXAError)

    def test_validation_error_backward_compatibility(self):
        """Test ValidationError backward compatibility alias."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, OpenDXAError)
        assert isinstance(error, DXAValidationError)
        # Verify it's actually the same class
        assert ValidationError is DXAValidationError

    def test_state_error(self):
        """Test StateError."""
        error = StateError("Invalid state")
        assert str(error) == "Invalid state"
        assert isinstance(error, OpenDXAError)

    def test_dxa_memory_error(self):
        """Test DXAMemoryError."""
        error = DXAMemoryError("Memory allocation failed")
        assert str(error) == "Memory allocation failed"
        assert isinstance(error, OpenDXAError)

    def test_dxa_context_error(self):
        """Test DXAContextError."""
        error = DXAContextError("Context error")
        assert str(error) == "Context error"
        assert isinstance(error, OpenDXAError)
