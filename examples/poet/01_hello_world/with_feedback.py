#!/usr/bin/env python3
"""
POET Feedback Demo - Learning Loop

This example demonstrates POET's learning capabilities:
1. Use @poet(optimize_for="accuracy") to enable learning
2. Provide feedback in any format
3. See how functions learn and improve
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from opendxa.dana.poet import poet
from opendxa.common.utils.logging import DXA_LOGGER


@poet(optimize_for="accuracy")
def classify_sentiment(text: str) -> dict:
    """Simple sentiment classifier that learns from feedback"""
    # Basic sentiment analysis
    positive_words = ["good", "great", "excellent", "amazing", "wonderful"]
    negative_words = ["bad", "terrible", "awful", "horrible", "disappointing"]

    text_lower = text.lower()

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    if positive_count > negative_count:
        sentiment = "positive"
        confidence = 0.7
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = 0.7
    else:
        sentiment = "neutral"
        confidence = 0.5

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "text": text,
        "positive_signals": positive_count,
        "negative_signals": negative_count,
    }


@poet(domain="ml_monitoring", optimize_for="reliability")
def monitor_api_health(response_time: float, error_rate: float) -> dict:
    """API health monitor that learns optimal thresholds"""
    # Simple thresholds that can be learned/adjusted
    slow_threshold = 1000  # ms
    error_threshold = 0.05  # 5%

    is_healthy = response_time < slow_threshold and error_rate < error_threshold

    health_score = 1.0
    if response_time >= slow_threshold:
        health_score -= 0.3
    if error_rate >= error_threshold:
        health_score -= 0.5

    health_score = max(0.0, health_score)

    return {
        "is_healthy": is_healthy,
        "health_score": health_score,
        "response_time": response_time,
        "error_rate": error_rate,
        "slow_threshold": slow_threshold,
        "error_threshold": error_threshold,
        "status": "healthy" if is_healthy else "degraded",
    }


def main():
    """Demonstrate POET feedback and learning"""
    print("🧠 POET Feedback Demo - Learning Loop")
    print("=" * 50)

    print("\n1. Sentiment classification with learning:")
    print("   @poet(optimize_for='accuracy') enables Train phase")

    try:
        # Test sentiment classification
        test_texts = [
            "This product is absolutely amazing!",
            "The service was terrible and disappointing.",
            "It's okay, nothing special.",
        ]

        results = []
        for text in test_texts:
            result = classify_sentiment(text)
            results.append(result)
            sentiment_data = result.unwrap()
            print(f"   '{text[:30]}...' → {sentiment_data['sentiment']} ({sentiment_data['confidence']:.2f})")

        print("\n2. Providing feedback:")
        print("   POET accepts feedback in ANY format - text, numbers, structured data")

        # Import feedback function
        from opendxa.dana.poet import feedback

        # Provide various types of feedback
        feedback_examples = [
            "The first prediction was perfect!",
            {"rating": 4, "comment": "Good but could be more confident"},
            0.3,  # Just a number
            {"correct": False, "expected": "neutral", "reason": "Missing context"},
        ]

        for i, fb in enumerate(feedback_examples):
            if i < len(results):
                print(f"   Feedback {i + 1}: {fb}")
                feedback(results[i], fb)
                print(f"   ✅ Processed feedback for execution {results[i]._poet['execution_id'][:8]}...")

    except Exception as e:
        DXA_LOGGER.error(f"Error in sentiment demo: {e}")
        print(f"   ❌ Error: {e}")

    print("\n3. API health monitoring with domain expertise:")
    print("   @poet(domain='ml_monitoring', optimize_for='reliability')")

    try:
        # Test API health monitoring
        test_cases = [
            (500, 0.02),  # Good performance
            (1500, 0.01),  # Slow but reliable
            (800, 0.08),  # Fast but unreliable
            (2000, 0.12),  # Poor performance
        ]

        health_results = []
        for response_time, error_rate in test_cases:
            result = monitor_api_health(response_time, error_rate)
            health_results.append(result)
            health_data = result.unwrap()
            print(
                f"   API ({response_time}ms, {error_rate:.1%} errors) → {health_data['status']} (score: {health_data['health_score']:.2f})"
            )

        print("\n4. Learning from operations feedback:")
        print("   Providing operational feedback to improve thresholds")

        # Operational feedback
        operational_feedback = [
            "1000ms threshold too strict - users complain at 1500ms",
            {"threshold_adjustment": "increase_response_time", "suggested_value": 1200},
            "False alarm - 5% error rate is normal during peak hours",
            "The health score calculation seems too harsh",
        ]

        for i, fb in enumerate(operational_feedback):
            if i < len(health_results):
                print(f"   Ops feedback {i + 1}: {fb}")
                feedback(health_results[i], fb)
                print(f"   ✅ Learning from operations feedback")

    except Exception as e:
        DXA_LOGGER.error(f"Error in health monitoring demo: {e}")
        print(f"   ❌ Error: {e}")

    print("\n5. How POET learning works:")
    print("   - Train phase activated by optimize_for parameter")
    print("   - LLM translates ANY feedback format into learning signals")
    print("   - Functions learn patterns and improve over time")
    print("   - No manual feedback schema required")
    print("   - Learning state persisted in .poet/ directory")

    print("\n✅ Feedback and learning demo complete!")
    print("   Check .poet/ directory for stored function versions and feedback")
    print("   Next: Try 02_basic_usage/ for more realistic scenarios")


if __name__ == "__main__":
    main()
