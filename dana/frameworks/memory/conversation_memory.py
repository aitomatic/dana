"""
Backward compatibility import for ConversationMemory.
"""

# Import from new location for backward compatibility
from dana.core.agent.mind.memory.conversation import ConversationMemory

__all__ = ["ConversationMemory"]
