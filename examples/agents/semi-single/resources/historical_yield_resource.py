"""HistoricalYieldResource - Access historical yield data for trend analysis."""

from dana.core.resource.base_resource import BaseResource
from dana.core.workflow.validation import validate_input

from .mock_data import get_historical_yield_data, get_similar_failure_cases


class HistoricalYieldResource(BaseResource):
    """
    Resource for accessing historical yield data.

    Provides access to:
    - Yield trends over time
    - Similar historical failure cases
    - Process change history
    """

    def __init__(self, resource_id: str | None = None, **kwargs):
        super().__init__(resource_id=resource_id or "historical-yield", **kwargs)

    @validate_input(
        product={"required": True, "type": str},
        weeks={"required": False, "type": int},
    )
    def get_product_yield_trend(self, product: str, weeks: int = 12):
        """
        Get yield trend for a product over time.

        Args:
            product: Product name
            weeks: Number of weeks of history (default 12)

        Returns:
            dict: Yield trend data including:
                - product: Product name
                - weeks: List of weekly yield data
                - trend: "improving", "degrading", or "stable"
                - trend_analysis: Human-readable trend summary
                - process_changes: List of recent process changes
        """
        return get_historical_yield_data(product, weeks)

    @validate_input(
        bin_id={"required": True, "type": str},
        product={"required": False, "type": str},
    )
    def get_similar_failures(self, bin_id: str, product: str | None = None):
        """
        Find historical similar failure patterns.

        Args:
            bin_id: Current failure bin to find similar cases for
            product: Product name (optional - for filtering)

        Returns:
            list: List of similar historical cases, each containing:
                - case_id: Historical case identifier
                - date: When the case occurred
                - product: Product affected
                - primary_bin: Main failure bin
                - root_cause: Identified root cause
                - resolution: How it was fixed
                - time_to_resolve_days: How long it took
                - revenue_recovered_usd: Financial impact of fix
                - similarity_score: 0.0-1.0 similarity to current case
                - notes: Additional context
        """
        cases = get_similar_failure_cases(bin_id)

        # Filter by product if specified
        if product:
            cases = [c for c in cases if product in c["product"]]

        # Sort by similarity score (highest first)
        cases.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        return cases

    @validate_input(
        product={"required": True, "type": str},
        weeks={"required": False, "type": int},
    )
    def analyze_yield_trend(self, product: str, weeks: int = 12):
        """
        Analyze yield trend and identify concerning patterns.

        Args:
            product: Product name
            weeks: Number of weeks to analyze

        Returns:
            dict: Trend analysis including:
                - current_yield: Latest yield percentage
                - average_yield: Average over period
                - yield_change: Change from N weeks ago
                - trend_direction: "up", "down", or "flat"
                - concerns: List of concerning patterns
                - opportunities: Potential improvement areas
        """
        trend_data = get_historical_yield_data(product, weeks)

        if not trend_data["weeks"]:
            return {"error": "No historical data available"}

        # Calculate statistics
        yields = [w["yield"] for w in trend_data["weeks"]]
        current_yield = yields[0]  # Most recent
        oldest_yield = yields[-1]  # Oldest in period
        average_yield = sum(yields) / len(yields)
        yield_change = current_yield - oldest_yield

        # Determine trend direction
        if yield_change < -2.0:
            trend_direction = "down"
            severity = "HIGH" if yield_change < -5.0 else "MEDIUM"
        elif yield_change > 2.0:
            trend_direction = "up"
            severity = "LOW"
        else:
            trend_direction = "flat"
            severity = "LOW"

        # Identify concerns
        concerns = []
        if trend_direction == "down":
            concerns.append(
                {
                    "type": "yield_degradation",
                    "severity": severity,
                    "description": f"Yield degraded {abs(yield_change):.1f}% over {weeks} weeks",
                    "impact": f"Revenue at risk: ~${abs(yield_change) * 100000:.0f}/week",
                }
            )

        # Check for process changes
        if trend_data.get("process_changes"):
            for change in trend_data["process_changes"]:
                concerns.append(
                    {
                        "type": "process_change_correlation",
                        "severity": "MEDIUM",
                        "description": f"Process change in week {change['week']}: {change['change']}",
                        "impact": change.get("impact", "Unknown impact"),
                    }
                )

        # Identify opportunities
        opportunities = []
        if current_yield < 75.0:
            gap_to_target = 75.0 - current_yield
            opportunities.append(
                {
                    "type": "yield_improvement",
                    "potential": f"{gap_to_target:.1f}% yield improvement possible",
                    "revenue_impact": f"${gap_to_target * 150000:.0f}/week potential revenue",
                    "priority": "HIGH" if gap_to_target > 5.0 else "MEDIUM",
                }
            )

        return {
            "product": product,
            "weeks_analyzed": weeks,
            "current_yield": round(current_yield, 2),
            "average_yield": round(average_yield, 2),
            "yield_change": round(yield_change, 2),
            "trend_direction": trend_direction,
            "trend_severity": severity if trend_direction == "down" else "LOW",
            "concerns": concerns,
            "opportunities": opportunities,
            "process_changes": trend_data.get("process_changes", []),
        }
