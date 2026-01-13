"""
BatchOrchestrationWorkflow - Orchestrate full research process.

Main workflow that coordinates:
1. Discovery (parallel by province)
2. Enrichment (batched)
3. Validation (MECE compliance)
"""

from dana.common.protocols.types import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output


class BatchOrchestrationWorkflow(BaseWorkflow):
    """
    Orchestrate complete research process across provinces.

    Phases:
    1. Discovery - Find all companies (parallel by province)
    2. Enrichment - Enrich in batches
    3. Validation - Ensure MECE compliance

    Provides incremental output after each batch.
    """

    def __init__(self, workflow_id: str | None = None, approval_callback=None, **kwargs):
        """
        Initialize BatchOrchestrationWorkflow.

        Args:
            workflow_id: Unique workflow identifier
            approval_callback: Optional function(gate_data: dict) -> bool
                Called at each gate. Returns True to proceed, False to abort.
                Gate types: "discovery", "enrichment", "final"
            **kwargs: Additional workflow parameters
        """
        super().__init__(workflow_id=workflow_id or "batch-orchestration", **kwargs)

        from workflows.company_discovery import CompanyDiscoveryWorkflow
        from workflows.company_enrichment import CompanyEnrichmentWorkflow
        from workflows.mece_validation import MECEValidationWorkflow

        self.discovery_workflow = CompanyDiscoveryWorkflow()
        self.enrichment_workflow = CompanyEnrichmentWorkflow()
        self.validation_workflow = MECEValidationWorkflow()
        self.approval_callback = approval_callback

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

                # Unwrap the result
                inner_result = discovery_result.get("result", {})
                if inner_result.get("success"):
                    companies = inner_result.get("companies", [])
                    all_discovered.extend(companies)

            if not all_discovered:
                return {"success": False, "error": "No companies discovered", "batches": [], "summary": {}}

            # >>> GATE 1: DISCOVERY APPROVAL <<<
            if self.approval_callback:
                gate_data = {
                    "gate": "discovery",
                    "total_companies": len(all_discovered),
                    "provinces": provinces,
                    "sample": all_discovered[:10],  # Show first 10 companies
                }
                approved = self.approval_callback(gate_data)
                if not approved:
                    return {"success": False, "aborted_at": "discovery", "batches": [], "summary": {}}

            # Phase 2: Enrichment (batched, with parallel processing within batches)
            enriched_batches = []
            all_enriched = []

            # Split into batches
            for i in range(0, len(all_discovered), batch_size):
                batch = all_discovered[i : i + batch_size]
                batch_number = (i // batch_size) + 1

                # Enrich companies in parallel within this batch
                enriched_batch = self._enrich_batch_parallel(batch)
                all_enriched.extend(enriched_batch)

                # Store batch
                enriched_batches.append({"batch_number": batch_number, "companies": enriched_batch, "count": len(enriched_batch)})

                # >>> GATE 2: ENRICHMENT PROGRESS REVIEW (every 5 batches) <<<
                if self.approval_callback and batch_number % 5 == 0:
                    quality_preview = self._compute_quality_preview(all_enriched)
                    gate_data = {
                        "gate": "enrichment",
                        "batch_number": batch_number,
                        "total_batches": (len(all_discovered) + batch_size - 1) // batch_size,  # Ceiling division
                        "enriched_so_far": len(all_enriched),
                        "total_to_enrich": len(all_discovered),
                        "sample": enriched_batch[:5],  # Show 5 from latest batch
                        "quality_preview": quality_preview,
                    }
                    approved = self.approval_callback(gate_data)
                    if not approved:
                        return {
                            "success": False,
                            "aborted_at": f"enrichment_batch_{batch_number}",
                            "batches": enriched_batches,
                            "summary": {
                                "total_companies": len(all_enriched),
                                "provinces": provinces,
                                "batches_created": len(enriched_batches),
                            },
                        }

            # Phase 3: Validation
            validation_result = self.validation_workflow.execute(companies=all_enriched, expected_provinces=provinces)

            # Unwrap the result
            inner_result = validation_result.get("result", {})
            mece_report = inner_result.get("mece_report", {}) if inner_result.get("success") else {}

            # >>> GATE 3: FINAL APPROVAL <<<
            if self.approval_callback:
                quality_report = self._compute_quality_preview(all_enriched)
                gate_data = {
                    "gate": "final",
                    "total_companies": len(all_enriched),
                    "provinces": provinces,
                    "mece_report": mece_report,
                    "quality_report": quality_report,
                }
                approved = self.approval_callback(gate_data)
                if not approved:
                    return {
                        "success": False,
                        "aborted_at": "final_review",
                        "batches": enriched_batches,
                        "summary": {
                            "total_companies": len(all_enriched),
                            "provinces": provinces,
                            "batches_created": len(enriched_batches),
                            "mece_report": mece_report,
                        },
                    }

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

    def _enrich_batch_parallel(self, batch: list[dict], max_workers: int = 5) -> list[dict]:
        """
        Enrich companies in parallel using ThreadPoolExecutor.

        Processes up to max_workers companies simultaneously to speed up enrichment.

        Args:
            batch: List of companies to enrich
            max_workers: Maximum parallel workers (default: 5)

        Returns:
            List of enriched companies
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def enrich_single(company: dict) -> dict | None:
            """Enrich a single company."""
            try:
                enrich_result = self.enrichment_workflow.execute(
                    company_name=company["name"], tax_id=company["tax_id"], province=company["province"]
                )

                inner_result = enrich_result.get("result", {})
                if inner_result.get("success"):
                    return inner_result.get("enriched_company", {})
            except Exception as e:
                print(f"Warning: Failed to enrich {company.get('name')}: {e}")

            return None

        enriched_companies = []

        # Use ThreadPoolExecutor for I/O-bound operations (web fetching)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all enrichment tasks
            future_to_company = {executor.submit(enrich_single, company): company for company in batch}

            # Collect results as they complete
            for future in as_completed(future_to_company):
                company = future_to_company[future]
                try:
                    enriched = future.result()
                    if enriched:
                        enriched_companies.append(enriched)
                except Exception as e:
                    print(f"Error enriching {company.get('name')}: {e}")

        return enriched_companies

    def _compute_quality_preview(self, companies: list[dict]) -> dict:
        """
        Compute quality distribution for enriched companies.

        Args:
            companies: List of enriched company dictionaries

        Returns:
            {
                "high": int,    # confidence >= 0.8
                "medium": int,  # 0.5 <= confidence < 0.8
                "low": int,     # confidence < 0.5
                "high_pct": float,
                "medium_pct": float,
                "low_pct": float
            }
        """
        if not companies:
            return {"high": 0, "medium": 0, "low": 0, "high_pct": 0.0, "medium_pct": 0.0, "low_pct": 0.0}

        high = sum(1 for c in companies if c.get("confidence", 0) >= 0.8)
        medium = sum(1 for c in companies if 0.5 <= c.get("confidence", 0) < 0.8)
        low = sum(1 for c in companies if c.get("confidence", 0) < 0.5)
        total = len(companies)

        return {
            "high": high,
            "medium": medium,
            "low": low,
            "high_pct": (high / total * 100) if total > 0 else 0,
            "medium_pct": (medium / total * 100) if total > 0 else 0,
            "low_pct": (low / total * 100) if total > 0 else 0,
        }
