"""
FinancialReportCoordinatorAgent - Orchestrates comprehensive financial report creation.

This agent creates structured financial reports by:
- Analyzing user requirements and designing report structure
- Breaking down complex questions into specific analysis tasks
- Delegating analysis tasks to FinancialAnalysisAgent
- Consolidating results into coherent, professional reports

The coordinator has access to:
- FinancialAnalysisAgent: For quantitative financial analysis and data extraction
- File operation resources: For creating, editing, and managing report drafts
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from dana.common.protocols import Notifiable, DictParams
from resources.read_file_resource import ReadFileResource
from resources.edit_file_resource import EditFileResource
from resources.create_file_resource import CreateFileResource
from resources.list_dir_resource import ListDirResource
from dana.core.agent.components.prompt_engineer_lite import PromptEngineerLite


class BroadcastNotificationHandler(Notifiable):
    """Notification handler that prints all broadcast messages."""

    def __init__(self, agent_name: str = "FinancialReportCoordinator", verbose: bool = True):
        """
        Initialize the notification handler.

        Args:
            agent_name: Name of the agent for display purposes
            verbose: Whether to print notifications
        """
        self.agent_name = agent_name
        self.verbose = verbose
        self.message_count = 0

    def notify(self, notifier: object, message: DictParams) -> None:
        """
        Receive and print notification messages.

        Args:
            notifier: The object sending the notification
            message: The notification message
        """
        self.message_count += 1

        # Only print if verbose is enabled
        if not self.verbose:
            return

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Extract notifier information
        notifier_id = getattr(notifier, "object_id", "unknown")
        notifier_type = getattr(notifier, "agent_type", getattr(notifier, "__class__.__name__", "unknown"))

        print(f"\n{'=' * 80}")
        print(f"🔔 NOTIFICATION #{self.message_count} [{timestamp}]")
        print(f"📡 From: {notifier_type} (ID: {notifier_id})")
        print(f"🎯 To: {self.agent_name}")
        print(f"{'=' * 80}")

        # Print message content
        for key, value in message.items():
            if key.startswith("trace_"):
                phase = key.replace("trace_", "").upper()
                print(f"\n📋 {phase} PHASE:")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:
                            print(f"   {sub_key}: {sub_value}")
                else:
                    print(f"   {value}")
            else:
                print(f"\n📝 {key.upper()}:")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:
                            print(f"   {sub_key}: {sub_value}")
                else:
                    print(f"   {value}")

        print(f"{'=' * 80}\n")


class FinancialReportCoordinatorAgent(STARAgent):
    """
    Agent specialized in orchestrating financial report creation.

    This agent coordinates the creation of comprehensive financial reports by:
    1. Analyzing user requirements and creating report outlines
    2. Identifying specific financial analyses needed
    3. Delegating analysis tasks to FinancialAnalysisAgent
    4. Consolidating results into well-structured reports
    5. Managing report drafts through file operations

    The coordinator works with:
    - FinancialAnalysisAgent: Handles all quantitative analysis and data extraction
    - CreateFileResource: Creates new report draft files
    - EditFileResource: Updates report sections with analysis results
    - ReadFileResource: Reads current report state
    - ListDirResource: Lists existing reports

    Report Types Supported:
    - Financial Health Report: Comprehensive analysis covering liquidity, profitability,
      leverage, and efficiency metrics
    """

    def __init__(
        self,
        agent_id: str | None = None,
        workspace_root: str | None = None,
        financial_analysis_agent=None,
        llm_provider: str = "openai",
        model: str = "gpt-4.1-mini",
        **kwargs,
    ):
        """
        Initialize the FinancialReportCoordinatorAgent.

        Args:
            agent_id: Unique identifier for this agent
            workspace_root: Root directory for report files (defaults to cwd)
            financial_analysis_agent: FinancialAnalysisAgent instance for delegation
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="financial-report-coordinator",
            agent_id=agent_id or "coordinator-001",
            llm_provider=llm_provider,
            model=model,
            **kwargs,
        )

        self._prompt_engineer = PromptEngineerLite(self)

        # Store workspace root for reports
        self.workspace_root = workspace_root or str(Path.cwd())
        
        # Ensure reports directory exists
        reports_dir = Path(self.workspace_root) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Register the financial analysis agent as a sub-agent
        if financial_analysis_agent:
            self.with_agents(financial_analysis_agent)

        # Register file operation resources for report management
        self.with_resources(
            CreateFileResource(resource_id="create-file", workspace_root=workspace_root),
            EditFileResource(resource_id="edit-file", workspace_root=workspace_root, auto_save=True),
            ReadFileResource(resource_id="read-file", workspace_root=workspace_root),
            ListDirResource(resource_id="list-dir", workspace_root=workspace_root),
        )

        # Add notification handler
        self.notification_handler = BroadcastNotificationHandler("FinancialReportCoordinator")
        self.with_notifiable(self.notification_handler)

    def enable_notifications(self, verbose: bool = True) -> None:
        """
        Enable or disable notification printing.

        Args:
            verbose: Whether to print notifications
        """
        self.notification_handler.verbose = verbose

    def get_notification_count(self) -> int:
        """
        Get the total number of notifications received.

        Returns:
            Number of notifications received
        """
        return getattr(self.notification_handler, "message_count", 0)


if __name__ == "__main__":
    """
    Demo usage of FinancialReportCoordinatorAgent.
    
    This demonstrates the coordinator's ability to orchestrate report creation
    by delegating to FinancialAnalysisAgent and managing report files.
    """
    from financial_analysis_agent import FinancialAnalysisAgent

    print("=" * 80)
    print("FinancialReportCoordinatorAgent Demo")
    print("=" * 80)
    print()

    # Get the current directory (agents/)
    current_dir = Path(__file__).parent.parent
    
    # Initialize the financial analysis agent
    print("🤖 Initializing FinancialAnalysisAgent...")
    analyst = FinancialAnalysisAgent(
        agent_id="financial-analysis-001",
        workspace_root=str(current_dir / "data"),
        model="gpt-4.1-mini",
        max_context_tokens=40000
    )
    analyst.enable_notifications(verbose=False)

    # Initialize the coordinator agent with the analyst
    print("🤖 Initializing FinancialReportCoordinatorAgent...")
    coordinator = FinancialReportCoordinatorAgent(
        agent_id="coordinator-001",
        workspace_root=str(current_dir),
        financial_analysis_agent=analyst,
        model="gpt-4.1-mini"
    )

    # Disable notifications for cleaner output in demo
    coordinator.enable_notifications(verbose=False)

    print()
    print("📊 Creating a comprehensive financial health report for AMD...")
    print("=" * 80)
    print()

    # Execute report generation
    result = coordinator.converse(
        "Create a comprehensive financial health report for AMD based on the data in the data directory. "
        "The report should include liquidity analysis, profitability analysis, leverage analysis, and efficiency analysis."
    )

    print()
    print("=" * 80)
    print("✅ Report generation complete!")
    print(f"Reports are saved in: {current_dir / 'reports'}")

