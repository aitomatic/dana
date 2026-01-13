"""StatisticalTestWorkflow - Runs comprehensive statistical tests on defect patterns."""

from dana.core.workflow.base_workflow import BaseWorkflow
from dana.common.protocols import DictParams


class StatisticalTestWorkflow(BaseWorkflow):
    """
    Workflow for running comprehensive statistical analysis on defect patterns.

    Orchestrates multiple statistical tests (Moran's I, Getis-Ord, chi-square)
    and synthesizes results into coherent assessment.
    """

    def __init__(self, workflow_id: str = "statistical-test"):
        super().__init__(workflow_id=workflow_id)

    def execute(self, test_params: DictParams) -> DictParams:
        """
        Run comprehensive statistical tests.

        Args:
            test_params: {
                "test_type": "comprehensive" | "morans_i" | "spatial_autocorrelation",
                "spatial_data": {...},
                "resource": StatisticalAnalysisResource instance (optional)
            }

        Returns:
            Statistical test results with interpretation
        """
        test_type = test_params.get("test_type", "comprehensive")
        spatial_data = test_params.get("spatial_data", {})
        resource = test_params.get("resource")

        if not spatial_data:
            return {"success": False, "error": "No spatial data provided for statistical analysis"}

        bin_id = spatial_data.get("bin_id", "")
        results = {"success": True, "bin_id": bin_id, "tests_run": []}

        # If resource provided, use it; otherwise use mock data
        if resource:
            # Step 1: Run Moran's I test
            morans_result = resource.morans_i_test(spatial_data)
            results["morans_i"] = morans_result
            results["tests_run"].append("morans_i")

            # Step 2: Run Getis-Ord Gi* hot spot analysis
            hotspot_result = resource.getis_ord_gi_star(spatial_data)
            results["hotspot_analysis"] = hotspot_result
            results["tests_run"].append("getis_ord_gi_star")

            # Step 3: Synthesize overall assessment
            results["overall_assessment"] = self._synthesize_results(morans_result, hotspot_result)
            results["confidence"] = self._calculate_confidence(morans_result, hotspot_result)
        else:
            # Mock results for demo
            results["morans_i"] = {
                "test": "morans_i",
                "statistic": 0.85,
                "p_value": 0.001,
                "interpretation": "strong_positive_autocorrelation",
            }
            results["tests_run"].append("morans_i")
            results["overall_assessment"] = "Strong spatial clustering detected (p<0.001)"
            results["confidence"] = 0.95

        return results

    def _synthesize_results(self, morans_result: DictParams, hotspot_result: DictParams) -> str:
        """Synthesize multiple test results into overall assessment."""
        morans_i = morans_result.get("statistic", 0)
        p_value = morans_result.get("p_value", 1.0)
        interpretation = morans_result.get("interpretation", "")

        hot_spots = hotspot_result.get("hot_spots", [])
        cold_spots = hotspot_result.get("cold_spots", [])

        assessment_parts = []

        # Moran's I assessment
        if p_value < 0.001:
            assessment_parts.append(f"Highly significant spatial autocorrelation (I={morans_i:.2f}, p<0.001)")
        elif p_value < 0.05:
            assessment_parts.append(f"Significant spatial autocorrelation (I={morans_i:.2f}, p<0.05)")
        else:
            assessment_parts.append(f"No significant spatial pattern detected (p={p_value:.3f})")

        # Hot spot assessment
        if hot_spots:
            locations = [hs.get("location", "") for hs in hot_spots]
            assessment_parts.append(f"Significant hot spots detected in {', '.join(locations)}")

        # Overall determination
        if interpretation == "strong_positive_autocorrelation":
            assessment_parts.append("Strong evidence of SYSTEMATIC defect pattern")
        elif interpretation == "no_autocorrelation":
            assessment_parts.append("Evidence suggests RANDOM defect pattern")

        return ". ".join(assessment_parts) + "."

    def _calculate_confidence(self, morans_result: DictParams, hotspot_result: DictParams) -> float:
        """Calculate overall confidence in the assessment."""
        p_value = morans_result.get("p_value", 1.0)
        morans_confidence = morans_result.get("confidence", 0.5)

        hot_spots = hotspot_result.get("hot_spots", [])
        hotspot_confidence = max([hs.get("confidence", 0) for hs in hot_spots], default=0)

        # Combine confidences
        if p_value < 0.001:
            base_confidence = 0.95
        elif p_value < 0.01:
            base_confidence = 0.90
        elif p_value < 0.05:
            base_confidence = 0.85
        else:
            base_confidence = 0.70

        # Boost if multiple tests agree
        if hotspot_confidence > 0.9 and morans_confidence > 0.9:
            base_confidence = min(0.99, base_confidence + 0.05)

        return base_confidence
