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

from dana.common.llm.llm import LLM, LLMMessage
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
        self.llm = LLM(provider="anthropic")

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
        Generate contextual follow-up question using LLM for natural conversation flow.

        Analyzes conversation context to:
        - Detect if expert wants to end conversation
        - Generate varied, natural questions
        - Avoid repetition
        - Follow up on interesting points
        """
        # Get last expert message
        last_message = conversation_history[-1]["content"] if conversation_history else ""

        # Build context for LLM
        recent_history = ""
        if len(conversation_history) > 1:
            # Show last 3 exchanges
            for msg in conversation_history[-6:]:
                role = "Expert" if msg.get("role") == "user" else "Interviewer"
                recent_history += f"{role}: {msg.get('content', '')[:200]}\n"

        # Format gaps if present
        gaps_text = ""
        if gaps and gaps.get("gaps"):
            gaps_text = "\nKnowledge gaps identified:\n"
            for gap in gaps["gaps"][:2]:
                gaps_text += f"- {gap.get('description', '')}[:100]\n"

        # Format insights
        insights_text = ""
        if insights.get("expert_insights_original"):
            insights_text = "\nKey insights from last response:\n"
            for insight in insights["expert_insights_original"][:2]:
                insights_text += f"- {insight.get('original_quote', '')[:100]}\n"

        prompt = f"""You are an expert interviewer conducting a professional knowledge capture interview.

RECENT CONVERSATION:
{recent_history if recent_history else "This is the first exchange."}

EXPERT'S LAST MESSAGE: "{last_message}"

CURRENT TOPIC: {topics.get('current_focus', 'Unknown')}
{insights_text}
{gaps_text}

TASK: Generate the next interviewer question. Consider:
1. Is the expert signaling they want to end? (e.g., "that's enough", "quit", "I'm done")
2. Did they just answer your question? Don't repeat it!
3. Are there interesting details to explore?
4. Vary your question style - don't always ask "tell me more about X"

RULES:
- If expert wants to end or is frustrated, output: END_INTERVIEW
- If they gave a short/dismissive answer to your last question, try a different angle or topic
- Be conversational and natural
- Don't ask about the same thing twice in a row
- Ask open-ended questions that encourage detailed responses

OUTPUT: Just the next question (or "END_INTERVIEW" if conversation should end). No explanation."""

        try:
            response = asyncio.run(
                self.llm.chat_response(
                    messages=[LLMMessage(role="user", content=prompt)],
                    system_message="You are a skilled professional interviewer. Generate natural, context-aware questions.",
                    max_tokens=150,
                    temperature=0.7,
                )
            )

            question = response.content if hasattr(response, "content") else str(response)
            question = question.strip().strip("\"'")

            # Check if interview should end
            if "END_INTERVIEW" in question:
                return "Thank you for sharing your expertise. Is there anything else you'd like to add before we wrap up?"

            return question

        except Exception:
            # Fallback to simple question if LLM fails
            if topics.get("current_focus"):
                return f"Could you elaborate on {topics['current_focus']}?"
            return "What else would you like to share?"
