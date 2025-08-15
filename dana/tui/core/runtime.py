"""
Runtime system for Dana agents in the TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from collections.abc import AsyncIterator
from abc import ABC, abstractmethod

from dana.core.lang.dana_sandbox import DanaSandbox as CoreDanaSandbox, ExecutionResult
from dana.core.repl.repl import REPL
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.core.lang.log_manager import LogLevel
from .events import AgentEvent


class Agent(ABC):
    """Abstract base class for Dana agents."""

    def __init__(self, name: str):
        self.name = name
        self._metrics = {
            "tokens_per_sec": 0.0,
            "elapsed_time": 0.0,
            "current_step": "idle",
            "is_running": False,
            "last_tool": "",
            "progress": 0.0,
        }

    @abstractmethod
    async def chat(self, message: str) -> AsyncIterator[AgentEvent]:
        """Process a chat message and yield events."""
        raise NotImplementedError

    def get_metrics(self) -> dict:
        """Get current agent metrics for display."""
        return self._metrics.copy()

    def update_metric(self, key: str, value) -> None:
        """Update a metric value."""
        if key in self._metrics:
            self._metrics[key] = value


class DanaSandbox:
    """Sandbox environment for managing Dana agents with real Dana integration."""

    def __init__(self):
        self._agents: dict[str, Agent] = {}
        self._focused_agent: str | None = None

        # Initialize real Dana REPL engine
        self._repl = REPL(llm_resource=LegacyLLMResource(), log_level=LogLevel.WARN)

        # Keep reference to the underlying sandbox for direct access
        self._dana_sandbox = self._repl.sandbox

    def register(self, agent: Agent) -> None:
        """Register a new agent in the sandbox."""
        self._agents[agent.name] = agent
        # Focus the first agent if none focused
        if self._focused_agent is None:
            self._focused_agent = agent.name

    def unregister(self, name: str) -> bool:
        """Remove an agent from the sandbox."""
        if name not in self._agents:
            return False

        del self._agents[name]

        # Update focus if we removed the focused agent
        if self._focused_agent == name:
            if self._agents:
                self._focused_agent = next(iter(self._agents.keys()))
            else:
                self._focused_agent = None

        return True

    def get(self, name: str) -> Agent | None:
        """Get an agent by name."""
        return self._agents.get(name)

    def list(self) -> list[str]:
        """List all agent names, sorted."""
        return sorted(self._agents.keys())

    def get_focused(self) -> Agent | None:
        """Get the currently focused agent."""
        if self._focused_agent:
            return self._agents.get(self._focused_agent)
        return None

    def get_focused_name(self) -> str | None:
        """Get the name of the currently focused agent."""
        return self._focused_agent

    def set_focus(self, name: str) -> bool:
        """Set the focused agent. Returns True if successful."""
        if name in self._agents:
            self._focused_agent = name
            return True
        return False

    def get_all_agents(self) -> dict[str, Agent]:
        """Get all agents as a dictionary."""
        return self._agents.copy()

    def get_dana_context(self):
        """Get the underlying Dana context for advanced operations."""
        return self._repl.get_context()

    def get_dana_sandbox(self) -> CoreDanaSandbox:
        """Get the underlying Dana sandbox for direct access."""
        return self._dana_sandbox

    def exists(self, name: str) -> bool:
        """Check if an agent exists."""
        return name in self._agents

    def clear(self) -> None:
        """Remove all agents."""
        self._agents.clear()
        self._focused_agent = None

    def execute_string(self, code: str) -> ExecutionResult:
        """Execute Dana code string using the real Dana execution engine.

        Args:
            code: Dana source code to execute

        Returns:
            ExecutionResult from the Dana sandbox
        """
        try:
            # Execute using the real Dana REPL engine
            result = self._repl.execute(code)

            # Get any print output from the interpreter
            print_output = self._repl.interpreter.get_and_clear_output()

            # Return successful execution result
            return ExecutionResult(
                success=True,
                result=result,
                output=print_output or "",
                execution_time=0.0,  # We don't track timing in TUI for now
                final_context=self._repl.get_context(),
            )

        except Exception as e:
            # Return error result
            return ExecutionResult(success=False, error=e, output="", execution_time=0.0)
