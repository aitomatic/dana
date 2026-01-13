"""FailureCorrelationWorkflow - Correlate failures with historical data and process changes."""

import sys
import os

# Add parent directory to path for resource imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.lib.resources.conversation import ConversationResource

from resources.historical_yield_resource import HistoricalYieldResource


class FailureCorrelationWorkflow(BaseWorkflow):
    """
    Correlate current failures with historical data and process changes.

    Workflow ensures:
    1. Historical lookup (can't skip)
    2. Trend analysis (systematic)
    3. Process correlation (LLM intelligence)
    4. Root cause hypothesis generation (LLM)

    This provides context for understanding current failures.
    """

    def __init__(self, workflow_id: str | None = None, llm_provider: str = "anthropic", model: str | None = None, **kwargs):
        super().__init__(workflow_id=workflow_id or "failure-correlation", **kwargs)

        # Store config for step agent resources
        self._llm_provider = llm_provider
        self._model = model or "claude-3-5-sonnet-20241022"
        self._step_agent_configured = False

        # Historical data access
        self.historical = HistoricalYieldResource(resource_id="historical-yield")

    def _ensure_step_agent_configured(self):
        """Ensure workflow_step_agent is configured with necessary resources."""
        if not self._step_agent_configured:
            # Give step agent access to resources it needs
            self.workflow_step_agent.with_resources(
                ConversationResource(resource_id=f"{self.workflow_id}-llm", llm_provider=self._llm_provider, model=self._model)
            )
            self._step_agent_configured = True

    @validate_input(
        product={"required": True, "type": str},
        top_bins={"required": True, "type": list},
        weeks={"required": False, "type": int},
    )
    @validate_output(
        success={"required": True, "type": bool},
        correlation_findings={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute correlation analysis.

        Args:
            product: Product name
            top_bins: Top failing bins from Pareto analysis
            weeks: Number of weeks of history to analyze (default 12)

        Returns:
            {
                "success": True,
                "correlation_findings": {
                    "yield_trend": {...},
                    "similar_cases": [...],
                    "process_correlations": {...},
                    "root_cause_hypotheses": [...],
                },
            }
        """
        product = kwargs["product"]
        top_bins = kwargs["top_bins"]
        weeks = kwargs.get("weeks", 12)

        try:
            # STEP 1: Historical Yield Trend Lookup (MANDATORY)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "historical_lookup",
                        "message": f"Retrieving {weeks} weeks of yield history...",
                    }
                }
            )

            trend_data = self.historical.get_product_yield_trend(product=product, weeks=weeks)
            trend_analysis = self.historical.analyze_yield_trend(product=product, weeks=weeks)

            # STEP 2: Similar Failure Case Lookup (MANDATORY)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "similar_cases",
                        "message": "Searching for historical similar failure patterns...",
                    }
                }
            )

            similar_cases_all = []
            for bin_info in top_bins:
                bin_id = bin_info["bin_id"]
                cases = self.historical.get_similar_failures(bin_id=bin_id, product=product)
                similar_cases_all.extend(cases)

            # Remove duplicates and sort by similarity
            seen_ids = set()
            unique_cases = []
            for case in similar_cases_all:
                if case["case_id"] not in seen_ids:
                    seen_ids.add(case["case_id"])
                    unique_cases.append(case)

            unique_cases.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

            # STEP 3: Process Correlation Analysis (LLM Intelligence)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "process_correlation",
                        "message": "Analyzing process change correlations...",
                    }
                }
            )

            process_correlations = self._analyze_process_correlations(trend_data, trend_analysis, top_bins)

            # STEP 4: Root Cause Hypothesis Generation (LLM Intelligence)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "hypothesis_generation",
                        "message": "Generating root cause hypotheses...",
                    }
                }
            )

            hypotheses = self._generate_root_cause_hypotheses(top_bins, unique_cases, process_correlations, trend_analysis)

            # STEP 5: Output (MANDATORY)
            self.broadcast(
                {
                    "workflow_progress": {
                        "workflow_id": self.workflow_id,
                        "phase": "complete",
                        "message": f"Correlation analysis complete: {len(hypotheses)} hypotheses generated",
                    }
                }
            )

            return {
                "success": True,
                "correlation_findings": {
                    "yield_trend": {
                        "current_yield": trend_analysis["current_yield"],
                        "trend_direction": trend_analysis["trend_direction"],
                        "yield_change": trend_analysis["yield_change"],
                        "concerns": trend_analysis["concerns"],
                    },
                    "similar_cases": unique_cases[:3],  # Top 3 most similar
                    "process_correlations": process_correlations,
                    "root_cause_hypotheses": hypotheses,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e), "correlation_findings": {}}

    def _analyze_process_correlations(self, trend_data: dict, trend_analysis: dict, top_bins: list) -> dict:
        """
        Analyze correlation between process changes and yield degradation.

        Uses LLM to reason about timing and causality.
        """
        process_changes = trend_data.get("process_changes", [])

        if not process_changes:
            return {"correlations_found": False, "analysis": "No recent process changes recorded"}

        # Prepare context for LLM
        bins_summary = "\n".join(
            [
                f"- {bin['bin_id']}: {bin['description']} ({bin['count']} failures)"
                for bin in top_bins[:3]  # Top 3 bins
            ]
        )

        changes_summary = "\n".join([f"- Week {change['week']}: {change['change']}" for change in process_changes])

        trend_info = f"Yield trend: {trend_analysis['trend_direction']}, change: {trend_analysis['yield_change']:.1f}%"

        prompt = f"""Analyze the correlation between process changes and failure patterns:

**Top Failure Bins:**
{bins_summary}

**Recent Process Changes:**
{changes_summary}

**Yield Trend:**
{trend_info}

Questions:
1. Is there a timing correlation between process changes and yield degradation?
2. Which process change is most likely related to the current failure pattern?
3. What is the causal mechanism (how could this process change cause these failures)?
4. Confidence level: HIGH/MEDIUM/LOW

Provide structured analysis."""

        try:
            # Ensure step agent is configured with resources
            self._ensure_step_agent_configured()

            # Use step agent for intelligent correlation analysis
            result = self.workflow_step_agent.query(caller_message=prompt)
            analysis = result.get("response", "")

            # For demo, also provide structured correlation
            # (In production, would parse LLM response)
            if process_changes:
                primary_change = process_changes[0]
                return {
                    "correlations_found": True,
                    "primary_correlation": {
                        "process_change": primary_change["change"],
                        "timing": primary_change["week"],
                        "suspected_impact": primary_change.get("impact", "Unknown"),
                        "confidence": "MEDIUM-HIGH",
                    },
                    "agent_analysis": analysis,
                }
            else:
                return {
                    "correlations_found": False,
                    "agent_analysis": analysis,
                }

        except Exception as e:
            return {"correlations_found": False, "error": str(e), "analysis": "Agent correlation analysis failed"}

    def _generate_root_cause_hypotheses(
        self, top_bins: list, similar_cases: list, process_correlations: dict, trend_analysis: dict
    ) -> list:
        """
        Generate root cause hypotheses using LLM reasoning.

        Synthesizes:
        - Current failure patterns
        - Historical similar cases
        - Process change correlations
        - Yield trend data
        """
        # Prepare context for LLM
        bins_summary = "\n".join(
            [
                f"- {bin['bin_id']}: {bin['description']} ({bin['count']} failures, pattern: {bin.get('spatial_pattern', 'unknown')})"
                for bin in top_bins[:3]
            ]
        )

        cases_summary = (
            "\n".join(
                [
                    f"- Case {case['case_id']}: {case['primary_bin']}, "
                    f"Root cause: {case['root_cause']}, "
                    f"Resolution: {case['resolution']}, "
                    f"Similarity: {case['similarity_score']:.2f}"
                    for case in similar_cases[:2]
                ]
            )
            if similar_cases
            else "No highly similar historical cases found"
        )

        correlation_summary = (
            f"Process change correlation: {process_correlations.get('primary_correlation', {}).get('process_change', 'None identified')}"
            if process_correlations.get("correlations_found")
            else "No clear process change correlation"
        )

        prompt = f"""Generate root cause hypotheses for these failures:

**Current Failures:**
{bins_summary}

**Historical Similar Cases:**
{cases_summary}

**Process Correlation:**
{correlation_summary}

**Yield Trend:** {trend_analysis["trend_direction"]} ({trend_analysis["yield_change"]:.1f}% change)

Generate 2-3 ranked hypotheses with:
1. Hypothesis: What is the likely root cause?
2. Evidence: What supports this hypothesis?
3. Confidence: HIGH/MEDIUM/LOW
4. Next Steps: How to verify this hypothesis?

Rank by likelihood (most likely first)."""

        try:
            # Ensure step agent is configured with resources
            self._ensure_step_agent_configured()

            # Use step agent for intelligent hypothesis generation
            result = self.workflow_step_agent.query(caller_message=prompt)
            agent_hypotheses = result.get("response", "")

            # Also generate structured hypotheses based on data
            hypotheses = []

            # Hypothesis 1: Based on similar historical case (if exists)
            if similar_cases and similar_cases[0].get("similarity_score", 0) > 0.7:
                case = similar_cases[0]
                hypotheses.append(
                    {
                        "rank": 1,
                        "hypothesis": f"Similar to historical case: {case['root_cause']}",
                        "evidence": [
                            f"Very similar failure pattern (similarity: {case['similarity_score']:.2f})",
                            f"Historical case: {case['case_id']}",
                            f"Previous resolution: {case['resolution']}",
                        ],
                        "confidence": "HIGH" if case["similarity_score"] > 0.9 else "MEDIUM-HIGH",
                        "next_steps": f"Apply similar resolution approach: {case['resolution']}",
                    }
                )

            # Hypothesis 2: Based on process correlation (if exists)
            if process_correlations.get("correlations_found"):
                corr = process_correlations["primary_correlation"]
                hypotheses.append(
                    {
                        "rank": 2 if hypotheses else 1,
                        "hypothesis": f"Process change impact: {corr['suspected_impact']}",
                        "evidence": [
                            f"Process change: {corr['process_change']}",
                            f"Timing correlation: {corr['timing']}",
                            "Yield degradation coincides with change",
                        ],
                        "confidence": corr.get("confidence", "MEDIUM"),
                        "next_steps": "Run DOE to test process parameter sensitivity",
                    }
                )

            # If no strong hypotheses, add generic one
            if not hypotheses:
                hypotheses.append(
                    {
                        "rank": 1,
                        "hypothesis": "Process variation or random defects",
                        "evidence": [
                            "No clear historical similar cases",
                            "No obvious process change correlation",
                        ],
                        "confidence": "LOW",
                        "next_steps": "Detailed failure analysis, defect pareto, SEM imaging",
                    }
                )

            # Add agent analysis
            for h in hypotheses:
                h["agent_analysis"] = agent_hypotheses

            return hypotheses

        except Exception as e:
            # Fallback hypotheses
            return [
                {
                    "rank": 1,
                    "hypothesis": "Unknown - requires investigation",
                    "evidence": ["Agent hypothesis generation failed"],
                    "confidence": "LOW",
                    "next_steps": "Manual root cause analysis",
                    "error": str(e),
                }
            ]
