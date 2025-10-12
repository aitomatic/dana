"""
Conversation analysis workflows.

This module provides workflows for conversation analysis including:
- SummarizeWorkflow: Generate structured conversation summaries
"""

import time

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.callable_workflow import CallableWorkflow
from dana.lib.resources.conversation import ConversationResource


class SummarizeConversationWorkflow(BaseWorkflow):
    """
    Generate structured conversation summary.

    Analyzes conversation history to extract key topics, insights, terminology,
    and assess conversation stage and expertise level.

    USE FOR:
    - Conversation state tracking
    - Context-aware dialogue systems
    - Session summaries for review
    - Knowledge extraction from discussions

    EXAMPLES:
    - "Summarize the conversation so far"
    - "What have we been discussing?"
    - "Extract key topics from this session"
    """

    def __init__(self, workflow_id: str | None = None, **kwargs):
        """
        Initialize SummarizeConversationWorkflow.

        Args:
            workflow_id: Workflow identifier (default: "summarize-conversation")
            **kwargs: Additional arguments passed to BaseWorkflow
        """
        super().__init__(workflow_id=workflow_id or "summarize-conversation", **kwargs)
        self.conversation_resource = ConversationResource()

    def _do_execute(self, **kwargs) -> DictParams:
        """
        Generate structured conversation summary.

        Composed of sub-steps:
        1. Check conversation length (fast path for short conversations)
        2. Format conversation history into text
        3. Generate LLM analysis
        4. Add metadata (length, timestamps)

        Args:
            **kwargs: Input parameters containing:
                conversation_history (list[dict]): List of {"role": str, "content": str} messages (required)
                current_message (str, optional): Current user message to include

        Returns:
            DictParams: Dictionary with:
                - key_topics: List of main topics
                - technical_areas: Technical domains discussed
                - expert_insights: Key insights shared
                - terminology_introduced: New terms
                - context_switches: Topic changes
                - conversation_stage: early|middle|advanced
                - expertise_level: beginner|intermediate|expert
                - conversation_summary: Brief overview
                - conversation_length: Number of messages
                - processing_time: Time taken
                - timestamp: When generated

        Example:
            >>> workflow = SummarizeConversationWorkflow()
            >>> result = workflow.execute(conversation_history=[
            ...     {"role": "user", "content": "What is Python?"},
            ...     {"role": "assistant", "content": "Python is a programming language..."}
            ... ])
            >>> print(result["result"]["key_topics"])
            ['Python programming', 'programming languages']
        """

        conversation_history = kwargs.get("conversation_history", [])
        current_message = kwargs.get("current_message")
        start_time = time.time()

        # Fast path for minimal conversations
        if len(conversation_history) < 2:
            return self.conversation_resource._create_minimal_summary(conversation_history, current_message)

        def add_metadata(
            key_topics,
            technical_areas,
            expert_insights,
            terminology_introduced,
            context_switches,
            conversation_stage,
            expertise_level,
            conversation_summary,
        ):
            """Add metadata to the summary result."""
            return {
                "key_topics": key_topics,
                "technical_areas": technical_areas,
                "expert_insights": expert_insights,
                "terminology_introduced": terminology_introduced,
                "context_switches": context_switches,
                "conversation_stage": conversation_stage,
                "expertise_level": expertise_level,
                "conversation_summary": conversation_summary,
                "conversation_length": len(conversation_history),
                "processing_time": time.time() - start_time,
                "timestamp": time.time(),
            }

        try:
            # Compose the workflow pipeline using CallableWorkflow
            workflow = (
                CallableWorkflow(
                    self.conversation_resource._format_conversation,
                    "conversation_history=conversation_history, current_message=current_message -> conversation_text",
                )
                | CallableWorkflow(self.conversation_resource._generate_llm_summary, "conversation_text=conversation_text")
                | CallableWorkflow(
                    add_metadata,
                    # Simple keys auto-resolve from result first (new parameter resolution!)
                    "key_topics=key_topics, "
                    "technical_areas=technical_areas, "
                    "expert_insights=expert_insights, "
                    "terminology_introduced=terminology_introduced, "
                    "context_switches=context_switches, "
                    "conversation_stage=conversation_stage, "
                    "expertise_level=expertise_level, "
                    "conversation_summary=conversation_summary",
                )
            )

            result = workflow.execute(**kwargs)
            return result["result"]

        except Exception as e:
            return self.conversation_resource._create_fallback_summary(conversation_history, current_message, str(e))
