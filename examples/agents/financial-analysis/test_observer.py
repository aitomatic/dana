import sys
from pathlib import Path

sys.path.append("examples/agents/financial-analysis")

from agents.financial_analysis_agent import FinancialAnalysisAgent
from agents.financial_report_coordinator import FinancialReportCoordinatorAgent
from observers.report_observers import ReportsFolderObserver
from leaners.william_learner import WilliamLearner

SESSION_ID = "financial-report-session-002"


print("=" * 80)
print("FinancialReportCoordinatorAgent Demo with Observer")
print("=" * 80)
print()

# Get the current directory (agents/)
current_dir = Path("examples/agents/financial-analysis")

# Create observer for reports folder
reports_folder = current_dir / "reports"
reports_observer = ReportsFolderObserver(reports_folder)

# Initialize the financial analysis agent with observer
print("🤖 Initializing FinancialAnalysisAgent with observer...")
analyst = FinancialAnalysisAgent(
    agent_id="financial-analysis-001",
    workspace_root=str(current_dir / "data"),
    model="gpt-4.1-mini",
    max_context_tokens=40000,
    # codec=CSXMLCodec,
    observer=reports_observer,  # Add observer
)
analyst.enable_notifications(verbose=False)
analyst._learner = WilliamLearner(agent=analyst)


# Initialize the coordinator agent with the analyst and observer
print("🤖 Initializing FinancialReportCoordinatorAgent with observer...")
coordinator = FinancialReportCoordinatorAgent(
    agent_id="coordinator-001",
    workspace_root=str(current_dir),
    financial_analysis_agent=analyst,
    model="gpt-4.1-mini",
    # codec=CSXMLCodec,
    max_context_tokens=40000,
    observer=reports_observer,  # Add observer
)

# Disable notifications for cleaner output in demo
coordinator.enable_notifications(verbose=False)
coordinator._learner = WilliamLearner(agent=coordinator)

# Start observer monitoring
reports_observer.start()

print()
print("📊 Creating a comprehensive financial health report for AMD...")
print("=" * 80)
print()

# Execute report generation with session_id
result = coordinator.converse(
    session_id=SESSION_ID,
    initial_message="Create a comprehensive financial health report for AMD based on the data in the data directory. "
    "The report should include liquidity analysis, profitability analysis, leverage analysis, and efficiency analysis.",
)

# Observe final state
final_observation = reports_observer.observe()
print()
print("=" * 80)
print("✅ Report generation complete!")
print(f"Reports are saved in: {current_dir / 'reports'}")
print()
print("📊 Final Reports Folder State:")
print(f"  Folder: {final_observation['folder_path']}")
print(f"  Files: {final_observation['file_count']}")
print(f"  Total Size: {final_observation['total_size_kb']} KB ({final_observation['total_size_mb']} MB)")
print()
if final_observation["files"]:
    print("  Files:")
    for file_info in final_observation["files"]:
        print(f"    - {file_info['path']}: {file_info['size_kb']} KB")
print("=" * 80)


# Stop observer monitoring
reports_observer.stop()
