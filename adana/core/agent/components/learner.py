"""
Learner: Handles the four learning phases of STAR reflection.

This component provides functionality for:
- ACQUISITIVE learning (immediate experience reflection)
- EPISODIC learning (episode-level reflection)
- INTEGRATIVE learning (multi-episode integration)
- RETENTIVE learning (long-term learning)
"""

from datetime import datetime
from typing import TYPE_CHECKING

from adana.common.observable import observable
from adana.common.protocols import DictParams


if TYPE_CHECKING:
    from adana.core.agent.star_agent import STARAgent


class Learner:
    """Component providing STAR learning phase implementations."""

    def __init__(self, agent: "STARAgent"):
        """
        Initialize the component with a reference to the agent.

        Args:
            agent: The agent instance this component belongs to
        """
        self._agent = agent

    # ============================================================================
    # LEARNING PHASES (STAR REFLECTION IMPLEMENTATIONS)
    # ============================================================================

    @observable
    def _reflect_acquisitive(self, trace_acquisitive: DictParams) -> DictParams:
        """
        Reflect on the acquisitions (immediate learning phase).

        Args:
            trace_acquisitive from the ACT phase containing tool_results

        Returns:
            trace_learning: Learning insights from the acquisitions
        """
        tool_results = trace_acquisitive.get("tool_results", [])

        trace_learning = {
            "acquisitions_summary": f"Processed acquisitions with {len(tool_results)} tool results",
            "timestamp": datetime.now().isoformat(),
            "tool_results": tool_results,
        }
        return {"trace_learning": trace_learning}

    @observable
    def _reflect_episodic(self, trace_episodic: DictParams) -> DictParams:
        """
        Reflect on an episode (collection of experiences).

        Args:
            trace_episodic: Collection of experiences from the episode

        Returns:
            trace_learning: Learning insights from the episode
        """
        # Basic episode reflection - can be overridden by subclasses
        trace_learning = {
            "episode_summary": f"Processed episode with {len(trace_episodic)} interactions",
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}

    @observable
    def _reflect_integrative(self, trace_integrative: DictParams) -> DictParams:
        """
        Reflect on integration (collection of episodes).

        Args:
            trace_integrative: Collection of episodes to integrate

        Returns:
            trace_learning: Integrated learning insights
        """
        # Basic integration reflection - can be overridden by subclasses
        trace_learning = {"integrative_summary": "Integrated learning from multiple episodes", "timestamp": datetime.now().isoformat()}
        return {"trace_learning": trace_learning}

    @observable
    def _reflect_retentive(self, trace_retentive: DictParams) -> DictParams:
        """
        Reflect on retention (long-term learning).

        Args:
            trace_retentive: Long-term learning data

        Returns:
            trace_learning: Retained learning insights
        """
        # Basic retention reflection - can be overridden by subclasses
        trace_learning = {
            "retentive_summary": "Long-term learning retention",
            "timestamp": datetime.now().isoformat(),
        }
        return {"trace_learning": trace_learning}
