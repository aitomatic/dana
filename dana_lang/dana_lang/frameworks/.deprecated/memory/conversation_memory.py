"""
Backward compatibility import for ConversationMemory.
"""

# Import from new location for backward compatibility
from dana_lang.core.agent.mind.memory.conversation import ConversationMemory

__all__ = ["ConversationMemory"]
