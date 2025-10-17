"""YieldParetoWorkflow - Systematic Pareto analysis of wafer test failures."""

import sys
import os

# Add parent directory to path for resource imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.lib.resources.conversation import ConversationResource
from dana.lib.agents.workflow_step_agent import WorkflowStepAgent

from resources.test_data_resource import TestDataResource


class YieldParetoWorkflow(BaseWorkflow):
    """
    Systematic Pareto analysis of yield failures.

    Workflow ensures:
    1. Complete data collection (can't skip)
    2. Proper Pareto calculation (80/20 rule)
    3. Top bin identification (systematic)
    4. Pattern recognition (LLM intelligence)

    This workflow ALWAYS executes all steps - deterministic behavior.
    """

    def __init__(
        self,
        workflow_id: str | None = None,
        llm_provider: str = "anthropic",
        model: str | None = None,
        **kwargs
    ):
        super().__init__(
            workflow_id=workflow_id or "pareto-analysis",
            **kwargs
        )

        # Store config for step agent resources
        self._llm_provider = llm_provider
        self._model = model or "claude-3-5-sonnet-20241022"
        self._step_agent_configured = False

        # Test data access
        self.test_data = TestDataResource(resource_id="test-data")

    def _ensure_step_agent_configured(self):
        """Ensure workflow_step_agent is configured with necessary resources."""
        if not self._step_agent_configured:
            # Give step agent access to resources it needs
            self.workflow_step_agent.with_resources(
                ConversationResource(
                    resource_id=f"{self.workflow_id}-llm",
                    llm_provider=self._llm_provider,
                    model=self._model
                )
            )
            self._step_agent_configured = True

    @validate_input(
        wafer_id={"required": False, "type": str},
    )
    @validate_output(
        success={"required": True, "type": bool},
        pareto_analysis={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute systematic Pareto analysis.

        Args:
            wafer_id: Wafer identifier (optional - uses mock data if not provided)

        Returns:
            {
                "success": True,
                "pareto_analysis": {
                    "wafer_id": str,
                    "total_failures": int,
                    "pareto_bins": [...],  # Top bins representing 80% of failures
                    "all_bins_sorted": [...],  # All bins sorted by count
                },
                "pattern_classifications": {...},  # LLM analysis of patterns
            }
        """
        wafer_id = kwargs.get("wafer_id")

        try:
            # STEP 1: Data Collection (MANDATORY)
            self.broadcast({
                "workflow_progress": {
                    "workflow_id": self.workflow_id,
                    "phase": "data_collection",
                    "message": "Collecting wafer test data..."
                }
            })

            test_results = self.test_data.get_test_results(wafer_id=wafer_id)

            if not test_results or "failure_bins" not in test_results:
                return {
                    "success": False,
                    "error": "No test data available",
                    "pareto_analysis": {}
                }

            # STEP 2: Bin Sorting (MANDATORY)
            self.broadcast({
                "workflow_progress": {
                    "workflow_id": self.workflow_id,
                    "phase": "sorting",
                    "message": "Sorting failure bins by count..."
                }
            })

            failure_bins = test_results["failure_bins"]
            total_failures = sum(bin_data["count"] for bin_data in failure_bins.values())

            # Sort bins by failure count (descending)
            sorted_bins = sorted(
                failure_bins.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )

            # STEP 3: Pareto Calculation (MANDATORY)
            self.broadcast({
                "workflow_progress": {
                    "workflow_id": self.workflow_id,
                    "phase": "pareto_calc",
                    "message": "Calculating Pareto cumulative percentages..."
                }
            })

            cumulative_count = 0
            pareto_bins = []
            all_bins_sorted = []
            pareto_threshold_reached = False

            for bin_id, bin_data in sorted_bins:
                cumulative_count += bin_data["count"]
                cumulative_percent = 100.0 * cumulative_count / total_failures

                bin_analysis = {
                    "bin_id": bin_id,
                    "description": bin_data["description"],
                    "count": bin_data["count"],
                    "percent_of_total": round(100.0 * bin_data["count"] / total_failures, 1),
                    "cumulative_percent": round(cumulative_percent, 1),
                    "spatial_pattern": bin_data.get("spatial_pattern", "unknown"),
                    "test_type": bin_data.get("test_type", "unknown"),
                }

                all_bins_sorted.append(bin_analysis)

                # STEP 4: Top Bin Identification (MANDATORY - 80% rule)
                # Include bins until we reach/exceed 80% cumulative
                if not pareto_threshold_reached:
                    pareto_bins.append(bin_analysis)
                    if cumulative_percent >= 80.0:
                        pareto_threshold_reached = True

            # STEP 5: Pattern Recognition (LLM Intelligence)
            self.broadcast({
                "workflow_progress": {
                    "workflow_id": self.workflow_id,
                    "phase": "pattern_recognition",
                    "message": "Analyzing failure patterns with LLM..."
                }
            })

            pattern_classifications = self._classify_failure_patterns(pareto_bins, test_results)

            # STEP 6: Output (MANDATORY)
            self.broadcast({
                "workflow_progress": {
                    "workflow_id": self.workflow_id,
                    "phase": "complete",
                    "message": f"Pareto analysis complete: {len(pareto_bins)} top bins identified (80% rule)"
                }
            })

            return {
                "success": True,
                "pareto_analysis": {
                    "wafer_id": test_results["wafer_id"],
                    "product": test_results["product"],
                    "total_failures": total_failures,
                    "total_dies": test_results["total_dies"],
                    "yield_percent": test_results["yield_percent"],
                    "pareto_bins": pareto_bins,  # Top bins (80% rule)
                    "all_bins_sorted": all_bins_sorted,  # All bins for reference
                    "top_bin_count": len(pareto_bins),
                },
                "pattern_classifications": pattern_classifications,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "pareto_analysis": {}
            }

    def _classify_failure_patterns(self, pareto_bins: list, test_results: dict) -> dict:
        """
        Use ULTIMATE WorkflowStepAgent with Resources and Workflows to classify patterns.

        This is ULTIMATE Deterministic Autonomy:
        - WorkflowStepAgent is equipped with Resources and Workflows
        - Given high-level OBJECTIVE (not step-by-step instructions)
        - Agent autonomously decides which tools to use and in what order
        - Agent synthesizes multi-source evidence into structured result

        Args:
            pareto_bins: Top failing bins from Pareto analysis
            test_results: Full test results with spatial pattern info

        Returns:
            dict: Pattern classifications with high-confidence, evidence-based data
        """
        # Prepare context
        wafer_id = test_results.get("wafer_id", "unknown")
        bins_summary = "\n".join([
            f"- {bin['bin_id']}: {bin['description']} ({bin['count']} failures, "
            f"{bin['percent_of_total']}%, spatial pattern: {bin.get('spatial_pattern', 'unknown')})"
            for bin in pareto_bins
        ])

        try:
            # Ensure step agent has basic resources
            self._ensure_step_agent_configured()

            # ULTIMATE PATTERN: Equip agent with powerful Resources
            print("\n🔧 ULTIMATE PATTERN: Equipping WorkflowStepAgent with Resources...")
            from resources.wafer_map_resource import WaferMapResource
            from resources.statistical_analysis_resource import StatisticalAnalysisResource
            from resources.historical_pattern_resource import HistoricalPatternResource

            self.workflow_step_agent.with_resources(
                WaferMapResource(resource_id="wafer-map"),
                StatisticalAnalysisResource(resource_id="stats"),
                HistoricalPatternResource(resource_id="historical-patterns")
            )
            print("  ✓ Added: WaferMapResource, StatisticalAnalysisResource, HistoricalPatternResource")

            # ULTIMATE PATTERN: Equip agent with analysis Workflows
            from workflows.spatial_clustering_workflow import SpatialClusteringWorkflow
            from workflows.statistical_test_workflow import StatisticalTestWorkflow

            self.workflow_step_agent.with_workflows(
                SpatialClusteringWorkflow(),
                StatisticalTestWorkflow()
            )
            print("  ✓ Added: SpatialClusteringWorkflow, StatisticalTestWorkflow")
            print("🔧 WorkflowStepAgent now equipped with 3 Resources + 2 Workflows")
            print()

            # ULTIMATE PATTERN: Give agent OBJECTIVE (not simple prompt)
            objective = f"""OBJECTIVE: Determine if failure patterns for bins {[b['bin_id'] for b in pareto_bins]}
are SYSTEMATIC or RANDOM, with HIGH CONFIDENCE (>0.9).

CONTEXT:
- Wafer ID: {wafer_id}
- Top failing bins:
{bins_summary}

MUST PROVIDE:
- pattern_type: SYSTEMATIC|RANDOM for each bin
- confidence: 0.0-1.0 (must be >0.9 for high confidence)
- evidence: Statistical tests, spatial analysis, historical matches
- reasoning: Why you reached this conclusion

AVAILABLE TOOLS (use autonomously):
1. WaferMapResource:
   - get_spatial_data(wafer_id, bin_id): Get spatial defect distribution maps

2. StatisticalAnalysisResource:
   - morans_i_test(spatial_data): Spatial autocorrelation test (detects clustering)
   - getis_ord_gi_star(spatial_data): Hot spot analysis
   - chi_square_test(observed, expected): Goodness of fit test

3. HistoricalPatternResource:
   - find_similar_patterns(pattern_signature): Compare with known systematic/random patterns
   - get_systematic_pattern_library(): Get library of known systematic defect patterns

4. SpatialClusteringWorkflow:
   - execute(spatial_data): Run DBSCAN/K-means clustering analysis

5. StatisticalTestWorkflow:
   - execute({{"test_type": "comprehensive", "spatial_data": ..., "resource": StatisticalAnalysisResource}}):
     Run comprehensive statistical tests and synthesize results

METHODOLOGY:
You are AUTONOMOUS - decide which tools to use and in what order. Recommended approach:
1. Get spatial data for each bin using WaferMapResource
2. Analyze clustering using SpatialClusteringWorkflow
3. Run statistical tests using StatisticalTestWorkflow or direct resource calls
4. Compare with historical patterns using HistoricalPatternResource
5. Synthesize all evidence into high-confidence classification

REQUIREMENTS:
- Use multiple sources of evidence for each bin
- Provide statistical significance (p-values) where applicable
- Include confidence score (0.0-1.0)
- Return structured JSON (no markdown)

Return JSON with this EXACT structure:
{{
    "classifications": {{
        "BIN_X": {{
            "pattern_type": "SYSTEMATIC|RANDOM",
            "confidence": 0.95,
            "fixability": "HIGH|MEDIUM|LOW",
            "investigation_priority": "HIGH|MEDIUM|LOW",
            "root_cause_category": "process|design|package|random",
            "evidence": {{
                "spatial_clustering": {{"method": "...", "result": "..."}},
                "statistical_tests": {{"morans_i": 0.87, "p_value": 0.001}},
                "historical_match": {{"case_id": "...", "similarity": 0.91}},
                "defect_morphology": {{"type": "...", "confidence": 0.92}}
            }},
            "reasoning": "Detailed explanation with evidence"
        }}
    }},
    "overall_assessment": "Summary with confidence statement",
    "has_systematic_patterns": true|false,
    "tools_used": ["list", "of", "tools", "called"]
}}
"""

            # Agent autonomously accomplishes objective using available tools
            print("📤 Sending OBJECTIVE to WorkflowStepAgent...")
            print(f"   Objective length: {len(objective)} chars")

            # DEBUG: Print what resources/workflows the agent has
            print(f"\n🔍 Agent has {len(self.workflow_step_agent.available_resources)} resources:")
            for r in self.workflow_step_agent.available_resources:
                desc = r.public_description[:100] if len(r.public_description) > 100 else r.public_description
                print(f"   - {r.object_id}: {desc}")

            print(f"\n🔍 Agent has {len(self.workflow_step_agent.available_workflows)} workflows:")
            for w in self.workflow_step_agent.available_workflows:
                desc = w.public_description[:100] if len(w.public_description) > 100 else w.public_description
                print(f"   - {w.object_id}: {desc}")
            print()

            result = self.workflow_step_agent.query(caller_message=objective)

            # Extract response content
            import json
            response_text = result.get("response", "{}")

            print(f"📥 Agent response received: {len(response_text)} chars")
            print("📋 Agent response preview:")
            print("-" * 80)
            print(response_text[:500] if len(response_text) > 500 else response_text)
            print("-" * 80)
            print()

            # Try to parse JSON response
            try:
                # Clean up any markdown code blocks if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                classifications_data = json.loads(response_text)

                return {
                    "classifications": classifications_data.get("classifications", {}),
                    "overall_assessment": classifications_data.get("overall_assessment", ""),
                    "has_systematic_patterns": classifications_data.get("has_systematic_patterns", False),
                }
            except json.JSONDecodeError:
                # Fallback: build structured data from spatial patterns
                classifications = {}
                has_systematic = False

                for bin_info in pareto_bins:
                    bin_id = bin_info["bin_id"]
                    spatial_pattern = bin_info.get("spatial_pattern", "unknown")

                    # Heuristic classification based on spatial pattern
                    if spatial_pattern in ["clustered", "systematic"]:
                        pattern_type = "SYSTEMATIC"
                        fixability = "HIGH"
                        priority = "HIGH" if bin_info["percent_of_total"] > 10.0 else "MEDIUM"
                        has_systematic = True
                    elif spatial_pattern == "random":
                        pattern_type = "RANDOM"
                        fixability = "LOW"
                        priority = "LOW"
                    else:
                        pattern_type = "UNKNOWN"
                        fixability = "MEDIUM"
                        priority = "MEDIUM"

                    classifications[bin_id] = {
                        "pattern_type": pattern_type,
                        "fixability": fixability,
                        "investigation_priority": priority,
                        "reasoning": f"Spatial pattern: {spatial_pattern}"
                    }

                return {
                    "classifications": classifications,
                    "overall_assessment": "Fallback classification based on spatial patterns",
                    "has_systematic_patterns": has_systematic,
                    "agent_response": response_text,  # Include raw response for debugging
                }

        except Exception as e:
            # Fallback if agent fails
            return {
                "classifications": {},
                "overall_assessment": f"Agent analysis failed: {str(e)}",
                "has_systematic_patterns": False,
                "error": str(e)
            }
