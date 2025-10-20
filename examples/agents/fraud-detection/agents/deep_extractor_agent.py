"""
DeepExtractorAgent - Extracts text from PDF and image files.

This agent is forced via system prompt to always call the DeepExtractionResource
for text extraction from documents.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from dana.common.protocols import Notifiable, DictParams
from resources.deep_extraction_resource import DeepExtractionResource


class BroadcastNotificationHandler(Notifiable):
    """Notification handler that prints all broadcast messages."""

    def __init__(self, agent_name: str = "DeepExtractorAgent", verbose: bool = True):
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

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds

        # Extract notifier information
        notifier_id = getattr(notifier, "object_id", "unknown")
        notifier_type = getattr(notifier, "agent_type", getattr(notifier, "__class__.__name__", "unknown"))

        print(f"\n{'=' * 80}")
        print(f"🔔 BROADCAST NOTIFICATION #{self.message_count} [{timestamp}]")
        print(f"📡 From: {notifier_type} (ID: {notifier_id})")
        print(f"🎯 To: {self.agent_name}")
        print(f"{'=' * 80}")

        # Print message content in a structured way
        for key, value in message.items():
            if key.startswith("trace_"):
                phase = key.replace("trace_", "").upper()
                print(f"\n📋 {phase} PHASE:")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:  # Only print non-empty values
                            print(f"   {sub_key}: {sub_value}")
                else:
                    print(f"   {value}")
            else:
                print(f"\n📝 {key.upper()}:")
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_value:  # Only print non-empty values
                            print(f"   {sub_key}: {sub_value}")
                else:
                    print(f"   {value}")

        print(f"{'=' * 80}\n")


class DeepExtractorAgent(STARAgent):
    """
    Agent specialized in extracting text from PDF and image files.

    This agent is configured to ALWAYS call the DeepExtractionResource
    for document text extraction. The system prompt enforces this behavior.
    """

    def __init__(self, agent_id: str | None = None, llm_provider: str = "openai", model: str = "gpt-4.1-mini", **kwargs):
        """
        Initialize the DeepExtractorAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="deep-extractor", agent_id=agent_id or "deep-extractor-001", llm_provider=llm_provider, model=model, **kwargs
        )

        # Register the DeepExtractionResource with LLM provider and model
        self.with_resources(DeepExtractionResource(resource_id="deep-extraction", llm_provider=llm_provider, model=model))

        # Add notification handler to print all broadcast messages
        self.notification_handler = BroadcastNotificationHandler("DeepExtractorAgent")
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
    # Test the DeepExtractorAgent with notifications
    agent = DeepExtractorAgent()

    # Enable notifications to see all broadcast messages
    agent.enable_notifications(verbose=True)

    print("🚀 Testing DeepExtractorAgent Notification System")
    print("=" * 60)
    print(f"📊 Initial notification count: {agent.get_notification_count()}")

    # Test text extraction with notification monitoring
    print("\n🔍 Starting text extraction with notification monitoring...")
    print("=" * 60)

    try:
        # Run a simple test conversation
        result = agent.converse(initial_message="Extract text from a sample document")

        print("\n" + "=" * 60)
        print("✅ Text extraction test completed!")
        print(f"📊 Total notifications received: {agent.get_notification_count()}")
        print(f"📋 Final result: {result}")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
