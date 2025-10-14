"""
BatchOrchestrationWorkflow - Orchestrate full research process.

Main workflow that coordinates:
1. Discovery (parallel by province)
2. Enrichment (batched)
3. Validation (MECE compliance)
"""

from dana.common.protocols.types import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow, validate_input, validate_output


class BatchOrchestrationWorkflow(BaseWorkflow):
    """
    Orchestrate complete research process across provinces.

    Phases:
    1. Discovery - Find all companies (parallel by province)
    2. Enrichment - Enrich in batches
    3. Validation - Ensure MECE compliance

    Provides incremental output after each batch.
    """

    def __init__(self, workflow_id: str | None = None, **kwargs):
        super().__init__(workflow_id=workflow_id or "batch-orchestration", **kwargs)

        from .company_discovery import CompanyDiscoveryWorkflow
        from .company_enrichment import CompanyEnrichmentWorkflow
        from .mece_validation import MECEValidationWorkflow

        self.discovery_workflow = CompanyDiscoveryWorkflow()
        self.enrichment_workflow = CompanyEnrichmentWorkflow()
        self.validation_workflow = MECEValidationWorkflow()

    @validate_input(
        provinces={"required": True, "type": list, "min_length": 1},
        batch_size={"type": int, "min_value": 1, "max_value": 50, "default": 15},
    )
    @validate_output(
        success={"required": True, "type": bool},
        batches={"required": True, "type": list},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute full research process.

        Args:
            provinces: List of province names
            batch_size: Number of companies per batch (default: 15)
            max_companies_per_province: Optional limit for MVP testing

        Returns:
            {
                "success": bool,
                "batches": [
                    {
                        "batch_number": int,
                        "companies": [enriched company dicts],
                        "count": int
                    },
                    ...
                ],
                "summary": {
                    "total_companies": int,
                    "provinces": [str],
                    "mece_report": dict
                }
            }
        """
        provinces = kwargs["provinces"]
        batch_size = kwargs.get("batch_size", 15)
        max_per_province = kwargs.get("max_companies_per_province", None)

        try:
            # Phase 1: Discovery (parallel by province)
            all_discovered = []

            for province in provinces:
                discovery_result = self.discovery_workflow.execute(province=province, max_results=max_per_province or 100)

                if discovery_result["success"]:
                    companies = discovery_result["result"]["companies"]
                    all_discovered.extend(companies)

            if not all_discovered:
                return {"success": False, "error": "No companies discovered", "batches": [], "summary": {}}

            # Phase 2: Enrichment (batched)
            enriched_batches = []
            all_enriched = []

            # Split into batches
            for i in range(0, len(all_discovered), batch_size):
                batch = all_discovered[i : i + batch_size]
                batch_number = (i // batch_size) + 1

                # Enrich each company in batch
                enriched_batch = []
                for company in batch:
                    enrich_result = self.enrichment_workflow.execute(
                        company_name=company["name"], tax_id=company["tax_id"], province=company["province"]
                    )

                    if enrich_result["success"]:
                        enriched_company = enrich_result["result"]["enriched_company"]
                        enriched_batch.append(enriched_company)
                        all_enriched.append(enriched_company)

                # Store batch
                enriched_batches.append({"batch_number": batch_number, "companies": enriched_batch, "count": len(enriched_batch)})

            # Phase 3: Validation
            validation_result = self.validation_workflow.execute(companies=all_enriched, expected_provinces=provinces)

            mece_report = validation_result["result"]["mece_report"] if validation_result["success"] else {}

            return {
                "success": True,
                "batches": enriched_batches,
                "summary": {
                    "total_companies": len(all_enriched),
                    "provinces": provinces,
                    "batches_created": len(enriched_batches),
                    "mece_report": mece_report,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e), "batches": [], "summary": {}}
