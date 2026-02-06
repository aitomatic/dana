"""Status line component showing current agent, model, and turn info."""


class StatusLineComponent:
    """Displays a persistent status line with agent context.

    Shows the current agent ID, model name, and turn progress
    in a compact format suitable for the bottom of the terminal.
    """

    def __init__(self) -> None:
        self._agent_id = ""
        self._model = ""
        self._turn = 0
        self._max_turns = 0

    @property
    def agent_id(self) -> str:
        """Current agent identifier."""
        return self._agent_id

    @property
    def model(self) -> str:
        """Current model name."""
        return self._model

    @property
    def turn(self) -> int:
        """Current turn number."""
        return self._turn

    @property
    def max_turns(self) -> int:
        """Maximum number of turns."""
        return self._max_turns

    def update(
        self,
        agent_id: str = "",
        model: str = "",
        turn: int = 0,
        max_turns: int = 0,
    ) -> None:
        """Update the status line fields.

        Args:
            agent_id: The current agent identifier.
            model: The current model name.
            turn: The current turn number.
            max_turns: The maximum number of turns.
        """
        self._agent_id = agent_id
        self._model = model
        self._turn = turn
        self._max_turns = max_turns

    def render(self) -> str:
        """Render the status line as a formatted string.

        Format: 'agent_id | model | turn N/M'
        Turn info is only shown if turn > 0.

        Returns:
            Formatted status line string.
        """
        parts: list[str] = []

        if self._agent_id:
            parts.append(self._agent_id)

        if self._model:
            parts.append(self._model)

        if self._turn > 0:
            parts.append(f"turn {self._turn}/{self._max_turns}")

        return " | ".join(parts)
