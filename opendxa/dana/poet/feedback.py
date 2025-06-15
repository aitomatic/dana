"""POET Feedback System - Alpha Implementation

In-memory feedback processing with LLM-powered translation.
No PubSub integration in Alpha - focuses on immediate feedback learning.
"""

from typing import Any, Dict, Optional
from pathlib import Path
import json
import uuid
from datetime import datetime

from opendxa.common.utils.logging import DXA_LOGGER
from opendxa.common.resource.llm_resource import LLMResource
from .types import POETResult, POETFeedbackError


class AlphaFeedbackSystem:
    """Alpha implementation of POET feedback system with in-memory storage"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or ".poet")
        self.executions: Dict[str, Dict[str, Any]] = {}  # In-memory execution storage
        self.feedback_data: Dict[str, list[Dict[str, Any]]] = {}  # execution_id -> feedback list
        self.trainers: Dict[str, Any] = {}  # Cached train() methods
        self.llm = LLMResource()

        # Ensure storage directory exists
        self.storage_path.mkdir(exist_ok=True)
        (self.storage_path / "executions").mkdir(exist_ok=True)
        (self.storage_path / "feedback").mkdir(exist_ok=True)

        DXA_LOGGER.info(f"Alpha feedback system initialized with storage at {self.storage_path}")

    def _make_serializable(self, obj: Any) -> Any:
        """Convert any object to JSON-serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
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

        DXA_LOGGER.info(f"Processing feedback for {function_name} execution {execution_id}")

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
                DXA_LOGGER.info(f"Feedback processed by trainer for {function_name}")
            else:
                DXA_LOGGER.info(f"No trainer available for {function_name} - feedback stored only")

        except Exception as e:
            DXA_LOGGER.error(f"Feedback processing failed: {e}")
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
        elif isinstance(result, (list, tuple)):
            return f"{type(result).__name__} with {len(result)} items"
        elif isinstance(result, (int, float, bool)):
            return f"{type(result).__name__}: {result}"
        elif isinstance(result, str):
            return f"string: {result[:100]}..." if len(result) > 100 else f"string: {result}"
        else:
            return f"{type(result).__name__}: {str(result)[:100]}"

    def _process_feedback(self, feedback_payload: Any, result: POETResult) -> Dict[str, Any]:
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
        try:
            processed = self._translate_feedback_with_llm(feedback_payload, context)
        except Exception as e:
            DXA_LOGGER.warning(f"LLM feedback translation failed: {e}, using basic processing")
            processed = self._basic_feedback_processing(feedback_payload)

        # Add metadata
        processed.update(
            {
                "raw_feedback": feedback_payload,
                "processed_timestamp": datetime.now().isoformat(),
                "processing_method": "llm" if "sentiment" in processed else "basic",
            }
        )

        return processed

    def _translate_feedback_with_llm(self, feedback_payload: Any, context: Dict[str, Any]) -> Dict[str, Any]:
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
            from opendxa.common.types import BaseRequest

            request = BaseRequest(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a feedback analysis expert. Extract structured learning signals from any feedback format. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            response_obj = self.llm.query_sync(request)
            response = response_obj.content

            # Try to parse as JSON
            import json

            if isinstance(response, dict):
                # Already parsed - ensure it's serializable
                return self._make_serializable(response)
            elif isinstance(response, str):
                parsed = json.loads(response.strip())
                return self._make_serializable(parsed)
            else:
                # Try to parse whatever we got
                parsed = json.loads(str(response).strip())
                return self._make_serializable(parsed)

        except Exception as e:
            DXA_LOGGER.warning(f"LLM JSON parsing failed: {e}")
            raise

    def _basic_feedback_processing(self, feedback_payload: Any) -> Dict[str, Any]:
        """Fallback basic feedback processing when LLM fails"""

        # Simple heuristic processing
        feedback_str = str(feedback_payload).lower()

        # Determine sentiment
        positive_words = ["good", "great", "excellent", "works", "correct", "accurate", "fast"]
        negative_words = ["bad", "wrong", "slow", "error", "failed", "broken", "inaccurate"]

        positive_count = sum(1 for word in positive_words if word in feedback_str)
        negative_count = sum(1 for word in negative_words if word in feedback_str)

        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "feedback_type": "general",
            "confidence": 0.6,  # Lower confidence for basic processing
            "key_issues": [feedback_str[:100]] if sentiment == "negative" else [],
            "suggestions": [],
            "learning_priority": "medium",
            "business_impact": "medium",
        }

    def _store_feedback(self, execution_id: str, processed_feedback: Dict[str, Any]) -> None:
        """Store processed feedback"""
        if execution_id not in self.feedback_data:
            self.feedback_data[execution_id] = []

        feedback_entry = {
            "feedback_id": str(uuid.uuid4()),
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            **processed_feedback,
        }

        self.feedback_data[execution_id].append(feedback_entry)

        # Persist to file with JSON serialization safety
        feedback_file = self.storage_path / "feedback" / f"{execution_id}_feedback.json"
        try:
            with open(feedback_file, "w") as f:
                json.dump(self.feedback_data[execution_id], f, indent=2, default=str)
        except Exception as e:
            DXA_LOGGER.error(f"Failed to persist feedback to file: {e}")
            # Try with string conversion fallback
            try:
                serializable_data = self._make_serializable(self.feedback_data[execution_id])
                with open(feedback_file, "w") as f:
                    json.dump(serializable_data, f, indent=2)
            except Exception as e2:
                DXA_LOGGER.error(f"Failed to persist feedback even with fallback: {e2}")
                # Continue without persisting to file

        DXA_LOGGER.debug(f"Stored feedback for execution {execution_id}")

    def _get_trainer(self, function_name: str, version: str) -> Optional[Any]:
        """Get or create trainer for a function (if optimize_for was specified)"""
        trainer_key = f"{function_name}_{version}"

        if trainer_key in self.trainers:
            return self.trainers[trainer_key]

        # Check if a train.py file exists for this function
        train_file = self.storage_path / function_name / version / "train.py"
        if train_file.exists():
            try:
                # Load the trainer class
                trainer = self._load_trainer_from_file(train_file)
                self.trainers[trainer_key] = trainer
                return trainer
            except Exception as e:
                DXA_LOGGER.warning(f"Failed to load trainer for {function_name}: {e}")

        # For Alpha: create basic trainer if optimize_for was used
        # (In real implementation, this would be generated during transpilation)
        basic_trainer = BasicAlphaTrainer(function_name, version)
        self.trainers[trainer_key] = basic_trainer
        return basic_trainer

    def _load_trainer_from_file(self, train_file: Path) -> Any:
        """Load trainer class from generated train.py file"""
        # For Alpha: simplified loading
        # In full implementation, this would properly load generated trainer classes
        namespace = {}
        with open(train_file, "r") as f:
            code = f.read()
        exec(code, namespace)

        # Look for trainer class
        for name, obj in namespace.items():
            if hasattr(obj, "train") and callable(getattr(obj, "train")):
                return obj()

        raise ValueError("No trainer class found in train.py")

    def get_feedback_summary(self, function_name: str) -> Dict[str, Any]:
        """Get feedback summary for a function"""
        all_feedback = []
        for execution_id, feedback_list in self.feedback_data.items():
            execution = self.executions.get(execution_id, {})
            if execution.get("function_name") == function_name:
                all_feedback.extend(feedback_list)

        if not all_feedback:
            return {"function_name": function_name, "total_feedback": 0}

        # Aggregate statistics
        sentiments = [f.get("sentiment", "unknown") for f in all_feedback]
        feedback_types = [f.get("feedback_type", "unknown") for f in all_feedback]

        return {
            "function_name": function_name,
            "total_feedback": len(all_feedback),
            "sentiment_distribution": {sentiment: sentiments.count(sentiment) for sentiment in set(sentiments)},
            "feedback_type_distribution": {ftype: feedback_types.count(ftype) for ftype in set(feedback_types)},
            "recent_feedback": all_feedback[-5:] if len(all_feedback) >= 5 else all_feedback,
        }


class BasicAlphaTrainer:
    """Basic trainer for Alpha implementation when optimize_for is specified"""

    def __init__(self, function_name: str, version: str):
        self.function_name = function_name
        self.version = version
        self.learning_state: Dict[str, Any] = {"feedback_count": 0, "patterns": [], "improvement_suggestions": []}

        DXA_LOGGER.info(f"BasicAlphaTrainer initialized for {function_name} {version}")

    def train(self, execution_id: str, processed_feedback: Dict[str, Any]) -> None:
        """Process feedback for learning (Alpha implementation)"""
        self.learning_state["feedback_count"] += 1

        # Simple pattern detection
        if processed_feedback.get("sentiment") == "negative":
            if processed_feedback.get("learning_priority") == "high":
                pattern = {
                    "type": "high_priority_negative_feedback",
                    "execution_id": execution_id,
                    "issues": processed_feedback.get("key_issues", []),
                    "timestamp": processed_feedback.get("processed_timestamp"),
                }
                self.learning_state["patterns"].append(pattern)

        # Generate improvement suggestions (basic for Alpha)
        if processed_feedback.get("suggestions"):
            self.learning_state["improvement_suggestions"].extend(processed_feedback["suggestions"])

        DXA_LOGGER.info(
            f"Training completed for {self.function_name}: {self.learning_state['feedback_count']} total feedback items processed"
        )

        # For Alpha: just log the learning state
        # In full implementation: trigger regeneration if needed
        if self.learning_state["feedback_count"] % 5 == 0:
            DXA_LOGGER.info(f"Learning milestone: {self.learning_state}")


# Global feedback system instance
_default_feedback_system: Optional[AlphaFeedbackSystem] = None


def get_default_feedback_system() -> AlphaFeedbackSystem:
    """Get or create the default feedback system"""
    global _default_feedback_system
    if _default_feedback_system is None:
        _default_feedback_system = AlphaFeedbackSystem()
    return _default_feedback_system
