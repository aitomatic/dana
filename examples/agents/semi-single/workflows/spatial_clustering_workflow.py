"""SpatialClusteringWorkflow - Analyzes spatial clustering of defects."""

from dana.core.workflow.base_workflow import BaseWorkflow
from dana.common.protocols import DictParams


class SpatialClusteringWorkflow(BaseWorkflow):
    """
    Workflow for analyzing spatial clustering patterns in defect data.

    Uses DBSCAN and other clustering algorithms to identify spatial patterns.
    """

    def __init__(self, workflow_id: str = "spatial-clustering"):
        super().__init__(workflow_id=workflow_id)

    def execute(self, spatial_data: DictParams) -> DictParams:
        """
        Analyze spatial clustering patterns.

        Args:
            spatial_data: Spatial defect distribution data with coordinates

        Returns:
            Clustering analysis results
        """
        # Step 1: Extract spatial coordinates
        defect_locations = spatial_data.get("defect_locations", [])
        defect_count = spatial_data.get("defect_count", 0)
        bin_id = spatial_data.get("bin_id", "")

        if defect_count == 0:
            return {"success": False, "error": "No defects to analyze"}

        # Step 2: Calculate clustering metrics (mock for demo)
        # In production, would use sklearn DBSCAN, K-means, etc.

        # Analyze center vs edge distribution
        distribution = spatial_data.get("spatial_distribution", {})
        center_density = distribution.get("center_region", {}).get("density", 0)
        edge_density = distribution.get("edge_region", {}).get("density", 0)

        # Calculate density ratio
        if edge_density > 0:
            density_ratio = center_density / edge_density
        else:
            density_ratio = float("inf") if center_density > 0 else 1.0

        # Step 3: Determine clustering pattern
        if density_ratio > 3.0:
            pattern_type = "center_clustered"
            clustering_strength = "strong"
        elif density_ratio < 0.5:
            pattern_type = "edge_clustered"
            clustering_strength = "strong"
        elif 0.8 <= density_ratio <= 1.2:
            pattern_type = "uniform_random"
            clustering_strength = "none"
        else:
            pattern_type = "moderate_clustering"
            clustering_strength = "moderate"

        # Step 4: Generate results
        result = {
            "success": True,
            "bin_id": bin_id,
            "defect_count": defect_count,
            "pattern_type": pattern_type,
            "clustering_strength": clustering_strength,
            "metrics": {"center_density": center_density, "edge_density": edge_density, "density_ratio": density_ratio},
            "clusters_detected": 1 if clustering_strength == "strong" else 0,
            "interpretation": self._interpret_clustering(pattern_type, clustering_strength, density_ratio),
        }

        return result

    def _interpret_clustering(self, pattern_type: str, strength: str, ratio: float) -> str:
        """Generate human-readable interpretation."""
        if pattern_type == "center_clustered":
            return (
                f"Strong center clustering detected (density ratio {ratio:.2f}:1). "
                "Suggests systematic process issue affecting wafer center, "
                "possibly CMP non-uniformity or center-weighted defect mechanism."
            )
        elif pattern_type == "edge_clustered":
            return (
                f"Strong edge clustering detected (density ratio 1:{1 / ratio:.2f}). "
                "Suggests edge-ring effects or peripheral circuit stress."
            )
        elif pattern_type == "uniform_random":
            return (
                "Uniform random distribution (no significant clustering). "
                "Suggests random defect mechanism, possibly process variation "
                "within spec limits."
            )
        else:
            return "Moderate spatial variation detected."
