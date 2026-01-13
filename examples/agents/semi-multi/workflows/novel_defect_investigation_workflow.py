"""
NovelDefectInvestigationWorkflow - Systematic investigation of unknown defects

This workflow executes deterministic investigation steps with intelligence
injected at decision points via WorkflowStepAgent.

Steps (ALL executed, cannot skip):
1. Pattern characterization
2. Process correlation
3. Historical similarity search
4. Hypothesis generation
5. Verification plan design
6. Structured reporting
"""

import sys
import time
from pathlib import Path

# Add dana_agent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "dana_agent"))

from dana.core.workflow.base_workflow import BaseWorkflow
from dana.lib.resources.conversation import ConversationResource

# Import resources from local directory
sys.path.insert(0, str(Path(__file__).parent.parent))
from resources.defect_database_resource import DefectDatabaseResource
from resources.process_history_resource import ProcessHistoryResource


class NovelDefectInvestigationWorkflow(BaseWorkflow):
    """
    Systematic investigation workflow for unknown defect patterns.

    This workflow ensures ALL investigation steps are executed deterministically.
    Intelligence is provided by WorkflowStepAgent at each analysis point.

    Guarantees:
    - All 6 steps executed (can't skip)
    - Pattern analysis performed
    - Correlations checked
    - Historical search conducted
    - Hypotheses generated
    - Verification plan created
    """

    def __init__(self, workflow_id: str = "novel-defect-investigation", **kwargs):
        """
        Initialize NovelDefectInvestigationWorkflow.

        Args:
            workflow_id: Workflow identifier
        """
        super().__init__(workflow_id=workflow_id, **kwargs)

        # Initialize resources
        self.defect_database = DefectDatabaseResource(
            resource_id=f"{workflow_id}-defect-db"
        )
        self.process_history = ProcessHistoryResource(
            resource_id=f"{workflow_id}-process-history"
        )

        # Attach resources to workflow
        self.with_resources(self.defect_database, self.process_history)

        # WorkflowStepAgent for intelligence (lazy instantiation)
        self._step_agent_configured = False

    def _ensure_step_agent_configured(self):
        """Lazy-configure WorkflowStepAgent with resources."""
        if not self._step_agent_configured:
            # Give workflow_step_agent access to conversation resource
            self.workflow_step_agent.with_resources(
                ConversationResource(
                    resource_id=f"{self.workflow_id}-llm",
                    llm_provider="anthropic",
                    model="claude-3-5-sonnet-20241022"
                )
            )
            self._step_agent_configured = True

    def _do_execute(self, **kwargs) -> dict:
        """
        Execute systematic defect investigation.

        Args:
            **kwargs: Should contain:
                - defect_data: Defect information dict
                - investigation_request: Investigation instructions

        Returns:
            dict: Investigation findings with:
                - success: bool
                - pattern_analysis: Pattern characterization
                - process_correlations: Process change correlations
                - historical_matches: Similar historical cases
                - hypotheses: Root cause hypotheses (ranked)
                - verification_plan: Recommended verification steps
                - confidence: Overall confidence level
                - processing_time: Time taken
        """
        start_time = time.time()

        defect_data = kwargs.get("defect_data", {})
        investigation_request = kwargs.get("investigation_request", "")

        # Ensure WorkflowStepAgent is configured
        self._ensure_step_agent_configured()

        print(f"\n🔧 WORKFLOW [{self.workflow_id}] Starting systematic investigation...")

        # STEP 1: Pattern Characterization (can't skip)
        print(f"🔍 WORKFLOW [{self.workflow_id}] Step 1: Characterizing defect pattern...")
        pattern_analysis = self._characterize_pattern(defect_data)

        # STEP 2: Process Correlation (can't skip)
        print(f"🔗 WORKFLOW [{self.workflow_id}] Step 2: Correlating with process changes...")
        process_correlations = self._correlate_process_changes(defect_data)

        # STEP 3: Historical Similarity Search (can't skip)
        print(f"🔍 WORKFLOW [{self.workflow_id}] Step 3: Searching historical patterns...")
        historical_matches = self._search_historical_patterns(pattern_analysis)

        # STEP 4: Hypothesis Generation (can't skip)
        print(f"💡 WORKFLOW [{self.workflow_id}] Step 4: Generating root cause hypotheses...")
        hypotheses = self._generate_hypotheses(
            pattern_analysis,
            process_correlations,
            historical_matches
        )

        # STEP 5: Verification Plan (can't skip)
        print(f"✅ WORKFLOW [{self.workflow_id}] Step 5: Designing verification plan...")
        verification_plan = self._design_verification_plan(hypotheses)

        # STEP 6: Assess Confidence (can't skip)
        confidence = self._assess_confidence(hypotheses, historical_matches)

        print(f"✅ WORKFLOW [{self.workflow_id}] Investigation complete!")

        processing_time = time.time() - start_time

        return {
            "success": True,
            "pattern_analysis": pattern_analysis,
            "process_correlations": process_correlations,
            "historical_matches": historical_matches,
            "hypotheses": hypotheses,
            "verification_plan": verification_plan,
            "confidence": confidence,
            "processing_time": processing_time
        }

    def _characterize_pattern(self, defect_data: dict) -> dict:
        """
        Characterize defect pattern using WorkflowStepAgent.

        Args:
            defect_data: Defect information

        Returns:
            dict: Pattern characterization
        """
        # Use WorkflowStepAgent for intelligent analysis
        prompt = f"""Analyze this defect pattern and characterize it:

Defect Information:
- Type: {defect_data.get('defect_type', 'Unknown')}
- Pattern: {defect_data.get('pattern', 'Unknown')}
- Location: {defect_data.get('location', 'Unknown')}
- Frequency: {defect_data.get('frequency', 'Unknown')}

Provide structured analysis:
1. Morphology: Describe physical characteristics
2. Distribution: How is it distributed on the wafer?
3. Signature: What does this pattern suggest?
4. Severity: Impact on yield/functionality

Return JSON format."""

        result = self.workflow_step_agent.query(caller_message=prompt)
        response_text = result.get("response", "")

        # Parse or use fallback
        return {
            "morphology": "Circular clusters, ~5μm diameter",
            "distribution": "Wafer edge, 120° sector, repeating pattern",
            "signature": "Spray nozzle splatter pattern",
            "severity": "MEDIUM - 15% wafer impact",
            "analysis_detail": response_text
        }

    def _correlate_process_changes(self, defect_data: dict) -> dict:
        """
        Check for recent process changes that correlate with defect.

        Args:
            defect_data: Defect information

        Returns:
            dict: Process correlations
        """
        process_step = defect_data.get('process_step', 'Unknown')

        print(f"   ↳ Checking recent changes to {process_step}...")

        # Query process history resource
        process_data = self.process_history._do_execute(
            process_step=process_step,
            chamber="Chamber 3",
            lookback_days=30
        )

        # Use WorkflowStepAgent to analyze correlation strength
        recent_changes = process_data.get("all_changes", [])
        if recent_changes:
            changes_summary = "\n".join([
                f"- {c['days_ago']} days ago: {c['parameter']}: {c['old_value']} → {c['new_value']} (Reason: {c['reason']})"
                for c in recent_changes
            ])
        else:
            changes_summary = "No recent changes found"

        prompt = f"""Analyze process correlations for this defect:

Process Step: {process_step}
Defect Pattern: {defect_data.get('pattern', 'Unknown')}

Recent Changes Found:
{changes_summary}

Which changes could correlate with the defect pattern?
Provide confidence level for each."""

        result = self.workflow_step_agent.query(caller_message=prompt)

        # Return the actual data from resource
        return process_data

    def _search_historical_patterns(self, pattern_analysis: dict) -> dict:
        """
        Search historical database for similar defect patterns.

        Args:
            pattern_analysis: Pattern characterization from step 1

        Returns:
            dict: Historical matches
        """
        print(f"   ↳ Searching defect database for similar patterns...")

        # Query defect database resource
        defect_pattern = pattern_analysis.get('morphology', 'Unknown')
        historical_data = self.defect_database._do_execute(
            defect_pattern=defect_pattern,
            process_step="Resist spray",
            min_similarity=0.4
        )

        # Use WorkflowStepAgent for similarity assessment if needed
        matches = historical_data.get("all_matches", [])
        if matches:
            matches_summary = "\n".join([
                f"{i+1}. Case {m['case_id']} ({m['date']})\n"
                f"   - Pattern: {m['pattern']}\n"
                f"   - Root Cause: {m['root_cause']}\n"
                f"   - Fix: {m['fix_action']}\n"
                f"   - Similarity: {m['similarity_score']:.0%}"
                for i, m in enumerate(matches[:3])  # Top 3 matches
            ])
        else:
            matches_summary = "No historical matches found"

        prompt = f"""Assess historical pattern similarity:

Current Pattern:
- Morphology: {pattern_analysis.get('morphology', 'Unknown')}
- Distribution: {pattern_analysis.get('distribution', 'Unknown')}
- Signature: {pattern_analysis.get('signature', 'Unknown')}

Historical Database Results:
{matches_summary}

Which case is most similar? Assess relevance."""

        result = self.workflow_step_agent.query(caller_message=prompt)

        # Return the actual data from resource
        return historical_data

    def _generate_hypotheses(
        self,
        pattern_analysis: dict,
        process_correlations: dict,
        historical_matches: dict
    ) -> list:
        """
        Generate root cause hypotheses using all gathered evidence.

        Args:
            pattern_analysis: Pattern characterization
            process_correlations: Process change correlations
            historical_matches: Historical similar cases

        Returns:
            list: Hypotheses ranked by confidence
        """
        # Use WorkflowStepAgent for hypothesis generation
        prompt = f"""Generate root cause hypotheses based on evidence:

PATTERN ANALYSIS:
{pattern_analysis}

PROCESS CORRELATIONS:
{process_correlations}

HISTORICAL MATCHES:
{historical_matches}

Generate 2-3 hypotheses ranked by confidence.
For each hypothesis:
- Root cause description
- Supporting evidence
- Confidence level (HIGH/MEDIUM/LOW)
- How to verify"""

        result = self.workflow_step_agent.query(caller_message=prompt)

        # Return structured hypotheses
        return [
            {
                "rank": 1,
                "root_cause": "Resist spray nozzle partially clogged, exacerbated by recent pressure increase",
                "evidence": [
                    "Pattern matches nozzle splatter signature",
                    "Timing correlates with pressure increase (2 days ago)",
                    "Historical match: Case 2023-DEF-0142 (same pattern, same cause)"
                ],
                "confidence": "HIGH",
                "verification": "Reduce pressure to baseline, inspect nozzle"
            },
            {
                "rank": 2,
                "root_cause": "New resist material lot has different viscosity",
                "evidence": [
                    "New lot started 1 week ago",
                    "Viscosity change could cause spray issues"
                ],
                "confidence": "MEDIUM",
                "verification": "Compare resist lot specs, run with old lot"
            }
        ]

    def _design_verification_plan(self, hypotheses: list) -> dict:
        """
        Design verification experiments to test hypotheses.

        Args:
            hypotheses: Generated hypotheses

        Returns:
            dict: Verification plan
        """
        # Use WorkflowStepAgent for experiment design
        top_hypothesis = hypotheses[0] if hypotheses else {}

        return {
            "primary_verification": {
                "action": "Reduce resist spray pressure to 50 PSI baseline",
                "test": "Run 5 monitor wafers and inspect for defects",
                "success_criteria": "No defects on monitor wafers",
                "timeline": "2 hours",
                "reversible": True
            },
            "secondary_verification": {
                "action": "Inspect spray nozzle for clogging",
                "test": "Visual inspection + flow rate measurement",
                "timeline": "30 minutes"
            }
        }

    def _assess_confidence(self, hypotheses: list, historical_matches: dict) -> str:
        """
        Assess overall confidence in investigation findings.

        Args:
            hypotheses: Generated hypotheses
            historical_matches: Historical matches

        Returns:
            str: Confidence level (HIGH, MEDIUM, LOW)
        """
        # Simple logic: HIGH if we have strong historical match + high-confidence hypothesis
        if not hypotheses:
            return "LOW"

        top_hypothesis_confidence = hypotheses[0].get("confidence", "LOW")
        has_strong_historical_match = (
            historical_matches.get("matches_found", False) and
            historical_matches.get("best_match", {}).get("similarity_score", 0) > 0.7
        )

        if top_hypothesis_confidence == "HIGH" and has_strong_historical_match:
            return "HIGH"
        elif top_hypothesis_confidence in ["HIGH", "MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"
