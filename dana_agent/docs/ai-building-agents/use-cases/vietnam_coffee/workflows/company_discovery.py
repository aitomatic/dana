"""
CompanyDiscoveryWorkflow - Discover coffee companies in target provinces.

This workflow orchestrates the discovery of coffee producers from multiple sources:
- Government business registries (masothue.com)
- Industry association lists (VICOFA)
- Export databases

For MVP: Demonstrates the pattern with simulated discovery. In production,
would integrate with actual Vietnamese government APIs and web scraping.
"""

from dana.common.protocols.types import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow, validate_input, validate_output


class CompanyDiscoveryWorkflow(BaseWorkflow):
    """
    Discover all coffee companies in a target province.

    Responsibilities:
    - Query multiple data sources (government, associations, export DB)
    - Deduplicate across sources
    - Return candidate list with basic info

    Success Criteria:
    - Recall: ≥95% of registered companies found
    - Precision: ≥90% are actual coffee producers
    - No duplicates in output
    """

    def __init__(self, workflow_id: str | None = None, **kwargs):
        """
        Initialize CompanyDiscoveryWorkflow.

        Args:
            workflow_id: Workflow identifier
            **kwargs: Additional arguments for BaseWorkflow
        """
        super().__init__(workflow_id=workflow_id or "company-discovery", **kwargs)

        # Import resources dynamically to avoid circular imports
        from dana.lib.resources.web_research.fetch import FetchResource
        from dana.lib.resources.web_research.search import SearchResource

        from ..resources.vietnamese_data_normalization import VietnameseDataNormalizationResource

        self.search_resource = SearchResource()
        self.fetch_resource = FetchResource()
        self.vietnamese_norm = VietnameseDataNormalizationResource()

    @validate_input(
        province={"required": True, "type": str, "min_length": 2},
        industry_keywords={"type": list, "default": ["coffee", "cà phê"]},
        max_results={"type": int, "min_value": 1, "max_value": 1000, "default": 100},
    )
    @validate_output(
        success={"required": True, "type": bool},
        companies={"required": True, "type": list},
        sources_queried={"required": True, "type": list},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Discover companies in the target province.

        Args:
            province (str): Province name (e.g., "Đắk Lắk")
            industry_keywords (list): Keywords for filtering (default: ["coffee", "cà phê"])
            max_results (int): Maximum companies to return

        Returns:
            {
                "success": bool,
                "companies": [
                    {
                        "name": str,
                        "tax_id": str,
                        "province": str,
                        "sources": [str],  # Which sources found this company
                        "confidence": float
                    },
                    ...
                ],
                "sources_queried": [str],
                "total_found": int,
                "duplicates_removed": int
            }
        """
        province = kwargs["province"]
        industry_keywords = kwargs.get("industry_keywords", ["coffee", "cà phê"])
        max_results = kwargs.get("max_results", 100)

        try:
            # Step 1: Query multiple sources in parallel
            # (In production, these would be actual API calls)
            government_companies = self._query_government_registry(province, industry_keywords)

            association_companies = self._query_vicofa(province)

            export_companies = self._query_export_database(province, industry_keywords)

            # Step 2: Merge results from all sources
            all_companies = []
            all_companies.extend(government_companies)
            all_companies.extend(association_companies)
            all_companies.extend(export_companies)

            # Step 3: Deduplicate
            deduplicated, duplicates_count = self._deduplicate_companies(all_companies)

            # Step 4: Limit results
            limited = deduplicated[:max_results]

            return {
                "success": True,
                "companies": limited,
                "sources_queried": ["government_registry", "vicofa", "export_database"],
                "total_found": len(limited),
                "duplicates_removed": duplicates_count,
                "province": province,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "companies": [], "sources_queried": [], "total_found": 0, "duplicates_removed": 0}

    # ============================================================================
    # SOURCE QUERY METHODS (MVP: Simulated)
    # ============================================================================

    def _query_government_registry(self, province: str, keywords: list[str]) -> list[dict]:
        """
        Query government business registry (masothue.com).

        MVP: Returns simulated data. In production, would:
        1. Use SearchResource to find masothue.com search page
        2. Use FetchResource to POST search query
        3. Parse HTML results
        4. Extract company data

        Args:
            province: Province name
            keywords: Industry keywords to filter by

        Returns:
            List of companies from government registry
        """
        # MVP: Simulated data for demonstration
        # In production: actual web scraping implementation

        simulated_companies = [
            {
                "name": f"Công ty TNHH Cà phê {province} {i}",
                "tax_id": f"010{i:07d}",
                "province": province,
                "sources": ["government_registry"],
                "confidence": 0.95,  # High confidence from official source
            }
            for i in range(1, 11)  # Simulate 10 companies
        ]

        return simulated_companies

    def _query_vicofa(self, province: str) -> list[dict]:
        """
        Query Vietnam Coffee & Cocoa Association member list.

        MVP: Returns simulated data. In production, would:
        1. Use FetchResource to get VICOFA member directory
        2. Filter by province
        3. Extract member information

        Args:
            province: Province name

        Returns:
            List of companies from VICOFA
        """
        # MVP: Simulated data
        simulated_companies = [
            {
                "name": f"Công ty Cổ phần Cà phê Hữu cơ {province} {i}",
                "tax_id": f"020{i:07d}",
                "province": province,
                "sources": ["vicofa"],
                "confidence": 0.85,  # Good confidence from association
            }
            for i in range(1, 6)  # Simulate 5 association members
        ]

        return simulated_companies

    def _query_export_database(self, province: str, keywords: list[str]) -> list[dict]:
        """
        Query Vietnam customs export database.

        MVP: Returns simulated data. In production, would:
        1. Use FetchResource to query customs database
        2. Filter by HS code for coffee (0901*)
        3. Filter by province
        4. Extract exporter information

        Args:
            province: Province name
            keywords: Product keywords

        Returns:
            List of companies from export database
        """
        # MVP: Simulated data
        simulated_companies = [
            {
                "name": f"Công ty Xuất khẩu Cà phê {province} {i}",
                "tax_id": f"030{i:07d}",
                "province": province,
                "sources": ["export_database"],
                "confidence": 0.90,  # High confidence (verified exporters)
            }
            for i in range(1, 8)  # Simulate 7 exporters
        ]

        return simulated_companies

    # ============================================================================
    # DEDUPLICATION
    # ============================================================================

    def _deduplicate_companies(self, companies: list[dict]) -> tuple[list[dict], int]:
        """
        Deduplicate companies using tax ID (primary) and fuzzy name matching (secondary).

        Args:
            companies: List of company dictionaries

        Returns:
            (deduplicated_list, duplicates_removed_count)
        """
        seen_tax_ids = {}
        seen_names = {}
        deduplicated = []
        duplicates_count = 0

        for company in companies:
            tax_id = company.get("tax_id")
            name = company.get("name")

            # Primary: Deduplicate by tax ID
            if tax_id and tax_id in seen_tax_ids:
                # Merge sources from duplicate
                existing = seen_tax_ids[tax_id]
                existing_sources = set(existing.get("sources", []))
                new_sources = set(company.get("sources", []))
                existing["sources"] = list(existing_sources | new_sources)

                # Keep higher confidence
                existing["confidence"] = max(existing.get("confidence", 0), company.get("confidence", 0))

                duplicates_count += 1
                continue

            # Secondary: Fuzzy match by name
            is_duplicate = False
            if name:
                # Normalize name for comparison
                norm_result = self.vietnamese_norm.normalize_company_name(name)
                if norm_result["success"]:
                    dedup_key = norm_result["deduplication_key"]

                    # Check if similar name already exists
                    for existing_key, existing_company in seen_names.items():
                        # Simple similarity check (could use fuzzy_match for production)
                        if dedup_key == existing_key:
                            # Merge
                            existing_sources = set(existing_company.get("sources", []))
                            new_sources = set(company.get("sources", []))
                            existing_company["sources"] = list(existing_sources | new_sources)

                            existing_company["confidence"] = max(existing_company.get("confidence", 0), company.get("confidence", 0))

                            duplicates_count += 1
                            is_duplicate = True
                            break

                    if is_duplicate:
                        continue

                    # Add to seen names
                    seen_names[dedup_key] = company

            # Not a duplicate - add to results
            if tax_id:
                seen_tax_ids[tax_id] = company

            deduplicated.append(company)

        return deduplicated, duplicates_count
