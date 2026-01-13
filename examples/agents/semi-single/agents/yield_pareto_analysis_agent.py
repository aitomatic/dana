"""YieldParetoAnalysisAgent - Deterministic yield analysis using systematic workflows."""

import sys
import os

# Add parent directory to path for workflow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols import DictParams
from dana.core.agent.star_agent import STARAgent

from workflows.yield_pareto_workflow import YieldParetoWorkflow
from workflows.failure_correlation_workflow import FailureCorrelationWorkflow
from workflows.roi_prioritization_workflow import ROIPrioritizationWorkflow


class YieldParetoAnalysisAgent(STARAgent):
    """
    Deterministic Yield Pareto Analysis Agent.

    This agent demonstrates DETERMINISTIC AUTONOMY by:
    1. Using workflows to enforce systematic analysis steps (can't skip)
    2. Leveraging LLM intelligence at specific decision points
    3. Guaranteeing comprehensive coverage (Pareto → Correlation → ROI)
    4. Providing consistent, explainable, actionable output

    Contrast with:
    - Automation: No AI intelligence, rigid rules only
    - Probabilistic Autonomy: LLM decides everything, inconsistent results

    The agent orchestrates three workflows:
    1. YieldParetoWorkflow: Systematic Pareto analysis (80/20 rule)
    2. FailureCorrelationWorkflow: Correlation with historical data
    3. ROIPrioritizationWorkflow: ROI-based action prioritization
    """

    def __init__(
        self,
        agent_id: str = "yield-pareto-agent",
        llm_provider: str = "anthropic",
        model: str = "claude-3-5-sonnet-20241022",
        **kwargs
    ):
        """
        Initialize the Yield Pareto Analysis Agent.

        Args:
            agent_id: Unique identifier for this agent
            llm_provider: LLM provider (anthropic, openai, etc.)
            model: Model name
            **kwargs: Additional arguments passed to STARAgent
        """
        # System prompt defining agent role and behavior
        system_prompt = """You are a Semiconductor Yield Analysis Expert Agent.

Your role is to analyze wafer test failures using systematic, deterministic workflows
that combine rigorous engineering methodology with AI intelligence.

You orchestrate three workflows in sequence:
1. **Pareto Analysis**: Identify top failing bins (80/20 rule)
2. **Correlation Analysis**: Connect failures to historical data and process changes
3. **ROI Prioritization**: Rank improvement opportunities by revenue impact vs fix difficulty

Key principles:
- **Systematic**: Never skip analysis steps - follow engineering best practices
- **Data-driven**: Base conclusions on actual test data and historical evidence
- **Actionable**: Provide specific recommendations with timelines and ROI
- **Explainable**: Show reasoning at each step for engineer trust

Your output should be comprehensive, technically sound, and immediately actionable
for semiconductor yield engineers and fab managers."""

        super().__init__(
            agent_id=agent_id,
            llm_provider=llm_provider,
            model=model,
            system_prompt=system_prompt,
            **kwargs
        )

        # Initialize workflows (deterministic execution sequence)
        self.pareto_workflow = YieldParetoWorkflow(
            workflow_id="pareto-analysis",
            llm_provider=llm_provider,
            model=model
        )

        self.correlation_workflow = FailureCorrelationWorkflow(
            workflow_id="failure-correlation",
            llm_provider=llm_provider,
            model=model
        )

        self.roi_workflow = ROIPrioritizationWorkflow(
            workflow_id="roi-prioritization",
            llm_provider=llm_provider,
            model=model
        )

    def _do_execute(self, caller_message: str, **kwargs) -> DictParams:
        """
        Execute deterministic yield analysis.

        This method orchestrates three workflows in a fixed sequence,
        demonstrating deterministic autonomy.

        Args:
            caller_message: User request (e.g., "Analyze yield for wafer W12345-789")
            **kwargs: Additional parameters (wafer_id, weeks, etc.)

        Returns:
            Comprehensive analysis results with actionable recommendations
        """
        wafer_id = kwargs.get("wafer_id")
        weeks = kwargs.get("weeks", 12)

        # Broadcast agent start
        self.broadcast({
            "agent_progress": {
                "agent_id": self.agent_id,
                "phase": "start",
                "message": f"Starting deterministic yield analysis{' for ' + wafer_id if wafer_id else ''}..."
            }
        })

        try:
            # ========================================
            # PHASE 1: PARETO ANALYSIS (MANDATORY)
            # ========================================
            self.broadcast({
                "agent_progress": {
                    "agent_id": self.agent_id,
                    "phase": "pareto",
                    "message": "Phase 1/3: Running Pareto analysis..."
                }
            })

            pareto_results = self.pareto_workflow.execute(wafer_id=wafer_id)
            pareto_result = pareto_results.get("result", {})

            if not pareto_result.get("success"):
                return {
                    "success": False,
                    "error": f"Pareto analysis failed: {pareto_result.get('error')}",
                    "phase": "pareto"
                }

            pareto_analysis = pareto_result["pareto_analysis"]
            pattern_classifications = pareto_result.get("pattern_classifications", {})
            top_bins = pareto_analysis["pareto_bins"]

            # ========================================
            # PHASE 2: CORRELATION ANALYSIS (MANDATORY)
            # ========================================
            self.broadcast({
                "agent_progress": {
                    "agent_id": self.agent_id,
                    "phase": "correlation",
                    "message": f"Phase 2/3: Correlating {len(top_bins)} top bins with historical data..."
                }
            })

            correlation_results = self.correlation_workflow.execute(
                product=pareto_analysis["product"],
                top_bins=top_bins,
                weeks=weeks
            )
            correlation_result = correlation_results.get("result", {})

            if not correlation_result.get("success"):
                return {
                    "success": False,
                    "error": f"Correlation analysis failed: {correlation_result.get('error')}",
                    "phase": "correlation"
                }

            correlation_findings = correlation_result["correlation_findings"]

            # ========================================
            # PHASE 3: ROI PRIORITIZATION (MANDATORY)
            # ========================================
            self.broadcast({
                "agent_progress": {
                    "agent_id": self.agent_id,
                    "phase": "roi",
                    "message": "Phase 3/3: Calculating ROI and prioritizing actions..."
                }
            })

            # Need to get product context for ROI calculation
            # (In real implementation, this would come from test data)
            product_context = {
                "average_selling_price_usd": 150,
                "monthly_volume_wafers": 10000,
                "customer_tier": "Tier-1 datacenter",
                "revenue_criticality": "HIGH",
            }

            roi_results = self.roi_workflow.execute(
                top_bins=top_bins,
                product_context=product_context
            )
            roi_result = roi_results.get("result", {})

            if not roi_result.get("success"):
                return {
                    "success": False,
                    "error": f"ROI prioritization failed: {roi_result.get('error')}",
                    "phase": "roi"
                }

            prioritized_actions = roi_result["prioritized_actions"]
            total_opportunity = roi_result["total_opportunity_usd"]

            # ========================================
            # SYNTHESIS: COMPREHENSIVE REPORT
            # ========================================
            self.broadcast({
                "agent_progress": {
                    "agent_id": self.agent_id,
                    "phase": "synthesis",
                    "message": "Synthesizing comprehensive analysis report..."
                }
            })

            # Build executive summary
            yield_percent = pareto_analysis["yield_percent"]
            total_failures = pareto_analysis["total_failures"]
            top_bin_count = len(top_bins)

            yield_trend = correlation_findings["yield_trend"]
            trend_direction = yield_trend["trend_direction"]
            yield_change = yield_trend["yield_change"]

            root_cause_hypotheses = correlation_findings.get("root_cause_hypotheses", [])
            top_hypothesis = root_cause_hypotheses[0] if root_cause_hypotheses else None

            top_priority = prioritized_actions[0] if prioritized_actions else None

            executive_summary = {
                "wafer_id": pareto_analysis["wafer_id"],
                "product": pareto_analysis["product"],
                "current_yield": yield_percent,
                "yield_trend": trend_direction,
                "yield_change_pct": yield_change,
                "total_failures": total_failures,
                "pareto_bins_identified": top_bin_count,
                "total_revenue_opportunity_usd": total_opportunity,
                "top_priority_bin": top_priority["bin_id"] if top_priority else None,
                "top_priority_impact_usd": top_priority["revenue_impact_usd"] if top_priority else 0,
                "likely_root_cause": top_hypothesis["hypothesis"] if top_hypothesis else "Unknown",
                "confidence": top_hypothesis["confidence"] if top_hypothesis else "LOW",
            }

            # ========================================
            # FINAL OUTPUT
            # ========================================
            self.broadcast({
                "agent_progress": {
                    "agent_id": self.agent_id,
                    "phase": "complete",
                    "message": f"Analysis complete: ${total_opportunity:,.0f} opportunity identified across {top_bin_count} bins"
                }
            })

            return {
                "success": True,
                "executive_summary": executive_summary,
                "pareto_analysis": pareto_analysis,
                "pattern_classifications": pattern_classifications,
                "correlation_findings": correlation_findings,
                "prioritized_actions": prioritized_actions,
                "analysis_metadata": {
                    "agent_id": self.agent_id,
                    "analysis_type": "deterministic",
                    "workflows_executed": [
                        "YieldParetoWorkflow",
                        "FailureCorrelationWorkflow",
                        "ROIPrioritizationWorkflow"
                    ],
                    "historical_weeks_analyzed": weeks,
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "phase": "unknown"
            }

    def analyze_yield(self, wafer_id: str | None = None, weeks: int = 12) -> DictParams:
        """
        Convenience method to run yield analysis.

        Args:
            wafer_id: Wafer identifier (optional - uses mock data if not provided)
            weeks: Number of weeks of historical data to analyze

        Returns:
            Comprehensive yield analysis results
        """
        return self.execute(
            caller_message=f"Analyze yield{' for wafer ' + wafer_id if wafer_id else ''}",
            wafer_id=wafer_id,
            weeks=weeks
        )
