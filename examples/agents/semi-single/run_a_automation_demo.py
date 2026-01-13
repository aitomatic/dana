#!/usr/bin/env python3
"""
(A) AUTOMATION Demo - Fixed sequence, no intelligence

This demonstrates pure automation:
- No LLM/agent decisions
- Fixed workflow sequence
- Just deterministic orchestration
- Like a cron job or script

Use when: The process is well-defined and never changes.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from workflows.yield_pareto_workflow import YieldParetoWorkflow
from workflows.failure_correlation_workflow import FailureCorrelationWorkflow
from workflows.roi_prioritization_workflow import ROIPrioritizationWorkflow


def run_automation_demo(wafer_id: str = "W12345"):
    """
    Pure automation: Fixed sequence, no decisions.

    This is like a traditional script - just execute steps in order.
    No intelligence, no adaptation to the data.
    """

    print("=" * 80)
    print("(A) AUTOMATION DEMO - Fixed Sequence, No Intelligence")
    print("=" * 80)
    print("\nTask: Analyze yield failures for wafer", wafer_id)
    print("\nApproach: Run fixed sequence of workflows")
    print("  1. Pareto Analysis (always)")
    print("  2. Failure Correlation (always)")
    print("  3. ROI Prioritization (always)")
    print("\nNo decisions made - just execute the script.\n")

    # STEP 1: Always run Pareto (no decision)
    print("\n" + "=" * 80)
    print("STEP 1: Running Pareto Analysis (fixed step)")
    print("=" * 80)
    pareto_wf = YieldParetoWorkflow()
    pareto_exec_result = pareto_wf.execute(wafer_id=wafer_id)
    pareto_result = pareto_exec_result.get("result", {})

    if not pareto_result.get("success"):
        print("❌ Pareto analysis failed:", pareto_result.get("error"))
        return

    pareto_data = pareto_result["pareto_analysis"]
    top_bins = pareto_data["pareto_bins"]

    print(f"\n✓ Pareto complete: {len(top_bins)} top bins identified")
    print(f"  Total failures: {pareto_data['total_failures']}")
    print(f"  Yield: {pareto_data['yield_percent']:.1f}%")

    # STEP 2: Always run Correlation (no decision)
    print("\n" + "=" * 80)
    print("STEP 2: Running Failure Correlation (fixed step)")
    print("=" * 80)
    correlation_wf = FailureCorrelationWorkflow()
    correlation_exec_result = correlation_wf.execute(product=pareto_data["product"], top_bins=top_bins, weeks=12)
    correlation_result = correlation_exec_result.get("result", {})

    if not correlation_result.get("success"):
        print("❌ Correlation analysis failed:", correlation_result.get("error"))
        return

    correlation_data = correlation_result["correlation_findings"]
    hypotheses = correlation_data["root_cause_hypotheses"]

    print(f"\n✓ Correlation complete: {len(hypotheses)} hypotheses generated")

    # STEP 3: Always run ROI (no decision)
    print("\n" + "=" * 80)
    print("STEP 3: Running ROI Prioritization (fixed step)")
    print("=" * 80)
    roi_wf = ROIPrioritizationWorkflow()
    roi_exec_result = roi_wf.execute(
        top_bins=top_bins,
        product_context={
            "average_selling_price_usd": 150,
            "monthly_volume_wafers": 10000,
        },
    )
    roi_result = roi_exec_result.get("result", {})

    if not roi_result.get("success"):
        print("❌ ROI prioritization failed:", roi_result.get("error"))
        return

    actions = roi_result["prioritized_actions"]
    total_opportunity = roi_result["total_opportunity_usd"]

    print(f"\n✓ ROI complete: {len(actions)} actions prioritized")
    print(f"  Total opportunity: ${total_opportunity:,.0f}/year")

    # Final Report (no intelligence, just print data)
    print("\n" + "=" * 80)
    print("FINAL REPORT (Fixed Format)")
    print("=" * 80)
    print(f"\nWafer: {wafer_id}")
    print(f"Yield: {pareto_data['yield_percent']:.1f}%")
    print(f"Top failure bins: {len(top_bins)}")
    print(f"Root cause hypotheses: {len(hypotheses)}")
    print(f"Revenue opportunity: ${total_opportunity:,.0f}/year")
    print(f"\nTop action: {actions[0]['bin_id']} - {actions[0]['description']}")
    print(f"  ROI Score: {actions[0]['roi_score']:,.0f}")
    print(f"  Difficulty: {actions[0]['fix_difficulty']}")

    print("\n" + "=" * 80)
    print("AUTOMATION DEMO COMPLETE")
    print("=" * 80)
    print("\nCharacteristics:")
    print("  ✓ Fast and predictable")
    print("  ✓ Always runs the same steps")
    print("  ✗ No adaptation to data")
    print("  ✗ No intelligence or reasoning")
    print("  ✗ Might run unnecessary steps or miss important insights")


if __name__ == "__main__":
    wafer_id = sys.argv[1] if len(sys.argv) > 1 else "W12345"
    run_automation_demo(wafer_id)
