from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from dana.api.server import models, schemas
from dana.api.server.server import create_app
from dana.api.server.services import ChatService, ConversationService, MessageService


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


class TestChatEndpoint:
    """Test cases for chat endpoint"""

    def test_chat_with_agent_success(self, client):
        """Test successful chat with agent"""
        with patch('dana.api.server.routers.chat.get_agent') as mock_get_agent, \
             patch('dana.api.server.routers.chat.ChatService') as mock_chat_service_class:
            
            # Mock agent retrieval
            sample_agent = models.Agent(
                id=1,
                name="Test Agent",
                description="A test agent",
                config={"model": "gpt-4", "temperature": 0.7}
            )
            mock_get_agent.return_value = sample_agent
            
            # Mock chat service
            mock_chat_service = Mock()
            mock_chat_service.chat_with_agent = AsyncMock(return_value={
                "success": True,
                "message": "Hello, agent!",
                "conversation_id": 1,
                "message_id": 2,
                "agent_response": "Hello! How can I help you today?",
                "context": {"user_id": 123},
                "error": None
            })
            mock_chat_service_class.return_value = mock_chat_service
            
            # Test request
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": 1,
                    "context": {"user_id": 123}
                }
            )
            
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

    def test_chat_with_agent_not_found(self, client):
        """Test chat with non-existent agent"""
        with patch('dana.api.server.routers.chat.get_agent') as mock_get_agent:
            # Mock agent not found
            mock_get_agent.return_value = None
            
            # Test request
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": 999,
                    "context": {"user_id": 123}
                }
            )
            
            # Assertions
            assert response.status_code == 404
            data = response.json()
            assert "Agent 999 not found" in data["detail"]

    def test_chat_with_agent_service_error(self, client):
        """Test chat when service returns error"""
        with patch('dana.api.server.routers.chat.get_agent') as mock_get_agent, \
             patch('dana.api.server.routers.chat.ChatService') as mock_chat_service_class:
            
            # Mock agent retrieval
            sample_agent = models.Agent(
                id=1,
                name="Test Agent",
                description="A test agent",
                config={"model": "gpt-4", "temperature": 0.7}
            )
            mock_get_agent.return_value = sample_agent
            
            # Mock chat service error
            mock_chat_service = Mock()
            mock_chat_service.chat_with_agent = AsyncMock(return_value={
                "success": False,
                "message": "Hello, agent!",
                "conversation_id": 0,
                "message_id": 0,
                "agent_response": "",
                "context": {"user_id": 123},
                "error": "Agent execution failed"
            })
            mock_chat_service_class.return_value = mock_chat_service
            
            # Test request
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": 1,
                    "context": {"user_id": 123}
                }
            )
            
            # Assertions
            assert response.status_code == 500
            data = response.json()
            assert "Agent execution failed" in data["detail"]

    def test_chat_with_agent_exception(self, client):
        """Test chat when service raises exception"""
        with patch('dana.api.server.routers.chat.get_agent') as mock_get_agent, \
             patch('dana.api.server.routers.chat.ChatService') as mock_chat_service_class:
            
            # Mock agent retrieval
            sample_agent = models.Agent(
                id=1,
                name="Test Agent",
                description="A test agent",
                config={"model": "gpt-4", "temperature": 0.7}
            )
            mock_get_agent.return_value = sample_agent
            
            # Mock chat service exception
            mock_chat_service = Mock()
            mock_chat_service.chat_with_agent = AsyncMock(side_effect=Exception("Unexpected error"))
            mock_chat_service_class.return_value = mock_chat_service
            
            # Test request
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": 1,
                    "context": {"user_id": 123}
                }
            )
            
            # Assertions
            assert response.status_code == 500
            data = response.json()
            assert "Chat failed" in data["detail"]

    def test_chat_with_agent_missing_required_fields(self, client):
        """Test chat with missing required fields"""
        # Test missing message
        response = client.post(
            "/api/chat/",
            json={
                "agent_id": 1,
                "context": {"user_id": 123}
            }
        )
        assert response.status_code == 422
        
        # Test missing agent_id
        response = client.post(
            "/api/chat/",
            json={
                "message": "Hello, agent!",
                "context": {"user_id": 123}
            }
        )
        assert response.status_code == 422

    def test_chat_with_agent_invalid_data_types(self, client):
        """Test chat with invalid data types"""
        # Test invalid agent_id type
        response = client.post(
            "/api/chat/",
            json={
                "message": "Hello, agent!",
                "agent_id": "not_a_number",
                "context": {"user_id": 123}
            }
        )
        assert response.status_code == 422
        
        # Test invalid message type
        response = client.post(
            "/api/chat/",
            json={
                "message": 123,
                "agent_id": 1,
                "context": {"user_id": 123}
            }
        )
        assert response.status_code == 422


class TestChatService:
    """Test cases for ChatService"""

    @pytest.fixture
    def chat_service(self):
        """Create ChatService instance for testing"""
        conversation_service = Mock(spec=ConversationService)
        message_service = Mock(spec=MessageService)
        return ChatService(conversation_service, message_service)

    @pytest.mark.asyncio
    async def test_chat_with_agent_new_conversation(self, chat_service):
        """Test chat with new conversation creation"""
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        # Mock conversation service
        new_conversation = models.Conversation(
            id=1,
            title="Chat with Agent 1",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00"
        )
        chat_service.conversation_service.create_conversation.return_value = new_conversation
        
        # Mock message service
        user_message = models.Message(
            id=1,
            conversation_id=1,
            sender="user",
            content="Hello, agent!",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00"
        )
        agent_message = models.Message(
            id=2,
            conversation_id=1,
            sender="agent",
            content="Hello! How can I help you?",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00"
        )
        chat_service.message_service.create_message.side_effect = [user_message, agent_message]
        
        # Mock DanaSandbox.quick_run
        with patch('dana.api.server.services.DanaSandbox.quick_run') as mock_quick_run:
            # Create a mock response object
            mock_response = Mock()
            mock_response.result = "Hello! How can I help you?"
            mock_quick_run.return_value = mock_response
            
            # Test
            result = await chat_service.chat_with_agent(
                db=mock_db,
                agent_id=1,
                user_message="Hello, agent!",
                conversation_id=None,
                context={"user_id": 123}
            )
            
            # Assertions
            assert result["success"] is True
            assert result["message"] == "Hello, agent!"
            assert result["conversation_id"] == 1
            assert result["message_id"] == 2
            assert result["agent_response"] == "Hello! How can I help you?"
            assert result["context"] == {"user_id": 123}
            assert result["error"] is None
            
            # Verify service calls
            chat_service.conversation_service.create_conversation.assert_called_once()
            assert chat_service.message_service.create_message.call_count == 2
            
            # Verify DanaSandbox was called
            mock_quick_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_agent_existing_conversation(self, chat_service):
        """Test chat with existing conversation"""
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        # Mock conversation service
        existing_conversation = models.Conversation(
            id=1,
            title="Existing Conversation",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00"
        )
        chat_service.conversation_service.get_conversation.return_value = existing_conversation
        
        # Mock message service
        user_message = models.Message(
            id=3,
            conversation_id=1,
            sender="user",
            content="Hello, agent!",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00"
        )
        agent_message = models.Message(
            id=4,
            conversation_id=1,
            sender="agent",
            content="Hello! How can I help you?",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00"
        )
        chat_service.message_service.create_message.side_effect = [user_message, agent_message]
        
        # Mock DanaSandbox.quick_run
        with patch('dana.api.server.services.DanaSandbox.quick_run') as mock_quick_run:
            # Create a mock response object
            mock_response = Mock()
            mock_response.result = "Hello! How can I help you?"
            mock_quick_run.return_value = mock_response
            
            # Test
            result = await chat_service.chat_with_agent(
                db=mock_db,
                agent_id=1,
                user_message="Hello, agent!",
                conversation_id=1,
                context={"user_id": 123}
            )
            
            # Assertions
            assert result["success"] is True
            assert result["conversation_id"] == 1
            assert result["message_id"] == 4
            
            # Verify service calls
            chat_service.conversation_service.get_conversation.assert_called_once_with(mock_db, 1)
            assert chat_service.message_service.create_message.call_count == 2
            
            # Verify DanaSandbox was called
            mock_quick_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_agent_conversation_not_found(self, chat_service):
        """Test chat with non-existent conversation"""
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        # Mock conversation service - conversation not found
        chat_service.conversation_service.get_conversation.return_value = None
        
        # Test
        result = await chat_service.chat_with_agent(
            db=mock_db,
            agent_id=1,
            user_message="Hello, agent!",
            conversation_id=999,
            context={"user_id": 123}
        )
        
        # Assertions
        assert result["success"] is False
        assert "Conversation 999 not found" in result["error"]

    @pytest.mark.asyncio
    async def test_chat_with_agent_execution_error(self, chat_service):
        """Test chat when agent execution fails"""
        # Create mock database session
        mock_db = Mock(spec=Session)
        
        # Mock conversation service
        new_conversation = models.Conversation(
            id=1,
            title="Chat with Agent 1",
            created_at="2025-01-27T10:00:00",
            updated_at="2025-01-27T10:00:00"
        )
        chat_service.conversation_service.create_conversation.return_value = new_conversation
        
        # Mock DanaSandbox.quick_run to raise exception
        with patch('dana.api.server.services.DanaSandbox.quick_run') as mock_quick_run:
            mock_quick_run.side_effect = Exception("Agent execution failed")
            
            # Test
            result = await chat_service.chat_with_agent(
                db=mock_db,
                agent_id=1,
                user_message="Hello, agent!",
                conversation_id=None,
                context={"user_id": 123}
            )
            
            # Assertions
            assert result["success"] is False
            assert "Agent execution failed" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_agent_implementation(self, chat_service):
        """Test the _execute_agent method with mocked DanaSandbox"""
        # Mock DanaSandbox.quick_run
        with patch('dana.api.server.services.DanaSandbox.quick_run') as mock_quick_run:
            # Create a mock response object
            mock_response = Mock()
            mock_response.result = "Hello! I received your message: Hello, agent!"
            mock_quick_run.return_value = mock_response
            
            # Test
            result = await chat_service._execute_agent(
                agent_id=1,
                message="Hello, agent!",
                context={"user_id": 123}
            )
            
            # Assertions
            assert isinstance(result, str)
            assert "Hello! I received your message: Hello, agent!" == result
            
            # Verify DanaSandbox was called
            mock_quick_run.assert_called_once()


class TestChatSchemas:
    """Test cases for chat schemas"""

    def test_chat_request_valid(self):
        """Test valid ChatRequest"""
        request = schemas.ChatRequest(
            message="Hello, agent!",
            agent_id=1,
            context={"user_id": 123}
        )
        assert request.message == "Hello, agent!"
        assert request.agent_id == 1
        assert request.context == {"user_id": 123}
        assert request.conversation_id is None

    def test_chat_request_with_conversation_id(self):
        """Test ChatRequest with conversation_id"""
        request = schemas.ChatRequest(
            message="Hello, agent!",
            agent_id=1,
            conversation_id=5,
            context={"user_id": 123}
        )
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
            error=None
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
            error="Agent execution failed"
        )
        assert response.success is False
        assert response.error == "Agent execution failed" 