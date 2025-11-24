"""
LlamaStack Conversation Resource

A Dana Resource that wraps LlamaStack's Conversation API for session management.
This module USES LlamaStack's Conversation API and converts to our internal Timeline structure.
"""

from datetime import datetime
from typing import Any

import structlog

from dana.common.protocols.war import tool_use
from dana.core.agent.timeline import TimelineEntry, TimelineEntryType
from dana.core.resource.base_resource import BaseResource

from .client import LlamaStackClientManager


logger = structlog.get_logger()


class ConversationResource(BaseResource):
    """
    Dana Resource that wraps LlamaStack's Conversation API.

    Provides access to conversation sessions via LlamaStack's Conversation API.
    This resource converts LlamaStack conversation format to Dana Timeline/TimelineEntry format.
    """

    def __init__(self, **kwargs):
        """
        Initialize Conversation Resource.

        Args:
            **kwargs: Additional arguments for BaseResource
        """
        super().__init__(
            resource_type="conversation",
            **kwargs,
        )

        self.client = LlamaStackClientManager.get_client()

        logger.info("ConversationResource initialized")

    def _convert_role_to_entry_type(self, role: str) -> TimelineEntryType:
        """
        Convert LlamaStack role to TimelineEntryType.

        Args:
            role: LlamaStack role (user/assistant/system)

        Returns:
            Corresponding TimelineEntryType
        """
        role_lower = role.lower()
        if role_lower == "user":
            return TimelineEntryType.USER_MESSAGE
        elif role_lower == "assistant":
            return TimelineEntryType.AGENT_RESPONSE
        elif role_lower == "system":
            return TimelineEntryType.AGENT_THOUGHTS
        else:
            logger.warning("Unknown role, defaulting to USER_MESSAGE", role=role)
            return TimelineEntryType.USER_MESSAGE

    def _convert_turn_to_entry(self, turn: dict[str, Any], session_id: str | None = None) -> TimelineEntry:
        """
        Convert a LlamaStack conversation turn to a TimelineEntry.

        Args:
            turn: Turn data from LlamaStack API
            session_id: Optional session ID for metadata

        Returns:
            TimelineEntry representing the turn
        """
        # Extract message content
        content = turn.get("message", turn.get("content", ""))
        if isinstance(content, dict):
            content = content.get("text", content.get("content", str(content)))

        # Extract role
        role = turn.get("role", turn.get("sender", "user"))

        # Extract timestamp
        timestamp_str = turn.get("timestamp", turn.get("created_at", turn.get("time")))
        if isinstance(timestamp_str, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                timestamp = datetime.now()
        elif isinstance(timestamp_str, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp_str)
        else:
            timestamp = datetime.now()

        # Build metadata
        metadata = {
            "session_id": session_id or turn.get("session_id"),
            "turn_id": turn.get("turn_id", turn.get("id")),
            "llamastack_turn": turn,  # Preserve original for debugging
        }

        entry_type = self._convert_role_to_entry_type(role)

        return TimelineEntry(
            entry_type=entry_type,
            content=str(content),
            timestamp=timestamp,
            metadata=metadata,
        )

    async def _create_session_internal(self, metadata: dict[str, Any] | None = None) -> str:
        """
        Internal method to call LlamaStack Conversation API to create a session.

        Args:
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        if self.client and hasattr(self.client, "conversations"):
            result = self.client.conversations.create(metadata=metadata or {})
            session_id = result.get("session_id") or result.get("id") or str(result)
        else:
            # Fallback: generate a session ID if API not available
            logger.warning("LlamaStack conversation API not available, generating session ID")
            import uuid

            session_id = str(uuid.uuid4())

        return session_id

    @tool_use
    async def create_session(self, metadata: dict[str, Any] | None = None) -> str:
        """
        Create a new conversation session.

        Args:
            metadata: Optional session metadata dictionary

        Returns:
            Session ID string
        """
        try:
            session_id = await self._create_session_internal(metadata=metadata)
            logger.info("Created conversation session", session_id=session_id)
            return session_id
        except Exception as e:
            logger.error("Failed to create conversation session", error=str(e))
            raise

    async def _add_turn_internal(self, session_id: str, message: str, role: str = "user") -> dict[str, Any]:
        """
        Internal method to call LlamaStack Conversation API to add a turn.

        Args:
            session_id: Conversation session ID
            message: Message content
            role: Message role (user/assistant/system)

        Returns:
            Turn data from LlamaStack API
        """
        if self.client and hasattr(self.client, "conversations"):
            turn_data = self.client.conversations.add_turn(session_id=session_id, message=message, role=role)
        else:
            # Fallback: create a turn dict if API not available
            logger.warning("LlamaStack client doesn't have conversations API, creating turn locally")
            turn_data = {
                "session_id": session_id,
                "message": message,
                "role": role,
                "timestamp": datetime.now().isoformat(),
            }

        return turn_data

    @tool_use
    async def add_turn(self, session_id: str, message: str, role: str = "user") -> dict[str, Any]:
        """
        Add a turn to an existing conversation.

        Args:
            session_id: Conversation session ID
            message: Message content
            role: Message role (user/assistant/system, default: "user")

        Returns:
            TimelineEntry data as dictionary with:
            - entry_type: Type of timeline entry
            - content: Message content
            - timestamp: When the turn was added
            - metadata: Additional metadata including session_id, turn_id
        """
        try:
            # Call LlamaStack Conversation API
            turn_data = await self._add_turn_internal(session_id=session_id, message=message, role=role)

            # Convert to TimelineEntry
            entry = self._convert_turn_to_entry(turn_data, session_id=session_id)
            logger.debug("Added turn to session", session_id=session_id, entry_type=entry.entry_type)

            # Return as dict for tool response
            return {
                "entry_type": entry.entry_type.value,
                "content": entry.content,
                "timestamp": entry.timestamp.isoformat(),
                "metadata": entry.metadata,
            }
        except Exception as e:
            logger.error("Failed to add turn to conversation", session_id=session_id, error=str(e))
            raise

    async def _get_session_internal(self, session_id: str) -> dict[str, Any]:
        """
        Internal method to call LlamaStack Conversation API to get session.

        Args:
            session_id: Session ID

        Returns:
            Session data from LlamaStack API
        """
        if self.client and hasattr(self.client, "conversations"):
            session_data = self.client.conversations.get(session_id=session_id)
        else:
            # Fallback: return empty session if API not available
            logger.warning("LlamaStack client doesn't have conversations API, returning empty session")
            session_data = {"session_id": session_id, "turns": [], "metadata": {}}

        return session_data

    @tool_use
    async def get_timeline(self, session_id: str) -> dict[str, Any]:
        """
        Get conversation session as a Timeline.

        Args:
            session_id: Session ID

        Returns:
            Timeline data as dictionary with:
            - session_id: The session identifier
            - entries: List of timeline entries, each with:
              - entry_type: Type of entry (user_message, agent_response, etc.)
              - content: Entry content
              - timestamp: When the entry was created
              - metadata: Additional metadata
        """
        try:
            # Get session data from LlamaStack
            session_data = await self._get_session_internal(session_id)

            # Extract turns/history
            turns = session_data.get("turns", session_data.get("history", session_data.get("messages", [])))

            # Convert turns to TimelineEntry format
            entries = []
            for turn in turns:
                entry = self._convert_turn_to_entry(turn, session_id=session_id)
                entries.append(
                    {
                        "entry_type": entry.entry_type.value,
                        "content": entry.content,
                        "timestamp": entry.timestamp.isoformat(),
                        "metadata": entry.metadata,
                    }
                )

            logger.info("Retrieved session timeline", session_id=session_id, entry_count=len(entries))
            return {
                "session_id": session_id,
                "entries": entries,
            }
        except Exception as e:
            logger.error("Failed to get session timeline", session_id=session_id, error=str(e))
            raise
