#!/usr/bin/env python3
"""
(B) PROBABILISTIC AUTONOMY Demo - Agent decides, but workflows might be incomplete

This demonstrates probabilistic autonomy:
- Agent (LLM) makes decisions about what to do
- BUT: Agent might skip important steps
- BUT: Workflows might not guarantee completeness
- Risk of incomplete analysis

Use when: You want flexibility but can accept incomplete results.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dana.core.agent.star_agent import STARAgent
from workflows.yield_pareto_workflow import YieldParetoWorkflow
from workflows.failure_correlation_workflow import FailureCorrelationWorkflow
from workflows.roi_prioritization_workflow import ROIPrioritizationWorkflow


class ProbabilisticAutonomyAgent(STARAgent):
    """
    Agent with probabilistic autonomy.

    Makes decisions about what to analyze, but might skip steps
    or make choices that lead to incomplete analysis.
    """

    def __init__(self):
        super().__init__(
            agent_type="yield_analysis",
            agent_id="probabilistic-agent"
        )

        # Agent has access to workflows but makes probabilistic decisions
        self.pareto_wf = YieldParetoWorkflow()
        self.correlation_wf = FailureCorrelationWorkflow()
        self.roi_wf = ROIPrioritizationWorkflow()

    def analyze_wafer(self, wafer_id: str):
        """
        Agent decides what analysis to do, but decisions are probabilistic.
        Might skip important steps based on initial assessment.
        """

        print("\n" + "=" * 80)
        print("AGENT REASONING: What should I do first?")
        print("=" * 80)
        print(f"\nAnalyzing wafer {wafer_id}...")
        print("I should probably run Pareto analysis to see the failure distribution.")

        # Always run Pareto (agent decides)
        print("\n→ Agent decision: Run Pareto workflow")
        pareto_exec_result = self.pareto_wf.execute(wafer_id=wafer_id)

        pareto_result = pareto_exec_result.get("result", {})

        if not pareto_result.get("success"):
            print("❌ Pareto failed, stopping analysis")
            return

        pareto_data = pareto_result["pareto_analysis"]
        top_bins = pareto_data["pareto_bins"]
        classifications = pareto_result.get("pattern_classifications", {})

        print(f"\n✓ Pareto complete: {len(top_bins)} top bins")
        print(f"  Yield: {pareto_data['yield_percent']:.1f}%")

        # PROBABILISTIC DECISION: Agent might skip correlation!
        print("\n" + "=" * 80)
        print("AGENT REASONING: Should I run correlation analysis?")
        print("=" * 80)

        # Simulate agent reasoning (probabilistic)
        has_systematic = classifications.get("has_systematic_patterns", False)

        if not has_systematic:
            print("\nAgent reasoning: Hmm, patterns look random...")
            print("→ Agent decision: SKIP correlation analysis (probably not needed)")
            print("  ⚠️  RISK: Might be missing important historical context!")
            correlation_data = None
        else:
            print("\nAgent reasoning: I see systematic patterns...")
            print("→ Agent decision: Run correlation workflow")
            correlation_exec_result = self.correlation_wf.execute(
                product=pareto_data["product"],
                top_bins=top_bins,
                weeks=12
            )
            correlation_result = correlation_exec_result.get("result", {})
            correlation_data = correlation_result.get("correlation_findings")
            print(f"✓ Correlation complete")

        # PROBABILISTIC DECISION: Agent decides on ROI
        print("\n" + "=" * 80)
        print("AGENT REASONING: Should I calculate ROI?")
        print("=" * 80)

        if len(top_bins) > 3:
            print("\nAgent reasoning: Many failure bins, ROI analysis makes sense")
            print("→ Agent decision: Run ROI workflow")
            roi_exec_result = self.roi_wf.execute(
                top_bins=top_bins,
                product_context={
                    "average_selling_price_usd": 150,
                    "monthly_volume_wafers": 10000,
                }
            )
            roi_result = roi_exec_result.get("result", {})
            actions = roi_result.get("prioritized_actions", [])
            total_opportunity = roi_result.get("total_opportunity_usd", 0)
            print(f"✓ ROI complete: ${total_opportunity:,.0f}/year opportunity")
        else:
            print("\nAgent reasoning: Only a few bins, ROI seems obvious...")
            print("→ Agent decision: SKIP ROI calculation (just fix the top bin)")
            print("  ⚠️  RISK: Might be prioritizing wrong bin without ROI analysis!")
            actions = None
            total_opportunity = None

        # Generate report (might be incomplete)
        print("\n" + "=" * 80)
        print("FINAL REPORT (Based on agent's decisions)")
        print("=" * 80)
        print(f"\nWafer: {wafer_id}")
        print(f"Yield: {pareto_data['yield_percent']:.1f}%")
        print(f"Top failure bins: {len(top_bins)}")

        if correlation_data:
            hypotheses = correlation_data.get("root_cause_hypotheses", [])
            print(f"Root cause hypotheses: {len(hypotheses)}")
        else:
            print("Root cause analysis: SKIPPED ⚠️")

        if actions:
            print(f"Prioritized actions: {len(actions)}")
            print(f"Revenue opportunity: ${total_opportunity:,.0f}/year")
            print(f"\nTop recommendation: {actions[0]['bin_id']} - {actions[0]['description']}")
        else:
            print("ROI prioritization: SKIPPED ⚠️")
            print(f"\nSimple recommendation: Fix {top_bins[0]['bin_id']} (highest count)")


def run_probabilistic_autonomy_demo(wafer_id: str = "W12345"):
    """Run probabilistic autonomy demo."""

    print("=" * 80)
    print("(B) PROBABILISTIC AUTONOMY DEMO - Agent Decides, Might Skip Steps")
    print("=" * 80)
    print("\nTask: Analyze yield failures for wafer", wafer_id)
    print("\nApproach: Agent makes decisions, but might skip important steps")
    print("  - Agent decides what workflows to run")
    print("  - BUT: Decisions are probabilistic, might skip important analysis")
    print("  - Risk: Incomplete or sub-optimal results")

    agent = ProbabilisticAutonomyAgent()
    agent.analyze_wafer(wafer_id)

    print("\n" + "=" * 80)
    print("PROBABILISTIC AUTONOMY DEMO COMPLETE")
    print("=" * 80)
    print("\nCharacteristics:")
    print("  ✓ Intelligent - agent makes decisions")
    print("  ✓ Flexible - adapts to data")
    print("  ✗ Might skip important steps")
    print("  ✗ Results might be incomplete")
    print("  ✗ Hard to guarantee quality")


if __name__ == "__main__":
    wafer_id = sys.argv[1] if len(sys.argv) > 1 else "W12345"
    run_probabilistic_autonomy_demo(wafer_id)
