"""
Agent conversation loop implementation using Mixin pattern.

This module provides a ConverseMixin that can be added to AgentInstance
to enable conversation loop functionality with different IO adapters.
"""

from dataclasses import dataclass
from collections.abc import Callable
from typing import Any, Protocol, cast

from dana.core.lang.sandbox_context import SandboxContext
from dana.core.workflow.workflow_system import WorkflowInstance

from ..timeline.timeline_event import ConversationTurn
from .solvers.base import BaseSolverMixin

# --- Response and IO Types ---


@dataclass
class Response:
    """Response object returned by the solver, compatible with Dana's conversation system."""

    type: str  # e.g. "answer", "ask", "escalate", "error"
    text: str  # human-readable response text
    citations: list[str] | None = None
    extra: dict[str, Any] | None = None


class IOAdapter(Protocol):
    """Interface for input/output adapters (CLI, Slack, web, etc.)."""

    def get_input(self) -> tuple[str | None, list[Any]]:
        """Get next user input and any associated artifacts.

        Returns:
            Tuple of (message, artifacts) where message is None for end-of-stream
        """
        ...

    def send_output(self, response: Response) -> None:
        """Send response back to user.

        Args:
            response: The response to send
        """
        ...


# --- ConverseMixin ---


class ConverseMixin:
    """Mixin that adds conversation loop functionality to agents."""

    def converse_sync(
        self,
        io: IOAdapter,
        solve_fn: Callable[[str | WorkflowInstance, dict[str, Any] | None, SandboxContext | None], Any] | None = None,
        sandbox_context: SandboxContext | None = None,
    ) -> str:
        """
        Synchronous conversation loop method.

        Args:
            io: IO adapter providing get_input() / send_output()
            solve_fn: Optional custom solver function with same signature as solve_sync(). If None, uses agent's solve_sync method
            sandbox_context: Sandbox context for execution

        Returns:
            String indicating conversation end reason
        """
        turn_number = 0

        while True:
            # 1. Get next user input
            message, artifacts = io.get_input()
            if message is None:  # end-of-stream or user quit
                break

            turn_number += 1

            # 2. Start new conversation turn in timeline
            conversation_turn = ConversationTurn.start_new_turn(message, turn_number)
            self.state.timeline.add_event(conversation_turn)

            # 3. Dispatch to solver
            try:
                artifacts = {}
                if solve_fn is not None:
                    # Use custom solver function with solve_sync signature
                    result = solve_fn(message, artifacts, sandbox_context, **{})
                else:
                    # Use agent's own solve method
                    me = cast(BaseSolverMixin, self)
                    result = me.solve_sync(message, artifacts, sandbox_context)

                # Convert result to Response
                if isinstance(result, str):
                    response = Response(type="answer", text=result)
                else:
                    response = Response(type="answer", text=str(result))

                # 4. Complete the conversation turn
                conversation_turn.complete_turn(response.text)

                # 5. Send response back
                io.send_output(response)

            except Exception as e:
                # Handle errors gracefully
                error_response = Response(type="error", text=f"I encountered an error: {str(e)}")
                conversation_turn.complete_turn(error_response.text)
                io.send_output(error_response)

        return "conversation ended"


# --- Example CLI adapter for testing ---


class CLIAdapter:
    """Simple CLI adapter for testing the conversation loop."""

    def get_input(self) -> tuple[str | None, list[Any]]:
        """Get input from command line."""
        try:
            msg = input("user> ")
            return msg, []
        except EOFError:
            return None, []
        except KeyboardInterrupt:
            print("\nGoodbye!")
            return None, []

    def send_output(self, response: Response) -> None:
        """Send output to command line."""
        print(f"agent> {response.text}")
        if response.citations:
            print(f"citations: {', '.join(response.citations)}")


# --- Example echo solver for demonstration ---


def echo_solver(message: str | WorkflowInstance, sandbox_context: SandboxContext | None = None, **kwargs) -> str:
    """Simple echo solver for testing with solve_sync signature."""
    return f"You said: {message}"


# --- Run example if invoked directly ---

if __name__ == "__main__":
    # Example usage would require an agent instance with ConverseMixin
    print("This module provides ConverseMixin for agent conversation loops.")
    print("To use, add ConverseMixin to your AgentInstance class.")
