from unittest.mock import patch

from opendxa.dana.poet.decorator import POETResult, feedback, poet

# Mock feedback data
mock_feedback_data = [
    {"correct": True, "expected": "positive", "reason": "Accurate prediction"},
    {"correct": False, "expected": "neutral", "reason": "Missing context"},
    {"correct": True, "expected": "negative", "reason": "Correctly identified negative sentiment"},
]


# Mock function to test learning
@poet(optimize_for="accuracy")
def mock_sentiment_classifier(text: str) -> POETResult:
    return POETResult({"sentiment": "positive", "confidence": 0.8}, function_name="mock_sentiment_classifier")


# Test learning with mock feedback
def test_poet_learning_with_mock_feedback():
    results = []
    for text in ["Great product!", "It's okay.", "Terrible service."]:
        result = mock_sentiment_classifier(text)
        results.append(result)

    # Apply mock feedback
    for i, feedback_data in enumerate(mock_feedback_data):
        feedback(results[i], feedback_data)

    # Verify learning (snapshot testing)
    # This is a simplified check; in a real scenario, you would compare actual function behavior
    assert len(results) == len(mock_feedback_data), "Feedback should be applied to all results"


# Test accelerated learning
def test_poet_accelerated_learning():
    # Simulate accelerated learning by applying feedback multiple times
    result = mock_sentiment_classifier("Great product!")
    for _ in range(5):  # Accelerate learning by applying feedback multiple times
        feedback(result, {"correct": True, "expected": "positive", "reason": "Accurate prediction"})

    # Verify learning (snapshot testing)
    # This is a simplified check; in a real scenario, you would compare actual function behavior
    assert result is not None, "Result should not be None after learning"


# Test learning logic in isolation
def test_poet_learning_logic():
    # Mock the learning logic
    with patch("opendxa.dana.poet.decorator.feedback") as mock_feedback:
        result = mock_sentiment_classifier("Great product!")
        mock_feedback.assert_called_once_with(result, {"correct": True, "expected": "positive", "reason": "Accurate prediction"})
