from dana.common.protocols import DictParams
from dana.core.llm.llm import LLM

from .base_star_agent import BaseSTARAgent


class CompactSTARAgent(BaseSTARAgent):
    """STARAgent implementation using composition-based architecture."""

    # Configuration constants
    MAX_THINK_RETRIES = 3  # Maximum retries when output format or done/response rules are invalid

    def __init__(self, agent_type: str | None = None, agent_id: str | None = None, llm: LLM | None = None, **kwargs):
        """
        Initialize the CompactSTARAgent.
        """
        super().__init__(agent_type, agent_id, **kwargs)
        self.llm = llm

    def _see(self, trace_inputs: DictParams) -> DictParams:
        """
        SEE: See the inputs and produce percepts.
        """
        ...

    def _think(self, trace_percepts: DictParams) -> DictParams:
        """
        THINK: Think about the percepts and produce thoughts.
        """
        ...

    def _act(self, trace_thoughts: DictParams) -> DictParams:
        """
        ACT: Act on the thoughts and produce outputs.
        """
        ...

    def _reflect(self, trace_outputs: DictParams) -> DictParams:
        """
        pass
        """
        ...
