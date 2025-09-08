"""
CORRAL Engineer - Core logic for knowledge lifecycle management.
"""

from collections.abc import Iterator
from datetime import datetime
from typing import Any, Union

from dana.core.agent import ProblemContext
from dana.core.agent.context import ExecutionContext
from dana.common.mixins.loggable import Loggable
from .config import DEFAULT_CONFIG, CORRALConfig
from .engines import ActionEngine, CurationEngine, LearningEngine, OrganizationEngine, ReasoningEngine, RetrievalEngine
from .knowledge import Knowledge, KnowledgeCategory
from .operations import ActionResult, CORRALResult, CurationResult, LearningResult, OrganizationResult, ReasoningResult, RetrievalResult


class CORRALEngineer(Loggable):
    """Core engineer responsible for knowledge lifecycle management.

    This class encapsulates the actual work of CORRAL knowledge operations:
    - Knowledge curation from various sources
    - Knowledge organization and categorization
    - Knowledge retrieval and relevance scoring
    - Reasoning with knowledge
    - Action execution based on reasoning
    - Learning from outcomes and feedback
    """

    def __init__(self, config: CORRALConfig | None = None):
        """
        Initialize the CORRAL engineer.

        Args:
            config: CORRAL configuration (uses default if None)
        """
        super().__init__()
        self.config = config or DEFAULT_CONFIG
        self._knowledge_base: dict[str, Knowledge] = {}
        self._initialize_engines()

    def _initialize_engines(self) -> None:
        """Initialize CORRAL processing engines."""
        self._curation_engine = CurationEngine(self.config)
        self._organization_engine = OrganizationEngine(self.config)
        self._retrieval_engine = RetrievalEngine(self.config)
        self._reasoning_engine = ReasoningEngine(self.config)
        self._action_engine = ActionEngine(self.config)
        self._learning_engine = LearningEngine(self.config)

    # ===================== Knowledge Lifecycle Operations =====================

    def curate_knowledge(
        self,
        source: Union[str, Any],
        context: dict[str, Any] | None = None,
        quality_threshold: float | None = None,
        auto_categorize: bool = True,
    ) -> CurationResult:
        """Curate knowledge from various sources.

        Args:
            source: Information source (text, resource, workflow result, etc.)
            context: Additional context for curation
            quality_threshold: Minimum quality score for acceptance
            auto_categorize: Whether to automatically categorize curated knowledge

        Returns:
            CurationResult with curated knowledge items and metadata
        """
        return self._curation_engine.curate(
            source=source,
            context=context or {},
            quality_threshold=quality_threshold or self.config.quality_threshold,
            auto_categorize=auto_categorize,
        )

    def curate_from_interaction(
        self, user_query: str, agent_response: str, outcome: Any, user_feedback: Any | None = None
    ) -> CurationResult:
        """Curate knowledge from agent-user interactions."""
        interaction_data = {
            "user_query": user_query,
            "agent_response": agent_response,
            "outcome": outcome,
            "user_feedback": user_feedback,
            "interaction_type": "user_agent",
        }
        return self.curate_knowledge(interaction_data, {"source_type": "interaction"})

    def curate_from_workflow_execution(
        self, workflow: Any, execution_result: Any, performance_metrics: dict[str, float] | None = None
    ) -> CurationResult:
        """Learn from workflow execution outcomes."""
        workflow_data = {
            "workflow": workflow,
            "execution_result": execution_result,
            "performance_metrics": performance_metrics or {},
            "execution_time": datetime.now(),
        }
        return self.curate_knowledge(workflow_data, {"source_type": "workflow"})

    def organize_knowledge(
        self,
        knowledge_items: list[Knowledge] | None = None,
        categories: list[KnowledgeCategory] | None = None,
        create_relationships: bool = True,
        update_indices: bool = True,
    ) -> OrganizationResult:
        """Organize knowledge into structured, indexed form.

        Args:
            knowledge_items: Raw or partially structured knowledge (None = all knowledge)
            categories: Target categories (auto-detected if None)
            create_relationships: Whether to establish cross-references
            update_indices: Whether to update search indices

        Returns:
            OrganizationResult with structured knowledge graph
        """
        items = knowledge_items or list(self._knowledge_base.values())
        return self._organization_engine.organize(
            knowledge_items=items, categories=categories, create_relationships=create_relationships, update_indices=update_indices
        )

    def categorize_knowledge(self, knowledge: Knowledge, confidence_threshold: float = 0.8) -> KnowledgeCategory:
        """Automatically categorize knowledge into CORRAL taxonomy."""
        return self._organization_engine.categorize(knowledge, confidence_threshold)

    def retrieve_knowledge(
        self,
        query: Union[str, Any],
        categories: list[KnowledgeCategory] | None = None,
        context: dict[str, Any] | None = None,
        max_results: int | None = None,
        min_confidence: float | None = None,
    ) -> RetrievalResult:
        """Retrieve relevant knowledge for current needs.

        Args:
            query: Search query or problem context
            categories: Specific knowledge categories to search
            context: Additional context for relevance scoring
            max_results: Maximum number of results to return
            min_confidence: Minimum confidence threshold

        Returns:
            RetrievalResult with ranked, relevant knowledge
        """
        return self._retrieval_engine.retrieve(
            query=query,
            knowledge_base=self._knowledge_base,
            categories=categories,
            context=context or {},
            max_results=max_results or self.config.max_retrieval_results,
            min_confidence=min_confidence or self.config.min_confidence_threshold,
        )

    def retrieve_for_problem(self, problem_context: ProblemContext) -> RetrievalResult:
        """Get knowledge specifically relevant to current problem."""
        return self.retrieve_knowledge(query=problem_context.problem_statement, context=problem_context.to_dict())

    def retrieve_analogous_situations(self, current_context: dict[str, Any], similarity_threshold: float = 0.7) -> RetrievalResult:
        """Find similar past situations and their outcomes."""
        return self._retrieval_engine.retrieve_analogous(
            current_context=current_context, knowledge_base=self._knowledge_base, similarity_threshold=similarity_threshold
        )

    def reason_with_knowledge(
        self, knowledge_set: list[Knowledge], problem: Union[str, ProblemContext], reasoning_type: str | None = None
    ) -> ReasoningResult:
        """Apply reasoning to knowledge for problem solving.

        Args:
            knowledge_set: Available knowledge for reasoning
            problem: Problem to solve or question to answer
            reasoning_type: Specific type of reasoning (causal, analogical, etc.)

        Returns:
            ReasoningResult with conclusions and reasoning trace
        """
        return self._reasoning_engine.reason(knowledge_set=knowledge_set, problem=problem, reasoning_type=reasoning_type)

    def explain_decision(self, decision: Any, knowledge_used: list[Knowledge]) -> dict[str, Any]:
        """Generate explanation for agent decisions using causal knowledge."""
        return self._reasoning_engine.explain_decision(decision, knowledge_used)

    def predict_outcomes(self, proposed_action: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Predict likely outcomes of proposed actions."""
        return self._reasoning_engine.predict_outcomes(proposed_action, context)

    def act_on_knowledge(self, reasoning_result: ReasoningResult, execution_context: ExecutionContext | None = None) -> ActionResult:
        """Convert reasoning results into executable actions.

        Args:
            reasoning_result: Output from reasoning process
            execution_context: Context for action execution

        Returns:
            ActionResult with executed actions and outcomes
        """
        return self._action_engine.act(
            reasoning_result=reasoning_result,
            execution_context=execution_context,
            agent_instance=None,  # Will be provided by mixin
        )

    def recommend_workflow(self, problem: str, available_resources: list[Any] | None = None) -> dict[str, Any]:
        """Recommend workflows based on procedural knowledge."""
        procedural_knowledge = [k for k in self._knowledge_base.values() if k.category == KnowledgeCategory.PROCEDURAL]
        return self._action_engine.recommend_workflow(problem, procedural_knowledge, available_resources)

    def suggest_resources(self, problem_context: ProblemContext) -> dict[str, Any]:
        """Suggest relevant resources based on declarative knowledge."""
        declarative_knowledge = [k for k in self._knowledge_base.values() if k.category == KnowledgeCategory.DECLARATIVE]
        return self._action_engine.suggest_resources(problem_context, declarative_knowledge)

    def learn_from_outcome(
        self, knowledge_used: list[Knowledge], action_taken: Any, outcome: Any, context: dict[str, Any]
    ) -> LearningResult:
        """Update knowledge based on action outcomes.

        Args:
            knowledge_used: Knowledge that informed the action
            action_taken: Action that was executed
            outcome: Result of the action
            context: Situational context

        Returns:
            LearningResult with knowledge updates and insights
        """
        learning_result = self._learning_engine.learn(
            knowledge_used=knowledge_used, action_taken=action_taken, outcome=outcome, context=context
        )

        # Apply learning updates to knowledge base
        self._apply_learning_updates(learning_result)

        return learning_result

    def _apply_learning_updates(self, learning_result: LearningResult) -> None:
        """Apply learning updates to the knowledge base."""
        for update in learning_result.knowledge_updates:
            if update.knowledge_id in self._knowledge_base:
                knowledge = self._knowledge_base[update.knowledge_id]
                if update.update_type == "confidence_update":
                    knowledge.update_confidence(update.new_value, "learning_engine", update.evidence)
                # Add more update types as needed

        # Remove knowledge marked for removal
        for knowledge_id in learning_result.knowledge_removals:
            self._knowledge_base.pop(knowledge_id, None)

    def update_knowledge_confidence(self, knowledge_items: list[Knowledge], validation_results: list[Any]) -> dict[str, float]:
        """Update confidence scores based on validation results."""
        return self._learning_engine.update_confidence(knowledge_items, validation_results)

    def discover_patterns(self, experience_history: list[dict[str, Any]], pattern_types: list[str] | None = None) -> list[dict[str, Any]]:
        """Discover new patterns from accumulated experience."""
        return self._learning_engine.discover_patterns(experience_history, pattern_types)

    # ===================== Complete Cycle Operations =====================

    def execute_corral_cycle(
        self,
        problem: Union[str, ProblemContext],
        initial_knowledge: list[Knowledge] | None = None,
        agent_instance: Any | None = None,
    ) -> CORRALResult:
        """Execute complete CORRAL cycle for problem solving.

        Args:
            problem: Problem to solve using CORRAL
            initial_knowledge: Starting knowledge (if any)
            agent_instance: Agent instance for action execution

        Returns:
            CORRALResult with complete cycle outcome and learned knowledge
        """
        start_time = datetime.now()
        problem_str = problem if isinstance(problem, str) else problem.problem_statement

        try:
            # 1. CURATE: Gather relevant information for the problem
            curation_result = self.curate_knowledge(source=problem, context={"cycle_start": True, "problem": problem_str})

            # Add initial knowledge if provided
            if initial_knowledge:
                curation_result.curated_knowledge.extend(initial_knowledge)

            # Update knowledge base
            for knowledge in curation_result.curated_knowledge:
                self._knowledge_base[knowledge.id] = knowledge

            # 2. ORGANIZE: Structure the curated knowledge
            organization_result = self.organize_knowledge(curation_result.curated_knowledge)

            # 3. RETRIEVE: Get relevant knowledge for problem solving
            retrieval_result = self.retrieve_knowledge(problem, context={"problem": problem_str})

            # 4. REASON: Apply reasoning to develop solution
            reasoning_result = self.reason_with_knowledge(retrieval_result.knowledge_items, problem)

            # 5. ACT: Execute actions based on reasoning
            action_result = self._action_engine.act(
                reasoning_result=reasoning_result,
                execution_context=getattr(agent_instance, "state", {}).get("execution") if agent_instance else None,
                agent_instance=agent_instance,
            )

            # 6. LEARN: Update knowledge based on outcomes
            learning_result = self.learn_from_outcome(
                knowledge_used=retrieval_result.knowledge_items,
                action_taken=action_result.executed_actions,
                outcome=action_result.outcomes,
                context={"problem": problem_str, "cycle": True},
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            cycle_success = action_result.success_rate > 0.5  # Simple success criterion

            return CORRALResult(
                problem_statement=problem_str,
                curation_result=curation_result,
                organization_result=organization_result,
                retrieval_result=retrieval_result,
                reasoning_result=reasoning_result,
                action_result=action_result,
                learning_result=learning_result,
                cycle_success=cycle_success,
                total_execution_time=execution_time,
            )

        except Exception as e:
            # Return partial result on failure
            execution_time = (datetime.now() - start_time).total_seconds()
            return CORRALResult(
                problem_statement=problem_str,
                curation_result=CurationResult([], {}, []),
                organization_result=OrganizationResult([], {}, [], []),
                retrieval_result=RetrievalResult([], 0, 0.0),
                reasoning_result=ReasoningResult([], {}, [], []),
                action_result=ActionResult([], [], 0.0),
                learning_result=LearningResult([], [], {}, []),
                cycle_success=False,
                total_execution_time=execution_time,
                metadata={"error": str(e)},
            )

    def continuous_corral(self, problem_stream: Iterator[ProblemContext], agent_instance: Any | None = None) -> Iterator[CORRALResult]:
        """Execute CORRAL continuously on stream of problems."""
        for problem_context in problem_stream:
            result = self.execute_corral_cycle(problem_context, agent_instance=agent_instance)
            yield result

    # ===================== Knowledge Base Management =====================

    def add_knowledge(self, knowledge: Knowledge) -> None:
        """Add knowledge to the knowledge base."""
        self._knowledge_base[knowledge.id] = knowledge

    def get_knowledge(self, knowledge_id: str) -> Knowledge | None:
        """Get knowledge by ID."""
        return self._knowledge_base.get(knowledge_id)

    def get_knowledge_state(self) -> dict[str, Any]:
        """Get current knowledge state for integration with AgentState."""
        return {
            "knowledge_count": len(self._knowledge_base),
            "categories": {cat.value: len([k for k in self._knowledge_base.values() if k.category == cat]) for cat in KnowledgeCategory},
            "average_confidence": sum(k.confidence for k in self._knowledge_base.values()) / max(len(self._knowledge_base), 1),
            "last_updated": max((k.timestamp for k in self._knowledge_base.values()), default=datetime.now()),
            "config": self.config,
        }

    def set_knowledge_state(self, knowledge_state: dict[str, Any]) -> None:
        """Set knowledge state from AgentState."""
        if "config" in knowledge_state:
            self.config = knowledge_state["config"]
            self._initialize_engines()

    def contribute_to_context(self, problem_context: ProblemContext, context_depth: str = "standard") -> dict[str, Any]:
        """Contribute knowledge-based context to ContextEngine."""
        relevant_knowledge = self.retrieve_for_problem(problem_context)

        context_contribution = {
            "relevant_knowledge_count": len(relevant_knowledge.knowledge_items),
            "knowledge_confidence": relevant_knowledge.retrieval_confidence,
        }

        if context_depth in ["standard", "comprehensive"]:
            # Add top knowledge items
            top_knowledge = relevant_knowledge.knowledge_items[:3]
            context_contribution["top_relevant_knowledge"] = [
                {
                    "category": k.category.value,
                    "confidence": k.confidence,
                    "content_summary": str(k.content)[:200] + "..." if len(str(k.content)) > 200 else str(k.content),
                }
                for k in top_knowledge
            ]

        return context_contribution

    # ===================== Factory Methods =====================

    @classmethod
    def from_agent(cls, agent: Any, **config) -> "CORRALEngineer":
        """Create a CORRAL engineer for an agent."""
        corral_config = config.get("corral_config", DEFAULT_CONFIG)
        return cls(corral_config)
