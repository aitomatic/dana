"""
Expert Interview Workflow

Conducts structured expert interviews with parallel analysis:
- Topic extraction
- Expert insight analysis
- Knowledge gap detection (if reference materials provided)
- Next question generation

Built on Dana's conversation and analysis resources.
"""

import asyncio

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input
from dana.lib.resources.conversation import ConversationResource

from ..resources import ExpertInsightAnalyzer, KnowledgeGapDetector


class ExpertInterviewWorkflow(BaseWorkflow):
    """
    Conduct structured expert interview with parallel analysis.

    This workflow orchestrates the interview process by:
    1. Extracting topics from expert statements
    2. Analyzing expert insights with quote preservation
    3. Detecting knowledge gaps (if reference materials provided)
    4. Generating contextual follow-up questions

    USE FOR:
    - Technical expert interviews
    - Knowledge capture sessions
    - Professional consultations
    - Subject matter expert (SME) documentation
    - Process knowledge extraction

    EXAMPLES:
    - "Interview an engineer about their crystallization process"
    - "Capture knowledge from a senior developer"
    - "Document expert practices for training materials"
    """

    def __init__(
        self, reference_materials: list[str] | None = None, expert_profile: dict | None = None, workflow_id: str | None = None, **kwargs
    ):
        """
        Initialize ExpertInterviewWorkflow.

        Args:
            reference_materials: Optional reference documents/knowledge base
            expert_profile: Optional expert profile (name, role, experience)
            workflow_id: Workflow identifier
            **kwargs: Additional arguments
        """
        super().__init__(workflow_id=workflow_id or "expert-interview", **kwargs)

        # Initialize resources
        self.conversation = ConversationResource()
        self.insight_analyzer = ExpertInsightAnalyzer()
        self.gap_detector = KnowledgeGapDetector()

        # Store configuration
        self.reference_materials = reference_materials or []
        self.expert_profile = expert_profile or {}

    @validate_input(
        expert_message={"required": True, "type": str, "min_length": 1},
        conversation_history={"type": list, "default": []},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Process expert message through parallel analysis pipeline.

        Args:
            **kwargs: Input parameters containing:
                expert_message (str): The expert's current message (required)
                conversation_history (list): Previous conversation (optional)

        Returns:
            DictParams: Dictionary with:
                - topics: Extracted topics with terminology
                - insights: Expert insights with original quotes
                - gaps: Knowledge gaps (if reference materials provided)
                - next_question: Suggested follow-up question
                - instant_context: Current interview context snapshot
                - processing_time: Total time taken
        """
        import time

        start_time = time.time()

        expert_message = kwargs["expert_message"]
        conversation_history = kwargs.get("conversation_history", [])

        # PHASE 1: Parallel information gathering
        async def phase1():
            """Extract topics and insights in parallel"""
            topic_task = asyncio.create_task(
                self.conversation._extract_topics(
                    message=expert_message, conversation_history=conversation_history, preserve_terminology=True
                )
            )

            insight_task = asyncio.create_task(
                self.insight_analyzer._analyze_insights(
                    message=expert_message, conversation_history=conversation_history, expert_profile=self.expert_profile
                )
            )

            return await asyncio.gather(topic_task, insight_task)

        topics, insights = asyncio.run(phase1())

        # PHASE 2: Gap detection and next question generation
        gaps = {}
        if self.reference_materials:
            # Only detect gaps if we have reference materials
            gaps = self.gap_detector.detect_gaps(
                source1_content=insights.get("expert_insights_original", []),
                source2_content=self.reference_materials,
                source1_label="Expert Knowledge",
                source2_label="Reference Materials",
                topic_context=topics,
            )

        # Generate next question based on analysis
        next_question = self._generate_next_question(topics, insights, gaps, conversation_history)

        # Build instant context snapshot
        instant_context = {
            "current_focus": topics.get("current_focus", "Unknown"),
            "active_topics": topics.get("active_topics", []),
            "expert_insights": [insight.get("original_quote", "") for insight in insights.get("expert_insights_original", [])],
            "terminology": topics.get("terminology", []),
            "gaps_identified": len(gaps.get("gaps", [])),
            "conversation_depth": len(conversation_history),
        }

        return {
            "topics": topics,
            "insights": insights,
            "gaps": gaps,
            "next_question": next_question,
            "instant_context": instant_context,
            "processing_time": time.time() - start_time,
        }

    def _generate_next_question(self, topics: dict, insights: dict, gaps: dict, conversation_history: list) -> str:
        """
        Generate contextual follow-up question.

        Simple rule-based generation for now. Could be replaced with LLM.
        """
        # Priority 1: Ask about identified gaps
        if gaps and gaps.get("gaps"):
            first_gap = gaps["gaps"][0]
            return f"You mentioned {first_gap.get('source1_quote', '...')}. Can you elaborate on that?"

        # Priority 2: Dig deeper into current focus
        if topics.get("current_focus"):
            focus = topics["current_focus"]
            return f"Can you tell me more about {focus}?"

        # Priority 3: Explore terminology
        if topics.get("terminology"):
            term = topics["terminology"][0]
            return f"You mentioned '{term}'. What's the significance of that?"

        # Default: Open-ended
        return "What else is important about this topic?"
