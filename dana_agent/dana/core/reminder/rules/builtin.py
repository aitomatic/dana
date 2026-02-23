"""
Built-in reminders for the Dana reminder system.

These reminders use lazy validity checking - they check if required resources
exist during evaluate() and return early (no mutation) if not applicable.

Reminders mutate the messages list directly, wrapping their own content
in <system-reminder> XML tags.

Reminders:
- TodoNeverCalledReminder: Nudges agent to start using todo tracking
- TodoUpdateReminder: Nudges agent to update todo list after activity
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dana.common.llm.types import LLMMessage


if TYPE_CHECKING:
    from dana.core.agent.star_agent import STARAgent
    from dana.core.agent.timeline import Timeline, TimelineEntry


def _entry_has_tool_call(entry: TimelineEntry, tool_name: str) -> bool:
    """Check if a TOOL_CALL entry contains a call to the named tool.

    Handles both formats:
    - Legacy XML: tool name appears in ``entry.content``
    - Native tool calls: tool name appears in ``entry.tool_calls[].function`` or ``.name``
    """
    # Legacy XML format — tool call is serialised as XML text in content
    if isinstance(entry.content, str) and tool_name in entry.content.lower():
        return True
    # Native tool call format — content is empty, data lives in tool_calls list
    if entry.tool_calls:
        for tc in entry.tool_calls:
            if isinstance(tc, dict):
                func = tc.get("function", "") or tc.get("name", "")
            else:
                func = getattr(tc, "function", "") or getattr(tc, "name", "")
            if tool_name in func.lower():
                return True
    return False


class TodoNeverCalledReminder:
    """
    Nudge the agent to start using todo tracking when it has the capability but hasn't used it.

    Triggers when:
    1. The agent has a ToDoResource registered
    2. The agent has gone through several turns without calling todo_write
    3. No todo_write calls exist in the timeline

    Attributes:
        name: "todo_never_called"
        turns_threshold: Number of turns before triggering (default: 2)
    """

    name: str = "todo_never_called"

    def __init__(self, turns_threshold: int = 1):
        """
        Initialize the TodoNeverCalledReminder.

        Args:
            turns_threshold: Number of turns before triggering the reminder
        """
        self.turns_threshold = turns_threshold

    def evaluate(self, agent: STARAgent, messages: list[LLMMessage]) -> None:
        """
        Evaluate if the agent should be nudged to start using todo tracking.

        Mutates messages by appending a system-reminder if the reminder fires.

        Args:
            agent: The STARAgent instance
            messages: The messages list to mutate in place
        """
        # Lazy validity check - does agent have ToDoResource?
        if not self._has_todo_resource(agent):
            return

        # Check turn count
        turn_count = getattr(agent, "_star_loop_count", 0)
        if turn_count < self.turns_threshold:
            return

        # Get timeline from agent
        timeline = getattr(agent, "_timeline", None)
        if timeline is None:
            return

        # Check if todo_write was ever called
        if self._todo_write_ever_called(timeline):
            return

        # Generate prompt and append as message
        prompt = "This is a reminder that your todo list is currently empty. DO NOT mention this to the user explicitly because they are already aware. If you are working on tasks that would benefit from a todo list please use the todo tool to create one. If not, please feel free to ignore. Again do not mention this message to the user."
        messages.append(LLMMessage(role="user", content=f"<system-reminder>\n{prompt}\n</system-reminder>"))

    def _has_todo_resource(self, agent: STARAgent) -> bool:
        """Check if the agent has a ToDoResource registered."""
        from dana.core.resource.todo_resource import ToDoResource

        resources = getattr(agent, "_resources", [])
        return any(isinstance(r, ToDoResource) for r in resources)

    def _todo_write_ever_called(self, timeline: Timeline) -> bool:
        """Check if todo_write was ever called in the timeline."""
        from dana.core.agent.timeline import TimelineEntryType

        for entry in timeline.timeline:
            if entry.entry_type == TimelineEntryType.TOOL_CALL:
                if _entry_has_tool_call(entry, "todo_write"):
                    return True
        return False


class SkillReminder:
    """
    Remind the agent about available skills each turn.

    Triggers when:
    1. The agent has a DanaSkillResource registered
    2. There are model-invocable skills available

    Attributes:
        name: "available_skills"
    """

    name: str = "available_skills"

    def evaluate(self, agent: STARAgent, messages: list[LLMMessage]) -> None:
        """
        Append a system-reminder listing available skills.

        Args:
            agent: The STARAgent instance
            messages: The messages list to mutate in place
        """
        skill_resource = self._get_skill_resource(agent)
        if not skill_resource:
            return

        skills = skill_resource.list_model_invocable()
        if not skills:
            return

        descriptions = skill_resource.get_prompt_descriptions()
        content = f"The following skills are available for use:\n" f"{descriptions}\n" f"Use skill tool to execute that skill."
        messages.append(LLMMessage(role="user", content=f"<system-reminder>\n{content}\n</system-reminder>"))

    def _get_skill_resource(self, agent: STARAgent):
        """Find DanaSkillResource on the agent, if any."""
        from dana.core.skills.dana_skills.skills import DanaSkillResource

        resources = getattr(agent, "_resources", [])
        for r in resources:
            if isinstance(r, DanaSkillResource):
                return r
        return None


class TodoUpdateReminder:
    """
    Nudge the agent to update the todo list after significant activity.

    Triggers when:
    1. The agent has a ToDoResource registered
    2. todo_write was called at least once (list exists)
    3. Either N turns OR K tokens have passed since the last todo_write call

    Attributes:
        name: "todo_update"
        turns_threshold: Number of turns since last todo_write before triggering (default: 3)
        tokens_threshold: Number of tokens since last todo_write before triggering (default: 2000)
    """

    name: str = "todo_update"

    def __init__(self, turns_threshold: int = 3, tokens_threshold: int = 2000):
        """
        Initialize the TodoUpdateReminder.

        Args:
            turns_threshold: Number of turns since last todo_write before triggering
            tokens_threshold: Number of tokens since last todo_write before triggering
        """
        self.turns_threshold = turns_threshold
        self.tokens_threshold = tokens_threshold

    def evaluate(self, agent: STARAgent, messages: list[LLMMessage]) -> None:
        """
        Evaluate if the agent should be nudged to update the todo list.

        Mutates messages by appending a system-reminder if the reminder fires.

        Args:
            agent: The STARAgent instance
            messages: The messages list to mutate in place
        """
        # Lazy validity check - does agent have ToDoResource?
        if not self._has_todo_resource(agent):
            return

        # Get timeline from agent
        timeline = getattr(agent, "_timeline", None)
        if timeline is None:
            return

        # Find last todo_write call
        last_todo_call_index = self._find_last_todo_write_index(timeline)

        # If never called, don't trigger (let TodoNeverCalledReminder handle it)
        if last_todo_call_index == -1:
            return

        # Check if N entries since last call (~2 entries per turn: call + result)
        entries_since = len(timeline.timeline) - last_todo_call_index - 1
        if entries_since >= self.turns_threshold * 2:
            prompt = self._generate_prompt()
            messages.append(LLMMessage(role="user", content=f"<system-reminder>\n{prompt}\n</system-reminder>"))
            return

        # Check if K tokens since last call
        tokens_since = self._estimate_tokens_since(timeline, last_todo_call_index)
        if tokens_since >= self.tokens_threshold:
            prompt = self._generate_prompt()
            messages.append(LLMMessage(role="user", content=f"<system-reminder>\n{prompt}\n</system-reminder>"))

    def _has_todo_resource(self, agent: STARAgent) -> bool:
        """Check if the agent has a ToDoResource registered."""
        from dana.core.resource.todo_resource import ToDoResource

        resources = getattr(agent, "_resources", [])
        return any(isinstance(r, ToDoResource) for r in resources)

    def _find_last_todo_write_index(self, timeline: Timeline) -> int:
        """Find the index of the last todo_write call in the timeline."""
        from dana.core.agent.timeline import TimelineEntryType

        for i in range(len(timeline.timeline) - 1, -1, -1):
            entry = timeline.timeline[i]
            if entry.entry_type == TimelineEntryType.TOOL_CALL:
                if _entry_has_tool_call(entry, "todo_write"):
                    return i
        return -1

    def _estimate_tokens_since(self, timeline: Timeline, from_index: int) -> int:
        """Estimate tokens since a given timeline index."""
        entries_since = timeline.timeline[from_index + 1 :]
        total_chars = sum(len(entry.content) for entry in entries_since)
        # Rough estimate: 1 token ≈ 4 characters
        return total_chars // 4

    def _generate_prompt(self) -> str:
        """Generate the update reminder message."""
        return (
            "Consider updating your todo list to reflect current progress. "
            "Mark completed tasks as 'completed' and update in-progress items. "
            "This keeps the user informed and helps you track remaining work."
        )


def get_builtin_reminders() -> list:
    """
    Get a list of all built-in reminder instances.

    Returns:
        List of built-in reminder instances
    """
    return [
        SkillReminder(),
        TodoNeverCalledReminder(),
        TodoUpdateReminder(),
    ]
