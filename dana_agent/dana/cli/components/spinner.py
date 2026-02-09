"""Spinner component with phase-based text for STAR loop display."""

import time

from rich.spinner import Spinner


# Phase display text mapping
_PHASE_TEXT = {
    "SEE": "Processing...",
    "THINK": "Thinking...",
    "ACT": "Executing...",
    "REFLECT": "Reflecting...",
}

# Rotating messages for the THINK phase
_THINK_MESSAGES = [
    "Thinking...",
    "Reasoning...",
    "Analyzing...",
    "Considering...",
    "Evaluating...",
]


class SpinnerComponent:
    """A spinner that updates its text based on the current STAR phase.

    Wraps rich.spinner.Spinner with phase-aware text updates
    and elapsed time tracking.
    """

    def __init__(self, style: str = "dots") -> None:
        self._spinner = Spinner(style)
        self._running = False
        self._text = ""
        self._start_time: float = 0.0
        self._tool_count: int = 0
        self._char_count: int = 0
        self._think_rotation: int = 0

    @property
    def running(self) -> bool:
        """Whether the spinner is currently active."""
        return self._running

    @property
    def text(self) -> str:
        """Current spinner text as a plain string."""
        return self._text

    @property
    def spinner(self) -> Spinner:
        """The underlying Rich Spinner instance."""
        return self._spinner

    @property
    def tool_count(self) -> int:
        """Number of tool calls tracked since last start."""
        return self._tool_count

    @property
    def elapsed_text(self) -> str:
        """Human-readable elapsed time since start."""
        if self._start_time == 0.0:
            return "0s"
        elapsed = time.time() - self._start_time
        if elapsed < 60:
            return f"{int(elapsed)}s"
        return f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

    @property
    def estimated_tokens_text(self) -> str:
        """Human-readable estimated token count (chars / 4)."""
        tokens = self._char_count // 4
        if tokens >= 1_000_000:
            return f"~{tokens / 1_000_000:.1f}M tokens"
        if tokens >= 1_000:
            return f"~{tokens / 1_000:.1f}k tokens"
        return f"~{tokens} tokens"

    def increment_chars(self, n: int) -> None:
        """Add to the character counter for token estimation."""
        self._char_count += n

    def increment_tool_count(self) -> None:
        """Increment the tool call counter."""
        self._tool_count += 1

    def update_phase(self, phase: str, context: dict[str, object] | None = None) -> None:
        """Update the spinner text based on the STAR phase.

        Args:
            phase: The STAR phase name (SEE, THINK, ACT, REFLECT).
            context: Optional context dict. For ACT phase, may contain
                'tools' key with a list of tool names.
        """
        context = context or {}

        if phase == "ACT":
            tools = context.get("tools")
            if tools and isinstance(tools, list) and len(tools) > 0:
                tool_names = ", ".join(str(t) for t in tools)
                self._text = f"Executing {tool_names}..."
            else:
                self._text = _PHASE_TEXT["ACT"]
        elif phase == "THINK":
            msg = _THINK_MESSAGES[self._think_rotation % len(_THINK_MESSAGES)]
            self._think_rotation += 1
            self._text = msg
        else:
            self._text = _PHASE_TEXT.get(phase, f"{phase}...")

        self._spinner.update(text=self._text)

    def start(self) -> None:
        """Mark the spinner as running and record start time."""
        self._running = True
        self._start_time = time.time()
        self._tool_count = 0
        self._char_count = 0

    def stop(self) -> None:
        """Mark the spinner as stopped."""
        self._running = False
