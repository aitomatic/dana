"""
Thought Logger - A Notifiable that outputs agent thought processes.

This module provides a Notifiable implementation that intercepts and displays
agent internal thought processes, including reasoning, tool calls, and reflections.
"""

import os
import sys

from adana.common.protocols import DictParams, Notifiable
from adana.core.agent.timeline import TimelineEntry, TimelineEntryType


# ANSI escape codes for terminal control
CURSOR_UP = "\033[F"
CLEAR_LINE = "\033[K"
FADED_COLOR = "\033[90m"  # Bright black (gray)
RESET_COLOR = "\033[0m"


def _get_terminal_width() -> int:
    """Get terminal width, default to 80 if unavailable."""
    try:
        return os.get_terminal_size().columns
    except (AttributeError, OSError):
        return 80


class ThoughtLogger(Notifiable):
    """
    A Notifiable that logs and displays agent thought processes.

    This class receives notifications from agents during their STAR loop
    and outputs relevant thought processes to help users understand what
    the agent is thinking and doing.
    """

    def __init__(self, verbose: bool = True, show_tool_calls: bool = True):
        """
        Initialize the ThoughtLogger.

        Args:
            verbose: If True, show detailed thought processes. If False, only show key decisions.
            show_tool_calls: If True, show tool call details.
        """
        self.verbose = verbose
        self.show_tool_calls = show_tool_calls
        self._last_thought_lines = 0  # Track how many lines the last thought occupied
        self._current_agent = None  # Track which agent's thoughts we're showing

    def notify(self, notifier: object, message: DictParams) -> None:
        """
        Receive notification from an agent and display relevant thought processes.

        Args:
            notifier: The agent sending the notification
            message: The notification message containing trace data
        """
        if not self.verbose and not self.show_tool_calls:
            return

        # Extract agent information
        agent_id = getattr(notifier, "object_id", "unknown")
        agent_type = getattr(notifier, "agent_type", "unknown")

        # Check for STAR loop phases (these are the primary notifications)
        # SEE phase - percepts
        trace_percepts = message.get("trace_percepts", {})
        if self.verbose and trace_percepts:
            caller_message = trace_percepts.get("caller_message")
            if caller_message:
                self._display_phase(agent_id, "👁️  SEE", f"Received: {caller_message}")

        # THINK phase - thoughts
        trace_thoughts = message.get("trace_thoughts", {})
        if self.verbose and trace_thoughts:
            response = trace_thoughts.get("response")
            reasoning = trace_thoughts.get("reasoning")
            tool_calls = trace_thoughts.get("tool_calls", [])

            if response and len(response) > 0:
                # Extract more informative content from response
                think_summary = self._extract_think_summary(response, reasoning, tool_calls)
                self._display_phase(agent_id, "💭 THINK", think_summary)

        # ACT phase - outputs
        # The notification from _act sends {"trace_outputs": {...}}
        # where the inner dict contains tool_calls
        trace_outputs = message.get("trace_outputs", {})
        if self.verbose and trace_outputs:
            tool_calls = trace_outputs.get("tool_calls", [])
            if tool_calls and len(tool_calls) > 0:
                tool_names = [tc.get("name", "unknown") for tc in tool_calls]
                self._display_phase(agent_id, "⚡ ACT", f"Calling: {', '.join(tool_names)}")

        # REFLECT phase - learning
        trace_learning = message.get("trace_learning", {})
        if self.verbose and trace_learning:
            learning_note = trace_learning.get("learning_note")
            if learning_note:
                phase = trace_learning.get("phase", "unknown")
                self._display_phase(agent_id, "🔄 REFLECT", f"[{phase}] {learning_note}")

        # Note: We skip timeline entries to avoid duplication since
        # the STAR phases above already show the relevant information

        # Check for tool calls in the message
        if self.show_tool_calls and "tool_calls" in message:
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                self._clear_thought()  # Clear thought before showing action
                self._display_tool_calls(agent_id, agent_type, tool_calls)

        # Check for tool results
        if self.show_tool_calls and "tool_results" in message:
            tool_results = message.get("tool_results", [])
            if tool_results:
                self._display_tool_results(agent_id, agent_type, tool_results)

    def _extract_think_summary(self, response: str, reasoning: str, tool_calls: list[DictParams]) -> str:
        """Extract a more informative summary from THINK phase using structured data.

        Args:
            response: The agent's full thinking response
            tool_calls: List of structured tool call dictionaries with 'function' and 'arguments'

        Returns:
            A more informative summary combining reasoning and structured tool intent
        """
        if reasoning:
            response += f" ({reasoning})"

        # If there are tool calls, show structured action plan
        if tool_calls and len(tool_calls) > 0:
            # Extract structured information from tool calls
            tool_descriptions = []
            for tc in tool_calls:
                function = tc.get("function", "unknown")
                arguments = tc.get("arguments", {})

                if function == "call_agent":
                    agent_id = arguments.get("object_id", "unknown")
                    tool_descriptions.append(f"agent:{agent_id}")
                elif function == "call_resource":
                    resource_id = arguments.get("resource_id", "unknown")
                    method = arguments.get("method", "")
                    tool_descriptions.append(f"resource:{resource_id}.{method}" if method else f"resource:{resource_id}")
                elif function == "call_workflow":
                    workflow_id = arguments.get("workflow_id", "unknown")
                    tool_descriptions.append(f"workflow:{workflow_id}")
                else:
                    tool_descriptions.append(function)

            tool_summary = f"→ {', '.join(tool_descriptions)}"

            # Show brief reasoning + structured tool intent
            if len(response) <= 150:
                return f"{response} {tool_summary}"
            else:
                # Truncate response but keep tool intent visible
                first_part = response[:150].strip()
                return f"{first_part}... {tool_summary}"

        # No tool calls - this is a final response, show concise reasoning
        if len(response) <= 400:
            return response
        else:
            # Truncate long responses
            return f"{response[:350].strip()}..."

    def _clear_thought(self) -> None:
        """Clear the previous thought display."""
        if self._last_thought_lines > 0:
            # Move cursor up and clear each line
            for _ in range(self._last_thought_lines):
                sys.stdout.write(CURSOR_UP + CLEAR_LINE)
            sys.stdout.flush()
            self._last_thought_lines = 0
            self._current_agent = None

    def _display_phase(self, agent_id: str, phase_label: str, content: str) -> None:
        """
        Display a STAR phase in faded color, overwriting previous display.

        Args:
            agent_id: ID of the agent
            phase_label: Label for the phase (e.g., "💭 THINK", "⚡ ACT")
            content: The content to display
        """
        # Only clear if we're displaying for the same agent
        # This prevents clearing when switching between agents
        if self._current_agent == agent_id:
            self._clear_thought()
        elif self._last_thought_lines > 0:
            # Different agent, add a line break instead of clearing
            print()
            self._last_thought_lines = 0

        self._current_agent = agent_id

        # Truncate long content
        max_length = 400
        display_text = content[:max_length] + "..." if len(content) > max_length else content

        # Format with faded color (without color codes in length calculation)
        prefix = f"{phase_label} [{agent_id}] "
        thought_text = f"{prefix}{display_text}"
        thought_line = f"{FADED_COLOR}{thought_text}{RESET_COLOR}"

        # Print the thought
        print(thought_line, flush=True)

        # Calculate how many terminal lines this will occupy
        # Account for terminal width wrapping
        terminal_width = _get_terminal_width()
        # Add visible length (excluding ANSI codes)
        visible_length = len(thought_text)
        lines_needed = max(1, (visible_length + terminal_width - 1) // terminal_width)
        self._last_thought_lines = lines_needed

    def _display_thought(self, agent_type: str, thought: str) -> None:
        """
        Display a thought in faded color, overwriting previous thought.
        This is a convenience wrapper for _display_phase.

        Args:
            agent_type: Type of the agent
            thought: The thought text to display
        """
        self._display_phase(agent_type, "💭", thought)

    def _display_entry(self, agent_id: str, agent_type: str, entry: TimelineEntry) -> None:
        """
        Display a timeline entry based on its type.

        Args:
            agent_id: ID of the agent
            agent_type: Type of the agent
            entry: The timeline entry to display
        """
        # Only show certain entry types
        if entry.entry_type == TimelineEntryType.MY_THOUGHTS:
            if self.verbose:
                self._display_thought(agent_type, entry.content)
        elif entry.entry_type == TimelineEntryType.MY_LEARNING:
            if self.verbose:
                self._clear_thought()
                print(f"\n🧠 [{agent_type}] Learning: {entry.content}")
        elif entry.entry_type == TimelineEntryType.TOOL_CALL:
            if self.show_tool_calls:
                self._clear_thought()
                print(f"\n🔧 [{agent_type}] Tool Call: {entry.content}")

    def _display_tool_calls(self, agent_id: str, agent_type: str, tool_calls: list[DictParams]) -> None:
        """
        Display tool calls being made by the agent.

        Args:
            agent_id: ID of the agent
            agent_type: Type of the agent
            tool_calls: List of tool call dictionaries
        """
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("arguments", {})
            print(f"\n🔧 [{agent_type}] Calling tool: {tool_name}")
            if self.verbose and tool_args:
                print(f"   Arguments: {tool_args}")

    def _display_tool_results(self, agent_id: str, agent_type: str, tool_results: list[DictParams]) -> None:
        """
        Display tool results received by the agent.

        Args:
            agent_id: ID of the agent
            agent_type: Type of the agent
            tool_results: List of tool result dictionaries
        """
        for result in tool_results:
            tool_name = result.get("name", "unknown")
            success = result.get("success", False)
            status = "✅" if success else "❌"
            print(f"\n{status} [{agent_type}] Tool result: {tool_name}")
            if self.verbose:
                output = result.get("output", "")
                if output and len(str(output)) < 200:
                    print(f"   Output: {output}")
                elif output:
                    print(f"   Output: {str(output)[:200]}...")
