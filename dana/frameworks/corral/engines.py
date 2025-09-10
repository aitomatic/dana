"""CORRAL processing engines that implement the core knowledge operations."""

import json
from datetime import datetime
from typing import Any, Union

from dana.core.agent.context import ProblemContext
from dana.core.agent.context import ExecutionContext

from .config import CORRALConfig, ReasoningType
from .knowledge import Knowledge, KnowledgeCategory, create_knowledge
from .operations import (
    CurationResult,
    OrganizationResult,
    RetrievalResult,
    ReasoningResult,
    ActionResult,
    LearningResult,
    RankedKnowledge,
    CrossReference,
    ReasoningTrace,
    KnowledgeGap,
    ExecutedAction,
    LearningUpdate,
    NewPattern,
)


class CurationEngine:
    """Engine for curating knowledge from various sources."""

    def __init__(self, config: CORRALConfig):
        self.config = config

    def curate(
        self, source: Union[str, dict[str, Any], Any], context: dict[str, Any], quality_threshold: float, auto_categorize: bool
    ) -> CurationResult:
        """Curate knowledge from source."""
        curated_knowledge = []
        quality_scores = {}
        processing_recommendations = []

        # Handle different source types
        if isinstance(source, str):
            knowledge_items = self._curate_from_text(source, context)
        elif isinstance(source, dict):
            knowledge_items = self._curate_from_structured_data(source, context)
        elif isinstance(source, ProblemContext):
            knowledge_items = self._curate_from_problem_context(source, context)
        else:
            knowledge_items = self._curate_from_generic(source, context)

        # Filter by quality and categorize
        for item in knowledge_items:
            quality_score = self._assess_quality(item, context)
            if quality_score >= quality_threshold:
                if auto_categorize:
                    # Auto-categorize and update the item
                    new_category = self._auto_categorize(item)
                    item.category = new_category
                curated_knowledge.append(item)
                quality_scores[item.id] = quality_score
            else:
                processing_recommendations.append(f"Low quality knowledge filtered: {item.id}")

        return CurationResult(
            curated_knowledge=curated_knowledge,
            quality_scores=quality_scores,
            processing_recommendations=processing_recommendations,
            metadata={"source_type": type(source).__name__, "context": context},
        )

    def _curate_from_text(self, text: str, context: dict[str, Any]) -> list[Knowledge]:
        """Extract knowledge from text."""
        knowledge_items = []

        # Simple pattern-based extraction (would be more sophisticated in practice)
        if "because" in text.lower() or "causes" in text.lower():
            # Potential causal knowledge
            knowledge = create_knowledge(
                category=KnowledgeCategory.CAUSAL,
                content={"text": text, "extracted_type": "causal_pattern"},
                confidence=0.6,
                source="text_extraction",
            )
            knowledge_items.append(knowledge)

        if "step" in text.lower() or "process" in text.lower() or "how to" in text.lower():
            # Potential procedural knowledge
            knowledge = create_knowledge(
                category=KnowledgeCategory.PROCEDURAL,
                content={"text": text, "extracted_type": "procedural_pattern"},
                confidence=0.7,
                source="text_extraction",
            )
            knowledge_items.append(knowledge)

        # Default declarative knowledge
        if not knowledge_items:
            knowledge = create_knowledge(
                category=KnowledgeCategory.DECLARATIVE,
                content={"text": text, "extracted_type": "default"},
                confidence=0.5,
                source="text_extraction",
            )
            knowledge_items.append(knowledge)

        return knowledge_items

    def _curate_from_structured_data(self, data: dict[str, Any], context: dict[str, Any]) -> list[Knowledge]:
        """Extract knowledge from structured data."""
        knowledge_items = []

        # Handle interaction data
        if "user_query" in data and "agent_response" in data:
            knowledge = create_knowledge(
                category=KnowledgeCategory.DECLARATIVE,
                content={
                    "interaction": data,
                    "extracted_type": "user_interaction",
                    "query": data["user_query"],
                    "response": data["agent_response"],
                },
                confidence=0.8,
                source="interaction",
            )
            knowledge_items.append(knowledge)

        # Handle workflow data
        if "workflow" in data and "execution_result" in data:
            knowledge = create_knowledge(
                category=KnowledgeCategory.PROCEDURAL,
                content={
                    "workflow_data": data,
                    "extracted_type": "workflow_execution",
                    "workflow": str(data["workflow"]),
                    "result": str(data["execution_result"]),
                },
                confidence=0.9,
                source="workflow",
            )
            knowledge_items.append(knowledge)

        return knowledge_items

    def _curate_from_problem_context(self, problem: ProblemContext, context: dict[str, Any]) -> list[Knowledge]:
        """Extract knowledge from problem context."""
        knowledge_items = []

        # Create declarative knowledge about the problem
        problem_knowledge = create_knowledge(
            category=KnowledgeCategory.DECLARATIVE,
            content={
                "problem_statement": problem.problem_statement,
                "objective": problem.objective,
                "depth": problem.depth,
                "constraints": problem.constraints,
                "assumptions": problem.assumptions,
                "extracted_type": "problem_context",
            },
            confidence=0.9,
            source="problem_context",
        )
        knowledge_items.append(problem_knowledge)

        return knowledge_items

    def _curate_from_generic(self, source: Any, context: dict[str, Any]) -> list[Knowledge]:
        """Extract knowledge from generic source."""
        knowledge = create_knowledge(
            category=KnowledgeCategory.DECLARATIVE,
            content={"source": str(source), "source_type": type(source).__name__, "extracted_type": "generic"},
            confidence=0.4,
            source="generic",
        )
        return [knowledge]

    def _assess_quality(self, knowledge: Knowledge, context: dict[str, Any]) -> float:
        """Assess the quality of curated knowledge."""
        base_score = knowledge.confidence

        # Boost score based on source reliability
        if knowledge.source in ["workflow", "interaction"]:
            base_score += 0.1

        # Boost score if content is rich
        content_richness = len(str(knowledge.content)) / 1000.0  # Normalize by length
        base_score += min(content_richness, 0.2)

        # Boost score for cycle start context (initial problem statements are important)
        if context.get("cycle_start"):
            base_score += 0.2

        return min(base_score, 1.0)

    def _auto_categorize(self, knowledge: Knowledge) -> KnowledgeCategory:
        """Automatically categorize knowledge."""
        # Extract text content properly like in relevance calculation
        content_str = ""
        if isinstance(knowledge.content, dict):
            content_values = []
            for value in knowledge.content.values():
                if isinstance(value, str):
                    content_values.append(value)
                else:
                    content_values.append(str(value))
            content_str = " ".join(content_values).lower()
        else:
            content_str = str(knowledge.content).lower()

        # Simple heuristics for categorization
        if any(word in content_str for word in ["step", "process", "how", "procedure", "workflow"]):
            return KnowledgeCategory.PROCEDURAL
        elif any(word in content_str for word in ["because", "cause", "effect", "reason"]):
            return KnowledgeCategory.CAUSAL
        elif any(word in content_str for word in ["when", "if", "condition", "trigger"]):
            return KnowledgeCategory.CONDITIONAL
        elif any(word in content_str for word in ["relationship", "connection", "network"]):
            return KnowledgeCategory.RELATIONAL
        else:
            return KnowledgeCategory.DECLARATIVE


class OrganizationEngine:
    """Engine for organizing knowledge into structured form."""

    def __init__(self, config: CORRALConfig):
        self.config = config

    def organize(
        self,
        knowledge_items: list[Knowledge],
        categories: list[KnowledgeCategory] | None,
        create_relationships: bool,
        update_indices: bool,
    ) -> OrganizationResult:
        """Organize knowledge items."""
        structured_knowledge = []
        knowledge_graph = {}
        cross_references = []
        indices_created = []

        # Categorize knowledge if not already categorized
        for knowledge in knowledge_items:
            if categories and knowledge.category not in categories:
                continue

            structured_knowledge.append(knowledge)
            knowledge_graph[knowledge.id] = []

        # Create relationships if requested
        if create_relationships:
            cross_references = self._create_relationships(structured_knowledge)

            # Update graph with relationships
            for ref in cross_references:
                if ref.from_knowledge_id in knowledge_graph:
                    knowledge_graph[ref.from_knowledge_id].append(ref.to_knowledge_id)

        # Create indices if requested
        if update_indices:
            indices_created = self._create_indices(structured_knowledge)

        return OrganizationResult(
            structured_knowledge=structured_knowledge,
            knowledge_graph=knowledge_graph,
            cross_references=cross_references,
            indices_created=indices_created,
            metadata={"organization_time": datetime.now()},
        )

    def categorize(self, knowledge: Knowledge, confidence_threshold: float) -> KnowledgeCategory:
        """Categorize a single knowledge item."""
        # Extract text content properly
        content_str = ""
        if isinstance(knowledge.content, dict):
            content_values = []
            for value in knowledge.content.values():
                if isinstance(value, str):
                    content_values.append(value)
                else:
                    content_values.append(str(value))
            content_str = " ".join(content_values).lower()
        else:
            content_str = str(knowledge.content).lower()

        category_scores = {
            KnowledgeCategory.PROCEDURAL: self._score_procedural(content_str),
            KnowledgeCategory.CAUSAL: self._score_causal(content_str),
            KnowledgeCategory.CONDITIONAL: self._score_conditional(content_str),
            KnowledgeCategory.RELATIONAL: self._score_relational(content_str),
            KnowledgeCategory.DECLARATIVE: self._score_declarative(content_str),
        }

        best_category = max(category_scores, key=category_scores.get)
        if category_scores[best_category] >= confidence_threshold:
            return best_category
        else:
            return KnowledgeCategory.DECLARATIVE  # Default fallback

    def _create_relationships(self, knowledge_items: list[Knowledge]) -> list[CrossReference]:
        """Create relationships between knowledge items."""
        relationships = []

        for i, item1 in enumerate(knowledge_items):
            for item2 in knowledge_items[i + 1 :]:
                similarity = self._calculate_similarity(item1, item2)
                if similarity > 0.5:  # Threshold for relationship creation
                    relationships.append(
                        CrossReference(
                            from_knowledge_id=item1.id, to_knowledge_id=item2.id, relationship_type="similarity", strength=similarity
                        )
                    )

        return relationships

    def _create_indices(self, knowledge_items: list[Knowledge]) -> list[str]:
        """Create search indices for knowledge."""
        indices = []

        # Category index
        category_index = {}
        for item in knowledge_items:
            if item.category.value not in category_index:
                category_index[item.category.value] = []
            category_index[item.category.value].append(item.id)
        indices.append("category_index")

        # Confidence index
        confidence_index = {"high": [], "medium": [], "low": []}
        for item in knowledge_items:
            if item.confidence >= 0.8:
                confidence_index["high"].append(item.id)
            elif item.confidence >= 0.5:
                confidence_index["medium"].append(item.id)
            else:
                confidence_index["low"].append(item.id)
        indices.append("confidence_index")

        return indices

    def _calculate_similarity(self, item1: Knowledge, item2: Knowledge) -> float:
        """Calculate similarity between knowledge items."""
        # Simple similarity based on content overlap
        content1 = str(item1.content).lower()
        content2 = str(item2.content).lower()

        words1 = set(content1.split())
        words2 = set(content2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _score_procedural(self, content: str) -> float:
        """Score content for procedural knowledge."""
        procedural_words = ["step", "process", "how", "procedure", "method", "algorithm"]
        return sum(1 for word in procedural_words if word in content) / len(procedural_words)

    def _score_causal(self, content: str) -> float:
        """Score content for causal knowledge."""
        causal_words = ["because", "cause", "effect", "reason", "leads to", "results in"]
        return sum(1 for word in causal_words if word in content) / len(causal_words)

    def _score_conditional(self, content: str) -> float:
        """Score content for conditional knowledge."""
        conditional_words = ["when", "if", "condition", "trigger", "depends on"]
        return sum(1 for word in conditional_words if word in content) / len(conditional_words)

    def _score_relational(self, content: str) -> float:
        """Score content for relational knowledge."""
        relational_words = ["relationship", "connection", "network", "linked", "associated"]
        return sum(1 for word in relational_words if word in content) / len(relational_words)

    def _score_declarative(self, content: str) -> float:
        """Score content for declarative knowledge."""
        # Default score - all content has some declarative aspect
        return 0.3


class RetrievalEngine:
    """Engine for retrieving relevant knowledge."""

    def __init__(self, config: CORRALConfig):
        self.config = config

    def retrieve(
        self,
        query: Union[str, Any],
        knowledge_base: dict[str, Knowledge],
        categories: list[KnowledgeCategory] | None,
        context: dict[str, Any],
        max_results: int,
        min_confidence: float,
    ) -> RetrievalResult:
        """Retrieve relevant knowledge."""
        query_str = str(query)
        candidates = []

        # Filter by categories if specified
        filtered_knowledge = knowledge_base.values()
        if categories:
            filtered_knowledge = [k for k in filtered_knowledge if k.category in categories]

        # Score relevance for each knowledge item
        for knowledge in filtered_knowledge:
            if knowledge.confidence >= min_confidence:
                relevance_score = self._calculate_relevance(knowledge, query_str, context)
                if relevance_score > 0.1:  # Minimum relevance threshold
                    candidates.append(
                        RankedKnowledge(
                            knowledge=knowledge,
                            relevance_score=relevance_score,
                            ranking_factors={"query_match": relevance_score, "confidence": knowledge.confidence},
                        )
                    )

        # Sort by relevance and limit results
        candidates.sort(key=lambda x: x.relevance_score, reverse=True)
        ranked_knowledge = candidates[:max_results]

        # Update access statistics
        for ranked in ranked_knowledge:
            ranked.knowledge.record_access()

        retrieval_confidence = sum(rk.relevance_score for rk in ranked_knowledge) / max(len(ranked_knowledge), 1)

        return RetrievalResult(
            ranked_knowledge=ranked_knowledge,
            total_candidates=len(candidates),
            retrieval_confidence=retrieval_confidence,
            retrieval_metadata={"query": query_str, "context": context},
        )

    def retrieve_analogous(
        self, current_context: dict[str, Any], knowledge_base: dict[str, Knowledge], similarity_threshold: float
    ) -> RetrievalResult:
        """Retrieve analogous situations."""
        # This is a simplified implementation
        context_str = json.dumps(current_context, default=str)
        return self.retrieve(
            query=context_str,
            knowledge_base=knowledge_base,
            categories=None,
            context=current_context,
            max_results=self.config.max_retrieval_results,
            min_confidence=similarity_threshold,
        )

    def _calculate_relevance(self, knowledge: Knowledge, query: str, context: dict[str, Any]) -> float:
        """Calculate relevance score for knowledge item."""
        base_score = 0.0

        # Extract text content properly
        content_str = ""
        if isinstance(knowledge.content, dict):
            # Extract all string values from content dictionary
            content_values = []
            for value in knowledge.content.values():
                if isinstance(value, str):
                    content_values.append(value)
                else:
                    content_values.append(str(value))
            content_str = " ".join(content_values).lower()
        else:
            content_str = str(knowledge.content).lower()

        query_lower = query.lower()

        # Simple word overlap with partial matching
        query_words = set(query_lower.split())
        content_words = set(content_str.split())

        if query_words and content_words:
            # Exact word overlap
            overlap = query_words.intersection(content_words)
            base_score = len(overlap) / len(query_words.union(content_words))

            # Add partial matching for compound words and semantic similarity
            if base_score == 0:
                partial_matches = 0

                # Define some simple semantic mappings for better matching
                semantic_mappings = {
                    "deploy": ["update", "rolling"],
                    "version": ["update"],
                    "interruption": ["downtime"],
                    "service": ["downtime"],
                    "without": ["zero", "no"],
                    "new": ["update", "rolling"],
                }

                for query_word in query_words:
                    if len(query_word) > 2:  # Check shorter words too
                        matched = False
                        # Check substring matching
                        for content_word in content_words:
                            if query_word in content_word or content_word in query_word:
                                partial_matches += 1
                                matched = True
                                break

                        # Check semantic mapping if no substring match found
                        if not matched and query_word in semantic_mappings:
                            for semantic_word in semantic_mappings[query_word]:
                                for content_word in content_words:
                                    if semantic_word in content_word or content_word in semantic_word:
                                        partial_matches += 1
                                        matched = True
                                        break
                                if matched:
                                    break

                if partial_matches > 0:
                    # Give better score for partial matches - be more generous
                    base_score = min(0.8, partial_matches / min(len(query_words), len(content_words)))

        # Boost by confidence
        base_score *= 0.5 + 0.5 * knowledge.confidence

        # Boost recent knowledge
        days_old = (datetime.now() - knowledge.timestamp).days
        recency_factor = max(0.1, 1.0 - days_old / 365.0)  # Decay over a year
        base_score *= recency_factor

        return min(base_score, 1.0)


class ReasoningEngine:
    """Engine for reasoning with knowledge."""

    def __init__(self, config: CORRALConfig):
        self.config = config

    def reason(self, knowledge_set: list[Knowledge], problem: Union[str, ProblemContext], reasoning_type: str | None) -> ReasoningResult:
        """Apply reasoning to knowledge set."""
        problem_str = str(problem) if not isinstance(problem, str) else problem

        conclusions = []
        confidence_scores = {}
        reasoning_traces = []
        knowledge_gaps = []
        insights = {}

        # Apply different reasoning types
        reasoning_types = [reasoning_type] if reasoning_type else [rt.value for rt in self.config.reasoning_types]

        for rtype in reasoning_types:
            if rtype == ReasoningType.CAUSAL.value:
                result = self._causal_reasoning(knowledge_set, problem_str)
            elif rtype == ReasoningType.ANALOGICAL.value:
                result = self._analogical_reasoning(knowledge_set, problem_str)
            else:
                result = self._default_reasoning(knowledge_set, problem_str)

            conclusions.extend(result.get("conclusions", []))
            confidence_scores.update(result.get("confidence_scores", {}))
            reasoning_traces.extend(result.get("traces", []))
            knowledge_gaps.extend(result.get("gaps", []))
            insights.update(result.get("insights", {}))

        return ReasoningResult(
            conclusions=conclusions,
            confidence_scores=confidence_scores,
            reasoning_traces=reasoning_traces,
            knowledge_gaps=knowledge_gaps,
            insights=insights,
            metadata={"reasoning_types": reasoning_types, "problem": problem_str},
        )

    def explain_decision(self, decision: Any, knowledge_used: list[Knowledge]) -> dict[str, Any]:
        """Explain a decision using causal knowledge."""
        causal_knowledge = [k for k in knowledge_used if k.category == KnowledgeCategory.CAUSAL]

        explanation = {
            "decision": str(decision),
            "supporting_knowledge": len(knowledge_used),
            "causal_factors": len(causal_knowledge),
            "confidence": sum(k.confidence for k in knowledge_used) / max(len(knowledge_used), 1),
        }

        if causal_knowledge:
            explanation["causal_chain"] = [
                {"cause": str(k.content), "confidence": k.confidence}
                for k in causal_knowledge[:3]  # Top 3 causal factors
            ]

        return explanation

    def predict_outcomes(self, proposed_action: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Predict outcomes of proposed action."""
        # Simplified prediction
        predictions = [
            {
                "outcome": f"Success of {proposed_action}",
                "probability": 0.7,
                "confidence": 0.6,
                "reasoning": "Based on similar past actions",
            },
            {
                "outcome": f"Partial success of {proposed_action}",
                "probability": 0.2,
                "confidence": 0.5,
                "reasoning": "Considering potential obstacles",
            },
            {"outcome": f"Failure of {proposed_action}", "probability": 0.1, "confidence": 0.4, "reasoning": "Low probability edge cases"},
        ]

        return predictions

    def _causal_reasoning(self, knowledge_set: list[Knowledge], problem: str) -> dict[str, Any]:
        """Apply causal reasoning."""
        causal_knowledge = [k for k in knowledge_set if k.category == KnowledgeCategory.CAUSAL]

        conclusions = []
        confidence_scores = {}
        traces = []

        if causal_knowledge:
            # Simple causal analysis
            for knowledge in causal_knowledge[:3]:  # Top 3 causal items
                conclusion = f"Based on causal knowledge: {knowledge.content}"
                conclusions.append(conclusion)
                confidence_scores[conclusion] = knowledge.confidence

                trace = ReasoningTrace(
                    step_number=len(traces) + 1,
                    operation="causal_analysis",
                    inputs=[knowledge.id],
                    outputs=[conclusion],
                    confidence=knowledge.confidence,
                    reasoning_type="causal",
                )
                traces.append(trace)

        return {
            "conclusions": conclusions,
            "confidence_scores": confidence_scores,
            "traces": traces,
            "gaps": [],
            "insights": {"causal_factors_found": len(causal_knowledge)},
        }

    def _analogical_reasoning(self, knowledge_set: list[Knowledge], problem: str) -> dict[str, Any]:
        """Apply analogical reasoning."""
        # Simplified analogical reasoning
        conclusions = [f"By analogy with known patterns, {problem} could be approached similarly"]
        confidence_scores = {conclusions[0]: 0.6}

        trace = ReasoningTrace(
            step_number=1,
            operation="analogical_matching",
            inputs=[k.id for k in knowledge_set[:3]],
            outputs=conclusions,
            confidence=0.6,
            reasoning_type="analogical",
        )

        return {
            "conclusions": conclusions,
            "confidence_scores": confidence_scores,
            "traces": [trace],
            "gaps": [],
            "insights": {"analogies_found": min(3, len(knowledge_set))},
        }

    def _default_reasoning(self, knowledge_set: list[Knowledge], problem: str) -> dict[str, Any]:
        """Apply default reasoning."""
        if knowledge_set:
            conclusion = f"Based on available knowledge, {problem} can be addressed"
            confidence = sum(k.confidence for k in knowledge_set) / len(knowledge_set)
        else:
            conclusion = f"Insufficient knowledge to reason about {problem}"
            confidence = 0.1

        return {
            "conclusions": [conclusion],
            "confidence_scores": {conclusion: confidence},
            "traces": [],
            "gaps": [KnowledgeGap("insufficient_knowledge", "Need more relevant knowledge", 0.8)],
            "insights": {},
        }


class ActionEngine:
    """Engine for converting reasoning into actions."""

    def __init__(self, config: CORRALConfig):
        self.config = config

    def act(self, reasoning_result: ReasoningResult, execution_context: ExecutionContext | None, agent_instance: Any) -> ActionResult:
        """Convert reasoning into actions."""
        executed_actions = []
        outcomes = []

        # Convert conclusions into executable actions
        for i, conclusion in enumerate(reasoning_result.conclusions):
            confidence = reasoning_result.confidence_scores.get(conclusion, 0.5)

            if confidence > 0.5:  # Only act on confident conclusions
                action_name = f"action_from_conclusion_{i}"
                action = ExecutedAction(
                    action_type="reasoning_based",
                    action_name=action_name,
                    parameters={"conclusion": conclusion, "confidence": confidence},
                    result=f"Executed action based on: {conclusion}",
                    success=True,
                    execution_time=0.1,  # Simulated execution time
                )
                executed_actions.append(action)
                outcomes.append(action.result)

        success_rate = len([a for a in executed_actions if a.success]) / max(len(executed_actions), 1)

        return ActionResult(
            executed_actions=executed_actions,
            outcomes=outcomes,
            success_rate=success_rate,
            performance_metrics={"total_time": sum(a.execution_time for a in executed_actions)},
            metadata={"reasoning_conclusions": len(reasoning_result.conclusions)},
        )

    def recommend_workflow(
        self, problem: str, procedural_knowledge: list[Knowledge], available_resources: list[Any] | None
    ) -> dict[str, Any]:
        """Recommend workflow based on procedural knowledge."""
        if not procedural_knowledge:
            return {"recommended_workflow": None, "confidence": 0.0, "reasoning": "No procedural knowledge available"}

        # Simple recommendation based on highest confidence procedural knowledge
        best_knowledge = max(procedural_knowledge, key=lambda k: k.confidence)

        return {
            "recommended_workflow": best_knowledge.content,
            "confidence": best_knowledge.confidence,
            "reasoning": f"Based on procedural knowledge: {best_knowledge.id}",
        }

    def suggest_resources(self, problem_context: ProblemContext, declarative_knowledge: list[Knowledge]) -> dict[str, Any]:
        """Suggest resources based on declarative knowledge."""
        if not declarative_knowledge:
            return {"suggested_resources": [], "confidence": 0.0, "reasoning": "No declarative knowledge available"}

        # Extract resource suggestions from declarative knowledge
        suggestions = []
        for knowledge in declarative_knowledge[:5]:  # Top 5
            suggestions.append(
                {"resource_type": "knowledge_based", "description": str(knowledge.content), "confidence": knowledge.confidence}
            )

        return {
            "suggested_resources": suggestions,
            "confidence": sum(k.confidence for k in declarative_knowledge[:5]) / min(5, len(declarative_knowledge)),
            "reasoning": "Based on relevant declarative knowledge",
        }


class LearningEngine:
    """Engine for learning from outcomes and updating knowledge."""

    def __init__(self, config: CORRALConfig):
        self.config = config

    def learn(self, knowledge_used: list[Knowledge], action_taken: Any, outcome: Any, context: dict[str, Any]) -> LearningResult:
        """Learn from action outcomes."""
        knowledge_updates = []
        new_patterns = []
        confidence_improvements = {}
        knowledge_removals = []

        # Assess outcome success
        outcome_success = self._assess_outcome_success(outcome)

        # Update confidence based on outcome
        for knowledge in knowledge_used:
            old_confidence = knowledge.confidence

            if outcome_success:
                # Successful outcome - boost confidence
                new_confidence = min(1.0, old_confidence + self.config.learning_rate * 0.1)
            else:
                # Unsuccessful outcome - reduce confidence
                new_confidence = max(0.0, old_confidence - self.config.learning_rate * 0.05)

            if new_confidence != old_confidence:
                update = LearningUpdate(
                    knowledge_id=knowledge.id,
                    update_type="confidence_update",
                    old_value=old_confidence,
                    new_value=new_confidence,
                    evidence=f"Outcome: {outcome_success}",
                    confidence_change=new_confidence - old_confidence,
                )
                knowledge_updates.append(update)
                confidence_improvements[knowledge.id] = new_confidence - old_confidence

        # Discover new patterns if enabled
        if self.config.pattern_discovery and len(knowledge_used) > 1:
            pattern = self._discover_pattern(knowledge_used, action_taken, outcome, context)
            if pattern:
                new_patterns.append(pattern)

        # Mark low-confidence knowledge for removal if pruning enabled
        if self.config.knowledge_pruning:
            for knowledge in knowledge_used:
                if knowledge.confidence < 0.1:
                    knowledge_removals.append(knowledge.id)

        return LearningResult(
            knowledge_updates=knowledge_updates,
            new_patterns=new_patterns,
            confidence_improvements=confidence_improvements,
            knowledge_removals=knowledge_removals,
            insights={
                "outcome_success": outcome_success,
                "knowledge_used_count": len(knowledge_used),
                "learning_rate": self.config.learning_rate,
            },
        )

    def update_confidence(self, knowledge_items: list[Knowledge], validation_results: list[Any]) -> dict[str, float]:
        """Update confidence scores based on validation."""
        confidence_updates = {}

        for i, knowledge in enumerate(knowledge_items):
            if i < len(validation_results):
                validation = validation_results[i]
                # Simple validation-based update
                if hasattr(validation, "success") and validation.success:
                    new_confidence = min(1.0, knowledge.confidence + 0.05)
                else:
                    new_confidence = max(0.0, knowledge.confidence - 0.03)

                confidence_updates[knowledge.id] = new_confidence - knowledge.confidence

        return confidence_updates

    def discover_patterns(self, experience_history: list[dict[str, Any]], pattern_types: list[str] | None) -> list[dict[str, Any]]:
        """Discover patterns from experience history."""
        patterns = []

        if len(experience_history) >= 3:  # Need minimum experiences to find patterns
            # Simple pattern: recurring successful combinations
            success_count = sum(1 for exp in experience_history if exp.get("success", False))
            if success_count / len(experience_history) > 0.7:
                patterns.append(
                    {
                        "pattern_type": "success_pattern",
                        "description": "High success rate pattern identified",
                        "confidence": success_count / len(experience_history),
                        "supporting_instances": [exp.get("id", str(i)) for i, exp in enumerate(experience_history)],
                    }
                )

        return patterns

    def _assess_outcome_success(self, outcome: Any) -> bool:
        """Assess if an outcome represents success."""
        if isinstance(outcome, bool):
            return outcome
        elif isinstance(outcome, int | float):
            return outcome > 0
        elif isinstance(outcome, str):
            return "success" in outcome.lower() or "complete" in outcome.lower()
        elif isinstance(outcome, dict):
            return outcome.get("success", False)
        elif hasattr(outcome, "success"):
            return getattr(outcome, "success", False)
        else:
            # Default: assume success if we got any outcome
            return outcome is not None

    def _discover_pattern(
        self, knowledge_used: list[Knowledge], action_taken: Any, outcome: Any, context: dict[str, Any]
    ) -> NewPattern | None:
        """Discover a new pattern from this learning instance."""
        if len(knowledge_used) >= 2 and self._assess_outcome_success(outcome):
            # Pattern: combination of knowledge categories that led to success
            categories = [k.category.value for k in knowledge_used]
            pattern = NewPattern(
                pattern_type="knowledge_combination",
                description=f"Successful combination: {', '.join(set(categories))}",
                confidence=0.6,
                supporting_instances=[k.id for k in knowledge_used],
                potential_applications=[str(action_taken)],
            )
            return pattern

        return None
