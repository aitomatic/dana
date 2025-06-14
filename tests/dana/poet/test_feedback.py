"""
Tests for POET Feedback System
"""

import pytest
import tempfile
import json
from unittest.mock import Mock, patch
from pathlib import Path

from opendxa.dana.poet.feedback import AlphaFeedbackSystem, BasicAlphaTrainer
from opendxa.dana.poet.types import POETResult


class TestAlphaFeedbackSystem:
    """Test Alpha Feedback System functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.feedback_system = AlphaFeedbackSystem(storage_path=self.temp_dir)

    def test_feedback_system_initialization(self):
        """Test feedback system initializes correctly"""
        assert self.feedback_system.storage_path.exists()
        assert (self.feedback_system.storage_path / "executions").exists()
        assert (self.feedback_system.storage_path / "feedback").exists()
        assert isinstance(self.feedback_system.executions, dict)
        assert isinstance(self.feedback_system.feedback_data, dict)
        assert isinstance(self.feedback_system.trainers, dict)

    def test_store_execution_context(self):
        """Test storing execution context"""
        result = POETResult({"value": 42}, "test_func", "v1")

        self.feedback_system._store_execution_context(result)

        execution_id = result._poet["execution_id"]
        assert execution_id in self.feedback_system.executions

        stored_data = self.feedback_system.executions[execution_id]
        assert stored_data["function_name"] == "test_func"
        assert stored_data["version"] == "v1"
        assert "timestamp" in stored_data

        # Check file persistence
        execution_file = self.feedback_system.storage_path / "executions" / f"{execution_id}.json"
        assert execution_file.exists()

        with open(execution_file) as f:
            file_data = json.load(f)
        assert file_data["function_name"] == "test_func"

    def test_summarize_result(self):
        """Test result summarization for different types"""
        # Test dict
        dict_summary = self.feedback_system._summarize_result({"key": "value", "num": 42})
        assert "dict with keys:" in dict_summary
        assert "key" in dict_summary and "num" in dict_summary

        # Test list
        list_summary = self.feedback_system._summarize_result([1, 2, 3, 4, 5])
        assert "list with 5 items" in list_summary

        # Test string
        string_summary = self.feedback_system._summarize_result("hello world")
        assert "string: hello world" in string_summary

        # Test long string
        long_string = "a" * 150
        long_summary = self.feedback_system._summarize_result(long_string)
        assert "..." in long_summary

        # Test number
        num_summary = self.feedback_system._summarize_result(42.5)
        assert "float: 42.5" in num_summary

    @patch("opendxa.dana.poet.feedback.LLMResource")
    def test_translate_feedback_with_llm_success(self, mock_llm_class):
        """Test LLM feedback translation success"""
        mock_llm = Mock()
        mock_llm.query.return_value = '{"sentiment": "positive", "feedback_type": "performance", "confidence": 0.8}'
        mock_llm_class.return_value = mock_llm

        result = POETResult({"value": 42}, "test_func")
        feedback_payload = "Great job!"

        processed = self.feedback_system._process_feedback(feedback_payload, result)

        assert processed["sentiment"] == "positive"
        assert processed["feedback_type"] == "performance"
        assert processed["confidence"] == 0.8
        assert processed["raw_feedback"] == "Great job!"
        assert processed["processing_method"] == "llm"

    @patch("opendxa.dana.poet.feedback.LLMResource")
    def test_translate_feedback_with_llm_failure(self, mock_llm_class):
        """Test LLM feedback translation with fallback"""
        mock_llm = Mock()
        mock_llm.query.side_effect = Exception("LLM error")
        mock_llm_class.return_value = mock_llm

        result = POETResult({"value": 42}, "test_func")
        feedback_payload = "This is bad and wrong"

        processed = self.feedback_system._process_feedback(feedback_payload, result)

        assert processed["sentiment"] == "negative"  # Basic processing detected negative words
        assert processed["processing_method"] == "basic"
        assert processed["confidence"] == 0.6  # Lower confidence for basic processing

    def test_basic_feedback_processing(self):
        """Test basic feedback processing fallback"""
        # Positive feedback
        positive_feedback = self.feedback_system._basic_feedback_processing("This is great and excellent!")
        assert positive_feedback["sentiment"] == "positive"

        # Negative feedback
        negative_feedback = self.feedback_system._basic_feedback_processing("This is bad and terrible!")
        assert negative_feedback["sentiment"] == "negative"

        # Neutral feedback
        neutral_feedback = self.feedback_system._basic_feedback_processing("This is okay")
        assert neutral_feedback["sentiment"] == "neutral"

    def test_store_feedback(self):
        """Test feedback storage"""
        execution_id = "test-execution-123"
        processed_feedback = {"sentiment": "positive", "feedback_type": "accuracy", "confidence": 0.9}

        self.feedback_system._store_feedback(execution_id, processed_feedback)

        # Check in-memory storage
        assert execution_id in self.feedback_system.feedback_data
        feedback_list = self.feedback_system.feedback_data[execution_id]
        assert len(feedback_list) == 1

        stored_feedback = feedback_list[0]
        assert stored_feedback["sentiment"] == "positive"
        assert stored_feedback["execution_id"] == execution_id
        assert "feedback_id" in stored_feedback
        assert "timestamp" in stored_feedback

        # Check file persistence
        feedback_file = self.feedback_system.storage_path / "feedback" / f"{execution_id}_feedback.json"
        assert feedback_file.exists()

        with open(feedback_file) as f:
            file_data = json.load(f)
        assert len(file_data) == 1
        assert file_data[0]["sentiment"] == "positive"

    def test_get_trainer_creates_basic_trainer(self):
        """Test trainer creation for functions with optimize_for"""
        trainer = self.feedback_system._get_trainer("test_func", "v1")

        assert isinstance(trainer, BasicAlphaTrainer)
        assert trainer.function_name == "test_func"
        assert trainer.version == "v1"

        # Should cache the trainer
        trainer2 = self.feedback_system._get_trainer("test_func", "v1")
        assert trainer is trainer2

    @patch("opendxa.dana.poet.feedback.LLMResource")
    def test_feedback_end_to_end(self, mock_llm_class):
        """Test complete feedback processing flow"""
        mock_llm = Mock()
        mock_llm.query.return_value = '{"sentiment": "negative", "feedback_type": "accuracy", "confidence": 0.9, "key_issues": ["threshold too low"], "suggestions": ["increase threshold"], "learning_priority": "high", "business_impact": "medium"}'
        mock_llm_class.return_value = mock_llm

        result = POETResult({"prediction": 0.8}, "classifier", "v1")
        feedback_text = "The prediction was wrong, threshold seems too low"

        self.feedback_system.feedback(result, feedback_text)

        execution_id = result._poet["execution_id"]

        # Check execution was stored
        assert execution_id in self.feedback_system.executions

        # Check feedback was processed and stored
        assert execution_id in self.feedback_system.feedback_data
        feedback_list = self.feedback_system.feedback_data[execution_id]
        assert len(feedback_list) == 1

        processed = feedback_list[0]
        assert processed["sentiment"] == "negative"
        assert processed["feedback_type"] == "accuracy"
        assert processed["key_issues"] == ["threshold too low"]
        assert processed["raw_feedback"] == feedback_text

    def test_get_feedback_summary(self):
        """Test feedback summary generation"""
        # Setup some test data
        function_name = "test_classifier"

        # Create executions and feedback
        for i in range(3):
            execution_id = f"exec-{i}"
            self.feedback_system.executions[execution_id] = {"execution_id": execution_id, "function_name": function_name, "version": "v1"}

            sentiment = ["positive", "negative", "neutral"][i]
            feedback_type = ["accuracy", "performance", "usability"][i]

            self.feedback_system.feedback_data[execution_id] = [
                {"sentiment": sentiment, "feedback_type": feedback_type, "timestamp": "2025-06-14T10:00:00Z"}
            ]

        summary = self.feedback_system.get_feedback_summary(function_name)

        assert summary["function_name"] == function_name
        assert summary["total_feedback"] == 3
        assert summary["sentiment_distribution"]["positive"] == 1
        assert summary["sentiment_distribution"]["negative"] == 1
        assert summary["sentiment_distribution"]["neutral"] == 1
        assert summary["feedback_type_distribution"]["accuracy"] == 1
        assert len(summary["recent_feedback"]) == 3


class TestBasicAlphaTrainer:
    """Test Basic Alpha Trainer functionality"""

    def test_trainer_initialization(self):
        """Test trainer initializes correctly"""
        trainer = BasicAlphaTrainer("test_func", "v1")

        assert trainer.function_name == "test_func"
        assert trainer.version == "v1"
        assert trainer.learning_state["feedback_count"] == 0
        assert trainer.learning_state["patterns"] == []
        assert trainer.learning_state["improvement_suggestions"] == []

    def test_trainer_processes_feedback(self):
        """Test trainer processes feedback and updates state"""
        trainer = BasicAlphaTrainer("test_func", "v1")

        processed_feedback = {
            "sentiment": "negative",
            "learning_priority": "high",
            "key_issues": ["threshold too sensitive"],
            "suggestions": ["increase threshold to 0.8"],
            "processed_timestamp": "2025-06-14T10:00:00Z",
        }

        trainer.train("exec-123", processed_feedback)

        assert trainer.learning_state["feedback_count"] == 1
        assert len(trainer.learning_state["patterns"]) == 1
        assert trainer.learning_state["improvement_suggestions"] == ["increase threshold to 0.8"]

        pattern = trainer.learning_state["patterns"][0]
        assert pattern["type"] == "high_priority_negative_feedback"
        assert pattern["execution_id"] == "exec-123"
        assert pattern["issues"] == ["threshold too sensitive"]

    def test_trainer_learning_milestones(self):
        """Test trainer logging at learning milestones"""
        trainer = BasicAlphaTrainer("test_func", "v1")

        # Process 5 feedback items to trigger milestone
        for i in range(5):
            feedback = {
                "sentiment": "positive" if i % 2 == 0 else "negative",
                "learning_priority": "medium",
                "key_issues": [],
                "suggestions": [],
            }
            trainer.train(f"exec-{i}", feedback)

        assert trainer.learning_state["feedback_count"] == 5
        # Milestone logging would be captured in logs (not easily tested without log capture)


class TestFeedbackIntegration:
    """Test feedback system integration scenarios"""

    def test_invalid_result_type(self):
        """Test feedback with invalid result type"""
        feedback_system = AlphaFeedbackSystem()

        with pytest.raises(Exception):  # Should raise POETFeedbackError
            feedback_system.feedback("not a result", "some feedback")

    @patch("opendxa.dana.poet.feedback.LLMResource")
    def test_multiple_feedback_same_execution(self, mock_llm_class):
        """Test multiple feedback for same execution"""
        mock_llm = Mock()
        mock_llm.query.return_value = '{"sentiment": "positive", "feedback_type": "general", "confidence": 0.7, "key_issues": [], "suggestions": [], "learning_priority": "low", "business_impact": "low"}'
        mock_llm_class.return_value = mock_llm

        feedback_system = AlphaFeedbackSystem()
        result = POETResult({"value": 42}, "test_func")

        # Submit multiple feedback for same execution
        feedback_system.feedback(result, "First feedback")
        feedback_system.feedback(result, "Second feedback")

        execution_id = result._poet["execution_id"]
        feedback_list = feedback_system.feedback_data[execution_id]

        assert len(feedback_list) == 2
        assert feedback_list[0]["raw_feedback"] == "First feedback"
        assert feedback_list[1]["raw_feedback"] == "Second feedback"

    def test_feedback_system_persistence_across_instances(self):
        """Test feedback persistence across system instances"""
        temp_dir = tempfile.mkdtemp()

        # First instance
        system1 = AlphaFeedbackSystem(storage_path=temp_dir)
        result = POETResult({"value": 42}, "test_func")

        # Store execution context
        system1._store_execution_context(result)
        execution_id = result._poet["execution_id"]

        # Second instance (simulating restart)
        system2 = AlphaFeedbackSystem(storage_path=temp_dir)

        # Should be able to load execution context
        execution_file = Path(temp_dir) / "executions" / f"{execution_id}.json"
        assert execution_file.exists()

        with open(execution_file) as f:
            loaded_data = json.load(f)
        assert loaded_data["function_name"] == "test_func"
