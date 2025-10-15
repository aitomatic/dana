"""
ResearchSession - Track research progress and enable interactive gates.

Maintains state across discovery → enrichment → validation phases,
allowing for reversibility, filtering, and re-execution of steps.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ResearchSession:
    """
    Tracks research progress and enables reversibility at gates.

    This session object is passed through all phases and gates,
    maintaining state so the agent can respond to user commands
    like "filter", "redo", "re-enrich", etc.
    """

    # Current state
    current_gate: Literal["discovery", "enrichment", "validation", "complete"] = "discovery"

    # Configuration (can be adjusted at gates)
    provinces: list[str] = field(default_factory=list)
    batch_size: int = 15
    max_companies_per_province: int | None = None

    # Results at each phase (for reversibility)
    discovered_companies: list[dict] | None = None
    enriched_companies: list[dict] = field(default_factory=list)
    validated_companies: list[dict] | None = None

    # Enrichment progress (for resuming)
    current_batch: int = 0
    total_batches: int = 0

    # Quality tracking
    quality_stats: dict | None = None
    mece_report: dict | None = None

    # Batches (for incremental delivery)
    enriched_batches: list[dict] = field(default_factory=list)

    def can_go_back(self) -> bool:
        """Check if we can go back to previous gate."""
        return self.current_gate != "discovery"

    def can_proceed(self) -> bool:
        """Check if we have data to proceed to next gate."""
        if self.current_gate == "discovery":
            return self.discovered_companies is not None and len(self.discovered_companies) > 0
        elif self.current_gate == "enrichment":
            return len(self.enriched_companies) > 0
        elif self.current_gate == "validation":
            return self.validated_companies is not None
        return False

    def reset_from_gate(self, gate: str):
        """
        Reset all data after a specific gate (for redo).

        Args:
            gate: Gate to reset from ("discovery", "enrichment", "validation")
        """
        if gate == "discovery":
            self.discovered_companies = None
            self.enriched_companies = []
            self.enriched_batches = []
            self.validated_companies = None
            self.current_batch = 0
            self.current_gate = "discovery"
        elif gate == "enrichment":
            self.enriched_companies = []
            self.enriched_batches = []
            self.validated_companies = None
            self.current_batch = 0
            self.current_gate = "enrichment"
        elif gate == "validation":
            self.validated_companies = None
            self.current_gate = "validation"

    def get_summary(self) -> dict:
        """
        Get current session summary.

        Returns:
            Dictionary with session state and statistics
        """
        return {
            "current_gate": self.current_gate,
            "provinces": self.provinces,
            "discovered_count": len(self.discovered_companies) if self.discovered_companies else 0,
            "enriched_count": len(self.enriched_companies),
            "validated_count": len(self.validated_companies) if self.validated_companies else 0,
            "batches_completed": len(self.enriched_batches),
            "mece_compliant": self.mece_report.get("mece_compliant") if self.mece_report else None,
        }
