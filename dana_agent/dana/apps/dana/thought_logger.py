"""
Thought Logger - A Notifiable that outputs agent thought processes.

This module provides a Notifiable implementation that intercepts and displays
agent internal thought processes, including reasoning, tool calls, and reflections.
"""

from dana.common.protocols import DictParams, Notifiable
from dana.core.agent.timeline import TimelineEntry, TimelineEntryType


# ANSI escape codes for colors
FADED_COLOR = "\033[90m"  # Bright black (gray)
RESET_COLOR = "\033[0m"


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
            # Initial perception: caller message
            caller_message = trace_percepts.get("caller_message")
            if caller_message:
                self._display_phase(agent_id, "👁️  SEE", f"Received: {caller_message}")

            # Subsequent perception: tool results
            perception = trace_percepts.get("perception")
            if perception and not caller_message:  # Don't show both
                self._display_phase(agent_id, "👁️  SEE", perception)

        # THINK phase - thoughts
        trace_thoughts = message.get("trace_thoughts", {})
        if self.verbose and trace_thoughts:
            response = trace_thoughts.get("response")
            reasoning = trace_thoughts.get("reasoning")
            tool_calls = trace_thoughts.get("tool_calls", [])
            todo_list = trace_thoughts.get("todo_list")

            # Display todo list if present
            if todo_list:
                self._display_todo_list(agent_id, todo_list)

            # Display if we have response OR reasoning
            if (response and len(response) > 0) or reasoning:
                # Extract more informative content from response
                think_summary = self._extract_think_summary(response or "", reasoning, tool_calls)
                self._display_phase(agent_id, "💭 THINK", think_summary)

        # ACT phase - outputs
        # The notification from _act sends {"trace_outputs": {...}}
        # where the inner dict contains tool_calls
        trace_outputs = message.get("trace_outputs", {})
        if self.verbose and trace_outputs:
            tool_calls = trace_outputs.get("tool_calls", [])
            if tool_calls and len(tool_calls) > 0:
                tool_summaries = [self._format_tool_call(tc) for tc in tool_calls]
                self._display_phase(agent_id, "⚡ ACT", f"Calling: {', '.join(tool_summaries)}")

        # REFLECT phase - learning
        trace_learning = message.get("trace_learning", {})
        if self.verbose and trace_learning:
            learning_note = trace_learning.get("learning_note")
            if learning_note:
                phase = trace_learning.get("phase", "unknown")
                self._display_phase(agent_id, "🔄 REFLECT", f"[{phase}] {learning_note}")

        # Workflow progress - show workflow thinking
        workflow_progress = message.get("workflow_progress", {})
        if self.verbose and workflow_progress:
            workflow_id = workflow_progress.get("workflow_id", "unknown")
            workflow_message = workflow_progress.get("message", "")
            phase = workflow_progress.get("phase", "unknown")

            # Use different emoji for different workflow phases
            phase_emoji = {
                "start": "🔧",
                "classify": "🔍",
                "llm_classify": "🤖",
                "complete": "✅",
                "extract": "📄",
                "themes": "🏷️",
                "overview": "📝",
                "gaps": "🔍",
                "confidence": "📊",
            }.get(phase, "⚙️")

            self._display_phase(workflow_id, f"{phase_emoji} WORKFLOW", workflow_message)

        # Skill progress - show skill execution progress
        skill_progress = message.get("skill_progress", {})
        if self.verbose and skill_progress:
            skill_id = skill_progress.get("skill_id", "claude-skills")
            skill_message = skill_progress.get("message", "")
            phase = skill_progress.get("phase", "unknown")

            # Use different emoji for different skill phases
            phase_emoji = {
                "init": "🔧",
                "discover": "🔍",
                "execute": "⚡",
                "complete": "✅",
                "error": "❌",
            }.get(phase, "🎯")

            self._display_phase(skill_id, f"{phase_emoji} SKILL", skill_message)

        # Note: We skip timeline entries to avoid duplication since
        # the STAR phases above already show the relevant information

        # Check for tool calls in the message
        if self.show_tool_calls and "tool_calls" in message:
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                self._display_tool_calls(agent_id, agent_type, tool_calls)

        # Check for tool results
        if self.show_tool_calls and "tool_results" in message:
            tool_results = message.get("tool_results", [])
            if tool_results:
                self._display_tool_results(agent_id, agent_type, tool_results)

    def _extract_think_summary(self, response: str, reasoning: str, tool_calls: list[DictParams]) -> str:
        """Extract a more informative summary from THINK phase using structured data.

        Args:
            response: The agent's full thinking response (final answer when done=true)
            reasoning: The agent's reasoning for this step
            tool_calls: List of structured tool call dictionaries with 'function' and 'arguments'

        Returns:
            A summary for display - reasoning + tool intent, or just reasoning for final answers
        """
        # If there are tool calls, show reasoning + tool intent
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

            # Show reasoning + structured tool intent
            display_text = reasoning or ""
            if len(display_text) <= 150:
                return f"{display_text} {tool_summary}".strip()
            else:
                return f"{display_text[:150].strip()}... {tool_summary}"

        # No tool calls - this is a final answer. Only show reasoning (response will be displayed separately)
        if reasoning:
            if len(reasoning) <= 400:
                return reasoning
            else:
                return f"{reasoning[:350].strip()}..."
        else:
            # No reasoning provided, just indicate completion
            return "Preparing final response..."

    def _format_tool_call(self, tc: DictParams) -> str:
        """Format a tool call for display, including key arguments.
        
        Args:
            tc: Tool call dictionary with 'function' and 'arguments'
            
        Returns:
            Formatted string like 'web_search__fetch_url(example.com)'
        """
        function = tc.get("function", "unknown")
        arguments = tc.get("arguments", {})
        
        # Extract the most relevant argument to display
        arg_display = ""
        if arguments:
            # Priority order for which argument to show
            if "url" in arguments:
                url = arguments["url"]
                # Truncate long URLs
                if len(url) > 50:
                    arg_display = f"({url[:47]}...)"
                else:
                    arg_display = f"({url})"
            elif "query" in arguments:
                query = arguments["query"]
                if len(query) > 40:
                    arg_display = f"({query[:37]}...)"
                else:
                    arg_display = f"({query})"
            elif "message" in arguments:
                msg = arguments["message"]
                if len(msg) > 40:
                    arg_display = f"({msg[:37]}...)"
                else:
                    arg_display = f"({msg})"
            elif "method" in arguments:
                arg_display = f"({arguments['method']})"
        
        return f"{function}{arg_display}"

    def _display_phase(self, agent_id: str, phase_label: str, content: str) -> None:
        """
        Display a STAR phase in faded color.

        Args:
            agent_id: ID of the agent
            phase_label: Label for the phase (e.g., "💭 THINK", "⚡ ACT")
            content: The content to display
        """
        # Truncate long content
        max_length = 400
        display_text = content[:max_length] + "..." if len(content) > max_length else content

        # Format with faded color
        thought_line = f"{FADED_COLOR}{phase_label} [{agent_id}] {display_text}{RESET_COLOR}"
        print(thought_line, flush=True)

    def _display_thought(self, agent_type: str, thought: str) -> None:
        """
        Display a thought in faded color.

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
        if entry.entry_type == TimelineEntryType.AGENT_THOUGHTS:
            if self.verbose:
                self._display_thought(agent_type, entry.content)
        elif entry.entry_type == TimelineEntryType.AGENT_LEARNING:
            if self.verbose:
                print(f"🧠 [{agent_type}] Learning: {entry.content}")
        elif entry.entry_type == TimelineEntryType.TOOL_CALL:
            if self.show_tool_calls:
                print(f"🔧 [{agent_type}] Tool Call: {entry.content}")

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
            print(f"🔧 [{agent_type}] Calling tool: {tool_name}")
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
            print(f"{status} [{agent_type}] Tool result: {tool_name}")
            if self.verbose:
                output = result.get("output", "")
                if output and len(str(output)) < 200:
                    print(f"   Output: {output}")
                elif output:
                    print(f"   Output: {str(output)[:200]}...")

    def _display_todo_list(self, agent_id: str, todo_list: list) -> None:
        """
        Display the agent's todo list with status indicators.

        Args:
            agent_id: ID of the agent
            todo_list: List of TodoItem objects with content and status
        """
        # Status indicators
        status_icons = {
            "in_progress": "🔄",
            "pending": "⏳",
            "completed": "✅",
        }

        # Build todo display
        todo_lines = []
        for item in todo_list:
            # Handle both TodoItem objects and dicts
            if hasattr(item, "status"):
                status = item.status
                content = item.content
            else:
                status = item.get("status", "pending")
                content = item.get("content", "")

            icon = status_icons.get(status, "•")
            todo_lines.append(f"  {icon} {content}")

        if todo_lines:
            todo_display = "\n".join(todo_lines)
            print(f"📋 [{agent_id}] Todo List:")
            print(f"{FADED_COLOR}{todo_display}{RESET_COLOR}")
