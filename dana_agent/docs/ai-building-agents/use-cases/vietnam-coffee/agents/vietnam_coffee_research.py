"""
VietnamCoffeeResearchAgent - Research specialist for Vietnamese coffee industry.

Single specialist agent that discovers, enriches, and validates datasets of
Vietnamese coffee producers with comprehensive business intelligence.
"""

from dana.core.agent.star_agent import STARAgent


class VietnamCoffeeResearchAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    I am a research specialist focused on the Vietnamese coffee industry.

    I discover and enrich datasets of coffee producers, cooperatives, and
    processors with comprehensive business intelligence including:
    - Revenue and financial data
    - Export activity and certifications
    - Geographic and contact information
    - Strategic priority scoring

    I ensure complete coverage (MECE compliance) and provide transparent
    source tracking for all data points. I work incrementally, delivering
    results in batches rather than waiting to complete everything at once.
    </PUBLIC_DESCRIPTION>

    <PRIVATE_IDENTITY>
    I am methodical and thorough in my research process. I maintain strict
    data quality standards, distinguishing verified facts from estimates.

    I work incrementally, providing checkpoints rather than waiting to
    deliver everything at once. I track the provenance of every data point
    I collect. When I encounter gaps in data, I explicitly flag them rather
    than fabricating information.

    I understand the importance of MECE compliance and actively work to
    prevent duplicates and ensure complete coverage across provinces.
    My research is designed to scale from dozens to thousands of companies
    while maintaining data quality.
    </PRIVATE_IDENTITY>
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        """
        Initialize VietnamCoffeeResearchAgent.

        Args:
            agent_id: Agent identifier
            **kwargs: Additional arguments for STARAgent
        """
        super().__init__(agent_type="vietnam-coffee-research", agent_id=agent_id or "vietnam-coffee-research-001", **kwargs)

        # Import components
        from resources.company_data_structuring import CompanyDataStructuringResource
        from resources.source_provenance import SourceProvenanceResource
        from resources.vietnamese_data_normalization import VietnameseDataNormalizationResource
        from workflows.batch_orchestration import BatchOrchestrationWorkflow
        from workflows.company_discovery import CompanyDiscoveryWorkflow
        from workflows.company_enrichment import CompanyEnrichmentWorkflow
        from workflows.mece_validation import MECEValidationWorkflow

        from dana.lib.resources.conversation import ConversationResource
        from dana.lib.resources.web_research.extract import ExtractResource
        from dana.lib.resources.web_research.fetch import FetchResource
        from dana.lib.resources.web_research.search import SearchResource

        # Compose resources (domain-agnostic, highly reusable)
        self.with_resources(
            SearchResource(resource_id="web-search"),
            FetchResource(resource_id="web-fetch"),
            ExtractResource(resource_id="content-extract"),
            ConversationResource(resource_id="llm-reasoning"),
            VietnameseDataNormalizationResource(resource_id="vietnamese-normalize"),
            CompanyDataStructuringResource(resource_id="company-structure"),
            SourceProvenanceResource(resource_id="source-tracking"),
        )

        # Compose workflows
        self.with_workflows(
            CompanyDiscoveryWorkflow(workflow_id="discover-companies"),
            CompanyEnrichmentWorkflow(workflow_id="enrich-company"),
            MECEValidationWorkflow(workflow_id="validate-mece"),
            BatchOrchestrationWorkflow(workflow_id="orchestrate-batches"),
        )

    def research_companies(self, provinces: list[str], batch_size: int = 15, max_companies_per_province: int | None = None) -> dict:
        """
        Research coffee companies across provinces.

        This is the main entry point for using the agent.

        Args:
            provinces: List of province names (e.g., ["Đắk Lắk", "Gia Lai"])
            batch_size: Companies per batch (default: 15)
            max_companies_per_province: Optional limit for testing

        Returns:
            {
                "success": bool,
                "batches": [batch data],
                "summary": {
                    "total_companies": int,
                    "provinces": [str],
                    "mece_report": dict
                }
            }

        Example:
            >>> agent = VietnamCoffeeResearchAgent()
            >>> result = agent.research_companies(
            ...     provinces=["Đắk Lắk"],
            ...     batch_size=10,
            ...     max_companies_per_province=50  # MVP testing
            ... )
            >>> for batch in result["batches"]:
            ...     print(f"Batch {batch['batch_number']}: {batch['count']} companies")
        """
        # Use the batch orchestration workflow
        result = self.execute_workflow(
            "orchestrate-batches", provinces=provinces, batch_size=batch_size, max_companies_per_province=max_companies_per_province
        )

        return result.get("result", {})

    def discover_in_province(self, province: str, max_results: int = 100) -> dict:
        """
        Discover companies in a single province.

        Args:
            province: Province name
            max_results: Maximum companies to discover

        Returns:
            Discovery result with company list
        """
        result = self.execute_workflow("discover-companies", province=province, max_results=max_results)

        return result.get("result", {})

    def enrich_company(self, company_name: str, tax_id: str, province: str) -> dict:
        """
        Enrich a single company with all fields.

        Args:
            company_name: Company name
            tax_id: Vietnamese tax ID
            province: Province

        Returns:
            Enrichment result with all fields
        """
        result = self.execute_workflow("enrich-company", company_name=company_name, tax_id=tax_id, province=province)

        return result.get("result", {})

    def validate_mece(self, companies: list[dict]) -> dict:
        """
        Validate MECE compliance of a dataset.

        Args:
            companies: List of company dictionaries

        Returns:
            Validation result with MECE report
        """
        result = self.execute_workflow("validate-mece", companies=companies)

        return result.get("result", {})

    def get_quality_report(self, company_ids: list[str] | None = None) -> dict:
        """
        Get data quality report.

        Args:
            company_ids: Optional list of tax IDs (if None, reports on all)

        Returns:
            Quality metrics across all tracked companies
        """
        # Access the source provenance resource
        provenance_resource = self.get_resource("source-tracking")

        if provenance_resource:
            result = provenance_resource.batch_quality_report(company_ids=company_ids)
            return result
        else:
            return {"success": False, "error": "Source tracking resource not available"}
