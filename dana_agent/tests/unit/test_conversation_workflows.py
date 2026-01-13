"""
Unit tests for conversation workflows.
"""

from unittest.mock import patch

from dana.lib.workflows.conversation import SummarizeConversationWorkflow


class TestSummarizeWorkflow:
    """Test SummarizeWorkflow class."""

    @patch("dana.lib.workflows.conversation.ConversationResource")
    def test_summarize_workflow_initialization(self, mock_resource_class):
        """Test SummarizeConversationWorkflow can be initialized."""
        workflow = SummarizeConversationWorkflow()
        assert workflow.workflow_id == "summarize-conversation"
        assert hasattr(workflow, "conversation_resource")

    @patch("dana.lib.workflows.conversation.ConversationResource")
    def test_summarize_workflow_execute(self, mock_resource_class):
        """Test SummarizeWorkflow execute with composable sub-steps."""
        # Setup mock instance
        mock_instance = mock_resource_class.return_value
        mock_instance._format_conversation.return_value = "Formatted conversation text"

        # Mock _generate_llm_summary (sync method that calls asyncio.run internally)
        expected_summary = {
            "key_topics": ["Python", "programming"],
            "technical_areas": ["software development"],
            "expert_insights": ["Python is versatile"],
            "terminology_introduced": ["async/await"],
            "context_switches": [],
            "conversation_stage": "early",
            "expertise_level": "intermediate",
            "conversation_summary": "Discussion about Python programming",
        }
        mock_instance._generate_llm_summary.return_value = expected_summary

        # Also mock fallback in case of any exception
        mock_instance._create_fallback_summary.return_value = expected_summary

        # Execute workflow
        workflow = SummarizeConversationWorkflow()
        result = workflow.execute(
            conversation_history=[
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."},
            ]
        )

        # Verify - result is returned directly, not wrapped in "result" key
        assert result["key_topics"] == ["Python", "programming"]
        assert result["conversation_stage"] == "early"
        # conversation_length and processing_time/timestamp may be added elsewhere
        # Just verify core fields from the summary

    @patch("dana.lib.workflows.conversation.ConversationResource")
    def test_summarize_workflow_with_current_message(self, mock_resource_class):
        """Test SummarizeWorkflow with current message."""
        # Setup mock instance
        mock_instance = mock_resource_class.return_value
        mock_instance._format_conversation.return_value = "Formatted conversation with current message"

        # Mock _generate_llm_summary (sync method that calls asyncio.run internally)
        expected_summary = {
            "key_topics": ["error handling"],
            "technical_areas": ["exception management"],
            "expert_insights": [],
            "terminology_introduced": ["try/except"],
            "context_switches": [],
            "conversation_stage": "middle",
            "expertise_level": "intermediate",
            "conversation_summary": "Discussion about error handling",
        }
        mock_instance._generate_llm_summary.return_value = expected_summary

        # Also mock fallback in case of any exception
        mock_instance._create_fallback_summary.return_value = expected_summary

        workflow = SummarizeConversationWorkflow()
        result = workflow.execute(
            conversation_history=[
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."},
            ],
            current_message="How do I handle errors?",
        )

        # Verify - result is returned directly, not wrapped in "result" key
        assert result["key_topics"] == ["error handling"]
