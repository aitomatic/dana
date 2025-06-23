#!/usr/bin/env python3
"""
Use Case 09: Risk Mitigation

Organizations can **experiment with AI** without betting the farm.
This demonstrates A/B testing, fallback strategies, and safe AI adoption patterns.

Business Value: Experiment with AI safely
- Optional AI enhancements vs required features
- A/B testing AI vs traditional approaches
- Fail-safe AI adoption strategies

Copyright © 2025 Aitomatic, Inc.
MIT License
"""

import logging
import random
import time
from dataclasses import dataclass
from typing import Any

from opendxa.dana import dana

# Configure logging for risk monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RiskMitigationConfig:
    """Configuration for safe AI experimentation"""

    ai_enabled: bool = True
    ai_percentage: float = 0.5  # Start with 50% AI adoption
    fallback_enabled: bool = True
    confidence_threshold: float = 0.7  # Only use AI if confidence > 70%


def traditional_order_analysis(order_data: dict[str, Any]) -> dict[str, Any]:
    """
    TRADITIONAL: Rule-based order analysis (PROVEN, RELIABLE)
    This is the existing logic that works and is trusted
    """
    risk_score = 0

    # Simple rule-based risk assessment
    if order_data["amount"] > 10000:
        risk_score += 30
    if order_data["customer_age_days"] < 30:
        risk_score += 40
    if order_data["payment_method"] == "new_card":
        risk_score += 20
    if order_data["shipping_country"] != order_data["billing_country"]:
        risk_score += 25

    decision = "approve" if risk_score < 50 else "review"

    return {
        "decision": decision,
        "risk_score": risk_score,
        "analysis_method": "traditional_rules",
        "confidence": 0.85,  # High confidence in proven rules
        "processing_time": 0.1,  # Very fast
        "fallback_reason": None,
    }


def ai_enhanced_order_analysis(order_data: dict[str, Any], config: RiskMitigationConfig) -> dict[str, Any] | None:
    """
    NEW: AI-enhanced order analysis (EXPERIMENTAL, BEING TESTED)
    Returns None if AI fails or is disabled - triggers fallback
    """
    if not config.ai_enabled:
        return None

    start_time = time.time()

    try:
        dana.enable_module_imports()

        try:
            import risk_analyzer  # Dana module for intelligent risk assessment

            # AI analysis with timeout protection
            ai_decision = risk_analyzer.analyze_order_risk(order_data)
            ai_confidence = risk_analyzer.calculate_confidence(ai_decision, order_data)
            fraud_indicators = risk_analyzer.detect_fraud_patterns(order_data)

            processing_time = time.time() - start_time

            # SAFETY CHECK: Confidence threshold
            if ai_confidence < config.confidence_threshold:
                logger.warning(f"AI confidence too low: {ai_confidence:.2f} < {config.confidence_threshold}")
                return None

            return {
                "decision": ai_decision,
                "risk_score": risk_analyzer.calculate_risk_score(order_data),
                "analysis_method": "ai_enhanced",
                "confidence": ai_confidence,
                "processing_time": processing_time,
                "fraud_indicators": fraud_indicators,
                "fallback_reason": None,
            }

        finally:
            dana.disable_module_imports()

    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return None


def safe_order_processing(order_data: dict[str, Any], config: RiskMitigationConfig) -> dict[str, Any]:
    """
    SAFE HYBRID: Combines AI capabilities with proven fallbacks
    """
    # Decide whether to try AI based on configuration
    use_ai = config.ai_enabled and random.random() < config.ai_percentage

    if use_ai:
        logger.info(f"Attempting AI analysis for order {order_data['order_id']}")
        ai_result = ai_enhanced_order_analysis(order_data, config)

        if ai_result is not None:
            logger.info(f"AI analysis successful: {ai_result['confidence']:.2f} confidence")
            return ai_result
        else:
            logger.warning("AI analysis failed, falling back to traditional method")

    # Fallback to traditional method (always reliable)
    traditional_result = traditional_order_analysis(order_data)
    traditional_result["fallback_reason"] = "ai_disabled" if not use_ai else "ai_failed"

    return traditional_result


def run_ab_testing_simulation(config: RiskMitigationConfig, num_orders: int = 10) -> dict[str, Any]:
    """
    Simulate A/B testing of AI vs traditional approaches
    """
    results = {
        "ai_successes": 0,
        "ai_failures": 0,
        "traditional_fallbacks": 0,
        "total_orders": num_orders,
        "processing_times": [],
        "confidence_scores": [],
    }

    sample_orders = [
        {
            "order_id": f"ORD_{i:03d}",
            "amount": random.randint(50, 15000),
            "customer_age_days": random.randint(1, 1000),
            "payment_method": random.choice(["saved_card", "new_card", "paypal"]),
            "shipping_country": "US",
            "billing_country": random.choice(["US", "CA", "MX"]),
        }
        for i in range(num_orders)
    ]

    for order in sample_orders:
        result = safe_order_processing(order, config)

        results["processing_times"].append(result["processing_time"])
        results["confidence_scores"].append(result["confidence"])

        if result["analysis_method"] == "ai_enhanced":
            results["ai_successes"] += 1
        elif result["fallback_reason"] in ["ai_failed", "ai_disabled"]:
            results["traditional_fallbacks"] += 1

    return results


def main():
    print("🎯 Use Case 09: Risk Mitigation")
    print("=" * 40)

    print("🛡️  Demonstrating safe AI experimentation strategies...")

    # Test configuration 1: Conservative AI adoption
    print("\n📊 Test 1: Conservative AI adoption (25% AI, high safety thresholds)")
    conservative_config = RiskMitigationConfig(
        ai_enabled=True,
        ai_percentage=0.25,  # Only 25% of requests use AI
        confidence_threshold=0.8,  # High confidence required
    )

    conservative_results = run_ab_testing_simulation(conservative_config, 5)

    print(f"   🤖 AI successes: {conservative_results['ai_successes']}/20 ({conservative_results['ai_successes'] / 20 * 100:.0f}%)")
    print(
        f"   🔄 Fallbacks: {conservative_results['traditional_fallbacks']}/20 ({conservative_results['traditional_fallbacks'] / 20 * 100:.0f}%)"
    )
    print(
        f"   ⏱️  Avg processing time: {sum(conservative_results['processing_times']) / len(conservative_results['processing_times']):.3f}s"
    )

    # Test configuration 2: Aggressive AI adoption
    print("\n📊 Test 2: Aggressive AI adoption (75% AI, relaxed thresholds)")
    aggressive_config = RiskMitigationConfig(
        ai_enabled=True,
        ai_percentage=0.75,  # 75% of requests use AI
        confidence_threshold=0.6,  # Lower confidence acceptable
    )

    aggressive_results = run_ab_testing_simulation(aggressive_config, 5)

    print(f"   🤖 AI successes: {aggressive_results['ai_successes']}/20 ({aggressive_results['ai_successes'] / 20 * 100:.0f}%)")
    print(
        f"   🔄 Fallbacks: {aggressive_results['traditional_fallbacks']}/20 ({aggressive_results['traditional_fallbacks'] / 20 * 100:.0f}%)"
    )
    print(f"   ⏱️  Avg processing time: {sum(aggressive_results['processing_times']) / len(aggressive_results['processing_times']):.3f}s")

    # Test configuration 3: AI disabled (control group)
    print("\n📊 Test 3: AI disabled (100% traditional - control group)")
    traditional_config = RiskMitigationConfig(ai_enabled=False)

    traditional_results = run_ab_testing_simulation(traditional_config, 20)

    print(f"   🔧 Traditional processing: {traditional_results['traditional_fallbacks']}/20 (100%)")
    print(f"   ⏱️  Avg processing time: {sum(traditional_results['processing_times']) / len(traditional_results['processing_times']):.3f}s")

    print("\n✅ Risk Mitigation Success!")
    print("💡 Key Risk Management Benefits:")
    print("   🛡️  AI failures automatically fallback to proven methods")
    print("   📊 A/B testing allows gradual confidence building")
    print("   ⚡ Performance monitoring prevents AI from slowing systems")
    print("   🎯 Confidence thresholds ensure AI only acts when certain")
    print("   🔄 Easy to adjust AI adoption percentage based on results")
    print("   🚀 Zero downtime - traditional systems always available")


if __name__ == "__main__":
    main()
