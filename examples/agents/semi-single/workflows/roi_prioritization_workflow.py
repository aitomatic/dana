"""ROIPrioritizationWorkflow - Calculate ROI and prioritize corrective actions."""

import sys
import os

# Add parent directory to path for resource imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.lib.resources.conversation import ConversationResource

from resources.test_data_resource import TestDataResource


class ROIPrioritizationWorkflow(BaseWorkflow):
    """
    Calculate ROI and prioritize corrective actions.

    Workflow ensures:
    1. Revenue impact calculation (systematic)
    2. Fix difficulty assessment (LLM intelligence)
    3. ROI scoring (systematic formula)
    4. Ranking by ROI (systematic)
    5. Action recommendation generation (LLM intelligence)

    This provides data-driven prioritization of yield improvement efforts.
    """

    def __init__(self, workflow_id: str | None = None, llm_provider: str = "anthropic", model: str | None = None, **kwargs):
        super().__init__(workflow_id=workflow_id or "roi-prioritization", **kwargs)

        # Store config for step agent resources
        self._llm_provider = llm_provider
        self._model = model or "claude-3-5-sonnet-20241022"
        self._step_agent_configured = False

        # Test data for product context and bin details
        self.test_data = TestDataResource(resource_id="test-data")

    def _ensure_step_agent_configured(self):
        """Ensure workflow_step_agent is configured with necessary resources."""
        if not self._step_agent_configured:
            # Give step agent access to resources it needs
            self.workflow_step_agent.with_resources(
                ConversationResource(resource_id=f"{self.workflow_id}-llm", llm_provider=self._llm_provider, model=self._model)
            )
            self._step_agent_configured = True

    @validate_input(
        top_bins={"required": True, "type": list},
        product_context={"required": True, "type": dict},
    )
    @validate_output(
        success={"required": True, "type": bool},
        prioritized_actions={"required": True, "type": list},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute ROI-based prioritization.

        Args:
            top_bins: Top failing bins from Pareto analysis
            product_context: Product business context (ASP, volume, etc.)

        Returns:
            {
                "success": True,
                "prioritized_actions": [
                    {
                        "rank": 1,
                        "bin_id": str,
                        "description": str,
                        "revenue_impact_usd": float,
                        "fix_difficulty": "EASY/MEDIUM/HARD",
                        "roi_score": float,
                        "recommended_actions": [str],
                        "priority_justification": str,
                    },
                    ...
                ],
                "total_opportunity_usd": float,
            }
        """
        top_bins = kwargs["top_bins"]
        product_context = kwargs["product_context"]

        try:
            # STEP 1: Revenue Impact Calculation (MANDATORY)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "revenue_calc",
                        "message": "Calculating revenue impact per bin...",
                    }
                }
            )

            asp = product_context.get("average_selling_price_usd", 150)
            monthly_volume = product_context.get("monthly_volume_wafers", 10000)

            bins_with_impact = []
            for bin_info in top_bins:
                failures_per_wafer = bin_info["count"]
                # Monthly revenue loss = failures per wafer × ASP × monthly volume
                monthly_impact = failures_per_wafer * asp * monthly_volume
                # Annualized
                annual_impact = monthly_impact * 12

                bins_with_impact.append(
                    {
                        **bin_info,
                        "failures_per_wafer": failures_per_wafer,
                        "monthly_revenue_impact_usd": monthly_impact,
                        "annual_revenue_impact_usd": annual_impact,
                    }
                )

            # STEP 2: Fix Difficulty Assessment (LLM Intelligence)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "difficulty_assessment",
                        "message": "Assessing fix difficulty with LLM...",
                    }
                }
            )

            bins_with_difficulty = self._assess_fix_difficulty(bins_with_impact)

            # STEP 3: ROI Score Calculation (MANDATORY)
            self.broadcast(
                {"workflow_progress": {"workflow_id": self.workflow_id, "phase": "roi_calculation", "message": "Calculating ROI scores..."}}
            )

            # Map difficulty to score multiplier (higher = better ROI)
            difficulty_multiplier = {
                "EASY": 3.0,  # Easy fixes get 3x multiplier
                "MEDIUM": 1.5,  # Medium fixes get 1.5x multiplier
                "HARD": 0.5,  # Hard fixes get 0.5x penalty
                "UNKNOWN": 1.0,
            }

            bins_with_roi = []
            for bin_info in bins_with_difficulty:
                difficulty = bin_info.get("fix_difficulty", "UNKNOWN")
                multiplier = difficulty_multiplier.get(difficulty, 1.0)

                # ROI score = annual revenue impact × difficulty multiplier
                # (Higher score = better ROI = prioritize this)
                roi_score = bin_info["annual_revenue_impact_usd"] * multiplier

                bins_with_roi.append(
                    {
                        **bin_info,
                        "roi_score": roi_score,
                    }
                )

            # STEP 4: Ranking by ROI (MANDATORY)
            self.broadcast(
                {"workflow_progress": {"workflow_id": self.workflow_id, "phase": "ranking", "message": "Ranking bins by ROI score..."}}
            )

            bins_with_roi.sort(key=lambda x: x["roi_score"], reverse=True)

            # STEP 5: Action Recommendation Generation (LLM Intelligence)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "recommendations",
                        "message": "Generating actionable recommendations with LLM...",
                    }
                }
            )

            prioritized_actions = self._generate_action_recommendations(bins_with_roi)

            # STEP 6: Output (MANDATORY)
            total_opportunity = sum(b["annual_revenue_impact_usd"] for b in bins_with_roi)

            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "complete",
                        "message": f"ROI prioritization complete: ${total_opportunity:,.0f} annual opportunity",
                    }
                }
            )

            return {
                "success": True,
                "prioritized_actions": prioritized_actions,
                "total_opportunity_usd": total_opportunity,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "prioritized_actions": []}

    def _assess_fix_difficulty(self, bins_with_impact: list) -> list:
        """
        Assess fix difficulty for each bin using LLM intelligence.

        Uses bin details (root causes, failure mechanism) to estimate
        how hard it would be to fix this issue.
        """
        bins_with_difficulty = []

        for bin_info in bins_with_impact:
            bin_id = bin_info["bin_id"]

            # Get detailed bin information
            bin_details = self.test_data.get_bin_details(bin_id=bin_id)

            if "error" in bin_details:
                # Fallback if bin details not found
                bins_with_difficulty.append(
                    {
                        **bin_info,
                        "fix_difficulty": "UNKNOWN",
                        "fix_difficulty_reasoning": "Bin details not available",
                        "estimated_time_to_fix_days": None,
                    }
                )
                continue

            # Use existing difficulty assessment from bin details if available
            existing_difficulty = bin_details.get("fix_difficulty", "UNKNOWN")
            existing_reasoning = bin_details.get("fix_difficulty_reasoning", "")
            estimated_time = bin_details.get("typical_time_to_fix_days", "Unknown")

            # Optionally use LLM to refine assessment based on current context
            # For now, use the pre-defined difficulty from bin details
            bins_with_difficulty.append(
                {
                    **bin_info,
                    "fix_difficulty": existing_difficulty,
                    "fix_difficulty_reasoning": existing_reasoning,
                    "estimated_time_to_fix_days": estimated_time,
                    "typical_root_causes": bin_details.get("typical_root_causes", []),
                }
            )

        return bins_with_difficulty

    def _generate_action_recommendations(self, bins_with_roi: list) -> list:
        """
        Generate specific actionable recommendations using LLM.

        Takes top ROI bins and generates concrete next steps.
        """
        # Prepare context for LLM
        top_3_bins = bins_with_roi[:3]  # Focus on top 3 ROI opportunities

        bins_summary = "\n".join(
            [
                f"{i + 1}. {bin['bin_id']}: {bin['description']}\n"
                f"   - Failures: {bin['count']} per wafer\n"
                f"   - Annual revenue impact: ${bin['annual_revenue_impact_usd']:,.0f}\n"
                f"   - Fix difficulty: {bin['fix_difficulty']}\n"
                f"   - ROI score: {bin['roi_score']:,.0f}\n"
                f"   - Typical root causes: {', '.join(bin.get('typical_root_causes', ['Unknown']))}\n"
                f"   - Est. time to fix: {bin.get('estimated_time_to_fix_days', 'Unknown')}"
                for i, bin in enumerate(top_3_bins)
            ]
        )

        prompt = f"""Generate specific actionable recommendations for these yield improvement opportunities:

{bins_summary}

For each bin, provide:
1. **Immediate Actions** (next 1-2 weeks): Specific steps to start investigation
2. **Root Cause Experiments** (2-4 weeks): DOE, characterization, analysis to confirm root cause
3. **Corrective Actions** (1-3 months): Specific process/design changes to fix the issue
4. **Validation Plan**: How to verify the fix works

Recommendations should be:
- Specific and actionable (not generic advice)
- Prioritized by ROI (highest ROI first)
- Time-bound with milestones
- Technically sound for semiconductor manufacturing

Provide recommendations in structured format."""

        try:
            # Ensure step agent is configured with resources
            self._ensure_step_agent_configured()

            # Use step agent for intelligent recommendations
            result = self.workflow_step_agent.query(caller_message=prompt)
            agent_recommendations = result.get("response", "")

            # Build structured action list
            prioritized_actions = []

            for rank, bin_info in enumerate(bins_with_roi, start=1):
                # Generate priority justification
                if rank <= 3:
                    if bin_info["fix_difficulty"] == "EASY":
                        justification = f"TOP PRIORITY: High revenue impact (${bin_info['annual_revenue_impact_usd']:,.0f}/year) with easy fix. Quick win opportunity."
                    elif bin_info["fix_difficulty"] == "MEDIUM":
                        justification = f"HIGH PRIORITY: Significant revenue impact (${bin_info['annual_revenue_impact_usd']:,.0f}/year) with moderate fix difficulty. Good ROI."
                    else:
                        justification = f"STRATEGIC: Large revenue impact (${bin_info['annual_revenue_impact_usd']:,.0f}/year) but hard to fix. Long-term investment."
                else:
                    justification = f"Lower priority: Revenue impact ${bin_info['annual_revenue_impact_usd']:,.0f}/year, difficulty {bin_info['fix_difficulty']}."

                # Extract recommended actions (structured)
                if bin_info["fix_difficulty"] == "EASY":
                    recommended_actions = [
                        "Immediate DOE on process parameters",
                        "Check recent process recipe changes",
                        "Compare with historical similar cases",
                        "Implement fix within 2-3 weeks",
                    ]
                elif bin_info["fix_difficulty"] == "MEDIUM":
                    recommended_actions = [
                        "Detailed failure analysis (SEM, TEM)",
                        "Process characterization split lots",
                        "Correlation with metrology data",
                        "Implement and validate fix (4-8 weeks)",
                    ]
                else:  # HARD
                    recommended_actions = [
                        "Deep root cause investigation",
                        "Design for manufacturability review",
                        "Long-term process development",
                        "Consider design changes or workarounds",
                    ]

                prioritized_actions.append(
                    {
                        "rank": rank,
                        "bin_id": bin_info["bin_id"],
                        "description": bin_info["description"],
                        "failures_per_wafer": bin_info["count"],
                        "revenue_impact_usd": bin_info["annual_revenue_impact_usd"],
                        "fix_difficulty": bin_info["fix_difficulty"],
                        "roi_score": bin_info["roi_score"],
                        "recommended_actions": recommended_actions,
                        "priority_justification": justification,
                        "estimated_timeline": bin_info.get("estimated_time_to_fix_days", "Unknown"),
                    }
                )

            # Add agent analysis to top priorities
            if prioritized_actions:
                prioritized_actions[0]["agent_detailed_plan"] = agent_recommendations

            return prioritized_actions

        except Exception as e:
            # Fallback: return actions without agent recommendations
            prioritized_actions = []
            for rank, bin_info in enumerate(bins_with_roi, start=1):
                prioritized_actions.append(
                    {
                        "rank": rank,
                        "bin_id": bin_info["bin_id"],
                        "description": bin_info["description"],
                        "revenue_impact_usd": bin_info["annual_revenue_impact_usd"],
                        "fix_difficulty": bin_info["fix_difficulty"],
                        "roi_score": bin_info["roi_score"],
                        "recommended_actions": ["Agent recommendation generation failed"],
                        "priority_justification": f"ROI score: {bin_info['roi_score']:,.0f}",
                        "error": str(e),
                    }
                )
            return prioritized_actions
