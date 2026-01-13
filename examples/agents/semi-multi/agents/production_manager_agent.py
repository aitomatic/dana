"""
ProductionManagerAgent - Coordinator for defect response

This agent serves as the user-facing coordinator for novel defect investigation.
It delegates technical work to specialists and presents strategic decisions to users.

Role: Production Manager (Fab Operations)
Responsibilities:
- Receive defect alerts from user
- Assess severity and delegate to specialists
- Translate technical findings to business language
- Present options and get user approval for production-impacting actions
- Orchestrate overall defect response workflow
"""

import sys
from pathlib import Path

# Add dana_agent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "dana_agent"))

from dana.core.agent.star_agent import STARAgent
from dana.lib.resources.conversation import ConversationResource


class ProductionManagerAgent(STARAgent):
    """
    Production Manager Agent - User-facing coordinator for defect response.

    This agent coordinates the overall defect response process:
    1. Receives defect alerts from users
    2. Delegates investigation to DefectSpecialistAgent
    3. Reviews findings and assesses risk
    4. Presents options to user with approval gates
    5. Orchestrates corrective actions
    6. Verifies effectiveness and closes loop

    This is a conversational agent that uses human-in-the-loop at strategic
    decision points.
    """

    def __init__(
        self,
        agent_id: str = "production-manager",
        llm_provider: str = "anthropic",
        model: str = None,
        **kwargs
    ):
        """
        Initialize ProductionManagerAgent.

        Args:
            agent_id: Agent identifier
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name (defaults to claude-3-5-sonnet)
        """
        # Note: System prompt loaded from prompts/ProductionManagerAgent.xml
        super().__init__(
            agent_id=agent_id,
            agent_type="ProductionManagerAgent",
            llm_provider=llm_provider,
            model=model or "claude-3-5-sonnet-20241022",
            **kwargs
        )

        # Conversation resource for multi-turn dialogue
        self.conversation = ConversationResource(
            resource_id=f"{agent_id}-conversation",
            llm_provider=llm_provider,
            model=model or "claude-3-5-sonnet-20241022"
        )

        # Track specialist agents (will be added via with_agents)
        self.defect_specialist = None

    def with_agents(self, defect_specialist=None, process_engineer=None):
        """
        Register specialist agents for delegation.

        Args:
            defect_specialist: DefectSpecialistAgent instance
            process_engineer: ProcessEngineerAgent instance (optional for MVP)
        """
        if defect_specialist:
            self.defect_specialist = defect_specialist
        if process_engineer:
            self.process_engineer = process_engineer
        return self

    def _do_execute(self, **kwargs) -> dict:
        """
        Main execution method for handling defect alerts.

        Args:
            **kwargs: Should contain:
                - caller_message: User's message/alert
                - conversation_history: Previous conversation context

        Returns:
            dict: Response with agent's reply and any structured data
        """
        user_message = kwargs.get("caller_message", "")
        conversation_history = kwargs.get("conversation_history", [])

        # Use conversation resource for natural dialogue
        response = self.conversation.send_message(
            message=user_message,
            conversation_history=conversation_history
        )

        return {
            "response": response.get("response", ""),
            "conversation_history": conversation_history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response.get("response", "")}
            ]
        }

    def delegate_investigation(self, defect_alert: dict) -> dict:
        """
        Delegate defect investigation to DefectSpecialist.

        Args:
            defect_alert: Defect information dict with:
                - lot_id: Wafer lot ID
                - defect_type: Defect type/pattern
                - location: Location on wafer
                - frequency: Percentage affected

        Returns:
            dict: Investigation findings from specialist
        """
        if not self.defect_specialist:
            return {
                "error": "No DefectSpecialist registered. Use with_agents() first."
            }

        # Delegate to specialist
        print(f"\n🔄 [ProductionManager] Delegating investigation to DefectSpecialist...")

        investigation_request = f"""Please investigate this defect:

Lot: {defect_alert.get('lot_id', 'Unknown')}
Defect Type: {defect_alert.get('defect_type', 'Unknown')}
Pattern: {defect_alert.get('pattern', 'Unknown')}
Location: {defect_alert.get('location', 'Unknown')}
Frequency: {defect_alert.get('frequency', 'Unknown')}
Process Step: {defect_alert.get('process_step', 'Unknown')}

Conduct systematic investigation and report findings."""

        # Call the specialist's _do_execute directly (not interactive)
        result = self.defect_specialist._do_execute(
            caller_message=investigation_request,
            defect_data=defect_alert
        )

        return result
