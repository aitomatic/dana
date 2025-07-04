"""POET Feedback System - Alpha Implementation

In-memory feedback processing with LLM-powered translation.
No PubSub integration in Alpha - focuses on immediate feedback learning.
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from dana.common.mixins.loggable import Loggable
from dana.common.resource.llm.llm_resource import LLMResource

from .types import POETFeedbackError, POETResult


class AlphaFeedbackSystem(Loggable):
    """Alpha implementation of POET feedback system with in-memory storage"""

    def __init__(self, storage_path: str | None = None):
        super().__init__()
        self.storage_path = Path(storage_path or ".poet")
        self.executions: dict[str, dict[str, Any]] = {}  # In-memory execution storage
        self.feedback_data: dict[str, list[dict[str, Any]]] = {}  # execution_id -> feedback list
        self.trainers: dict[str, Any] = {}  # Cached train() methods
        self.llm = LLMResource()

        # Ensure storage directory exists
        self.storage_path.mkdir(exist_ok=True)
        (self.storage_path / "executions").mkdir(exist_ok=True)
        (self.storage_path / "feedback").mkdir(exist_ok=True)

        self.log_info(f"Alpha feedback system initialized with storage at {self.storage_path}")

    def _make_serializable(self, obj: Any) -> Any:
        """Convert any object to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list | tuple):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, str | int | float | bool) or obj is None:
            return obj
        else:
            # Convert any non-serializable object to string
            return str(obj)

    def feedback(self, result: POETResult, feedback_payload: Any) -> None:
        """
        Universal feedback method - accepts ANY format and uses LLM to understand it

        Args:
            result: POETResult from POET function execution
            feedback_payload: Any feedback format (text, dict, number, etc.)
        """
        if not isinstance(result, POETResult):
            raise POETFeedbackError("result must be a POETResult instance")

        execution_id = result._poet["execution_id"]
        function_name = result._poet["function_name"]
        version = result._poet["version"]

        self.log_info(f"Processing feedback for {function_name} execution {execution_id}")

        try:
            # Store execution context if not already stored
            self._store_execution_context(result)

            # Process and store feedback
            processed_feedback = self._process_feedback(feedback_payload, result)
            self._store_feedback(execution_id, processed_feedback)

            # Try to get or create trainer for learning (if optimize_for was specified)
            trainer = self._get_trainer(function_name, version)
            if trainer:
                # Let trainer handle the feedback
                trainer.train(execution_id, processed_feedback)
                self.log_info(f"Feedback processed by trainer for {function_name}")
            else:
                self.log_info(f"No trainer available for {function_name} - feedback stored only")

        except Exception as e:
            self.log_error(f"Feedback processing failed: {e}")
            raise POETFeedbackError(f"Feedback processing failed: {e}")

    def _store_execution_context(self, result: POETResult) -> None:
        """Store execution context for future reference"""
        execution_id = result._poet["execution_id"]

        if execution_id not in self.executions:
            execution_data = {
                "execution_id": execution_id,
                "function_name": result._poet["function_name"],
                "version": result._poet["version"],
                "timestamp": datetime.now().isoformat(),
                "result_summary": self._summarize_result(result._result),
                "enhanced": result._poet.get("enhanced", True),
            }

            self.executions[execution_id] = execution_data

            # Also persist to file for Alpha reliability
            execution_file = self.storage_path / "executions" / f"{execution_id}.json"
            with open(execution_file, "w") as f:
                json.dump(execution_data, f, indent=2)

    def _summarize_result(self, result: Any) -> str:
        """Create a summary of the result for context"""
        if isinstance(result, dict):
            return f"dict with keys: {list(result.keys())}"
        elif isinstance(result, list | tuple):
            return f"{type(result).__name__} with {len(result)} items"
        elif isinstance(result, int | float | bool):
            return f"{type(result).__name__}: {result}"
        elif isinstance(result, str):
            return f"string: {result[:100]}..." if len(result) > 100 else f"string: {result}"
        else:
            return f"{type(result).__name__}: {str(result)[:100]}"

    def _process_feedback(self, feedback_payload: Any, result: POETResult) -> dict[str, Any]:
        """Process feedback using LLM to extract learning signals"""

        # Create context for LLM processing
        context = {
            "function_name": result._poet["function_name"],
            "execution_id": result._poet["execution_id"],
            "result_summary": self._summarize_result(result._result),
            "feedback_type": type(feedback_payload).__name__,
            "feedback_content": str(feedback_payload),
        }

        # Use LLM to translate feedback into structured learning signals
        processing_method = "llm"
        try:
            processed = self._translate_feedback_with_llm(feedback_payload, context)
        except Exception as e:
            self.log_warning(f"LLM feedback translation failed: {e}, using basic processing")
            processed = self._basic_feedback_processing(feedback_payload)
            processing_method = "basic"

        # Add metadata
        processed.update(
            {
                "raw_feedback": feedback_payload,
                "processed_timestamp": datetime.now().isoformat(),
                "processing_method": processing_method,
            }
        )

        return processed

    def _translate_feedback_with_llm(self, feedback_payload: Any, context: dict[str, Any]) -> dict[str, Any]:
        """Use LLM to translate any feedback format into learning signals"""

        prompt = f"""
Analyze this feedback for a POET-enhanced function and extract learning signals.

Function: {context["function_name"]}
Result: {context["result_summary"]}
Feedback: {feedback_payload}

Extract and return a JSON object with these fields:
- sentiment: "positive" | "negative" | "neutral"
- feedback_type: "performance" | "accuracy" | "usability" | "error" | "suggestion"
- confidence: 0.0-1.0 (how confident you are in this assessment)
- key_issues: [list of specific issues mentioned]
- suggestions: [list of actionable suggestions]
- learning_priority: "high" | "medium" | "low"
- business_impact: "high" | "medium" | "low"

Return only the JSON object.
"""

        try:
            # Create request for LLMResource
            from dana.common.types import BaseRequest

            request = BaseRequest(
                arguments={
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a feedback analysis expert. Extract structured learning signals from any feedback format. Return only valid JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ]
                }
            )
            response_obj = self.llm.query_sync(request)
            response = response_obj.content

            # Try to parse as JSON
            import json

            if isinstance(response, dict):
                # Check if this is a full LLM response structure with 'choices'
                if "choices" in response and len(response["choices"]) > 0:
                    # Extract the actual message content from the first choice
                    message_content = response["choices"][0].get("message", {}).get("content", "")
                    if message_content:
                        parsed = json.loads(message_content.strip())
                        return self._make_serializable(parsed)
                # Otherwise, assume it's already parsed feedback data
                return self._make_serializable(response)
            elif isinstance(response, str):
                # Simple string response - parse as JSON
                parsed = json.loads(response.strip())
                return self._make_serializable(parsed)
            else:
                # Try to parse whatever we got
                parsed = json.loads(str(response).strip())
                return self._make_serializable(parsed)

        except Exception as e:
            self.log_error(f"LLM feedback translation failed: {e}")
            raise

    def _basic_feedback_processing(self, feedback_payload: Any) -> dict[str, Any]:
        """Basic feedback processing when LLM translation fails"""
        processed = {
            "sentiment": "neutral",
            "feedback_type": "general",
            "confidence": 0.1,
            "key_issues": [],
            "suggestions": [],
            "learning_priority": "low",
            "business_impact": "low",
        }

        if isinstance(feedback_payload, dict):
            processed.update(feedback_payload)
            if processed.get("sentiment") not in ["positive", "negative", "neutral"]:
                processed["sentiment"] = "neutral"
            return processed

        if isinstance(feedback_payload, int | float):
            processed["feedback_type"] = "rating"
            if feedback_payload > 0:
                processed["sentiment"] = "positive"
            elif feedback_payload < 0:
                processed["sentiment"] = "negative"
            return processed

        # For strings, do simple keyword analysis
        import re

        text = str(feedback_payload).lower()
        positive_words = ["good", "great", "excellent", "awesome", "love", "like", "accurate"]
        negative_words = ["bad", "wrong", "terrible", "hate", "dislike", "error", "inaccurate"]

        is_positive = any(re.search(r"\b" + word + r"\b", text) for word in positive_words)
        is_negative = any(re.search(r"\b" + word + r"\b", text) for word in negative_words)

        if is_positive and not is_negative:
            processed["sentiment"] = "positive"
            processed["confidence"] = 0.6
        elif is_negative and not is_positive:
            processed["sentiment"] = "negative"
            processed["confidence"] = 0.6

        if "suggestion" in text or "should" in text:
            processed["feedback_type"] = "suggestion"

        return processed

    def _store_feedback(self, execution_id: str, processed_feedback: dict[str, Any]) -> None:
        """Store processed feedback in memory and on disk."""
        feedback_id = str(uuid4())
        # Add metadata to processed feedback
        feedback_with_metadata = processed_feedback.copy()
        feedback_with_metadata.update(
            {
                "execution_id": execution_id,
                "feedback_id": feedback_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Store in memory
        if execution_id not in self.feedback_data:
            self.feedback_data[execution_id] = []
        self.feedback_data[execution_id].append(feedback_with_metadata)

        # Also persist to file for Alpha reliability
        feedback_file = self.storage_path / "feedback" / f"{execution_id}_feedback.json"
        with open(feedback_file, "w") as f:
            json.dump(self.feedback_data[execution_id], f, indent=2)

        self.log_debug(f"Stored feedback for execution {execution_id}")

    def _get_trainer(self, function_name: str, version: str) -> Any | None:
        """Get or create trainer for a function"""
        trainer_key = f"{function_name}_{version}"
        if trainer_key in self.trainers:
            return self.trainers[trainer_key]

        # Try to load trainer from file
        train_file = self.storage_path / function_name / version / "train.na"
        if train_file.exists():
            try:
                trainer = self._load_trainer_from_file(train_file)
                self.trainers[trainer_key] = trainer
                return trainer
            except Exception as e:
                self.log_warning(f"Failed to load trainer for {function_name}: {e}")

        # For Alpha implementation: always create a basic trainer
        trainer = BasicAlphaTrainer(function_name, version)
        self.trainers[trainer_key] = trainer
        return trainer

    def _load_trainer_from_file(self, train_file: Path) -> Any:
        """Load trainer from file"""
        # For Alpha: simple trainer that just logs feedback
        return BasicAlphaTrainer(train_file.parent.name, train_file.parent.parent.name)

    def get_feedback_summary(self, function_name: str) -> dict[str, Any]:
        """Get a summary of all feedback for a given function"""
        all_feedback = []
        for exec_id, execution in self.executions.items():
            if execution.get("function_name") == function_name:
                if exec_id in self.feedback_data:
                    all_feedback.extend(self.feedback_data[exec_id])

        if not all_feedback:
            return {
                "function_name": function_name,
                "message": f"No feedback found for function '{function_name}'",
                "total_feedback": 0,
                "sentiment_distribution": {},
                "feedback_type_distribution": {},
                "recent_feedback": [],
            }

        total_feedback = len(all_feedback)
        sentiment_counts = Counter(f.get("sentiment", "neutral") for f in all_feedback)
        type_counts = Counter(f.get("feedback_type", "unknown") for f in all_feedback)

        # Sort feedback by timestamp, most recent first
        recent_feedback = sorted(all_feedback, key=lambda f: f.get("processed_timestamp", ""), reverse=True)[:10]

        summary = {
            "function_name": function_name,
            "total_feedback": total_feedback,
            "sentiment_distribution": dict(sentiment_counts),
            "feedback_type_distribution": dict(type_counts),
            "learning_priority_distribution": {},
            "business_impact_distribution": {},
            "recent_feedback": recent_feedback,
        }

        return summary


class BasicAlphaTrainer:
    """Basic trainer for Alpha implementation"""

    def __init__(self, function_name: str, version: str):
        self.function_name = function_name
        self.version = version
        self.learning_state = {
            "feedback_count": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "learning_milestones": [],
            "patterns": [],
            "improvement_suggestions": [],
        }
        self.logger = Loggable.get_class_logger()

    def train(self, execution_id: str, processed_feedback: dict[str, Any]) -> None:
        """Basic training implementation that updates learning state"""
        sentiment = processed_feedback.get("sentiment", "unknown")
        learning_priority = processed_feedback.get("learning_priority", "low")

        # Update learning state
        self.learning_state["feedback_count"] += 1
        if sentiment == "positive":
            self.learning_state["positive_feedback"] += 1
        elif sentiment == "negative":
            self.learning_state["negative_feedback"] += 1

        # Track patterns for high priority feedback
        if learning_priority == "high" and sentiment == "negative":
            pattern = {
                "type": "high_priority_negative_feedback",
                "execution_id": execution_id,
                "issues": processed_feedback.get("key_issues", []),
                "timestamp": processed_feedback.get("processed_timestamp", datetime.now().isoformat()),
            }
            self.learning_state["patterns"].append(pattern)

        # Track improvement suggestions
        suggestions = processed_feedback.get("suggestions", [])
        for suggestion in suggestions:
            if suggestion not in self.learning_state["improvement_suggestions"]:
                self.learning_state["improvement_suggestions"].append(suggestion)

        # Check for learning milestones
        if self.learning_state["feedback_count"] % 5 == 0:
            milestone = f"Reached {self.learning_state['feedback_count']} feedback items"
            self.learning_state["learning_milestones"].append(milestone)

        self.logger.info(
            f"Training {self.function_name} v{self.version} with feedback: {sentiment} "
            f"({processed_feedback.get('feedback_type', 'unknown')}) - "
            f"Total feedback: {self.learning_state['feedback_count']}"
        )

        # Log key issues and suggestions
        if processed_feedback.get("key_issues"):
            self.logger.info(f"Key issues: {processed_feedback['key_issues']}")
        if processed_feedback.get("suggestions"):
            self.logger.info(f"Suggestions: {processed_feedback['suggestions']}")


# Global feedback system instance
_default_feedback_system: AlphaFeedbackSystem | None = None


def get_default_feedback_system() -> AlphaFeedbackSystem:
    """Get default feedback system instance"""
    global _default_feedback_system
    if _default_feedback_system is None:
        _default_feedback_system = AlphaFeedbackSystem()
    return _default_feedback_system
