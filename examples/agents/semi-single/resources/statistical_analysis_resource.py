"""StatisticalAnalysisResource - Provides statistical analysis capabilities."""

from dana.core.resource.base_resource import BaseResource
from dana.common.protocols import DictParams


class StatisticalAnalysisResource(BaseResource):
    """
    Resource for running statistical tests on defect data.

    Provides spatial autocorrelation tests, clustering tests, etc.
    """

    def __init__(self, resource_id: str = "statistical-analysis"):
        super().__init__(resource_id=resource_id)

    def morans_i_test(self, spatial_data: DictParams) -> DictParams:
        """
        Run Moran's I spatial autocorrelation test.

        Args:
            spatial_data: Spatial defect distribution data

        Returns:
            Test results with I statistic, p-value, interpretation
        """
        bin_id = spatial_data.get("bin_id", "")

        if bin_id == "BIN_1":
            # Clustered pattern - high positive autocorrelation
            return {
                "test": "morans_i",
                "bin_id": bin_id,
                "statistic": 0.87,
                "p_value": 0.0001,
                "z_score": 8.45,
                "interpretation": "strong_positive_autocorrelation",
                "conclusion": "Defects are significantly clustered (p<0.001)",
                "confidence": 0.99
            }
        elif bin_id == "BIN_2":
            # Random pattern - near-zero autocorrelation
            return {
                "test": "morans_i",
                "bin_id": bin_id,
                "statistic": 0.03,
                "p_value": 0.72,
                "z_score": 0.36,
                "interpretation": "no_autocorrelation",
                "conclusion": "Defects show no significant spatial pattern (p=0.72)",
                "confidence": 0.75
            }
        else:
            return {"error": "No data for analysis"}

    def chi_square_test(self, observed: list, expected: list) -> DictParams:
        """
        Run chi-square goodness of fit test.

        Args:
            observed: Observed frequencies
            expected: Expected frequencies

        Returns:
            Test results
        """
        # Mock calculation for demo
        return {
            "test": "chi_square",
            "chi_square_statistic": 45.23,
            "degrees_of_freedom": 5,
            "p_value": 0.0001,
            "conclusion": "Observed distribution significantly different from expected (p<0.001)"
        }

    def getis_ord_gi_star(self, spatial_data: DictParams) -> DictParams:
        """
        Run Getis-Ord Gi* hot spot analysis.

        Identifies statistically significant hot spots and cold spots.
        """
        bin_id = spatial_data.get("bin_id", "")

        if bin_id == "BIN_1":
            return {
                "test": "getis_ord_gi_star",
                "bin_id": bin_id,
                "hot_spots": [
                    {"location": "center", "gi_star": 3.85, "p_value": 0.0001, "confidence": 0.99},
                ],
                "cold_spots": [
                    {"location": "edge", "gi_star": -2.14, "p_value": 0.032, "confidence": 0.95}
                ],
                "conclusion": "Significant hot spot in center region (Gi*=3.85, p<0.001)"
            }
        else:
            return {
                "test": "getis_ord_gi_star",
                "bin_id": bin_id,
                "hot_spots": [],
                "cold_spots": [],
                "conclusion": "No statistically significant hot or cold spots detected"
            }
