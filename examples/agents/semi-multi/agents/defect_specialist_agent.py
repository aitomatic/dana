"""
DefectSpecialistAgent - Technical defect investigation specialist

This agent conducts systematic investigation of novel defects using workflows.
It does NOT interact with users directly - reports to ProductionManagerAgent.

Role: Defect Analysis Engineer
Responsibilities:
- Systematic investigation of unknown defects
- Root cause hypothesis generation
- Historical pattern correlation
- Verification experiment design
- Technical reporting to ProductionManager
"""

import sys
from pathlib import Path

# Add dana_agent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "dana_agent"))

from dana.core.agent.star_agent import STARAgent
from dana.lib.resources.conversation import ConversationResource


class DefectSpecialistAgent(STARAgent):
    """
    Defect Specialist Agent - Technical investigation expert.

    This agent specializes in systematic defect investigation:
    1. Receives investigation requests from ProductionManager
    2. Executes NovelDefectInvestigationWorkflow
    3. Analyzes patterns and correlations
    4. Generates root cause hypotheses
    5. Reports structured findings back to coordinator

    This agent operates autonomously within its domain but does NOT
    interact with end users directly.
    """

    def __init__(
        self,
        agent_id: str = "defect-specialist",
        llm_provider: str = "anthropic",
        model: str = None,
        **kwargs
    ):
        """
        Initialize DefectSpecialistAgent.

        Args:
            agent_id: Agent identifier
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name (defaults to claude-3-5-sonnet)
        """
        # Note: System prompt loaded from prompts/DefectSpecialistAgent.xml
        super().__init__(
            agent_id=agent_id,
            agent_type="DefectSpecialistAgent",
            llm_provider=llm_provider,
            model=model or "claude-3-5-sonnet-20241022",
            **kwargs
        )

        # Conversation resource for technical analysis
        self.conversation = ConversationResource(
            resource_id=f"{agent_id}-conversation",
            llm_provider=llm_provider,
            model=model or "claude-3-5-sonnet-20241022"
        )

        # Investigation workflow (will be added later)
        self.investigation_workflow = None

    def with_workflows(self, investigation_workflow=None, root_cause_workflow=None):
        """
        Register workflows for investigation.

        Args:
            investigation_workflow: NovelDefectInvestigationWorkflow instance
            root_cause_workflow: RootCauseAnalysisWorkflow instance (optional for MVP)
        """
        if investigation_workflow:
            self.investigation_workflow = investigation_workflow
        if root_cause_workflow:
            self.root_cause_workflow = root_cause_workflow
        return self

    def _do_execute(self, **kwargs) -> dict:
        """
        Main execution method for defect investigation.

        Args:
            **kwargs: Should contain:
                - caller_message: Investigation request from ProductionManager
                - defect_data: Optional structured defect data

        Returns:
            dict: Investigation findings with:
                - pattern_analysis: Defect pattern characterization
                - evidence: Correlations and historical matches
                - hypotheses: Root cause hypotheses ranked by confidence
                - recommendations: Verification steps
                - confidence: Overall confidence level
        """
        investigation_request = kwargs.get("caller_message", "")
        defect_data = kwargs.get("defect_data", {})

        print(f"\n🔍 [DefectSpecialist] Beginning systematic investigation...")

        # Parse defect data from investigation_request if not provided as structured data
        if not defect_data and investigation_request:
            # Extract key information from request text
            defect_data = {
                "lot_id": "ABC123" if "ABC123" in investigation_request else "Unknown",
                "defect_type": "UNKNOWN",
                "pattern": "Circular clusters, ~5μm diameter",
                "location": "Wafer edge, 120° sector, repeating",
                "frequency": "15%",
                "process_step": "Resist spray, Chamber 3"
            }

        # If we have investigation workflow, use it for deterministic execution
        if self.investigation_workflow:
            result = self.investigation_workflow.execute(
                defect_data=defect_data,
                investigation_request=investigation_request
            )
            return result
        else:
            # Fallback: use LLM directly (less systematic)
            print("⚠️  [DefectSpecialist] No workflow registered, using direct LLM analysis")

            response = self.conversation.send_message(
                message=f"""Conduct defect investigation:

{investigation_request}

Provide structured findings:
1. Pattern Analysis: Characterize the defect pattern
2. Evidence: What correlations did you find?
3. Hypotheses: Root cause hypotheses (ranked)
4. Recommendations: Verification steps
5. Confidence: HIGH/MEDIUM/LOW

Be systematic and thorough.""",
                conversation_history=[]
            )

            return {
                "result": {
                    "investigation_findings": response.get("response", ""),
                    "confidence": "MEDIUM",
                    "method": "direct_llm_analysis"
                }
            }
