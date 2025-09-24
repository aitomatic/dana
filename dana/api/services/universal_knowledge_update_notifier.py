"""
Universal Knowledge Update Notifier

A centralized service for notifying frontend clients about any knowledge updates
across the entire system. This ensures consistent real-time updates regardless
of the source of the knowledge modification.
"""

import json
import logging
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from fastapi import WebSocket
from collections import defaultdict

logger = logging.getLogger(__name__)


class UniversalKnowledgeUpdateNotifier:
    """
    Universal notifier for all knowledge updates across the system.
    
    This service provides a centralized way to notify frontend clients
    about any changes to domain knowledge, regardless of the source.
    """
    
    def __init__(self):
        # Map of websocket_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of agent_id -> set of websocket_ids for that agent
        self.agent_connections: Dict[str, set] = defaultdict(set)
    
    async def connect(self, websocket_id: str, websocket: WebSocket, agent_id: Optional[str] = None):
        """Connect a WebSocket client to the notification system."""
        await websocket.accept()
        self.active_connections[websocket_id] = websocket
        
        if agent_id:
            self.agent_connections[agent_id].add(websocket_id)
            logger.info(f"[UniversalNotifier] Connected WebSocket {websocket_id} for agent {agent_id}")
        else:
            logger.info(f"[UniversalNotifier] Connected WebSocket {websocket_id}")
    
    def disconnect(self, websocket_id: str):
        """Disconnect a WebSocket client from the notification system."""
        if websocket_id in self.active_connections:
            del self.active_connections[websocket_id]
            
            # Remove from agent connections
            for agent_id, connections in self.agent_connections.items():
                connections.discard(websocket_id)
                if not connections:
                    del self.agent_connections[agent_id]
            
            logger.info(f"[UniversalNotifier] Disconnected WebSocket {websocket_id}")
    
    async def notify_knowledge_update(
        self,
        agent_id: str | int,
        update_type: str,
        update_data: Optional[Dict[str, Any]] = None,
        websocket_id: Optional[str] = None
    ):
        """
        Universal method to notify about any knowledge update.
        
        Args:
            agent_id: ID of the agent whose knowledge was updated
            update_type: Type of update (e.g., "tree_modified", "content_generated", "status_changed")
            update_data: Additional data about the update
            websocket_id: Optional specific WebSocket to notify (if None, notifies all for agent)
        """
        try:
            message = {
                "type": "knowledge_update",
                "agent_id": str(agent_id),
                "update_type": update_type,
                "timestamp": datetime.now(UTC).isoformat(),
                "data": update_data or {}
            }
            
            logger.info(f"[UniversalNotifier] Sending knowledge update notification: agent={agent_id}, type={update_type}")
            
            # Determine which connections to notify
            connections_to_notify = []
            
            if websocket_id:
                # Notify specific WebSocket
                if websocket_id in self.active_connections:
                    connections_to_notify.append((websocket_id, self.active_connections[websocket_id]))
            else:
                # Notify all connections for this agent
                agent_id_str = str(agent_id)
                if agent_id_str in self.agent_connections:
                    for ws_id in self.agent_connections[agent_id_str]:
                        if ws_id in self.active_connections:
                            connections_to_notify.append((ws_id, self.active_connections[ws_id]))
            
            # Send notifications
            disconnected_connections = []
            for ws_id, websocket in connections_to_notify:
                try:
                    await websocket.send_text(json.dumps(message))
                    logger.debug(f"[UniversalNotifier] Sent notification to WebSocket {ws_id}")
                except Exception as e:
                    logger.error(f"[UniversalNotifier] Failed to send notification to {ws_id}: {e}")
                    disconnected_connections.append(ws_id)
            
            # Clean up disconnected connections
            for ws_id in disconnected_connections:
                self.disconnect(ws_id)
                
        except Exception as e:
            logger.error(f"[UniversalNotifier] Error sending knowledge update notification: {e}")
    
    async def notify_tree_modified(self, agent_id: str | int, operation: str, details: Optional[Dict] = None):
        """Convenience method for tree modification notifications."""
        await self.notify_knowledge_update(
            agent_id=agent_id,
            update_type="tree_modified",
            update_data={
                "operation": operation,
                "details": details or {}
            }
        )
    
    async def notify_content_generated(self, agent_id: str | int, topic: str, details: Optional[Dict] = None):
        """Convenience method for content generation notifications."""
        await self.notify_knowledge_update(
            agent_id=agent_id,
            update_type="content_generated",
            update_data={
                "topic": topic,
                "details": details or {}
            }
        )
    
    async def notify_status_changed(self, agent_id: str | int, topic: str, status: str, details: Optional[Dict] = None):
        """Convenience method for status change notifications."""
        await self.notify_knowledge_update(
            agent_id=agent_id,
            update_type="status_changed",
            update_data={
                "topic": topic,
                "status": status,
                "details": details or {}
            }
        )
    
    def get_connection_count(self, agent_id: Optional[str] = None) -> int:
        """Get the number of active connections."""
        if agent_id:
            return len(self.agent_connections.get(str(agent_id), set()))
        return len(self.active_connections)
    
    def get_agent_connections(self) -> Dict[str, set]:
        """Get all agent connections."""
        return dict(self.agent_connections)


# Global instance
universal_knowledge_notifier = UniversalKnowledgeUpdateNotifier()
