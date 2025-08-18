"""
Runtime system for Dana agents in the TUI.

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

from dana.apps.repl.repl import REPL
from dana.common.sys_resource.llm.legacy_llm_resource import LegacyLLMResource
from dana.core.lang.dana_sandbox import DanaSandbox as CoreDanaSandbox
from dana.core.lang.dana_sandbox import ExecutionResult
from dana.core.lang.interpreter.struct_system import StructInstance
from dana.core.lang.log_manager import LogLevel
from dana.registry import AGENT_REGISTRY


class DanaSandbox:
    """Sandbox environment for managing Dana agents with real Dana integration."""

    def __init__(self):
        # Initialize real Dana REPL engine
        self._repl = REPL(llm_resource=LegacyLLMResource(), log_level=LogLevel.WARN)

        # Keep reference to the underlying sandbox for direct access
        self._dana_sandbox = self._repl.sandbox

    def get(self, name: str) -> StructInstance | None:
        """Get an agent by name from AGENT_REGISTRY."""
        # Get agent instance from global registry
        instances = AGENT_REGISTRY.list_instances()
        for instance in instances:
            if hasattr(instance, "name") and instance.name == name:
                return instance
        return None

    def list(self) -> list[str]:
        """List all agent names from AGENT_REGISTRY, sorted."""
        instances = AGENT_REGISTRY.list_instances()
        agent_names = []
        for instance in instances:
            if hasattr(instance, "name"):
                agent_names.append(instance.name)
        return sorted(agent_names)

    def get_all_agents(self) -> dict[str, StructInstance]:
        """Get all agents as a dictionary from AGENT_REGISTRY."""
        instances = AGENT_REGISTRY.list_instances()
        agents = {}
        for instance in instances:
            if hasattr(instance, "name"):
                agents[instance.name] = instance
        return agents

    def get_dana_context(self):
        """Get the underlying Dana context for advanced operations."""
        return self._repl.get_context()

    def get_dana_sandbox(self) -> CoreDanaSandbox:
        """Get the underlying Dana sandbox for direct access."""
        return self._dana_sandbox

    def clear(self) -> None:
        """Clear the sandbox (agents are managed by AGENT_REGISTRY)."""
        # Agents are managed by the global registry, so we don't clear them here
        pass

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
