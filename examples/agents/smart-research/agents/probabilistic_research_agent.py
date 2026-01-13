"""ProbabilisticAgent - Transparent research assistant with visible STAR loop."""

from dana.core.agent.star_agent import STARAgent
from dana.lib.resources.conversation import ConversationResource
from dana.lib.resources.web_research.search import SearchResource
from dana.lib.resources.web_research.web_fetcher import WebFetcher
from dana.lib.workflows.web_research import GoogleLookupWorkflow

# Import local components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from resources.source_ranking import SourceRankingResource
from workflows.research_strategy import ResearchStrategyWorkflow
from workflows.parallel_gathering import ParallelGatheringWorkflow
from workflows.synthesis import SynthesisWorkflow


class ProbabilisticResearchAgent(STARAgent):
    """
    Transparent research assistant showing visible STAR loop.

    Unlike black-box AI tools, ProbabilisticResearchAgent shows you:
    - SEE: How it understands your query
    - THINK: What research strategy it chooses and why
    - ACT: Where it searches and how it evaluates sources
    - REFLECT: How confident it is and what's missing

    Features:
    - Magic function interface (agent.research_topic_name())

    See design.md for complete specification.
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        super().__init__(
            agent_type="probabilistic-research",
            agent_id=agent_id or "probabilistic-research-001",
            llm_provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            **kwargs
        )

        # Compose resources (80% reused from framework)
        self.with_resources(
            SearchResource(resource_id="web-search"),
            WebFetcher(resource_id="web-fetch"),
            ConversationResource(
                resource_id="llm-reasoning",
                llm_provider="anthropic",
                model="claude-3-5-sonnet-20241022"
            ),
            SourceRankingResource(resource_id="source-ranking"),
        )

        # Compose workflows
        """
        self.with_workflows(
            ResearchStrategyWorkflow(workflow_id="strategy-selection"),
            ParallelGatheringWorkflow(workflow_id="parallel-gather"),
            SynthesisWorkflow(workflow_id="synthesis"),
            GoogleLookupWorkflow(workflow_id="quick-lookup"),
        )
        """

    def __getattr__(self, name: str):
        """
        Magic function support: Convert method calls to natural language.

        Examples:
            agent.research_quantum_computing() -> converse("research quantum computing")
            agent.compare_react_vs_vue() -> converse("compare react vs vue")
            agent.explain_transformer_architecture() -> converse("explain transformer architecture")

        This provides an intuitive interface while maintaining full STAR loop autonomy.
        """
        def magic_method(*args, **kwargs):
            # Convert method name to natural language
            natural_language = name.replace("_", " ").strip()

            # Add any positional arguments as additional context
            if args:
                args_str = " ".join(str(arg) for arg in args)
                natural_language += f" {args_str}"

            # Add any keyword arguments as additional context
            if kwargs:
                kwargs_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
                natural_language += f" {kwargs_str}"

            # Call converse with the natural language message
            return self.converse(initial_message=natural_language)

        return magic_method
