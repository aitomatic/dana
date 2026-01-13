"""
FinancialAnalysisAgent - Agent with complete file operation capabilities.

This agent demonstrates the use of all file operation resources:
- ReadFileResource: Read files with line range support
- RipgrepSearchResource: Fast text search across files
- EditFileResource: Edit files with search-replace or full replacement
- CreateFileResource: Create new files with optional content
- ListDirResource: List directory contents with filtering
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from dana.common.protocols import Notifiable, DictParams
from resources.semantic_search_resource import SemanticSearchResource


class BroadcastNotificationHandler(Notifiable):
    """Notification handler that prints all broadcast messages."""

    def __init__(self, agent_name: str = "FinancialAnalysisAgent", verbose: bool = True):
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


class FinancialAnalysisAgent(STARAgent):
    """
    Agent specialized in file operations.

    This agent has access to five file operation resources:
    1. ReadFileResource - Read files with line ranges and size limits
    2. RipgrepSearchResource - Fast text search using ripgrep or Python fallback
    3. EditFileResource - Edit files using search-replace or full replacement
    4. CreateFileResource - Create new files with optional initial content
    5. ListDirResource - List directory contents with filtering

    The agent can perform complex file operation workflows like:
    - Creating project scaffolding
    - Reading and analyzing code
    - Searching for patterns across multiple files
    - Making targeted edits to existing files
    - Exploring directory structures
    """

    def __init__(
        self,
        agent_id: str | None = None,
        workspace_root: str | None = None,
        llm_provider: str = "openai",
        model: str = "gpt-4.1-nano",
        **kwargs,
    ):
        """
        Initialize the FinancialAnalysisAgent.

        Args:
            agent_id: Unique identifier for this agent
            workspace_root: Root directory for file operations (defaults to cwd)
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="financial-analysis",
            agent_id=agent_id or "financial-analysis-001",
            llm_provider=llm_provider,
            model=model,
            **kwargs,
        )
        self._resources = []

        # Register all file operation resources
        self.workspace_root = workspace_root
        self.with_resources(
            # ReadFileResource(resource_id="read-file", workspace_root=workspace_root),
            # RipgrepSearchResource(resource_id="ripgrep-search", workspace_root=workspace_root),
            # EditFileResource(resource_id="edit-file", workspace_root=workspace_root, auto_save=True),
            # CreateFileResource(resource_id="create-file", workspace_root=workspace_root),
            # ListDirResource(resource_id="list-dir", workspace_root=workspace_root),
            SemanticSearchResource(resource_id="semantic-search", workspace_root=os.path.join(os.path.dirname(__file__), "..", "data")),
        )

        # Add notification handler
        self.notification_handler = BroadcastNotificationHandler("FinancialAnalysisAgent")
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
    Demo usage of FinancialAnalysisAgent.
    
    This demonstrates the agent's ability to use all four file operation resources
    in a coordinated workflow.
    """
    from pathlib import Path

    print("=" * 80)
    print("FinancialAnalysisAgent Demo")
    print("=" * 80)
    print()

    # Initialize the agent
    print("🤖 Initializing FinancialAnalysisAgent with all file operation resources...")
    agent = FinancialAnalysisAgent(workspace_root=str(Path.cwd()), model="gpt-4.1-mini")

    # Disable notifications for cleaner output in demo
    agent.enable_notifications(verbose=False)

    # agent.converse(input("Agent: Hello, what can I help you with?\n\nYou: "))

    agent.converse("Based on `examples/agents/financial-analysis/data` analyze AMD")
