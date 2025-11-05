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
coordinator._learner = WilliamLearner(agent=coordinator)
coordinator.set_session_id(SESSION_ID)
# Disable notifications for cleaner output in demo
coordinator.enable_notifications(verbose=False)

# Start observer monitoring
reports_observer.start()

print()
print("📊 Creating a comprehensive financial health report for AMD...")
print("=" * 80)
print()


# READ EVENT LOG
for event in coordinator._event_log.read_since(checkpoint=-2):
    print(event)

# READ TIMELINE
for timeline_entry in coordinator._timeline.read_since(checkpoint=-2):
    print(timeline_entry)
