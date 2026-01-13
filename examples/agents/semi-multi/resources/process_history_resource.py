"""
ProcessHistoryResource - Mock process change tracking

Simulates a semiconductor fab's process history system for correlating
defects with recent process changes.
"""

import sys
from pathlib import Path
from typing import Any

# Add dana_agent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "dana_agent"))

from dana.core.resource.base_resource import BaseResource


class ProcessHistoryResource(BaseResource):
    """
    Mock process history resource for process-defect correlation.

    In a real system, this would connect to:
    - Equipment recipe history (FDC data)
    - Material lot tracking (batch IDs, suppliers)
    - Maintenance logs (PM schedules, part replacements)
    - Process control charts (SPC violations)
    """

    def __init__(self, resource_id: str = "process-history"):
        """Initialize process history with mock recent changes."""
        super().__init__(resource_id=resource_id)

        # Mock recent process changes
        self.recent_changes = [
            {
                "change_id": "CHG-2025-0142",
                "date": "2025-01-13",
                "days_ago": 2,
                "process_step": "Resist spray",
                "chamber": "Chamber 3",
                "change_type": "Recipe parameter",
                "parameter": "Spray pressure",
                "old_value": "55 PSI",
                "new_value": "65 PSI",
                "reason": "Improve edge coverage",
                "approved_by": "Process Engineer J.Smith",
                "confidence": "HIGH",
            },
            {
                "change_id": "CHG-2025-0138",
                "date": "2025-01-10",
                "days_ago": 5,
                "process_step": "Resist spray",
                "chamber": "Chamber 3",
                "change_type": "Material lot",
                "parameter": "Resist material",
                "old_value": "Lot ABC-2024-12",
                "new_value": "Lot ABC-2025-01",
                "reason": "Routine lot rotation",
                "approved_by": "Materials Manager K.Lee",
                "confidence": "MEDIUM",
            },
            {
                "change_id": "CHG-2025-0095",
                "date": "2024-12-20",
                "days_ago": 26,
                "process_step": "Pre-coat bake",
                "chamber": "Hotplate 5",
                "change_type": "Equipment maintenance",
                "parameter": "Temperature calibration",
                "old_value": "120°C (±1°C)",
                "new_value": "120°C (±0.5°C)",
                "reason": "Scheduled PM",
                "approved_by": "Maintenance Tech R.Chen",
                "confidence": "LOW",
            },
        ]

    def _do_execute(self, **kwargs) -> dict[str, Any]:
        """
        Query process history for recent changes.

        Args:
            **kwargs: Should contain:
                - process_step: Process step to query
                - chamber: Optional chamber filter
                - lookback_days: Days to look back (default: 30)

        Returns:
            dict: Recent process changes with correlation confidence
        """
        process_step = kwargs.get("process_step", "")
        chamber = kwargs.get("chamber", "")
        lookback_days = kwargs.get("lookback_days", 30)

        # Filter changes by process step and chamber
        relevant_changes = []
        for change in self.recent_changes:
            # Check if process step matches
            step_match = process_step.lower() in change["process_step"].lower()

            # Check if chamber matches (if specified)
            chamber_match = True
            if chamber:
                chamber_match = chamber.lower() in change.get("chamber", "").lower()

            # Check if within lookback period
            time_match = change["days_ago"] <= lookback_days

            if step_match and chamber_match and time_match:
                relevant_changes.append(change)

        # Sort by date (most recent first)
        relevant_changes.sort(key=lambda x: x["days_ago"])

        # Identify primary correlation (most likely cause)
        primary_correlation = None
        if relevant_changes:
            # In real system: statistical correlation analysis
            # For now: most recent recipe change with HIGH confidence
            for change in relevant_changes:
                if change["confidence"] == "HIGH" and change["change_type"] == "Recipe parameter":
                    primary_correlation = {
                        "change_id": change["change_id"],
                        "change": f"{change['parameter']}: {change['old_value']} → {change['new_value']}",
                        "days_ago": change["days_ago"],
                        "confidence": change["confidence"],
                        "correlation_strength": "Strong temporal correlation",
                    }
                    break

        return {
            "correlations_found": len(relevant_changes) > 0,
            "change_count": len(relevant_changes),
            "primary_correlation": primary_correlation,
            "all_changes": relevant_changes,
        }

    def get_change_details(self, change_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific change.

        Args:
            change_id: Change identifier

        Returns:
            dict: Change details or None if not found
        """
        for change in self.recent_changes:
            if change["change_id"] == change_id:
                return change
        return None
