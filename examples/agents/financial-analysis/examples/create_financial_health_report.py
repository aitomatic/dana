"""
Demo script for Financial Report Coordinator Agent.

This script demonstrates how to use the FinancialReportCoordinatorAgent
to create a comprehensive financial health report by coordinating with
the FinancialAnalysisAgent.

Usage:
    python examples/create_financial_health_report.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.financial_analysis_agent import FinancialAnalysisAgent
from agents.financial_report_coordinator import FinancialReportCoordinatorAgent


def main():
    """
    Demonstrate creating a comprehensive financial health report for AMD.
    """
    print("=" * 80)
    print("Financial Report Coordinator Demo")
    print("=" * 80)
    print()
    print("This demo creates a comprehensive financial health report for AMD")
    print("by coordinating analysis tasks between the coordinator and analyst agents.")
    print()
    print("=" * 80)
    print()

    # Get the base directory (financial-analysis/)
    base_dir = Path(__file__).parent.parent

    # Setup directories
    data_dir = base_dir / "data"
    reports_dir = base_dir / "reports"

    print(f"📂 Data directory: {data_dir}")
    print(f"📂 Reports directory: {reports_dir}")
    print()

    # Step 1: Initialize FinancialAnalysisAgent
    print("Step 1: Initializing FinancialAnalysisAgent...")
    print("-" * 80)

    financial_analyst = FinancialAnalysisAgent(agent_id="financial-analysis-001", workspace_root=str(data_dir), model="gpt-4.1-mini")

    # Disable verbose notifications for cleaner demo output
    financial_analyst.enable_notifications(verbose=False)

    print("✅ FinancialAnalysisAgent initialized")
    print(f"   - Agent ID: {financial_analyst.object_id}")
    print(f"   - Agent Type: {financial_analyst.agent_type}")
    print(f"   - Resources: {len(financial_analyst.available_resources)} registered")
    print()

    # Step 2: Initialize FinancialReportCoordinatorAgent
    print("Step 2: Initializing FinancialReportCoordinatorAgent...")
    print("-" * 80)

    coordinator = FinancialReportCoordinatorAgent(
        agent_id="coordinator-001", workspace_root=str(base_dir), financial_analysis_agent=financial_analyst, model="gpt-4.1-mini"
    )

    # Enable verbose notifications to see coordination in action
    coordinator.enable_notifications(verbose=True)

    print("✅ FinancialReportCoordinatorAgent initialized")
    print(f"   - Agent ID: {coordinator.object_id}")
    print(f"   - Agent Type: {coordinator.agent_type}")
    print(f"   - Sub-agents: {len(coordinator.available_agents)} registered")
    print(f"   - Resources: {len(coordinator.available_resources)} registered")
    print()

    # Step 3: Create the financial health report
    print("Step 3: Creating Financial Health Report for AMD...")
    print("=" * 80)
    print()
    print("Requesting: Comprehensive financial health report for AMD")
    print()
    print("The coordinator will:")
    print("  1. Create a report outline structure")
    print("  2. Delegate specific analyses to FinancialAnalysisAgent")
    print("  3. Consolidate results into sections")
    print("  4. Synthesize findings into executive summary")
    print("  5. Finalize the report")
    print()
    print("=" * 80)
    print()

    # Send request to coordinator
    request_message = (
        "Create a comprehensive financial health report for AMD. "
        "The report should include:\n"
        "- Liquidity analysis (current ratio, quick ratio)\n"
        "- Profitability analysis (gross, operating, and net margins)\n"
        "- Leverage analysis (debt-to-equity ratio)\n"
        "- Efficiency analysis (asset turnover)\n"
        "- Executive summary and conclusions\n\n"
        "Use data from the data directory. Save the report in the reports directory."
    )

    try:
        result = coordinator.converse(request_message)

        print()
        print("=" * 80)
        print("✅ Report Generation Complete!")
        print("=" * 80)
        print()

        # List generated reports
        print("📄 Generated Reports:")
        print("-" * 80)
        if reports_dir.exists():
            reports = sorted(reports_dir.glob("*.md"))
            if reports:
                for report in reports:
                    size = report.stat().st_size
                    print(f"  - {report.name} ({size:,} bytes)")
            else:
                print("  No reports found (this may indicate an issue)")
        print()

        # Show statistics
        print("📊 Coordination Statistics:")
        print("-" * 80)
        print(f"  - Notifications received: {coordinator.get_notification_count()}")
        print("  - Sub-agent delegations: Multiple analysis tasks")
        print("  - Report sections: Liquidity, Profitability, Leverage, Efficiency")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ Error during report generation")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        import traceback

        traceback.print_exc()
        return 1

    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  - Review the generated report in the reports/ directory")
    print("  - Try modifying the request to create different report types")
    print("  - Experiment with different companies (if data available)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
