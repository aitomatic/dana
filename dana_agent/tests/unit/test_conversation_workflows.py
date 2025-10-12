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

        # Mock sync method (_generate_llm_summary is sync, calls asyncio.run internally)
        def mock_generate_summary(*args, **kwargs):
            return {
                "key_topics": ["Python", "programming"],
                "technical_areas": ["software development"],
                "expert_insights": ["Python is versatile"],
                "terminology_introduced": ["async/await"],
                "context_switches": [],
                "conversation_stage": "early",
                "expertise_level": "intermediate",
                "conversation_summary": "Discussion about Python programming",
            }

        mock_instance._generate_llm_summary = mock_generate_summary

        # Execute workflow
        workflow = SummarizeConversationWorkflow()
        result = workflow.execute(
            conversation_history=[
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."},
            ]
        )

        # Verify
        assert "result" in result
        assert result["result"]["key_topics"] == ["Python", "programming"]
        assert result["result"]["conversation_stage"] == "early"
        assert result["result"]["conversation_length"] == 2
        assert "processing_time" in result["result"]
        assert "timestamp" in result["result"]

    @patch("dana.lib.workflows.conversation.ConversationResource")
    def test_summarize_workflow_with_current_message(self, mock_resource_class):
        """Test SummarizeWorkflow with current message."""
        # Setup mock instance
        mock_instance = mock_resource_class.return_value
        mock_instance._format_conversation.return_value = "Formatted conversation with current message"

        # Mock sync method (_generate_llm_summary is sync, calls asyncio.run internally)
        def mock_generate_summary(*args, **kwargs):
            return {
                "key_topics": ["error handling"],
                "technical_areas": ["exception management"],
                "expert_insights": [],
                "terminology_introduced": ["try/except"],
                "context_switches": [],
                "conversation_stage": "middle",
                "expertise_level": "intermediate",
                "conversation_summary": "Discussion about error handling",
            }

        mock_instance._generate_llm_summary = mock_generate_summary

        workflow = SummarizeConversationWorkflow()
        result = workflow.execute(
            conversation_history=[
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."},
            ],
            current_message="How do I handle errors?",
        )

        assert "result" in result
        assert result["result"]["key_topics"] == ["error handling"]
