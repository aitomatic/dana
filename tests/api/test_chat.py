from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from dana.api.core import models, schemas
from dana.api.server.server import create_app
from dana.api.services.chat_service import ChatService
from dana.api.services.conversation_service import ConversationService
from dana.core.lang.sandbox_context import SandboxContext


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


class TestChatEndpoint:
    """Test cases for chat endpoint"""

    def test_chat_with_agent_success(self, client):
        """Test successful chat with agent"""
        from dana.api.services.chat_service import get_chat_service

        # Mock chat service
        mock_chat_service = Mock()
        mock_chat_service.process_chat_message = AsyncMock(
            return_value=schemas.ChatResponse(
                success=True,
                message="Hello, agent!",
                conversation_id=1,
                message_id=2,
                agent_response="Hello! How can I help you today?",
                context={"user_id": 123},
                error=None,
            )
        )

        # Override FastAPI dependency
        client.app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

        try:
            # Test request
            response = client.post("/api/chat/", json={"message": "Hello, agent!", "agent_id": 1, "context": {"user_id": 123}})

            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Hello, agent!"
            assert data["conversation_id"] == 1
            assert data["message_id"] == 2
            assert data["agent_response"] == "Hello! How can I help you today?"
            assert data["context"] == {"user_id": 123}
            assert data["error"] is None
        finally:
            # Clean up dependency override
            client.app.dependency_overrides.clear()

    def test_chat_with_agent_not_found(self, client):
        """Test chat with non-existent agent"""
        from dana.api.services.chat_service import get_chat_service

        # Mock chat service to raise agent not found error
        mock_chat_service = Mock()
        mock_chat_service.process_chat_message = AsyncMock(side_effect=HTTPException(status_code=404, detail="Agent 999 not found"))

        # Override FastAPI dependency
        client.app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

        try:
            # Test request
            response = client.post("/api/chat/", json={"message": "Hello, agent!", "agent_id": 999, "context": {"user_id": 123}})

            # Assertions
            assert response.status_code == 404
            data = response.json()
            assert "Agent 999 not found" in data["detail"]
        finally:
            # Clean up dependency override
            client.app.dependency_overrides.clear()

    def test_chat_with_agent_service_error(self, client):
        """Test chat when service returns error"""
        from dana.api.services.chat_service import get_chat_service

        # Mock chat service error
        mock_chat_service = Mock()
        mock_chat_service.process_chat_message = AsyncMock(
            return_value=schemas.ChatResponse(
                success=False,
                message="Hello, agent!",
                conversation_id=0,
                message_id=0,
                agent_response="",
                context={"user_id": 123},
                error="Agent execution failed",
            )
        )

        # Override FastAPI dependency
        client.app.dependency_overrides[get_chat_service] = lambda: mock_chat_service

        try:
            # Test request
            response = client.post("/api/chat/", json={"message": "Hello, agent!", "agent_id": 1, "context": {"user_id": 123}})

            # Assertions
            assert response.status_code == 200  # Service error returned as response, not HTTP error
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "Agent execution failed"
        finally:
            # Clean up dependency override
            client.app.dependency_overrides.clear()

    def test_chat_with_agent_missing_required_fields(self, client):
        """Test chat with missing required fields"""
        # Test missing message
        response = client.post("/api/chat/", json={"agent_id": 1, "context": {"user_id": 123}})
        assert response.status_code == 422

        # Test missing agent_id
        response = client.post("/api/chat/", json={"message": "Hello, agent!", "context": {"user_id": 123}})
        assert response.status_code == 422

    def test_chat_with_agent_invalid_data_types(self, client):
        """Test chat with invalid data types"""
        # Test invalid agent_id type - use a string with invalid characters
        response = client.post("/api/chat/", json={"message": "Hello, agent!", "agent_id": "invalid@agent#id", "context": {"user_id": 123}})
        assert response.status_code == 422

        # Test invalid message type
        response = client.post("/api/chat/", json={"message": 123, "agent_id": 1, "context": {"user_id": 123}})
        assert response.status_code == 422


@pytest.mark.skip(reason="ChatService interface changed during refactoring - these tests are obsolete")
class TestChatService:
    """Test cases for ChatService"""

    @pytest.fixture
    def chat_service(self):
        """Create ChatService instance for testing"""
        _conversation_service = Mock(spec=ConversationService)
        return ChatService()

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def mock_agent(self):
        agent = Mock(spec=models.Agent)
        agent.id = 1
        agent.name = "Test Agent"
        agent.config = {
            "dana_code": """\"\"\"A simple assistant agent that can help with various tasks.\"\"\"

# Agent Card declaration
agent AssistantAgent:
    name : str = "General Assistant Agent"
    description : str = "A helpful assistant that can answer questions and provide guidance"
    resources : list = []

# Agent's problem solver
def solve(assistant_agent : AssistantAgent, problem : str):
    \"\"\"Solve problems using AI reasoning.\"\"\"
    return reason(f"I'm here to help! Let me assist you with: {problem}")"""
        }
        return agent

    @pytest.mark.asyncio
    async def test_chat_with_agent_new_conversation(self, chat_service, mock_db, mock_agent):
        """Test chat with new conversation creation"""
        # Mock database query to return our agent
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent

        # Mock conversation service
        new_conversation = models.Conversation(
            id=1, title="Chat with Agent 1", created_at="2025-01-27T10:00:00", updated_at="2025-01-27T10:00:00"
        )
        chat_service.conversation_service.create_conversation.return_value = new_conversation

        # Mock message service
        mock_message = models.Message(
            id=1,
            conversation_id=1,
            sender="agent",
            content="Hello! How can I help you?",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00",
        )
        chat_service.message_service.create_message.return_value = mock_message

        # Mock SandboxContext.get_state() to return expected structure
        mock_state = {"local": {"response": "Hello! How can I help you?"}}

        with patch("dana.api.services.DanaSandbox.quick_run"), patch("dana.api.services.SandboxContext") as mock_sandbox_context_class:
            # Configure the mock SandboxContext
            mock_sandbox_context = Mock(spec=SandboxContext)
            mock_sandbox_context.get_state.return_value = mock_state
            mock_sandbox_context_class.return_value = mock_sandbox_context

            result = await chat_service.chat_with_agent(db=mock_db, agent_id=1, user_message="Hello, agent!")

            assert result["agent_response"] == "Hello! How can I help you?"
            assert result["success"] is True
            assert result["conversation_id"] == 1

    @pytest.mark.asyncio
    async def test_chat_with_agent_existing_conversation(self, chat_service, mock_db, mock_agent):
        """Test chat with existing conversation"""
        # Mock database query to return our agent
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent

        # Mock existing conversation
        existing_conversation = models.Conversation(
            id=1, title="Chat with Agent 1", created_at="2025-01-27T10:00:00", updated_at="2025-01-27T10:00:00"
        )
        chat_service.conversation_service.get_conversation.return_value = existing_conversation

        # Mock message service
        mock_message = models.Message(
            id=1,
            conversation_id=1,
            sender="agent",
            content="Hello! How can I help you?",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00",
        )
        chat_service.message_service.create_message.return_value = mock_message

        # Mock SandboxContext.get_state() to return expected structure
        mock_state = {"local": {"response": "Hello! How can I help you?"}}

        with (
            patch("dana.api.services.DanaSandbox.quick_run") as mock_quick_run,
            patch("dana.api.services.SandboxContext") as mock_sandbox_context_class,
        ):
            # Configure the mock SandboxContext
            mock_sandbox_context = Mock(spec=SandboxContext)
            mock_sandbox_context.get_state.return_value = mock_state
            mock_sandbox_context_class.return_value = mock_sandbox_context

            result = await chat_service.chat_with_agent(db=mock_db, agent_id=1, user_message="Hello, agent!", conversation_id=1)

            # Verify quick_run was called
            mock_quick_run.assert_called_once()
            assert result["agent_response"] == "Hello! How can I help you?"
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_chat_with_agent_conversation_not_found(self, chat_service):
        """Test chat with non-existent conversation"""
        # Create mock database session
        mock_db = Mock(spec=Session)

        # Mock conversation service - conversation not found
        chat_service.conversation_service.get_conversation.return_value = None

        # Test
        result = await chat_service.chat_with_agent(
            db=mock_db, agent_id=1, user_message="Hello, agent!", conversation_id=999, context={"user_id": 123}
        )

        # Assertions
        assert result["success"] is False
        assert "Conversation 999 not found" in result["error"]

    @pytest.mark.asyncio
    async def test_chat_with_agent_execution_error(self, chat_service, mock_db, mock_agent):
        """Test chat when agent execution fails"""
        # Mock database query to return our agent
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent

        # Mock conversation service
        new_conversation = models.Conversation(
            id=1, title="Chat with Agent 1", created_at="2025-01-27T10:00:00", updated_at="2025-01-27T10:00:00"
        )
        chat_service.conversation_service.create_conversation.return_value = new_conversation

        # Only mock create_message for the user message, not the agent message
        mock_user_message = models.Message(id=1, conversation_id=1, sender="user", content="Hello", created_at="2025-01-27T10:00:00")
        chat_service.message_service.create_message.return_value = mock_user_message

        # Mock SandboxContext.get_state() to return a dict
        mock_state = {"agent": mock_agent}

        with patch("dana.core.lang.sandbox_context.SandboxContext") as mock_sandbox_class:
            mock_sandbox = Mock()
            mock_sandbox.get_state.return_value = mock_state
            mock_sandbox_class.return_value = mock_sandbox

            # Patch the correct DanaSandbox.quick_run path
            with patch("dana.core.lang.dana_sandbox.DanaSandbox.quick_run", side_effect=Exception("Agent execution failed")):
                result = await chat_service.chat_with_agent(db=mock_db, agent_id=1, user_message="Hello", conversation_id=None)

        # Verify the result indicates failure
        assert result["success"] is False
        assert "Agent execution failed" in result["error"]
        assert result["conversation_id"] == 1
        assert result["message_id"] == 1

    @pytest.mark.asyncio
    async def test_execute_agent_implementation(self, chat_service, mock_db, mock_agent):
        """Test the _execute_agent method directly"""
        # Mock database query to return our agent
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent

        # Mock SandboxContext.get_state() to return expected structure
        mock_state = {"local": {"response": "Hello! I received your message: Hello, agent!"}}

        with patch("dana.api.services.DanaSandbox.quick_run"), patch("dana.api.services.SandboxContext") as mock_sandbox_context_class:
            # Configure the mock SandboxContext
            mock_sandbox_context = Mock(spec=SandboxContext)
            mock_sandbox_context.get_state.return_value = mock_state
            mock_sandbox_context_class.return_value = mock_sandbox_context

            result = await chat_service._execute_agent(db=mock_db, agent_id=1, message="Hello, agent!")

            assert "Hello! I received your message: Hello, agent!" == result


class TestChatSchemas:
    """Test cases for chat schemas"""

    def test_chat_request_valid(self):
        """Test valid ChatRequest"""
        request = schemas.ChatRequest(message="Hello, agent!", agent_id=1, context={"user_id": 123})
        assert request.message == "Hello, agent!"
        assert request.agent_id == 1
        assert request.context == {"user_id": 123}
        assert request.conversation_id is None

    def test_chat_request_with_conversation_id(self):
        """Test ChatRequest with conversation_id"""
        request = schemas.ChatRequest(message="Hello, agent!", agent_id=1, conversation_id=5, context={"user_id": 123})
        assert request.conversation_id == 5

    def test_chat_response_valid(self):
        """Test valid ChatResponse"""
        response = schemas.ChatResponse(
            success=True,
            message="Hello, agent!",
            conversation_id=1,
            message_id=2,
            agent_response="Hello! How can I help you?",
            context={"user_id": 123},
            error=None,
        )
        assert response.success is True
        assert response.message == "Hello, agent!"
        assert response.conversation_id == 1
        assert response.message_id == 2
        assert response.agent_response == "Hello! How can I help you?"
        assert response.context == {"user_id": 123}
        assert response.error is None

    def test_chat_response_error(self):
        """Test ChatResponse with error"""
        response = schemas.ChatResponse(
            success=False,
            message="Hello, agent!",
            conversation_id=0,
            message_id=0,
            agent_response="",
            context={"user_id": 123},
            error="Agent execution failed",
        )
        assert response.success is False
        assert response.error == "Agent execution failed"
