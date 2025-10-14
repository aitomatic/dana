"""
SourceProvenanceResource - Track data lineage and quality.

Domain-agnostic resource for tracking where data came from and its confidence level.
Useful for any research project requiring transparency and audit trails.
"""

from dana.common.protocols.types import DictParams
from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class SourceProvenanceResource(BaseResource):
    """
    <PUBLIC_DESCRIPTION>
    Tracks the provenance (origin) of data fields with confidence scoring.

    For each piece of data, records:
    - Source URL or identifier
    - Timestamp of collection
    - Confidence level (0.0-1.0)
    - Data quality notes

    Provides transparency for research projects where data quality
    and source verification are critical.
    </PUBLIC_DESCRIPTION>
    """

    def __init__(self, resource_id: str | None = None, **kwargs):
        """Initialize the SourceProvenanceResource."""
        super().__init__(resource_type="source-provenance", resource_id=resource_id or "source-provenance", **kwargs)
        # In-memory provenance store (company_id -> field -> provenance)
        self.provenance_db = {}

    @tool_use
    def record_source(
        self,
        company_id: str,
        field: str,
        value: str | int | float | bool | None,
        source_url: str,
        confidence: float,
        notes: str | None = None,
        **kwargs,
    ) -> DictParams:
        """
        Record the source of a data field.

        Args:
            company_id: Unique identifier for the company
            field: Name of the field (e.g., "revenue", "export_status")
            value: The actual value of the field
            source_url: URL or identifier of the data source
            confidence: Confidence score (0.0-1.0)
            notes: Optional notes about data quality or extraction

        Returns:
            Success confirmation
        """
        if company_id not in self.provenance_db:
            self.provenance_db[company_id] = {}

        self.provenance_db[company_id][field] = {
            "value": value,
            "source_url": source_url,
            "confidence": confidence,
            "notes": notes,
        }

        return {"success": True, "company_id": company_id, "field": field, "recorded": True}

    @tool_use
    def get_provenance(self, company_id: str, field: str | None = None, **kwargs) -> DictParams:
        """
        Get provenance information for a company's fields.

        Args:
            company_id: Unique identifier for the company
            field: Optional specific field (if None, returns all fields)

        Returns:
            Provenance data for requested field(s)
        """
        if company_id not in self.provenance_db:
            return {"success": False, "error": f"No provenance data for company {company_id}", "provenance": None}

        company_data = self.provenance_db[company_id]

        if field:
            if field in company_data:
                return {"success": True, "company_id": company_id, "field": field, "provenance": company_data[field]}
            else:
                return {"success": False, "error": f"No provenance data for field {field}", "provenance": None}

        # Return all fields
        return {"success": True, "company_id": company_id, "provenance": company_data}

    @tool_use
    def get_quality_report(self, company_id: str, **kwargs) -> DictParams:
        """
        Generate a data quality report for a company.

        Args:
            company_id: Unique identifier for the company

        Returns:
            Quality metrics (confidence distribution, source diversity, etc.)
        """
        if company_id not in self.provenance_db:
            return {"success": False, "error": f"No provenance data for company {company_id}", "report": None}

        company_data = self.provenance_db[company_id]

        # Calculate quality metrics
        confidences = [data["confidence"] for data in company_data.values()]
        sources = list(set(data["source_url"] for data in company_data.values()))

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        high_confidence_count = sum(1 for c in confidences if c >= 0.8)
        medium_confidence_count = sum(1 for c in confidences if 0.5 <= c < 0.8)
        low_confidence_count = sum(1 for c in confidences if c < 0.5)

        return {
            "success": True,
            "company_id": company_id,
            "report": {
                "total_fields": len(company_data),
                "average_confidence": avg_confidence,
                "confidence_distribution": {
                    "high (>=0.8)": high_confidence_count,
                    "medium (0.5-0.8)": medium_confidence_count,
                    "low (<0.5)": low_confidence_count,
                },
                "unique_sources": len(sources),
                "sources": sources,
            },
        }

    @tool_use
    def batch_quality_report(self, company_ids: list[str] | None = None, **kwargs) -> DictParams:
        """
        Generate aggregate quality report across multiple companies.

        Args:
            company_ids: List of company IDs (if None, reports on all)

        Returns:
            Aggregate quality metrics
        """
        target_ids = company_ids or list(self.provenance_db.keys())

        if not target_ids:
            return {"success": False, "error": "No companies in provenance database", "report": None}

        all_confidences = []
        all_sources = set()
        companies_analyzed = 0

        for company_id in target_ids:
            if company_id in self.provenance_db:
                companies_analyzed += 1
                company_data = self.provenance_db[company_id]
                confidences = [data["confidence"] for data in company_data.values()]
                all_confidences.extend(confidences)
                sources = set(data["source_url"] for data in company_data.values())
                all_sources.update(sources)

        if not all_confidences:
            return {"success": False, "error": "No data to analyze", "report": None}

        avg_confidence = sum(all_confidences) / len(all_confidences)
        high_confidence_pct = (sum(1 for c in all_confidences if c >= 0.8) / len(all_confidences)) * 100
        medium_confidence_pct = (sum(1 for c in all_confidences if 0.5 <= c < 0.8) / len(all_confidences)) * 100
        low_confidence_pct = (sum(1 for c in all_confidences if c < 0.5) / len(all_confidences)) * 100

        return {
            "success": True,
            "report": {
                "companies_analyzed": companies_analyzed,
                "total_data_points": len(all_confidences),
                "average_confidence": avg_confidence,
                "confidence_distribution": {
                    "high (>=0.8)": f"{high_confidence_pct:.1f}%",
                    "medium (0.5-0.8)": f"{medium_confidence_pct:.1f}%",
                    "low (<0.5)": f"{low_confidence_pct:.1f}%",
                },
                "unique_sources": len(all_sources),
                "sources": list(all_sources),
            },
        }
