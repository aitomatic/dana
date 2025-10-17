"""
DefectDatabaseResource - Mock historical defect pattern database

Simulates a semiconductor fab's defect database with historical cases
for pattern matching and root cause learning.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add dana_agent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "dana_agent"))

from dana.core.resource.base_resource import BaseResource


class DefectDatabaseResource(BaseResource):
    """
    Mock defect database resource for historical pattern matching.

    In a real system, this would connect to:
    - Defect library (classification, known patterns)
    - Historical case database (previous investigations)
    - Image repository (SEM/TEM images)
    - Resolution tracking (what fixes worked)
    """

    def __init__(self, resource_id: str = "defect-database"):
        """Initialize defect database with mock historical data."""
        super().__init__(resource_id=resource_id)

        # Mock historical defect cases
        self.historical_cases = [
            {
                "case_id": "2023-DEF-0142",
                "date": "2023-08-15",
                "product": "CPU_7nm_A53",
                "defect_type": "Circular clusters",
                "pattern": "Circular clusters, ~5μm diameter, wafer edge",
                "location": "Wafer edge, 90° sector",
                "frequency": "12%",
                "process_step": "Resist spray, Chamber 3",
                "root_cause": "Resist nozzle clogging",
                "fix_action": "Nozzle cleaning and spray pressure reduction",
                "effectiveness": "100% resolution",
                "similarity_score": 0.85
            },
            {
                "case_id": "2024-DEF-0089",
                "date": "2024-03-22",
                "product": "GPU_5nm_X1",
                "defect_type": "Edge exclusion defects",
                "pattern": "Irregular patterns at wafer edge",
                "location": "Wafer edge, 180° sector",
                "frequency": "20%",
                "process_step": "Resist coating",
                "root_cause": "Vacuum chuck seal degradation",
                "fix_action": "Chuck seal replacement",
                "effectiveness": "95% reduction",
                "similarity_score": 0.45
            },
            {
                "case_id": "2023-DEF-0298",
                "date": "2023-11-10",
                "product": "CPU_7nm_B52",
                "defect_type": "Spray pattern defects",
                "pattern": "Radial patterns from center",
                "location": "Wafer center",
                "frequency": "8%",
                "process_step": "Resist spray, Chamber 1",
                "root_cause": "Nozzle alignment drift",
                "fix_action": "Nozzle realignment and calibration",
                "effectiveness": "100% resolution",
                "similarity_score": 0.62
            }
        ]

    def _do_execute(self, **kwargs) -> Dict[str, Any]:
        """
        Query defect database for pattern matching.

        Args:
            **kwargs: Should contain:
                - defect_pattern: Pattern description to match
                - process_step: Process step to filter on
                - min_similarity: Minimum similarity threshold (default: 0.4)

        Returns:
            dict: Matching cases with similarity scores
        """
        defect_pattern = kwargs.get("defect_pattern", "")
        process_step = kwargs.get("process_step", "")
        min_similarity = kwargs.get("min_similarity", 0.4)

        # Simple pattern matching (in real system: ML-based similarity)
        matches = []
        for case in self.historical_cases:
            # Check if pattern keywords match
            pattern_match = any(
                keyword in case["pattern"].lower()
                for keyword in ["circular", "cluster", "edge"]
                if keyword in defect_pattern.lower()
            )

            # Check if process step matches
            step_match = process_step.lower() in case["process_step"].lower()

            if pattern_match and step_match:
                # Boost similarity if both match
                case_copy = case.copy()
                if case["similarity_score"] >= min_similarity:
                    matches.append(case_copy)

        # Sort by similarity score
        matches.sort(key=lambda x: x["similarity_score"], reverse=True)

        return {
            "matches_found": len(matches) > 0,
            "match_count": len(matches),
            "best_match": matches[0] if matches else None,
            "all_matches": matches
        }

    def get_case_details(self, case_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific case.

        Args:
            case_id: Case identifier

        Returns:
            dict: Case details or None if not found
        """
        for case in self.historical_cases:
            if case["case_id"] == case_id:
                return case
        return None
