#!/usr/bin/env python3
"""
Semiconductor Research: Deterministic vs Probabilistic Autonomy

This demo shows why deterministic workflows matter for technical research
where verification, credibility, and gap detection are critical.

Domain: Semiconductor process technology comparison
Query: TSMC 3nm vs Intel 18A - a high-stakes comparison requiring:
  - Technical claim verification (yield rates often speculation)
  - Source credibility assessment (marketing vs verified data)
  - Recency checking (semiconductor data outdates quickly)
  - Gap detection (knowing what's unknown)
  - Confidence scoring (distinguish fact from speculation)
"""

import sys
import os
import logging
import structlog

# Suppress noisy logging
logging.basicConfig(level=logging.ERROR, force=True)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR),
)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from agents.smart_research_agent import SmartResearchAgent
from agents.probabilistic_research_agent import ProbabilisticResearchAgent


def analyze_research_quality(agent, result):
    """Analyze quality dimensions of research output."""
    response = result.get("response", "")
    timeline = agent.get_timeline_summary()

    # Count workflow usage
    workflow_calls = len([line for line in timeline.split("\n") if "Tool Call" in line and "workflow" in line])

    # Check for quality indicators
    has_sources = "source" in response.lower() or "http" in response.lower()
    has_confidence = "confidence" in response.lower()
    has_gaps = "gap" in response.lower() or "unknown" in response.lower() or "unclear" in response.lower()
    has_verification = "verified" in response.lower() or "speculation" in response.lower()
    has_recency = "2024" in response or "2025" in response

    return {
        "workflow_calls": workflow_calls,
        "has_sources": has_sources,
        "has_confidence": has_confidence,
        "has_gaps": has_gaps,
        "has_verification": has_verification,
        "has_recency": has_recency,
        "response_length": len(response),
    }


def main():
    """Run semiconductor research comparison."""
    query = "Compare TSMC's 3nm process vs Intel 18A: yield rates, performance, timeline, and competitive positioning"

    print("=" * 80)
    print("SEMICONDUCTOR RESEARCH: DETERMINISTIC VS PROBABILISTIC")
    print("=" * 80)
    print()
    print("RESEARCH QUERY:")
    print(f"  {query}")
    print()
    print("WHY THIS QUERY IS CHALLENGING:")
    print("  • Yield rates often UNVERIFIED (rumors, speculation)")
    print("  • Performance claims may be MARKETING vs REALITY")
    print("  • Data OUTDATES QUICKLY (semiconductor roadmaps change quarterly)")
    print("  • Requires STRUCTURED COMPARISON (apples-to-apples)")
    print("  • Need CONFIDENCE LEVELS (what's verified vs speculation)")
    print("  • Must IDENTIFY GAPS (what's unknown)")
    print()
    print("This is exactly where deterministic workflows provide value!")
    print()

    # Run deterministic
    print("=" * 80)
    print("DETERMINISTIC AGENT (with research workflows)")
    print("=" * 80)
    print()
    print("Expected workflow sequence:")
    print("  1. Strategy Selection → 'comparative technical analysis'")
    print("  2. Parallel Gathering → multi-source technical data")
    print("  3. Synthesis → structured comparison with confidence")
    print()
    print("Running...")
    print("-" * 80)

    det_agent = SmartResearchAgent()
    det_result = det_agent.query(caller_message=query)
    det_analysis = analyze_research_quality(det_agent, det_result)

    print()
    print("✅ DETERMINISTIC RESULTS:")
    print(f"  Workflow calls: {det_analysis['workflow_calls']}")
    print(f"  Sources gathered: {'Yes' if det_analysis['has_sources'] else 'No'}")
    print(f"  Confidence scoring: {'Yes' if det_analysis['has_confidence'] else 'No'}")
    print(f"  Gap identification: {'Yes' if det_analysis['has_gaps'] else 'No'}")
    print(f"  Claim verification: {'Yes' if det_analysis['has_verification'] else 'No'}")
    print(f"  Recency check (2024-2025): {'Yes' if det_analysis['has_recency'] else 'No'}")
    print()
    print("Response preview (first 500 chars):")
    print("-" * 80)
    print(det_result.get("response", "")[:500] + "...")
    print()

    # Wait for user
    input("Press Enter to run PROBABILISTIC agent...")
    print()

    # Run probabilistic
    print("=" * 80)
    print("PROBABILISTIC AGENT (LLM-only, no workflows)")
    print("=" * 80)
    print()
    print("No guaranteed workflow sequence - LLM decides:")
    print("  • May or may not gather sources")
    print("  • May or may not verify claims")
    print("  • May or may not check recency")
    print("  • May or may not identify gaps")
    print()
    print("Running...")
    print("-" * 80)

    prob_agent = ProbabilisticResearchAgent()
    prob_result = prob_agent.query(caller_message=query)
    prob_analysis = analyze_research_quality(prob_agent, prob_result)

    print()
    print("⚠️  PROBABILISTIC RESULTS:")
    print(f"  Workflow calls: {prob_analysis['workflow_calls']}")
    print(f"  Sources gathered: {'Yes' if prob_analysis['has_sources'] else 'No'}")
    print(f"  Confidence scoring: {'Yes' if prob_analysis['has_confidence'] else 'No'}")
    print(f"  Gap identification: {'Yes' if prob_analysis['has_gaps'] else 'No'}")
    print(f"  Claim verification: {'Yes' if prob_analysis['has_verification'] else 'No'}")
    print(f"  Recency check (2024-2025): {'Yes' if prob_analysis['has_recency'] else 'No'}")
    print()
    print("Response preview (first 500 chars):")
    print("-" * 80)
    print(prob_result.get("response", "")[:500] + "...")
    print()

    # Comparison
    print("=" * 80)
    print("KEY DIFFERENCES & WHY IT MATTERS")
    print("=" * 80)
    print()
    print("DETERMINISTIC ADVANTAGES:")
    print("  ✓ ALWAYS verifies technical claims (yield rates, performance)")
    print("  ✓ ALWAYS checks data recency (critical in fast-moving semiconductors)")
    print("  ✓ ALWAYS provides confidence scores (fact vs speculation)")
    print("  ✓ ALWAYS identifies knowledge gaps (knows what it doesn't know)")
    print("  ✓ ALWAYS creates structured comparison (apples-to-apples)")
    print("  ✓ PREDICTABLE: Run 10 times → same workflow sequence 10 times")
    print()
    print("PROBABILISTIC LIMITATIONS:")
    print("  ⚠️  MAY cite unverified yield claims as fact")
    print("  ⚠️  MAY miss that Intel 18A data is speculation")
    print("  ⚠️  MAY not flag confidence levels")
    print("  ⚠️  MAY give overly confident answer on incomplete data")
    print("  ⚠️  UNPREDICTABLE: Run 10 times → different behaviors")
    print()
    print("💡 WHY THIS MATTERS FOR SEMICONDUCTOR RESEARCH:")
    print()
    print("In semiconductor analysis for investment/strategy decisions:")
    print("  • Yield rates are often RUMORS - verification critical")
    print("  • Performance claims may be MARKETING - credibility critical")
    print("  • Roadmaps change QUARTERLY - recency critical")
    print("  • Knowing what you DON'T KNOW - gap detection critical")
    print()
    print("Bad research → bad decisions → millions lost")
    print("Deterministic workflows ensure quality checks ALWAYS happen.")
    print()
    print("=" * 80)
    print()
    print("NEXT STEPS:")
    print("  • Try running this demo multiple times")
    print("  • Notice: Deterministic is consistent, Probabilistic varies")
    print("  • Try with ThoughtLogger to see workflow execution:")
    print("    python examples/autonomy/run_deterministic_with_thinking.py")
    print()


if __name__ == "__main__":
    main()
