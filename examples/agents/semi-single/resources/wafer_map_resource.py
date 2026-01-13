"""WaferMapResource - Provides spatial defect distribution data for wafers."""

from dana.core.resource.base_resource import BaseResource
from dana.common.protocols import DictParams


class WaferMapResource(BaseResource):
    """
    Resource for retrieving spatial defect maps of wafers.

    Provides spatial coordinates of defects, allowing analysis of
    clustering, edge vs center distribution, etc.
    """

    def __init__(self, resource_id: str = "wafer-map"):
        super().__init__(resource_id=resource_id)

    def get_spatial_data(self, wafer_id: str, bin_id: str) -> DictParams:
        """
        Get spatial defect distribution for a specific bin.

        Args:
            wafer_id: Wafer identifier
            bin_id: Failure bin identifier

        Returns:
            Spatial data with defect coordinates and density maps
        """
        # Mock data for demo - in production, would query actual fab database

        if bin_id == "BIN_1":
            # SRAM bit failures - clustered in center
            return {
                "wafer_id": wafer_id,
                "bin_id": bin_id,
                "defect_count": 180,
                "defect_locations": [
                    {"x": 50, "y": 50, "die_id": "D_050_050"},
                    {"x": 51, "y": 50, "die_id": "D_051_050"},
                    {"x": 50, "y": 51, "die_id": "D_050_051"},
                    {"x": 49, "y": 50, "die_id": "D_049_050"},
                    {"x": 52, "y": 52, "die_id": "D_052_052"},
                    # ... 175 more clustered defects in center region
                ],
                "spatial_distribution": {
                    "center_region": {"count": 147, "density": 0.82},
                    "mid_region": {"count": 28, "density": 0.23},
                    "edge_region": {"count": 5, "density": 0.05},
                },
                "wafer_diameter_mm": 300,
                "die_size_mm": 10,
            }
        elif bin_id == "BIN_2":
            # Logic timing violations - random distribution
            return {
                "wafer_id": wafer_id,
                "bin_id": bin_id,
                "defect_count": 75,
                "defect_locations": [
                    {"x": 10, "y": 25, "die_id": "D_010_025"},
                    {"x": 87, "y": 63, "die_id": "D_087_063"},
                    {"x": 33, "y": 91, "die_id": "D_033_091"},
                    {"x": 72, "y": 14, "die_id": "D_072_014"},
                    # ... 71 more randomly distributed defects
                ],
                "spatial_distribution": {
                    "center_region": {"count": 24, "density": 0.13},
                    "mid_region": {"count": 28, "density": 0.23},
                    "edge_region": {"count": 23, "density": 0.23},
                },
                "wafer_diameter_mm": 300,
                "die_size_mm": 10,
            }
        else:
            return {"error": f"No spatial data available for {bin_id}"}

    def get_wafer_map_image(self, wafer_id: str) -> DictParams:
        """
        Get full wafer map visualization data.

        Returns:
            Wafer map data with all defects marked
        """
        return {
            "wafer_id": wafer_id,
            "image_format": "png",
            "image_url": f"/data/wafer_maps/{wafer_id}_map.png",
            "resolution": "1000x1000",
            "color_coding": {"BIN_1": "red", "BIN_2": "blue", "BIN_3": "green"},
        }
