from dana.core.knowledge.prompts.codecs import CSXMLCodec

import sys
from pathlib import Path

sys.path.append("examples/agents/financial-analysis")

from observers.report_observers import ReportsFolderObserver
from agents.financial_analysis_agent import FinancialAnalysisAgent
from agents.financial_report_coordinator import FinancialReportCoordinatorAgent
from leaners.william_learner import WilliamLearner


SESSION_ID = "financial-report-session-002"

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

analyst.set_session_id(SESSION_ID)

analyst_learner = WilliamLearner(agent=analyst)

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
coordinator.set_session_id(SESSION_ID)
coordinator_learner = WilliamLearner(agent=coordinator)

# Disable notifications for cleaner output in demo
coordinator.enable_notifications(verbose=False)

# Start observer monitoring
reports_observer.start()

print()
print("📊 Creating a comprehensive financial health report for AMD...")
print("=" * 80)
print()


print(coordinator_learner._load_acquisitive())

# This can now learn independently from agent loop
trace_learning = coordinator_learner._reflect_episodic({})
learning_content = trace_learning.get("trace_learning", {}).get("simple_summary", "")
print(learning_content)

print("=" * 80)
print("Storing episodic learning")
print("=" * 80)
# Store episodic learning
coordinator_learner._store_episodic_learning(learning_content)
print(coordinator_learner._load_episodic())

print("=" * 80)
print("Storing feedback")
print("=" * 80)
# Store feedback
coordinator_learner.save_feedback("This is a test feedback")
print(coordinator_learner._load_feedback())

print("=" * 80)
print("Getting timeline entries")
print("=" * 80)
# Get timeline entries
timeline_entries = coordinator_learner._get_timeline_entries()
print(timeline_entries)