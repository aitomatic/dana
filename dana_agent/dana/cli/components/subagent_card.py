"""Subagent card component for collapsing nested tool calls into a single container."""

import time
from typing import Any

from rich.console import Group, RenderableType
from rich.text import Text


class SubagentCardComponent:
    """Container for tool calls made by a subagent.

    Collapses many tool calls into a single visual card, similar to
    Claude Code's subagent display:

    Collapsed (in progress):
      ● Explore(Explore codec runtime usage)
        └─ Search(pattern: "...", path: "...")
           +64 more tool uses

    Completed:
      ● Explore(Explore codec runtime usage)
        └─ Done (38 tool uses in 28s)
    """

    def __init__(self, agent_type: str, purpose: str) -> None:
        self.agent_type = agent_type
        self.purpose = purpose
        self.start_time = time.time()
        self.tool_calls: list[dict[str, Any]] = []
        self.tool_results: list[dict[str, Any]] = []
        self.is_complete = False
        self.completion_time: float | None = None

    def add_tool_call(self, tool_call: dict[str, Any]) -> None:
        """Record a tool call made inside this subagent."""
        self.tool_calls.append(tool_call)

    def add_tool_result(self, result: dict[str, Any]) -> None:
        """Record a tool result from inside this subagent."""
        self.tool_results.append(result)

    def complete(self) -> None:
        """Mark this subagent as completed."""
        self.is_complete = True
        self.completion_time = time.time()

    @property
    def tool_count(self) -> int:
        """Total tool calls recorded."""
        return len(self.tool_calls)

    @property
    def elapsed_seconds(self) -> float:
        """Seconds since subagent started."""
        end = self.completion_time if self.completion_time else time.time()
        return end - self.start_time

    @property
    def elapsed_text(self) -> str:
        """Human-readable elapsed time."""
        elapsed = self.elapsed_seconds
        if elapsed < 60:
            return f"{int(elapsed)}s"
        return f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

    def _format_last_tool(self) -> str:
        """Format the most recent tool call for the collapsed view."""
        if not self.tool_calls:
            return ""
        last = self.tool_calls[-1]
        func = last.get("function", "unknown")
        args = last.get("arguments", {})

        # Build a compact param summary
        if func.lower() in ("search", "grep", "find", "ripgrep"):
            pattern = args.get("pattern", "")
            path = args.get("path", "")
            parts = []
            if pattern:
                parts.append(f'pattern: "{pattern}"')
            if path:
                parts.append(f'path: "{path}"')
            return f"{func}({', '.join(parts)})" if parts else func
        elif func.lower() in ("read", "read_file"):
            path = args.get("file_path", args.get("path", ""))
            return f"{func}({path})" if path else func
        elif func.lower() in ("glob",):
            pattern = args.get("pattern", "")
            return f"{func}({pattern})" if pattern else func
        elif func.lower() in ("bash", "shell", "execute"):
            cmd = str(args.get("command", ""))
            if len(cmd) > 40:
                cmd = cmd[:40] + "..."
            return f"{func}({cmd})" if cmd else func
        else:
            return func

    def render(self, expanded: bool = False) -> RenderableType:
        """Render the subagent card.

        Args:
            expanded: If True, show all tool calls. If False, show collapsed.

        Returns:
            A Rich renderable (Group of Text lines).
        """
        lines: list[RenderableType] = []

        # Header line: ● AgentType(purpose)
        if self.is_complete:
            header = Text()
            header.append("  ", style="")
            header.append("● ", style="bold green")
            header.append(f"{self.agent_type}", style="bold")
            header.append(f"({self.purpose})", style="dim")
            lines.append(header)
        else:
            header = Text()
            header.append("  ", style="")
            header.append("● ", style="bold cyan")
            header.append(f"{self.agent_type}", style="bold")
            header.append(f"({self.purpose})", style="dim")
            lines.append(header)

        if expanded and self.tool_calls:
            # Show all tool calls
            for i, tc in enumerate(self.tool_calls):
                func = tc.get("function", "unknown")
                is_last = i == len(self.tool_calls) - 1
                connector = "└─" if is_last else "├─"
                line = Text()
                line.append(f"    {connector} ", style="dim")
                line.append(func, style="")
                lines.append(line)
        elif self.is_complete:
            # Completed summary
            summary = Text()
            summary.append("    └─ ", style="dim")
            summary.append(f"Done ({self.tool_count} tool uses in {self.elapsed_text})", style="dim")
            lines.append(summary)
        elif self.tool_calls:
            # Collapsed: show last tool + count
            last_tool = self._format_last_tool()
            detail = Text()
            detail.append("    └─ ", style="dim")
            detail.append(last_tool, style="")
            lines.append(detail)

            if self.tool_count > 1:
                more = Text()
                more.append(f"       +{self.tool_count - 1} more tool uses", style="dim")
                lines.append(more)

        return Group(*lines)

    def render_plain(self) -> str:
        """Render as plain text for no-color terminals."""
        if self.is_complete:
            return f"  ● {self.agent_type}({self.purpose}) - Done ({self.tool_count} tool uses in {self.elapsed_text})"
        elif self.tool_calls:
            last_tool = self._format_last_tool()
            result = f"  ● {self.agent_type}({self.purpose})\n    └─ {last_tool}"
            if self.tool_count > 1:
                result += f"\n       +{self.tool_count - 1} more tool uses"
            return result
        else:
            return f"  ● {self.agent_type}({self.purpose})"
