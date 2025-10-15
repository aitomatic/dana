"""TestDataResource - Access wafer test data for yield analysis."""

from dana.core.resource.base_resource import BaseResource
from dana.core.workflow.validation import validate_input

from .mock_data import (
    get_wafer_test_data,
    get_bin_details
)


class TestDataResource(BaseResource):
    """
    Resource for accessing wafer test data.

    Provides access to:
    - Wafer test results (pass/fail, bin counts)
    - Bin descriptions and failure modes
    - Product context (ASP, volume, customer)
    """

    def __init__(self, resource_id: str | None = None, **kwargs):
        super().__init__(
            resource_id=resource_id or "test-data",
            **kwargs
        )

    @validate_input(
        wafer_id={"required": False, "type": str},
    )
    def get_test_results(self, wafer_id: str | None = None):
        """
        Get wafer test results.

        Args:
            wafer_id: Wafer identifier (optional - returns mock data)

        Returns:
            dict: Wafer test results including:
                - wafer_id: Wafer identifier
                - product: Product name
                - total_dies: Total dies on wafer
                - good_dies: Passing dies
                - yield_percent: Yield percentage
                - failure_bins: Dict of bin_id -> {count, description, ...}
                - product_context: Business context (ASP, volume, customer)
                - manufacturing_context: Manufacturing info (fab, process, cost)
        """
        # For demo, return mock data
        # In production, this would query test database
        return get_wafer_test_data()

    @validate_input(
        bin_id={"required": True, "type": str},
    )
    def get_bin_details(self, bin_id: str):
        """
        Get detailed information about a specific failure bin.

        Args:
            bin_id: Bin identifier (e.g., "BIN_1")

        Returns:
            dict: Bin details including:
                - test_conditions: Test conditions for this bin
                - failure_mechanism: What fails
                - design_info: Design context
                - typical_root_causes: List of common root causes
                - fix_difficulty: EASY/MEDIUM/HARD
                - fix_difficulty_reasoning: Why it's easy/hard to fix
                - typical_time_to_fix_days: Expected resolution time
        """
        bin_details = get_bin_details(bin_id)

        if not bin_details:
            return {
                "error": f"Bin {bin_id} not found",
                "bin_id": bin_id
            }

        return {
            "bin_id": bin_id,
            **bin_details
        }

    @validate_input(
        wafer_id={"required": False, "type": str},
    )
    def get_failure_summary(self, wafer_id: str | None = None):
        """
        Get summary of failures for analysis.

        Args:
            wafer_id: Wafer identifier (optional)

        Returns:
            dict: Summary including:
                - total_failures: Total failed dies
                - failure_bins: List of bins with counts
                - yield_loss_percent: Percentage yield loss
        """
        test_data = self.get_test_results(wafer_id)

        total_fails = test_data["total_dies"] - test_data["good_dies"]
        yield_loss = 100.0 - test_data["yield_percent"]

        # Sort bins by count
        sorted_bins = sorted(
            test_data["failure_bins"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )

        return {
            "wafer_id": test_data["wafer_id"],
            "total_failures": total_fails,
            "yield_loss_percent": round(yield_loss, 2),
            "failure_bins": [
                {
                    "bin_id": bin_id,
                    "count": data["count"],
                    "description": data["description"],
                    "percent_of_total": round(100.0 * data["count"] / total_fails, 1)
                }
                for bin_id, data in sorted_bins
            ]
        }
