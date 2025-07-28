"""
Tests for POET Feedback System
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from dana.common.types import BaseResponse
from dana.frameworks.poet.core.types import POETFeedbackError, POETResult


class AlphaFeedbackSystem:
    def __init__(self, storage_path=None):
        self.storage_path = Path(storage_path) if storage_path else Path(tempfile.mkdtemp())
        self.executions = {}
        self.feedback_data = {}
        self.trainers = {}
        (self.storage_path / "executions").mkdir(exist_ok=True)
        (self.storage_path / "feedback").mkdir(exist_ok=True)

    def _store_execution_context(self, result):
        execution_id = result._poet["execution_id"]
        self.executions[execution_id] = {
            "function_name": result.function_name,
            "version": result.version,
            "timestamp": "2025-06-14T10:00:00Z",
        }
        with open(self.storage_path / "executions" / f"{execution_id}.json", "w") as f:
            json.dump(self.executions[execution_id], f)

    def _summarize_result(self, result):
        if isinstance(result, dict):
            return f"dict with keys: {', '.join(result.keys())}"
        if isinstance(result, list):
            return f"list with {len(result)} items"
        if isinstance(result, str):
            if len(result) > 100:
                return f"string: {result[:100]}..."
            return f"string: {result}"
        if isinstance(result, (int, float)):
            return f"{type(result).__name__}: {result}"
        return str(result)

    def _process_feedback(self, feedback_payload, result):
        if hasattr(self, "llm"):
            try:
                response = self.llm.query_sync(f"Analyze feedback: {feedback_payload}")
                if response.success:
                    data = json.loads(response.content)
                    data["raw_feedback"] = feedback_payload
                    data["processing_method"] = "llm"
                    return data
            except Exception:
                pass
        return self._basic_feedback_processing(feedback_payload)

    def _basic_feedback_processing(self, feedback_payload):
        sentiment = "neutral"
        if any(word in feedback_payload.lower() for word in ["good", "great", "excellent"]):
            sentiment = "positive"
        elif any(word in feedback_payload.lower() for word in ["bad", "wrong", "terrible"]):
            sentiment = "negative"
        return {"sentiment": sentiment, "processing_method": "basic", "confidence": 0.6, "raw_feedback": feedback_payload}

    def _store_feedback(self, execution_id, processed_feedback):
        if execution_id not in self.feedback_data:
            self.feedback_data[execution_id] = []

        feedback_entry = {
            "feedback_id": str(Path(tempfile.mkdtemp()).name),
            "execution_id": execution_id,
            "timestamp": "2025-06-14T10:00:00Z",
            **processed_feedback,
        }
        self.feedback_data[execution_id].append(feedback_entry)

        with open(self.storage_path / "feedback" / f"{execution_id}_feedback.json", "w") as f:
            json.dump(self.feedback_data[execution_id], f)

    def _get_trainer(self, function_name, version):
        if (function_name, version) not in self.trainers:
            self.trainers[(function_name, version)] = BasicAlphaTrainer(function_name, version)
        return self.trainers[(function_name, version)]

    def feedback(self, result, feedback_payload):
        if not isinstance(result, POETResult):
            raise POETFeedbackError("result must be a POETResult instance")
        self._store_execution_context(result)
        execution_id = result._poet["execution_id"]
        processed_feedback = self._process_feedback(feedback_payload, result)
        self._store_feedback(execution_id, processed_feedback)

    def get_feedback_summary(self, function_name):
        total_feedback = 0
        sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
        feedback_type_distribution = {}
        recent_feedback = []

        for exec_id, execution in self.executions.items():
            if execution["function_name"] == function_name:
                if exec_id in self.feedback_data:
                    for fb in self.feedback_data[exec_id]:
                        total_feedback += 1
                        sentiment = fb.get("sentiment", "neutral")
                        fb_type = fb.get("feedback_type", "general")
                        sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
                        feedback_type_distribution[fb_type] = feedback_type_distribution.get(fb_type, 0) + 1
                        recent_feedback.append(fb)

        return {
            "function_name": function_name,
            "total_feedback": total_feedback,
            "sentiment_distribution": sentiment_distribution,
            "feedback_type_distribution": feedback_type_distribution,
            "recent_feedback": recent_feedback,
        }


class BasicAlphaTrainer:
    def __init__(self, function_name, version):
        self.function_name = function_name
        self.version = version
        self.learning_state = {
            "feedback_count": 0,
            "patterns": [],
            "improvement_suggestions": [],
        }

    def train(self, execution_id, processed_feedback):
        self.learning_state["feedback_count"] += 1
        if processed_feedback.get("learning_priority") == "high":
            self.learning_state["patterns"].append(
                {
                    "type": "high_priority_negative_feedback",
                    "execution_id": execution_id,
                    "issues": processed_feedback.get("key_issues", []),
                }
            )
        if "suggestions" in processed_feedback:
            self.learning_state["improvement_suggestions"].extend(processed_feedback["suggestions"])


@pytest.mark.poet
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

    def test_translate_feedback_with_llm_success(self):
        """Test LLM feedback translation success"""
        # Mock the LLM directly on the feedback system instance
        mock_llm = Mock()
        mock_response = BaseResponse(
            content='{"sentiment": "positive", "feedback_type": "performance", "confidence": 0.8}',
            success=True,
        )
        mock_llm.query_sync.return_value = mock_response
        self.feedback_system.llm = mock_llm

        result = POETResult({"value": 42}, "test_func")
        feedback_payload = "Great job!"

        processed = self.feedback_system._process_feedback(feedback_payload, result)

        assert processed["sentiment"] == "positive"
        assert processed["feedback_type"] == "performance"
        assert processed["confidence"] == 0.8
        assert processed["raw_feedback"] == "Great job!"
        assert processed["processing_method"] == "llm"

    def test_translate_feedback_with_llm_failure(self):
        """Test LLM feedback translation with fallback"""
        # Mock the LLM directly on the feedback system instance
        mock_llm = Mock()
        mock_llm.query_sync.side_effect = Exception("LLM error")
        self.feedback_system.llm = mock_llm

        result = POETResult({"value": 42}, "test_func")
        feedback_payload = "This is bad and wrong"

        processed = self.feedback_system._process_feedback(feedback_payload, result)

        assert processed["sentiment"] == "negative"  # Basic processing detected negative words
        assert processed["processing_method"] == "basic"
        assert processed["confidence"] > 0.5  # Check for reasonable confidence

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

        # Empty feedback
        empty_feedback = self.feedback_system._basic_feedback_processing("")
        assert empty_feedback["sentiment"] == "neutral"

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

    def test_feedback_end_to_end(self):
        """Test complete feedback processing flow"""
        # Mock the LLM directly on the feedback system instance
        mock_llm = Mock()
        mock_response_content = '{"sentiment": "negative", "feedback_type": "accuracy", "confidence": 0.9, "key_issues": ["threshold too low"], "suggestions": ["increase threshold"], "learning_priority": "high", "business_impact": "medium"}'
        mock_response = BaseResponse(content=mock_response_content, success=True)
        mock_llm.query_sync.return_value = mock_response
        self.feedback_system.llm = mock_llm

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
        assert processed.get("key_issues") == ["threshold too low"]
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


@pytest.mark.poet
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


@pytest.mark.poet
class TestFeedbackIntegration:
    """Test feedback system integration scenarios"""

    def test_invalid_result_type(self):
        """Test feedback with invalid result type"""
        feedback_system = AlphaFeedbackSystem()
        with pytest.raises(POETFeedbackError, match="result must be a POETResult instance"):
            feedback_system.feedback({"not": "a result"}, "This should fail")  # type: ignore

    def test_multiple_feedback_same_execution(self):
        """Test multiple feedback for same execution"""
        # Create a fresh feedback system and mock its LLM
        feedback_system = AlphaFeedbackSystem()
        mock_llm = Mock()
        mock_llm.query_sync.return_value = BaseResponse(
            content='{"sentiment": "positive", "feedback_type": "general", "confidence": 0.7, "key_issues": [], "suggestions": [], "learning_priority": "low", "business_impact": "low"}',
            success=True,
        )
        feedback_system.llm = mock_llm

        result = POETResult({"value": 100}, "test_func", "v1")

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
        AlphaFeedbackSystem(storage_path=temp_dir)

        # Should be able to load execution context
        execution_file = Path(temp_dir) / "executions" / f"{execution_id}.json"
        assert execution_file.exists()

        with open(execution_file) as f:
            loaded_data = json.load(f)
        assert loaded_data["function_name"] == "test_func"
