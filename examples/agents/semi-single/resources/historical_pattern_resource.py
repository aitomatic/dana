"""HistoricalPatternResource - Provides access to historical failure pattern database."""

from dana.core.resource.base_resource import BaseResource
from dana.common.protocols import DictParams


class HistoricalPatternResource(BaseResource):
    """
    Resource for querying historical failure patterns.

    Allows comparison with past systematic/random patterns to
    leverage historical knowledge.
    """

    def __init__(self, resource_id: str = "historical-patterns"):
        super().__init__(resource_id=resource_id)

    def find_similar_patterns(self, pattern_signature: DictParams) -> DictParams:
        """
        Find historical patterns similar to current pattern.

        Args:
            pattern_signature: Characteristics of current pattern
                (spatial distribution, defect density, etc.)

        Returns:
            Similar historical cases with outcomes
        """
        # Mock historical database for demo
        bin_id = pattern_signature.get("bin_id", "")

        if bin_id == "BIN_1":
            # Matches known systematic gate oxide defect case
            return {
                "query": pattern_signature,
                "matches": [
                    {
                        "case_id": "CASE_2024_045",
                        "similarity_score": 0.91,
                        "product": "CPU_7nm_A72",
                        "defect_type": "SRAM_bit_line_short",
                        "pattern_type": "SYSTEMATIC",
                        "root_cause": "Gate oxide pinhole due to metal contamination",
                        "spatial_pattern": "center_clustered",
                        "resolution": "Increased post-CMP clean time from 45s to 75s",
                        "time_to_fix_days": 12,
                        "yield_improvement": 8.5,
                        "confidence": 0.91,
                    },
                    {
                        "case_id": "CASE_2023_128",
                        "similarity_score": 0.76,
                        "product": "CPU_7nm_A53",
                        "defect_type": "SRAM_gate_oxide_breakdown",
                        "pattern_type": "SYSTEMATIC",
                        "root_cause": "Thin oxide in center region due to CMP non-uniformity",
                        "resolution": "Optimized CMP pressure profile",
                        "time_to_fix_days": 18,
                        "yield_improvement": 6.2,
                        "confidence": 0.76,
                    },
                ],
                "best_match": "CASE_2024_045",
            }
        elif bin_id == "BIN_2":
            # Matches random defect pattern
            return {
                "query": pattern_signature,
                "matches": [
                    {
                        "case_id": "CASE_2024_067",
                        "similarity_score": 0.68,
                        "product": "CPU_5nm_X1",
                        "defect_type": "timing_violations_random",
                        "pattern_type": "RANDOM",
                        "root_cause": "Process variation within spec limits",
                        "resolution": "Tightened design margins, no process change",
                        "time_to_fix_days": 45,
                        "yield_improvement": 1.2,
                        "confidence": 0.68,
                    }
                ],
                "best_match": "CASE_2024_067",
            }
        else:
            return {"matches": [], "message": "No similar historical patterns found"}

    def get_systematic_pattern_library(self) -> DictParams:
        """
        Get library of known systematic defect patterns.

        Returns:
            Database of systematic patterns with signatures
        """
        return {
            "systematic_patterns": [
                {
                    "pattern_id": "SYSTEMATIC_001",
                    "name": "Center-clustered oxide defects",
                    "signature": {"spatial": "center_weighted", "morans_i_range": [0.75, 0.95], "center_density_ratio": [4.0, 8.0]},
                    "typical_causes": ["CMP non-uniformity", "metal contamination", "thin oxide"],
                },
                {
                    "pattern_id": "SYSTEMATIC_002",
                    "name": "Edge-ring defects",
                    "signature": {"spatial": "edge_weighted", "morans_i_range": [0.70, 0.90], "edge_density_ratio": [5.0, 10.0]},
                    "typical_causes": ["Edge bead removal issues", "peripheral circuit stress"],
                },
            ]
        }
