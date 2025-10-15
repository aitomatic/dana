"""YieldParetoWorkflow - Systematic Pareto analysis of wafer test failures."""

import sys
import os

# Add parent directory to path for resource imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dana.common.protocols import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.lib.resources.conversation import ConversationResource

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

        # LLM for intelligent pattern recognition
        self.conversation = ConversationResource(
            resource_id="llm-reasoning",
            llm_provider=llm_provider,
            model=model or "claude-3-5-sonnet-20241022"
        )

        # Test data access
        self.test_data = TestDataResource(resource_id="test-data")

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
        Use LLM to classify failure patterns (systematic vs random).

        Args:
            pareto_bins: Top failing bins from Pareto analysis
            test_results: Full test results with spatial pattern info

        Returns:
            dict: Pattern classifications with LLM reasoning
        """
        # Prepare context for LLM
        bins_summary = "\n".join([
            f"- {bin['bin_id']}: {bin['description']} ({bin['count']} failures, "
            f"{bin['percent_of_total']}%, spatial pattern: {bin.get('spatial_pattern', 'unknown')})"
            for bin in pareto_bins
        ])

        prompt = f"""Analyze these semiconductor test failure patterns:

{bins_summary}

For each bin, classify the failure pattern:

1. **Systematic vs Random:**
   - Systematic: Clustered spatial pattern, suggests process/design issue (fixable)
   - Random: Randomly distributed, suggests random defects (harder to fix)

2. **Root Cause Category:**
   - Process-related (etch, implant, deposition, etc.)
   - Design-related (timing, margin, functionality)
   - Package/Assembly-related
   - Random defects

3. **Priority for Investigation:**
   - HIGH: Systematic, high volume, likely process-related (easy to fix)
   - MEDIUM: Systematic but complex root cause
   - LOW: Random, low volume, hard to improve

Provide classification for each bin in structured format."""

        try:
            # Use LLM for intelligent pattern classification
            llm_response = self.conversation.send_message(
                message=prompt,
                conversation_history=[]
            )

            reasoning = llm_response.get("response", "")

            # Parse LLM response and structure it
            # For simplicity, we'll also add structured data based on spatial patterns
            classifications = {}

            for bin_info in pareto_bins:
                bin_id = bin_info["bin_id"]
                spatial_pattern = bin_info.get("spatial_pattern", "unknown")

                # Heuristic classification based on spatial pattern
                if spatial_pattern in ["clustered", "systematic"]:
                    pattern_type = "SYSTEMATIC"
                    fixability = "HIGH"
                    priority = "HIGH" if bin_info["percent_of_total"] > 10.0 else "MEDIUM"
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
                "llm_analysis": reasoning,
            }

        except Exception as e:
            # Fallback if LLM fails
            return {
                "classifications": {},
                "llm_analysis": f"LLM analysis failed: {str(e)}",
                "error": str(e)
            }
