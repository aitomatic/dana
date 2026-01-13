#!/usr/bin/env python3
"""
Deterministic Yield Analysis Demo

This demo shows DETERMINISTIC AUTONOMY in action:
- Systematic workflows enforce engineering methodology (can't skip steps)
- LLM intelligence applied at specific decision points
- Guaranteed comprehensive analysis (Pareto → Correlation → ROI)
- Consistent, explainable, actionable results

Contrast with:
- Automation: Rigid rules, no AI intelligence
- Probabilistic Autonomy: LLM decides everything, inconsistent

Run with:
    python demo_deterministic.py
"""

import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Load from project root
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on environment variables

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from agents.yield_pareto_analysis_agent import YieldParetoAnalysisAgent


def print_section(title: str, width: int = 80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width + "\n")


def print_executive_summary(summary: dict):
    """Print executive summary in a nice format."""
    print_section("EXECUTIVE SUMMARY")

    print(f"Wafer ID:          {summary['wafer_id']}")
    print(f"Product:           {summary['product']}")
    print(f"Current Yield:     {summary['current_yield']:.1f}%")
    print(f"Yield Trend:       {summary['yield_trend'].upper()} ({summary['yield_change_pct']:+.1f}%)")
    print(f"Total Failures:    {summary['total_failures']:,}")
    print()
    print(f"Pareto Bins:       {summary['pareto_bins_identified']} bins represent 80% of failures")
    print(f"Revenue at Risk:   ${summary['total_revenue_opportunity_usd']:,.0f} annually")
    print()
    print(f"Top Priority:      {summary['top_priority_bin']}")
    print(f"  Impact:          ${summary['top_priority_impact_usd']:,.0f}/year")
    print()
    print(f"Likely Root Cause: {summary['likely_root_cause']}")
    print(f"  Confidence:      {summary['confidence']}")


def print_pareto_bins(pareto_bins: list):
    """Print Pareto bins in a table."""
    print_section("PARETO ANALYSIS (Top Bins - 80% Rule)")

    print(f"{'Rank':<6} {'Bin ID':<12} {'Description':<30} {'Count':<8} {'%':<6} {'Cum%':<6} {'Pattern':<12}")
    print("-" * 80)

    for i, bin_info in enumerate(pareto_bins, start=1):
        print(
            f"{i:<6} "
            f"{bin_info['bin_id']:<12} "
            f"{bin_info['description'][:30]:<30} "
            f"{bin_info['count']:<8} "
            f"{bin_info['percent_of_total']:<6.1f} "
            f"{bin_info['cumulative_percent']:<6.1f} "
            f"{bin_info['spatial_pattern']:<12}"
        )


def print_root_cause_hypotheses(hypotheses: list):
    """Print root cause hypotheses."""
    print_section("ROOT CAUSE HYPOTHESES (Evidence-Based)")

    for i, hyp in enumerate(hypotheses, start=1):
        print(f"\nHypothesis #{hyp['rank']}: {hyp['hypothesis']}")
        print(f"  Confidence: {hyp['confidence']}")
        print("  Evidence:")
        for evidence in hyp.get("evidence", []):
            print(f"    • {evidence}")
        print(f"  Next Steps: {hyp.get('next_steps', 'Unknown')}")


def print_prioritized_actions(actions: list):
    """Print prioritized action plan."""
    print_section("PRIORITIZED ACTION PLAN (ROI-Ranked)")

    for action in actions[:5]:  # Top 5 priorities
        print(f"\n#{action['rank']} - {action['bin_id']}: {action['description']}")
        print(f"  Revenue Impact:  ${action['revenue_impact_usd']:,.0f}/year")
        print(f"  Fix Difficulty:  {action['fix_difficulty']}")
        print(f"  ROI Score:       {action['roi_score']:,.0f}")
        print(f"  Priority:        {action['priority_justification'][:80]}")
        if "estimated_timeline" in action:
            print(f"  Timeline:        {action['estimated_timeline']}")
        print("  Actions:")
        for rec_action in action.get("recommended_actions", [])[:3]:
            print(f"    • {rec_action}")


def main():
    """Run the deterministic yield analysis demo."""
    print_section("DETERMINISTIC YIELD ANALYSIS DEMO", 80)

    print("""
This demo demonstrates DETERMINISTIC AUTONOMY for semiconductor yield analysis.

The agent will execute three systematic workflows:
  1. Pareto Analysis     - Identify top failing bins (80/20 rule)
  2. Correlation Analysis - Connect to historical data and process changes
  3. ROI Prioritization   - Rank by revenue impact vs fix difficulty

Watch the workflow progress in real-time below...
    """)

    # ========================================
    # CHECK: Verify API key is set
    # ========================================
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ERROR: Anthropic API key not found!")
        print()
        print("This demo requires an Anthropic API key to run the LLM-powered workflows.")
        print()
        print("To fix this:")
        print("  1. Get an API key from: https://console.anthropic.com/")
        print("  2. Set it in your environment:")
        print("     export ANTHROPIC_API_KEY='your-key-here'")
        print("  3. Run the demo again")
        print()
        print("Alternatively, you can set it just for this run:")
        print("  ANTHROPIC_API_KEY='your-key-here' python demo_deterministic.py")
        print()
        return

    # ========================================
    # SETUP: Create agent
    # ========================================
    print("Setting up agent...")

    # Create agent
    agent = YieldParetoAnalysisAgent(agent_id="yield-pareto-agent", llm_provider="anthropic", model="claude-3-5-sonnet-20241022")

    print("✓ Agent ready\n")

    # ========================================
    # EXECUTE: Run deterministic analysis
    # ========================================
    print_section("EXECUTING DETERMINISTIC ANALYSIS")
    print("(Workflow progress shown below in gray...)\n")

    # Run the analysis directly via _do_execute to avoid REPL mode
    results = agent._do_execute(caller_message="Analyze yield", wafer_id=None, weeks=12)

    # ========================================
    # RESULTS: Display comprehensive output
    # ========================================
    if not results.get("success"):
        print(f"\n❌ Analysis FAILED: {results.get('error')}")
        print(f"   Phase: {results.get('phase')}")
        return

    print("\n✅ Analysis completed successfully!\n")

    # Display results
    print_executive_summary(results["executive_summary"])

    print_pareto_bins(results["pareto_analysis"]["pareto_bins"])

    correlation_findings = results["correlation_findings"]
    if correlation_findings.get("root_cause_hypotheses"):
        print_root_cause_hypotheses(correlation_findings["root_cause_hypotheses"])

    print_prioritized_actions(results["prioritized_actions"])

    # ========================================
    # VALUE DEMONSTRATION
    # ========================================
    print_section("VALUE OF DETERMINISTIC AUTONOMY")

    summary = results["executive_summary"]
    total_opportunity = summary["total_revenue_opportunity_usd"]

    print(f"""
✓ SYSTEMATIC: Executed {len(results["analysis_metadata"]["workflows_executed"])} workflows
  - Can't skip steps (engineering rigor)
  - Every bin analyzed (comprehensive)
  - Pareto, correlation, ROI always performed

✓ INTELLIGENT: LLM applied at key decision points
  - Pattern classification (systematic vs random)
  - Process correlation reasoning
  - Root cause hypothesis generation
  - Actionable recommendation synthesis

✓ ACTIONABLE: Clear prioritized plan
  - ${total_opportunity:,.0f} annual revenue opportunity identified
  - {summary["pareto_bins_identified"]} bins prioritized by ROI
  - Specific next steps with timelines
  - Evidence-based root cause hypotheses

✓ CONSISTENT: Same analysis every time
  - Deterministic workflow sequence
  - Reproducible results
  - Explainable reasoning
  - Engineer trust

Compare this to:
  × Automation: No AI intelligence, can't handle novel patterns
  × Probabilistic: Might skip steps, inconsistent analysis, hard to trust
    """)

    print_section("DEMO COMPLETE")
    print("""
This demo showed how DETERMINISTIC AUTONOMY combines:
  • Systematic engineering workflows (structure)
  • LLM intelligence (reasoning)
  → Reliable, comprehensive, actionable yield analysis

The workflows are visible, explainable, and trustworthy - perfect for
high-stakes semiconductor manufacturing where mistakes cost millions.
    """)


if __name__ == "__main__":
    main()
