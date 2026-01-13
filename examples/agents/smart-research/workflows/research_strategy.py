"""Research strategy selection workflow for SmartResearchAgent."""

import time

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.lib.resources.conversation import ConversationResource


class ResearchStrategyWorkflow(BaseWorkflow):
    """
    Analyzes user query and selects optimal research strategy.

    Strategies:
    - QUICK_FACT: Simple factual lookup
    - TECHNICAL_DEEP_DIVE: Deep technical research
    - CURRENT_EVENTS: Recent news and developments
    - COMPARATIVE_ANALYSIS: Compare multiple options
    """

    STRATEGIES = {
        "QUICK_FACT": {
            "description": "Simple factual lookup",
            "sources": ["google_search"],
            "depth": "shallow",
            "max_sources": 3,
            "time_estimate": "2-5s",
            "indicators": ["what is", "who is", "when was", "define", "meaning of"],
        },
        "TECHNICAL_DEEP_DIVE": {
            "description": "Deep technical research",
            "sources": ["academic", "documentation", "technical_blogs"],
            "depth": "deep",
            "max_sources": 20,
            "time_estimate": "15-25s",
            "indicators": ["explain", "how does", "architecture", "implementation", "detail"],
        },
        "CURRENT_EVENTS": {
            "description": "Recent news and developments",
            "sources": ["news", "blogs", "announcements"],
            "depth": "medium",
            "max_sources": 15,
            "time_estimate": "8-15s",
            "indicators": ["latest", "recent", "news", "2024", "2025", "update"],
        },
        "COMPARATIVE_ANALYSIS": {
            "description": "Compare multiple options",
            "sources": ["reviews", "benchmarks", "documentation"],
            "depth": "deep",
            "max_sources": 20,
            "time_estimate": "20-35s",
            "indicators": ["compare", "vs", "versus", "difference", "better"],
        },
    }

    def __init__(self, workflow_id: str | None = None, llm_provider: str = "anthropic", model: str | None = None, **kwargs):
        super().__init__(workflow_id=workflow_id or "research-strategy", **kwargs)
        self.conversation = ConversationResource(llm_provider=llm_provider, model=model or "claude-3-5-sonnet-20241022")

    @validate_input(
        query={"required": True, "type": str, "min_length": 1},
    )
    @validate_output(
        success={"required": True, "type": bool},
        strategy={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Analyze query and select research strategy.

        Args:
            query: User's research question

        Returns:
            {
                "success": True,
                "strategy": {strategy_config},
                "reasoning": str,
                "classification": {...}
            }
        """
        query = kwargs["query"]
        start_time = time.time()

        # Broadcast: Starting strategy selection
        self.broadcast(
            {
                "workflow_progress": {
                    "workflow_id": self.workflow_id,
                    "phase": "start",
                    "message": "Analyzing query to select research strategy...",
                }
            }
        )

        try:
            # Step 1: Classify query using simple keyword matching first (fast path)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "classify",
                        "message": "Classifying query type with keyword matching...",
                    }
                }
            )

            query_lower = query.lower()
            keyword_match = None

            for strategy_name, config in self.STRATEGIES.items():
                for indicator in config["indicators"]:
                    if indicator in query_lower:
                        keyword_match = strategy_name
                        break
                if keyword_match:
                    break

            # Step 2: If clear keyword match, use it
            if keyword_match:
                strategy_type = keyword_match
                reasoning = f"Matched keywords for {strategy_type}"
                confidence = 0.85

            else:
                # Step 3: Fall back to LLM-based classification
                self.broadcast(
                    {
                        "workflow_progress": {
                            "workflow_id": self.workflow_id,
                            "phase": "llm_classify",
                            "message": "No keyword match - using LLM for classification...",
                        }
                    }
                )

                classification = self._classify_with_llm(query)
                strategy_type = classification.get("strategy_type", "TECHNICAL_DEEP_DIVE")
                reasoning = classification.get("reasoning", "LLM-based classification")
                confidence = classification.get("confidence", 0.7)

            # Get strategy configuration
            strategy = self.STRATEGIES.get(strategy_type, self.STRATEGIES["TECHNICAL_DEEP_DIVE"])

            # Broadcast: Strategy selected
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "complete",
                        "message": f"Selected {strategy_type} strategy (confidence: {confidence:.2f})",
                    }
                }
            )

            processing_time = time.time() - start_time

            return {
                "success": True,
                "strategy": {"type": strategy_type, **strategy},
                "reasoning": reasoning,
                "confidence": confidence,
                "classification": {"query": query, "matched_type": strategy_type, "processing_time": round(processing_time, 3)},
                "timestamp": time.time(),
            }

        except Exception as e:
            # Graceful fallback
            return {
                "success": True,  # Don't fail, just use default
                "strategy": {"type": "TECHNICAL_DEEP_DIVE", **self.STRATEGIES["TECHNICAL_DEEP_DIVE"]},
                "reasoning": f"Defaulted to TECHNICAL_DEEP_DIVE due to error: {str(e)}",
                "confidence": 0.5,
                "classification": {"query": query, "matched_type": "TECHNICAL_DEEP_DIVE", "error": str(e)},
            }

    def _classify_with_llm(self, query: str) -> DictParams:
        """
        Use LLM to classify query when keyword matching is insufficient.

        Returns:
            {
                "strategy_type": str,
                "reasoning": str,
                "confidence": float
            }
        """
        try:
            # Use ConversationResource for intent detection
            result = self.conversation.detect_intent(
                message=query,
                conversation_history=[],
                intent_types=["quick_fact", "technical_deep_dive", "current_events", "comparative_analysis"],
            )

            # Map intent to strategy type
            intent_map = {
                "quick_fact": "QUICK_FACT",
                "technical_deep_dive": "TECHNICAL_DEEP_DIVE",
                "current_events": "CURRENT_EVENTS",
                "comparative_analysis": "COMPARATIVE_ANALYSIS",
                "question": "TECHNICAL_DEEP_DIVE",  # Default
            }

            intent = result.get("intent", "question")
            strategy_type = intent_map.get(intent, "TECHNICAL_DEEP_DIVE")

            return {"strategy_type": strategy_type, "reasoning": f"LLM classified as {intent}", "confidence": 0.75}

        except Exception as e:
            # Fallback to default
            return {"strategy_type": "TECHNICAL_DEEP_DIVE", "reasoning": f"LLM classification failed: {str(e)}", "confidence": 0.5}
