"""
CoordinatorAgent - Orchestrates the fraud detection pipeline.

This agent is forced via system prompt to always call the FraudDetectionWorkflow
for orchestrating the sequential execution of the 3 specialist agents.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.core.agent.star_agent import STARAgent
from dana.common.protocols import Notifiable, DictParams
from workflows.fraud_detection_workflow import FraudDetectionWorkflow
from agents.deep_extractor_agent import DeepExtractorAgent
from agents.field_normalizer_agent import FieldNormalizerAgent
from agents.fraud_indicator_agent import FraudIndicatorAgent


class BroadcastNotificationHandler(Notifiable):
    """Notification handler that prints all broadcast messages."""

    def __init__(self, agent_name: str = "CoordinatorAgent", verbose: bool = True):
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


class CoordinatorAgent(STARAgent):
    """
    Agent that orchestrates the fraud detection pipeline.

    This agent is configured to ALWAYS call the FraudDetectionWorkflow
    for coordinating the sequential execution of:
    1. DeepExtractor: PDF/Image → Text
    2. FieldNormalizer: Text → JSON
    3. FraudIndicator: JSON → Fraud Result

    The system prompt enforces this behavior.
    """

    def __init__(self, agent_id: str | None = None, llm_provider: str = "openai", model: str = "gpt-4.1-mini", **kwargs):
        """
        Initialize the CoordinatorAgent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        super().__init__(
            agent_type="fraud-coordinator", agent_id=agent_id or "fraud-coordinator-001", llm_provider=llm_provider, model=model, **kwargs
        )

        # Initialize the specialist agents
        self.deep_extractor = DeepExtractorAgent(agent_id="deep-extractor-001", llm_provider=llm_provider, model=model)

        self.field_normalizer = FieldNormalizerAgent(agent_id="field-normalizer-001", llm_provider=llm_provider, model=model)

        self.fraud_indicator = FraudIndicatorAgent(agent_id="fraud-indicator-001", llm_provider=llm_provider, model=model)

        # Initialize the workflow with agent references
        self.fraud_detection_workflow = FraudDetectionWorkflow(
            workflow_id="fraud-detection-pipeline",
            deep_extractor_agent=self.deep_extractor,
            field_normalizer_agent=self.field_normalizer,
            fraud_indicator_agent=self.fraud_indicator,
        )

        # Register the workflow
        self.with_workflows(self.fraud_detection_workflow)

        # Add notification handler to print all broadcast messages
        self.notification_handler = BroadcastNotificationHandler("CoordinatorAgent")
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
    coordinator = CoordinatorAgent()

    # Enable notifications to see all broadcast messages
    coordinator.enable_notifications(verbose=True)

    print("🚀 Starting fraud detection with notification monitoring...")
    print(f"📊 Initial notification count: {coordinator.get_notification_count()}")

    # Run the fraud detection
    result = coordinator.converse(
        initial_message="Analyze this document for fraud: examples/agents/fraud-detection/data/sample_document.pdf"
    )

    print("\n✅ Fraud detection completed!")
    print(f"📊 Total notifications received: {coordinator.get_notification_count()}")
    print(f"📋 Final result: {result}")
