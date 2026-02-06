"""Spinner component with phase-based text for STAR loop display."""

from rich.spinner import Spinner


# Phase display text mapping
_PHASE_TEXT = {
    "SEE": "Processing...",
    "THINK": "Thinking...",
    "ACT": "Executing...",
    "REFLECT": "Reflecting...",
}


class SpinnerComponent:
    """A spinner that updates its text based on the current STAR phase.

    Wraps rich.spinner.Spinner with phase-aware text updates.
    """

    def __init__(self, style: str = "dots") -> None:
        self._spinner = Spinner(style)
        self._running = False
        self._text = ""

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
        else:
            self._text = _PHASE_TEXT.get(phase, f"{phase}...")

        self._spinner.update(text=self._text)

    def start(self) -> None:
        """Mark the spinner as running."""
        self._running = True

    def stop(self) -> None:
        """Mark the spinner as stopped."""
        self._running = False
