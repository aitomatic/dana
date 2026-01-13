#!/usr/bin/env python3
"""
(C) DETERMINISTIC AUTONOMY Demo - Agent decides workflows, workflows guarantee completeness

This demonstrates deterministic autonomy (STRONGEST):
- Agent (LLM) decides which workflows to run
- Workflows execute deterministically (ALL steps, guaranteed)
- Workflows use WorkflowStepAgent for intelligence at decision points
- Agent gets complete, reliable data to make next decision

Use when: You need both intelligence AND systematic quality assurance.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dana.core.agent.star_agent import STARAgent
from workflows.yield_pareto_workflow import YieldParetoWorkflow
from workflows.failure_correlation_workflow import FailureCorrelationWorkflow
from workflows.roi_prioritization_workflow import ROIPrioritizationWorkflow


class DeterministicAutonomyAgent(STARAgent):
    """
    Agent with deterministic autonomy - STRONGEST pattern.

    - Agent decides which workflows to run (autonomous, goal-directed)
    - Workflows execute ALL steps deterministically (can't skip)
    - Workflows use WorkflowStepAgent for intelligence
    - Agent gets complete, structured data to make next decision
    """

    def __init__(self):
        super().__init__(agent_type="yield_analysis", agent_id="deterministic-agent")

        # Agent has access to complete, deterministic workflows
        self.pareto_wf = YieldParetoWorkflow()
        self.correlation_wf = FailureCorrelationWorkflow()
        self.roi_wf = ROIPrioritizationWorkflow()

    def analyze_wafer(self, wafer_id: str):
        """
        Agent decides what workflows to run, but workflows guarantee completeness.

        Key: Agent makes intelligent decisions, workflows ensure systematic quality.
        """

        print("\n" + "=" * 80)
        print("AGENT REASONING: What workflow should I run first?")
        print("=" * 80)
        print(f"\nTask: Analyze yield failures for wafer {wafer_id}")
        print("\nAgent decision: I need to understand failure distribution first.")
        print("→ Running Pareto workflow (deterministic - ALL steps executed)")

        # Agent decides to run Pareto
        pareto_exec_result = self.pareto_wf.execute(wafer_id=wafer_id)

        pareto_result = pareto_exec_result.get("result", {})

        if not pareto_result.get("success"):
            print("❌ Pareto workflow failed")
            return

        pareto_data = pareto_result["pareto_analysis"]
        top_bins = pareto_data["pareto_bins"]
        classifications = pareto_result.get("pattern_classifications", {})

        print("\n✓ Pareto workflow complete (all steps executed)")
        print(f"  - Data collected: {pareto_data['total_dies']} dies")
        print(f"  - Bins sorted: {len(pareto_data['all_bins_sorted'])} bins")
        print(f"  - Pareto calculated: {len(top_bins)} top bins (80% rule)")
        print(f"  - Patterns classified: {len(classifications.get('classifications', {}))} bins analyzed")
        print(f"  - Yield: {pareto_data['yield_percent']:.1f}%")

        # Agent reviews COMPLETE data and decides next step
        print("\n" + "=" * 80)
        print("AGENT REASONING: Based on complete Pareto data, what next?")
        print("=" * 80)

        has_systematic = classifications.get("has_systematic_patterns", False)

        print("\nAgent reviews structured data:")
        print(f"  - Systematic patterns detected: {has_systematic}")
        print(f"  - Top bins: {len(top_bins)}")

        print("\nAgent decision: I need historical context to understand root causes.")
        print("→ Running Correlation workflow (deterministic - ALL steps executed)")

        # Agent decides to run Correlation (workflow guarantees completeness)
        correlation_exec_result = self.correlation_wf.execute(product=pareto_data["product"], top_bins=top_bins, weeks=12)

        correlation_result = correlation_exec_result.get("result", {})
        if not correlation_result.get("success"):
            print("❌ Correlation workflow failed")
            return

        correlation_data = correlation_result["correlation_findings"]
        hypotheses = correlation_data["root_cause_hypotheses"]

        print("\n✓ Correlation workflow complete (all steps executed)")
        print(f"  - Historical data retrieved: {correlation_data['yield_trend']['current_yield']:.1f}% yield")
        print(f"  - Similar cases found: {len(correlation_data.get('similar_cases', []))}")
        print(f"  - Process correlations analyzed: {correlation_data.get('process_correlations', {}).get('correlations_found', False)}")
        print(f"  - Hypotheses generated: {len(hypotheses)}")

        # Agent reviews COMPLETE correlation data and decides next step
        print("\n" + "=" * 80)
        print("AGENT REASONING: Based on complete correlation data, what next?")
        print("=" * 80)

        print("\nAgent reviews structured data:")
        print(f"  - Root cause hypotheses: {len(hypotheses)}")
        print(f"  - Top hypothesis confidence: {hypotheses[0]['confidence'] if hypotheses else 'N/A'}")

        print("\nAgent decision: I have root causes. Now I need to prioritize by ROI.")
        print("→ Running ROI workflow (deterministic - ALL steps executed)")

        # Agent decides to run ROI (workflow guarantees completeness)
        roi_exec_result = self.roi_wf.execute(
            top_bins=top_bins,
            product_context={
                "average_selling_price_usd": 150,
                "monthly_volume_wafers": 10000,
            },
        )

        roi_result = roi_exec_result.get("result", {})

        if not roi_result.get("success"):
            print("❌ ROI workflow failed")
            return

        actions = roi_result["prioritized_actions"]
        total_opportunity = roi_result["total_opportunity_usd"]

        print("\n✓ ROI workflow complete (all steps executed)")
        print(f"  - Revenue impact calculated: All {len(top_bins)} bins")
        print(f"  - Fix difficulty assessed: All {len(top_bins)} bins")
        print("  - ROI scores calculated: Systematic formula")
        print(f"  - Actions ranked: {len(actions)} prioritized")
        print("  - Recommendations generated: Specific action plans")
        print(f"  - Total opportunity: ${total_opportunity:,.0f}/year")

        # Agent generates final comprehensive report
        print("\n" + "=" * 80)
        print("AGENT FINAL SYNTHESIS: Complete analysis with all data points")
        print("=" * 80)

        print(f"\nWafer: {wafer_id}")
        print(f"Product: {pareto_data['product']}")
        print(f"Current Yield: {pareto_data['yield_percent']:.1f}%")
        print("\nFailure Analysis:")
        print(f"  - Total failures: {pareto_data['total_failures']}")
        print(f"  - Pareto bins (80% rule): {len(top_bins)}")
        print(f"  - Systematic patterns: {has_systematic}")

        print("\nRoot Cause Analysis:")
        print(f"  - Historical similar cases: {len(correlation_data.get('similar_cases', []))}")
        print(f"  - Process correlations: {correlation_data.get('process_correlations', {}).get('correlations_found', False)}")
        print(f"  - Root cause hypotheses: {len(hypotheses)}")
        if hypotheses:
            print(f"  - Top hypothesis: {hypotheses[0]['hypothesis']}")
            print(f"    Confidence: {hypotheses[0]['confidence']}")

        print("\nROI Prioritization:")
        print(f"  - Total opportunity: ${total_opportunity:,.0f}/year")
        print(f"  - Top priority: {actions[0]['bin_id']} - {actions[0]['description']}")
        print(f"    ROI Score: {actions[0]['roi_score']:,.0f}")
        print(f"    Revenue Impact: ${actions[0]['revenue_impact_usd']:,.0f}/year")
        print(f"    Fix Difficulty: {actions[0]['fix_difficulty']}")
        print(f"    Timeline: {actions[0]['estimated_timeline']}")

        print("\n  Recommended Actions:")
        for i, action in enumerate(actions[0]["recommended_actions"][:3], 1):
            print(f"    {i}. {action}")

        print("\nAgent Confidence: HIGH - All workflows completed systematically")


def run_deterministic_autonomy_demo(wafer_id: str = "W12345"):
    """Run deterministic autonomy demo."""

    print("=" * 80)
    print("(C) DETERMINISTIC AUTONOMY DEMO - Agent Decides, Workflows Guarantee Completeness")
    print("=" * 80)
    print("\nTask: Analyze yield failures for wafer", wafer_id)
    print("\nApproach: STRONGEST - Agent intelligence + Systematic quality")
    print("  - Agent (LLM) decides which workflows to run")
    print("  - Workflows execute ALL steps deterministically (can't skip)")
    print("  - Workflows use WorkflowStepAgent for intelligence")
    print("  - Agent gets complete, structured data for next decision")

    agent = DeterministicAutonomyAgent()
    agent.analyze_wafer(wafer_id)

    print("\n" + "=" * 80)
    print("DETERMINISTIC AUTONOMY DEMO COMPLETE")
    print("=" * 80)
    print("\nCharacteristics:")
    print("  ✓ Intelligent - agent makes decisions")
    print("  ✓ Flexible - adapts to data")
    print("  ✓ Complete - workflows guarantee all steps executed")
    print("  ✓ Systematic - structured, reliable results")
    print("  ✓ STRONGEST - Combines intelligence with quality assurance")


if __name__ == "__main__":
    wafer_id = sys.argv[1] if len(sys.argv) > 1 else "W12345"
    run_deterministic_autonomy_demo(wafer_id)
