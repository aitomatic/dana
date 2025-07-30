from unittest.mock import AsyncMock, patch

import pytest

from dana.api.core import models
from dana.api.services.chat_service import ChatService


class TestChatIntegration:
    """Integration tests for chat functionality with real database"""

    # Use the global fixtures from conftest.py
    pass

    @pytest.fixture
    def sample_agent(self, db_session):
        """Create sample agent in test database"""
        agent = models.Agent(
            name="Test Agent",
            description="A test agent for integration testing",
            config={"model": "gpt-4", "temperature": 0.7}
        )
        db_session.add(agent)
        db_session.commit()
        db_session.refresh(agent)
        return agent

    def test_chat_end_to_end_new_conversation(self, client, db_session, sample_agent):
        """Test complete chat flow with new conversation"""
        with patch.object(ChatService, '_generate_agent_response', new_callable=AsyncMock) as mock_execute:
            # Mock agent execution
            mock_execute.return_value = "Hello! I'm your test agent. How can I help you today?"
            
            # Send chat request
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": sample_agent.id,
                    "context": {"user_id": 123}
                }
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Hello, agent!"
            assert data["agent_response"] == "Hello! I'm your test agent. How can I help you today?"
            assert data["context"] == {"user_id": 123}
            assert data["error"] is None
            
            # Verify conversation was created
            conversation_id = data["conversation_id"]
            conversation = db_session.query(models.Conversation).filter(
                models.Conversation.id == conversation_id
            ).first()
            assert conversation is not None
            assert conversation.title == f"Chat with Agent {sample_agent.id}"
            
            # Verify messages were created
            messages = db_session.query(models.Message).filter(
                models.Message.conversation_id == conversation_id
            ).order_by(models.Message.id).all()
            
            assert len(messages) == 2
            
            # User message
            user_message = messages[0]
            assert user_message.sender == "user"
            assert user_message.content == "Hello, agent!"
            
            # Agent message
            agent_message = messages[1]
            assert agent_message.sender == "agent"
            assert agent_message.content == "Hello! I'm your test agent. How can I help you today?"

    def test_chat_end_to_end_existing_conversation(self, client, db_session, sample_agent):
        """Test complete chat flow with existing conversation"""
        with patch.object(ChatService, '_generate_agent_response', new_callable=AsyncMock) as mock_execute:
            # Mock agent execution
            mock_execute.return_value = "I remember our conversation! How can I help you further?"
            
            # Create existing conversation with agent_id
            conversation = models.Conversation(title="Existing Test Conversation", agent_id=sample_agent.id)
            db_session.add(conversation)
            db_session.commit()
            db_session.refresh(conversation)
            
            # Add existing message
            existing_message = models.Message(
                conversation_id=conversation.id,
                sender="user",
                content="Previous message"
            )
            db_session.add(existing_message)
            db_session.commit()
            
            # Send chat request with existing conversation
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello again, agent!",
                    "agent_id": sample_agent.id,
                    "conversation_id": conversation.id,
                    "context": {"user_id": 123}
                }
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["conversation_id"] == conversation.id
            assert data["agent_response"] == "I remember our conversation! How can I help you further?"
            
            # Verify new messages were added to existing conversation
            messages = db_session.query(models.Message).filter(
                models.Message.conversation_id == conversation.id
            ).order_by(models.Message.id).all()
            
            assert len(messages) == 3  # Previous + new user + new agent
            
            # Verify new messages
            new_user_message = messages[1]
            assert new_user_message.sender == "user"
            assert new_user_message.content == "Hello again, agent!"
            
            new_agent_message = messages[2]
            assert new_agent_message.sender == "agent"
            assert new_agent_message.content == "I remember our conversation! How can I help you further?"

    def test_chat_agent_not_found(self, client, db_session):
        """Test chat with non-existent agent"""
        response = client.post(
            "/api/chat/",
            json={
                "message": "Hello, agent!",
                "agent_id": 999,
                "context": {"user_id": 123}
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Agent 999 not found" in data["detail"]

    def test_chat_conversation_not_found(self, client, db_session, sample_agent):
        """Test chat with non-existent conversation"""
        with patch.object(ChatService, '_generate_agent_response', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "Hello! How can I help you?"
            
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": sample_agent.id,
                    "conversation_id": 999,
                    "context": {"user_id": 123}
                }
            )
            
            # Should return error response
            assert response.status_code == 500
            data = response.json()
            assert "Conversation 999 not found" in data["detail"]

    def test_chat_agent_execution_error(self, client, db_session, sample_agent):
        """Test chat when agent execution fails"""
        with patch.object(ChatService, '_generate_agent_response', new_callable=AsyncMock) as mock_execute:
            # Mock agent execution error
            mock_execute.side_effect = Exception("Agent execution failed")
            
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": sample_agent.id,
                    "context": {"user_id": 123}
                }
            )
            
            # Should return error response
            assert response.status_code == 500
            data = response.json()
            assert "Agent execution failed" in data["detail"]

    def test_chat_multiple_messages_same_conversation(self, client, db_session, sample_agent):
        """Test multiple messages in the same conversation"""
        with patch.object(ChatService, '_generate_agent_response', new_callable=AsyncMock) as mock_execute:
            # Mock different responses for each call
            mock_execute.side_effect = [
                "Hello! How can I help you?",
                "I understand you want to know about Python. Python is a great programming language!",
                "Yes, Python is excellent for beginners and experts alike."
            ]
            
            conversation_id = None
            
            # First message
            response1 = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": sample_agent.id,
                    "context": {"user_id": 123}
                }
            )
            
            assert response1.status_code == 200
            data1 = response1.json()
            conversation_id = data1["conversation_id"]
            assert data1["agent_response"] == "Hello! How can I help you?"
            
            # Second message
            response2 = client.post(
                "/api/chat/",
                json={
                    "message": "Tell me about Python",
                    "agent_id": sample_agent.id,
                    "conversation_id": conversation_id,
                    "context": {"user_id": 123}
                }
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["conversation_id"] == conversation_id
            assert data2["agent_response"] == "I understand you want to know about Python. Python is a great programming language!"
            
            # Third message
            response3 = client.post(
                "/api/chat/",
                json={
                    "message": "Is it good for beginners?",
                    "agent_id": sample_agent.id,
                    "conversation_id": conversation_id,
                    "context": {"user_id": 123}
                }
            )
            
            assert response3.status_code == 200
            data3 = response3.json()
            assert data3["conversation_id"] == conversation_id
            assert data3["agent_response"] == "Yes, Python is excellent for beginners and experts alike."
            
            # Verify all messages in conversation
            messages = db_session.query(models.Message).filter(
                models.Message.conversation_id == conversation_id
            ).order_by(models.Message.id).all()
            
            assert len(messages) == 6  # 3 user messages + 3 agent responses
            
            # Verify message sequence
            assert messages[0].sender == "user" and messages[0].content == "Hello, agent!"
            assert messages[1].sender == "agent" and messages[1].content == "Hello! How can I help you?"
            assert messages[2].sender == "user" and messages[2].content == "Tell me about Python"
            assert messages[3].sender == "agent" and "Python is a great programming language" in messages[3].content
            assert messages[4].sender == "user" and messages[4].content == "Is it good for beginners?"
            assert messages[5].sender == "agent" and "beginners and experts alike" in messages[5].content

    def test_chat_with_context(self, client, db_session, sample_agent):
        """Test chat with context data"""
        with patch.object(ChatService, '_generate_agent_response', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = "I see you're working on project XYZ. How can I help?"
            
            context = {
                "user_id": 123,
                "project": "XYZ",
                "session_id": "abc-123",
                "preferences": {"language": "en", "theme": "dark"}
            }
            
            response = client.post(
                "/api/chat/",
                json={
                    "message": "Hello, agent!",
                    "agent_id": sample_agent.id,
                    "context": context
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["context"] == context
            assert data["agent_response"] == "I see you're working on project XYZ. How can I help?"

    def test_chat_schema_validation(self, client):
        """Test chat request schema validation"""
        # Test missing required fields
        response = client.post("/api/chat/", json={})
        assert response.status_code == 422
        
        # Test invalid agent_id type
        response = client.post(
            "/api/chat/",
            json={
                "message": "Hello",
                "agent_id": "invalid@agent#id"
            }
        )
        assert response.status_code == 422
        
        # Test invalid message type
        response = client.post(
            "/api/chat/",
            json={
                "message": 123,
                "agent_id": 1
            }
        )
        assert response.status_code == 422
        
        # Test invalid context type
        response = client.post(
            "/api/chat/",
            json={
                "message": "Hello",
                "agent_id": 1,
                "context": "not_a_dict"
            }
        )
        assert response.status_code == 422 