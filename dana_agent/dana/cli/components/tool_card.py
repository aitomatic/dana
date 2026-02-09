"""Tool card component for displaying tool invocations as formatted panels."""

from typing import Any

from rich.panel import Panel
from rich.text import Text


# Tool type to icon mapping
_TOOL_ICONS: dict[str, str] = {
    "bash": "🔧",
    "file-io": "📁",
    "search": "🔍",
    "task": "🤖",
}

_DEFAULT_ICON = "⚡"


class ToolCardComponent:
    """Renders a tool invocation as a formatted Rich Panel.

    Displays tool name with an icon and key parameters based on tool type.
    """

    def render(self, tool_call: dict[str, Any]) -> Panel:
        """Render a tool call as a Rich Panel.

        Args:
            tool_call: Dict with 'function' (str) and 'arguments' (dict).

        Returns:
            A Rich Panel displaying the tool invocation.
        """
        function_name = tool_call.get("function", "unknown")
        arguments = tool_call.get("arguments", {})

        tool_type = self._classify_tool(function_name)
        icon = _TOOL_ICONS.get(tool_type, _DEFAULT_ICON)
        title = f"{icon} {function_name}"
        body = self._format_params(tool_type, arguments)

        return Panel(
            body,
            title=title,
            title_align="left",
            border_style="dim",
            expand=False,
        )

    def _classify_tool(self, function_name: str) -> str:
        """Classify a tool function name into a tool type.

        Returns:
            One of 'bash', 'file-io', 'search', 'task', or 'other'.
        """
        name = function_name.lower()
        if name in ("bash", "shell", "execute"):
            return "bash"
        if name in ("read_file", "write_file", "edit_file", "read", "write", "edit", "glob"):
            return "file-io"
        if name in ("search", "grep", "find", "ripgrep"):
            return "search"
        if name in ("task", "agent", "subagent"):
            return "task"
        return "other"

    def _format_params(self, tool_type: str, arguments: dict[str, Any]) -> Text:
        """Format tool parameters based on tool type.

        Args:
            tool_type: The classified tool type.
            arguments: The tool call arguments dict.

        Returns:
            A Rich Text with formatted parameter display.
        """
        if tool_type == "bash":
            command = str(arguments.get("command", ""))
            if len(command) > 100:
                command = command[:100] + "…"
            return Text(command) if command else Text("(no command)")

        if tool_type == "file-io":
            path = str(arguments.get("path", arguments.get("file_path", "")))
            return Text(path) if path else Text("(no path)")

        if tool_type == "search":
            pattern = str(arguments.get("pattern", ""))
            path = str(arguments.get("path", ""))
            parts = []
            if pattern:
                parts.append(f"pattern: {pattern}")
            if path:
                parts.append(f"path: {path}")
            return Text(", ".join(parts)) if parts else Text("(no params)")

        if tool_type == "task":
            agent_id = str(arguments.get("agent_id", arguments.get("agent_type", "")))
            prompt = str(arguments.get("prompt", ""))
            if len(prompt) > 50:
                prompt = prompt[:50] + "…"
            parts = []
            if agent_id:
                parts.append(f"agent: {agent_id}")
            if prompt:
                parts.append(f"prompt: {prompt}")
            return Text(", ".join(parts)) if parts else Text("(no params)")

        # Default: show all arguments as key=value
        if arguments:
            items = [f"{k}={v}" for k, v in arguments.items()]
            return Text(", ".join(items))
        return Text("(no params)")
