"""
Unit tests for conversation workflows.
"""

import pytest
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

    @pytest.mark.live
    def test_summarize_workflow_execute(self):
        """Test SummarizeWorkflow execute with composable sub-steps.
        
        This test requires LLM API access and is marked as live.
        Run with: pytest tests/unit/test_conversation_workflows.py --live
        """
        workflow = SummarizeConversationWorkflow()
        
        # Execute workflow with real LLM (requires API key)
        result = workflow.execute(
            conversation_history=[
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."},
            ]
        )

        # Verify structure
        assert "key_topics" in result or "result" in result
        assert "conversation_length" in result
        assert "processing_time" in result or "timestamp" in result

    @pytest.mark.live
    def test_summarize_workflow_with_current_message(self):
        """Test SummarizeWorkflow with current message.
        
        This test requires LLM API access and is marked as live.
        Run with: pytest tests/unit/test_conversation_workflows.py --live
        """
        workflow = SummarizeConversationWorkflow()
        
        result = workflow.execute(
            conversation_history=[
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."},
            ],
            current_message="How do I handle errors?",
        )

        # Verify structure
        assert "key_topics" in result or "result" in result
