"""
Chat Service Module

This module provides business logic for chat functionality and conversation management.
"""

import json
import logging
import shutil
from pathlib import Path

from dana.api.core.models import Agent, Conversation, Message
from dana.api.core.schemas import ChatRequest, ChatResponse, ConversationCreate, MessageCreate

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for handling chat operations and conversation management.
    """

    def __init__(self):
        """Initialize the chat service."""
        pass

    def _get_prebuilt_agent_folder(self, agent_key: str) -> Path | None:
        """
        Get the path to a prebuilt agent folder if it exists.

        Args:
            agent_key: The string key identifying the prebuilt agent

        Returns:
            Path to prebuilt agent folder or None if not found
        """
        prebuilt_folder = Path(__file__).parent.parent / "server" / "assets" / agent_key
        return prebuilt_folder if prebuilt_folder.exists() else None

    def _ensure_prebuilt_agent_copied(self, agent_key: str) -> str | None:
        """
        Ensure prebuilt agent folder is copied to agents directory.

        Args:
            agent_key: The string key identifying the prebuilt agent

        Returns:
            Path to the copied agent folder or None if copy failed
        """
        try:
            # Check if prebuilt agent exists
            prebuilt_folder = self._get_prebuilt_agent_folder(agent_key)
            if not prebuilt_folder:
                logger.error(f"Prebuilt agent '{agent_key}' not found in assets")
                return None

            # Create agents directory if it doesn't exist
            agents_dir = Path("agents")
            agents_dir.mkdir(exist_ok=True)

            # Target folder in agents directory
            target_folder = agents_dir / agent_key

            # If target already exists, use it
            if target_folder.exists():
                logger.info(f"Prebuilt agent folder '{agent_key}' already exists at {target_folder}")
                return str(target_folder)

            # Copy prebuilt folder to agents directory
            shutil.copytree(prebuilt_folder, target_folder)
            logger.info(f"Copied prebuilt agent '{agent_key}' from {prebuilt_folder} to {target_folder}")

            return str(target_folder)

        except Exception as e:
            logger.error(f"Error copying prebuilt agent '{agent_key}': {e}")
            return None

    def _get_prebuilt_agent_info(self, agent_key: str) -> dict | None:
        """
        Get prebuilt agent information from the assets JSON file.

        Args:
            agent_key: The string key identifying the prebuilt agent

        Returns:
            Agent info dict or None if not found
        """
        try:
            assets_path = Path(__file__).parent.parent / "server" / "assets" / "prebuilt_agents.json"

            with open(assets_path, encoding="utf-8") as f:
                prebuilt_agents = json.load(f)

            return next((agent for agent in prebuilt_agents if agent["key"] == agent_key), None)
        except Exception as e:
            logger.error(f"Error loading prebuilt agent info for '{agent_key}': {e}")
            return None

    async def process_chat_message(self, chat_request: ChatRequest, db_session, websocket_id: str | None = None) -> ChatResponse:
        """
        Process a chat message and generate a response.

        Args:
            chat_request: The chat request containing message and context
            db_session: Database session for persistence

        Returns:
            ChatResponse with the agent's reply and conversation details
        """
        try:
            agent = None
            agent_name = None
            agent_description = None
            folder_path = None

            # Handle both integer and string agent IDs
            # Prebuilt agents have string IDs like "sofia_finance_expert"
            # Regular agents have integer IDs like 56, but may come as string "56" from JSON
            if isinstance(chat_request.agent_id, str) and not chat_request.agent_id.isdigit():
                # Handle prebuilt agent (string ID)
                logger.info(f"Processing chat for prebuilt agent: {chat_request.agent_id}")

                # Get prebuilt agent info
                prebuilt_info = self._get_prebuilt_agent_info(chat_request.agent_id)
                if not prebuilt_info:
                    raise ValueError(f"Prebuilt agent '{chat_request.agent_id}' not found")

                # Ensure prebuilt agent folder is copied to agents directory
                folder_path = self._ensure_prebuilt_agent_copied(chat_request.agent_id)
                if not folder_path:
                    raise ValueError(f"Failed to copy prebuilt agent '{chat_request.agent_id}'")

                agent_name = prebuilt_info["name"]
                agent_description = prebuilt_info.get("description", "A prebuilt Dana agent")

                # For prebuilt agents, we'll skip database operations for conversations
                # and generate response directly
                agent_response = await self._generate_prebuilt_agent_response(
                    chat_request, agent_name, agent_description, folder_path, websocket_id
                )

                return ChatResponse(
                    success=True,
                    message=chat_request.message,
                    conversation_id=0,  # No conversation tracking for prebuilt agents for now
                    message_id=0,
                    agent_response=agent_response,
                    context=chat_request.context,
                    error=None,
                )
            else:
                # Handle regular agent (integer ID or string representing a number)
                # Convert to integer if it's a string representation of a number
                if isinstance(chat_request.agent_id, str):
                    agent_id_int = int(chat_request.agent_id)
                else:
                    agent_id_int = chat_request.agent_id

                agent = db_session.query(Agent).filter(Agent.id == agent_id_int).first()
                if not agent:
                    raise ValueError(f"Agent {agent_id_int} not found")

                # Get or create conversation (only for regular agents)
                conversation = await self._get_or_create_conversation(chat_request, db_session)

                # Save user message
                user_message = await self._save_message(conversation.id, "user", chat_request.message, db_session)

                # Generate agent response with WebSocket support
                agent_response = await self._generate_agent_response(chat_request, conversation, db_session, websocket_id)

                # Save agent message
                await self._save_message(conversation.id, "agent", agent_response, db_session)

                return ChatResponse(
                    success=True,
                    message=chat_request.message,
                    conversation_id=conversation.id,
                    message_id=user_message.id,
                    agent_response=agent_response,
                    context=chat_request.context,
                    error=None,
                )

        except ValueError as e:
            logger.error(f"Validation error in chat message: {e}")
            # For validation errors, return as service error (200 status)
            return ChatResponse(
                success=False,
                message=chat_request.message,
                conversation_id=chat_request.conversation_id or 0,
                message_id=0,
                agent_response="",
                context=chat_request.context,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Error processing chat message: {e}")
            # For other exceptions, raise as HTTP exception (500 status)
            # This allows the router's exception handler to catch it
            raise e

    async def _get_or_create_conversation(self, chat_request: ChatRequest, db_session) -> Conversation:
        """Get existing conversation or create a new one."""
        if chat_request.conversation_id:
            # Get existing conversation
            conversation = db_session.query(Conversation).filter(Conversation.id == chat_request.conversation_id).first()
            if conversation:
                return conversation
            else:
                # Conversation not found - raise error instead of creating new one
                raise ValueError(f"Conversation {chat_request.conversation_id} not found")

        # Create new conversation
        conversation_data = ConversationCreate(title=f"Chat with Agent {chat_request.agent_id}", agent_id=chat_request.agent_id)

        conversation = Conversation(title=conversation_data.title, agent_id=conversation_data.agent_id)
        db_session.add(conversation)
        db_session.commit()
        db_session.refresh(conversation)

        return conversation

    async def _save_message(self, conversation_id: int, sender: str, content: str, db_session) -> Message:
        """Save a message to the database."""
        message_data = MessageCreate(sender=sender, content=content)

        message = Message(conversation_id=conversation_id, sender=message_data.sender, content=message_data.content)
        db_session.add(message)
        db_session.commit()
        db_session.refresh(message)

        return message

    async def _generate_agent_response(
        self, chat_request: ChatRequest, conversation: Conversation, db_session, websocket_id: str | None = None
    ) -> str:
        """Generate agent response using actual Dana execution."""
        try:
            # Get agent details for execution
            agent = db_session.query(Agent).filter(Agent.id == chat_request.agent_id).first()
            if not agent:
                return "Error: Agent not found"

            # Import agent test functionality
            from dana.__init__ import initialize_module_system, reset_module_system
            from dana.api.routers.agent_test import AgentTestRequest, test_agent

            # Initialize module system
            initialize_module_system()
            reset_module_system()

            # Extract agent details
            agent_name = agent.name
            agent_description = agent.description or "A Dana agent"
            folder_path = agent.config.get("folder_path") if agent.config else None

            # Create test request for agent execution
            test_request = AgentTestRequest(
                agent_code="",  # Will use folder_path for main.na
                message=chat_request.message,
                agent_name=agent_name,
                agent_description=agent_description,
                context=chat_request.context or {"user_id": "chat_user"},
                folder_path=folder_path,
                websocket_id=websocket_id,  # Enable WebSocket for real-time updates
            )

            # Execute agent using same logic as test endpoint
            result = await test_agent(test_request)

            if result.success:
                return result.agent_response
            else:
                return f"Error executing agent: {result.error or 'Unknown error'}"

        except Exception as e:
            logger.error(f"Error generating agent response: {e}")
            return f"Error generating response: {str(e)}"

    async def _generate_prebuilt_agent_response(
        self, chat_request: ChatRequest, agent_name: str, agent_description: str, folder_path: str, websocket_id: str | None = None
    ) -> str:
        """Generate agent response for prebuilt agents using folder execution."""
        try:
            # Import agent test functionality
            from dana.__init__ import initialize_module_system, reset_module_system
            from dana.api.routers.agent_test import AgentTestRequest, test_agent

            # Initialize module system
            initialize_module_system()
            reset_module_system()

            # Create test request for agent execution
            test_request = AgentTestRequest(
                agent_code="",  # Will use folder_path for main.na
                message=chat_request.message,
                agent_name=agent_name,
                agent_description=agent_description,
                context=chat_request.context or {"user_id": "chat_user"},
                folder_path=folder_path,
                websocket_id=websocket_id,  # Enable WebSocket for real-time updates
            )

            # Execute agent using same logic as test endpoint
            result = await test_agent(test_request)

            if result.success:
                return result.agent_response
            else:
                return f"Error executing prebuilt agent: {result.error or 'Unknown error'}"

        except Exception as e:
            logger.error(f"Error generating prebuilt agent response: {e}")
            return f"Error generating response: {str(e)}"


# Global service instance
_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """Get or create the global chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
