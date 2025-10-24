"""
PhotoresistChemist - Agent specialized in photoresist chemistry and materials science.

This agent demonstrates the use of structured data resources for semiconductor chemistry:
- RecipeDataResource: Access photoresist formulation data from CSV files
- PolymerDataResource: Query polymer composition and monomer breakdowns from Excel
- MonomerDataResource: Analyze chemical properties and molecular characteristics

The agent can perform complex photoresist analysis workflows like:
- Hierarchical chemical composition analysis
- Root cause analysis of performance issues
- Molecular weight impact analysis
- Component compatibility assessment
- Formulation optimization
- Chemical property analysis
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from dana.common.protocols import Notifiable, DictParams
from resources.recipe_data_resource import RecipeDataResource
from resources.polymer_data_resource import PolymerDataResource
from resources.monomer_data_resource import MonomerDataResource


class BroadcastNotificationHandler(Notifiable):
    """Notification handler that prints all broadcast messages."""

    def __init__(self, agent_name: str = "PhotoresistChemist", verbose: bool = True):
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


class PhotoresistChemist(STARAgent):
    """
    Agent specialized in photoresist chemistry and materials science.

    This agent has access to three structured data resources:
    1. RecipeDataResource - Access photoresist formulation data from CSV files
    2. PolymerDataResource - Query polymer composition and monomer breakdowns from Excel
    3. MonomerDataResource - Analyze chemical properties and molecular characteristics

    The agent can perform complex photoresist analysis workflows like:
    - Hierarchical chemical composition analysis (4-level decomposition)
    - Root cause analysis of performance issues and defects
    - Molecular weight impact analysis and film formation studies
    - Component compatibility assessment and failure mode analysis
    - Formulation optimization and process improvement
    - Chemical property analysis and structure-property relationships
    - Evidence-based problem diagnosis and resolution recommendations
    """

    def __init__(
        self,
        agent_id: str | None = None,
        data_root: str | None = None,
        llm_provider: str = "openai",
        model: str = "gpt-4.1-nano",
        **kwargs,
    ):
        """
        Initialize the PhotoresistChemist.

        Args:
            agent_id: Unique identifier for this agent
            data_root: Root directory for data files (defaults to resources directory)
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="photoresist-chemist",
            agent_id=agent_id or "photoresist-chemist-001",
            llm_provider=llm_provider,
            model=model,
            **kwargs,
        )

        # Set up data paths
        if data_root is None:
            current_dir = Path(__file__).parent
            data_root = current_dir.parent / "resources"

        self.data_root = Path(data_root)

        # Register all structured data resources
        self.with_resources(
            RecipeDataResource(
                resource_id="recipe-data",
                data_path=str(self.data_root / "Recipe_example_data.csv")
            ),
            PolymerDataResource(
                resource_id="polymer-data",
                data_path=str(self.data_root / "Polymer_example_data.xlsx")
            ),
            MonomerDataResource(
                resource_id="monomer-data",
                data_path=str(self.data_root / "Monomer_example_data.xlsx")
            ),
        )

        # Add notification handler
        self.notification_handler = BroadcastNotificationHandler("PhotoresistChemist")
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
    Demo usage of PhotoresistChemist.

    This demonstrates the agent's ability to perform comprehensive photoresist analysis
    using structured data resources.
    """
    print("=" * 80)
    print("PhotoresistChemist Demo")
    print("=" * 80)
    print()

    # Initialize the agent
    print("🤖 Initializing PhotoresistChemist with structured data resources...")
    agent = PhotoresistChemist(model="gpt-4.1-mini")

    # Disable notifications for cleaner output in demo
    agent.enable_notifications(verbose=False)

    print("\n🔬 Available analysis capabilities:")
    print("   • Comprehensive sample analysis (4-level hierarchical decomposition)")
    print("   • Root cause analysis of performance issues")
    print("   • Molecular weight impact analysis and film formation studies")
    print("   • Component compatibility assessment")
    print("   • Formulation optimization and process improvement")
    print("   • Chemical property analysis and structure-property relationships")
    print("   • Evidence-based problem diagnosis")
    print()

    # Interactive conversation
    agent.converse(input("Agent: Hello! I'm your Photoresist Chemist. What would you like me to analyze?\n\nYou: "))
