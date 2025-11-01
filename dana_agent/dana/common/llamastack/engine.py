"""
DanaEngine API - Entrypoint for LlamaStack Thin Adapter

This module defines the Dana-side API that LlamaStack's thin adapter calls into.
This is where LlamaStack calls INTO Dana (reverse of Dana calling LS APIs).

Flow:
- LlamaStack thin adapter (~230 lines in LS repo) receives LS types
- Adapter converts LS types → Dana types (e.g., AgentConfig → simple Python types)
- Adapter calls DanaEngine methods here
- Dana processes using STAR loop, workflows, learning, etc.
- Dana calls LS APIs directly (using providers injected via dependencies)
- When Dana USES LS APIs, type conversion happens in other modules:
  * conversation.py: LS Conversation API → Dana Timeline
  * storage.py: LS Storage/VectorIO API → Dana Resources
- Dana returns Dana types to adapter
- Adapter converts Dana types → LS types and returns to LlamaStack
"""

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


# Type stubs - to be fully specified
DanaAgentConfig = dict  # TBD: Proper config class
ProviderDependencies = dict  # TBD: Wrapper for 7 LS API providers
DanaSession = dict  # TBD: Session class
Message = dict  # TBD: Message format
AgentCreateResult = dict  # TBD: Result type
AgentTurnResult = dict  # TBD: Result type
AgentTurnStreamChunk = dict  # TBD: Stream chunk type


@runtime_checkable
class DanaEngineAPI(Protocol):
    """
    Protocol defining the DanaEngine API that LlamaStack's thin adapter calls into.

    This is the entrypoint where:
    - LlamaStack calls INTO Dana (via thin adapter)
    - Thin adapter converts LS types → Dana types before calling these methods
    - Dana processes using STAR loop and calls LS APIs directly (via injected providers)
    - Dana returns Dana types, adapter converts back to LS types

    Type conversions when Dana USES LS APIs (reverse direction):
    - conversation.py: LS Conversation → Dana Timeline
    - storage.py: LS VectorIO/Storage → Dana Resources
    """

    async def initialize(
        self,
        config: DanaAgentConfig,
        dependencies: ProviderDependencies,
    ) -> None:
        """
        Initialize Dana engine with LlamaStack API providers.

        Args:
            config: Dana-specific configuration
            dependencies: 7 LlamaStack API providers

        Raises:
            InitializationError: If setup fails
        """
        ...

    async def create_agent(
        self,
        model: str,
        instructions: str,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AgentCreateResult:
        """
        Create a new agent instance.

        Args:
            model: Model identifier
            instructions: System instructions
            tools: List of tool definitions
            **kwargs: Additional agent parameters

        Returns:
            AgentCreateResult with agent_id

        Raises:
            AgentCreationError: If creation fails
        """
        ...

    async def execute_turn(
        self,
        session: DanaSession,
        messages: list[Message],
        stream: bool = False,
    ) -> AgentTurnResult | AsyncIterator[AgentTurnStreamChunk]:
        """
        Execute a single agent turn.

        Args:
            session: Dana session (agent_id, session_id)
            messages: List of messages in conversation
            stream: Whether to stream response

        Returns:
            AgentTurnResult (non-streaming) or AsyncIterator (streaming)

        Raises:
            ExecutionError: If execution fails
        """
        ...
