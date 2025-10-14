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

    def research_companies(
        self, provinces: list[str], batch_size: int = 15, max_companies_per_province: int | None = None, interactive: bool = True
    ) -> dict:
        """
        Research coffee companies across provinces.

        This is the main entry point for using the agent.

        Args:
            provinces: List of province names (e.g., ["Đắk Lắk", "Gia Lai"])
            batch_size: Companies per batch (default: 15)
            max_companies_per_province: Optional limit for testing
            interactive: Enable human approval gates (default: True)

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
            ...     max_companies_per_province=50,  # MVP testing
            ...     interactive=True  # Enable approval gates with rich commands
            ... )
            >>> for batch in result["batches"]:
            ...     print(f"Batch {batch['batch_number']}: {batch['count']} companies")
        """
        # Initialize research session
        from agents.research_session import ResearchSession

        self.session = ResearchSession(
            provinces=provinces.copy(), batch_size=batch_size, max_companies_per_province=max_companies_per_province
        )

        # Get the batch orchestration workflow and execute it
        from workflows.batch_orchestration import BatchOrchestrationWorkflow

        # Create approval callback if interactive mode
        approval_callback = self._create_approval_gate() if interactive else None

        workflow = BatchOrchestrationWorkflow(approval_callback=approval_callback)
        result = workflow.execute(provinces=provinces, batch_size=batch_size, max_companies_per_province=max_companies_per_province)

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
        from workflows.company_discovery import CompanyDiscoveryWorkflow

        workflow = CompanyDiscoveryWorkflow()
        result = workflow.execute(province=province, max_results=max_results)

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
        from workflows.company_enrichment import CompanyEnrichmentWorkflow

        workflow = CompanyEnrichmentWorkflow()
        result = workflow.execute(company_name=company_name, tax_id=tax_id, province=province)

        return result.get("result", {})

    def validate_mece(self, companies: list[dict]) -> dict:
        """
        Validate MECE compliance of a dataset.

        Args:
            companies: List of company dictionaries

        Returns:
            Validation result with MECE report
        """
        from workflows.mece_validation import MECEValidationWorkflow

        workflow = MECEValidationWorkflow()
        result = workflow.execute(companies=companies)

        return result.get("result", {})

    def get_quality_report(self, company_ids: list[str] | None = None) -> dict:
        """
        Get data quality report.

        Args:
            company_ids: Optional list of tax IDs (if None, reports on all)

        Returns:
            Quality metrics across all tracked companies
        """
        # Create a new instance of the provenance resource
        from resources.source_provenance import SourceProvenanceResource

        provenance_resource = SourceProvenanceResource()
        result = provenance_resource.batch_quality_report(company_ids=company_ids)
        return result

    def _create_approval_gate(self):
        """
        Create approval callback for human-in-loop gates with rich commands.

        Returns a function that:
        - Displays gate data
        - Accepts multiple commands (not just yes/no)
        - Uses agent workflows/resources to execute commands
        - Returns True (proceed) or False (abort)
        """

        def approval_gate(gate_data: dict) -> bool:
            """Handle approval with multi-command support."""
            gate_name = gate_data["gate"]

            if gate_name == "discovery":
                return self._handle_discovery_gate(gate_data)
            elif gate_name == "enrichment":
                return self._handle_enrichment_gate(gate_data)
            elif gate_name == "final":
                return self._handle_final_gate(gate_data)
            else:
                return True

        return approval_gate

    # ============================================================
    # GATE HANDLERS - Multi-command interactive sessions
    # ============================================================

    def _handle_discovery_gate(self, gate_data: dict) -> bool:
        """
        Handle Gate 1: Discovery approval with rich commands.

        Available commands:
        - proceed: Start enrichment
        - show more: View more companies
        - filter <keyword>: Remove companies matching keyword
        - limit <N>: Only enrich first N companies
        - add province <name>: Discover in additional province
        - redo: Restart discovery
        - abort: Cancel research
        """
        # Store data in session for helper methods to access
        if not hasattr(self, "session"):
            # Fallback if session not initialized
            return True

        self.session.discovered_companies = gate_data.get("sample", [])  # Temporary, will be updated

        while True:
            print(f"\n{'=' * 70}")
            print("📍 GATE 1: DISCOVERY COMPLETE")
            print(f"{'=' * 70}")
            print(f"\n✅ Found {gate_data['total_companies']} companies")
            print(f"📊 Provinces: {', '.join(gate_data['provinces'])}")
            print("\n📋 Sample (first 10):")
            for i, company in enumerate(gate_data["sample"][:10], 1):
                print(f"   {i}. {company['name']} ({company['province']})")

            print("\n🤖 Available commands:")
            print(f"   • proceed             - Start enrichment for all {gate_data['total_companies']} companies")
            print("   • show more          - View companies 11-30")
            print("   • filter <keyword>   - Remove companies matching keyword")
            print("   • limit <N>          - Only enrich first N companies")
            print("   • add province <name> - Discover in additional province")
            print("   • redo               - Start discovery over")
            print("   • abort              - Cancel research")

            command = input("\n👤 Command: ").strip().lower()

            if command == "proceed":
                return True

            elif command == "show more":
                self._show_companies(gate_data.get("sample", []), start=10, limit=20)

            elif command.startswith("filter "):
                keyword = command.replace("filter ", "").strip()
                # This would modify the gate_data in a real implementation
                print("⚠️  Filter not yet connected to workflow (simulated data)")
                print(f"💡 In production: would remove companies matching '{keyword}'")

            elif command.startswith("limit "):
                try:
                    limit = int(command.replace("limit ", "").strip())
                    print(f"✅ Limit set to {limit} companies")
                    gate_data["total_companies"] = min(limit, gate_data["total_companies"])
                    gate_data["sample"] = gate_data["sample"][:limit]
                except ValueError:
                    print("❌ Invalid limit. Please use: limit <number>")

            elif command.startswith("add province "):
                province = command.replace("add province ", "").strip().title()
                print("⚠️  Add province not yet connected to workflow")
                print(f"💡 In production: would run discovery for '{province}'")

            elif command == "redo":
                print("⚠️  Redo not yet connected to workflow")
                print("💡 In production: would restart discovery with new parameters")
                return False  # Abort current, would trigger re-run

            elif command == "abort":
                return False

            else:
                print(f"❌ Unknown command: '{command}'")
                print("💡 Try: proceed, show more, filter <keyword>, limit <N>, abort")

    def _handle_enrichment_gate(self, gate_data: dict) -> bool:
        """
        Handle Gate 2: Enrichment progress with rich commands.

        Available commands:
        - continue: Keep enriching
        - show batch: View full latest batch
        - show stats: Detailed quality breakdown
        - show low quality: View low-confidence companies
        - pause: Stop and export what we have
        - abort: Cancel remaining enrichment
        """
        while True:
            print(f"\n{'=' * 70}")
            print(f"📍 GATE 2: ENRICHMENT PROGRESS (Batch {gate_data['batch_number']}/{gate_data['total_batches']})")
            print(f"{'=' * 70}")
            print(f"\n✅ Enriched {gate_data['enriched_so_far']} / {gate_data['total_to_enrich']} companies")

            quality = gate_data["quality_preview"]
            print("\n📊 Quality Distribution:")
            print(f"   High confidence (≥0.8): {quality['high']} companies ({quality['high_pct']:.1f}%)")
            print(f"   Medium confidence (0.5-0.8): {quality['medium']} companies ({quality['medium_pct']:.1f}%)")
            print(f"   Low confidence (<0.5): {quality['low']} companies ({quality['low_pct']:.1f}%)")

            print("\n📋 Latest batch sample:")
            for i, company in enumerate(gate_data["sample"][:5], 1):
                conf = company.get("confidence", 0)
                priority = company.get("priority_score", 0)
                print(f"   {i}. {company['name']} - Priority: {priority:.1f}, Confidence: {conf:.2f}")

            print("\n🤖 Available commands:")
            print("   • continue          - Keep enriching remaining companies")
            print("   • show batch        - View full details of latest batch")
            print("   • show stats        - Detailed quality breakdown by field")
            print("   • show low quality  - View low-confidence companies")
            print("   • pause             - Stop here and export results so far")
            print("   • abort             - Cancel remaining enrichment")

            command = input("\n👤 Command: ").strip().lower()

            if command == "continue":
                return True

            elif command == "show batch":
                self._show_companies(gate_data.get("sample", []), start=0, limit=len(gate_data.get("sample", [])))

            elif command == "show stats":
                self._show_quality_stats(quality)

            elif command == "show low quality":
                # Filter low quality from sample
                low_quality = [c for c in gate_data.get("sample", []) if c.get("confidence", 0) < 0.5]
                if low_quality:
                    self._show_companies(low_quality, start=0, limit=len(low_quality))
                else:
                    print("✅ No low-quality companies in latest batch")

            elif command == "pause":
                print("⏸️  Pausing enrichment. Results so far will be saved.")
                return False

            elif command == "abort":
                return False

            else:
                print(f"❌ Unknown command: '{command}'")
                print("💡 Try: continue, show batch, show stats, show low quality, pause, abort")

    def _handle_final_gate(self, gate_data: dict) -> bool:
        """
        Handle Gate 3: Final approval with rich commands.

        Available commands:
        - approve: Export and complete
        - export csv: Preview CSV format
        - show low quality: View low-confidence companies
        - re-enrich low quality: Re-run enrichment for low confidence
        - redo enrichment: Start enrichment phase over
        - abort: Discard results
        """
        while True:
            print(f"\n{'=' * 70}")
            print("📍 GATE 3: FINAL VALIDATION")
            print(f"{'=' * 70}")
            print(f"\n✅ Total companies: {gate_data['total_companies']}")
            print(f"📊 Provinces: {', '.join(gate_data['provinces'])}")

            mece = gate_data["mece_report"]
            print("\n📋 MECE Validation:")
            print(f"   Compliant: {'✅ Yes' if mece.get('mece_compliant') else '❌ No'}")
            print(f"   Duplicates removed: {mece.get('duplicates_removed', 0)}")

            quality = gate_data["quality_report"]
            print("\n📊 Final Quality Report:")
            print(f"   High confidence: {quality['high']} companies ({quality['high_pct']:.1f}%)")
            print(f"   Medium confidence: {quality['medium']} companies ({quality['medium_pct']:.1f}%)")
            print(f"   Low confidence: {quality['low']} companies ({quality['low_pct']:.1f}%)")

            print("\n🤖 Available commands:")
            print("   • approve               - Export results and complete research")
            print("   • export csv            - Preview CSV format")
            print("   • show low quality      - View low-confidence companies")
            print("   • re-enrich low quality - Re-run enrichment for low confidence")
            print("   • redo enrichment       - Start enrichment phase over")
            print("   • abort                 - Discard results")

            command = input("\n👤 Command: ").strip().lower()

            if command == "approve":
                print("\n✅ Results approved!")
                return True

            elif command == "export csv":
                print("\n💡 CSV export preview:")
                print("   company_name,tax_id,entity_type,product_category,...")
                print("   (Full export available after approval)")

            elif command == "show low quality":
                print("\n📋 Low-confidence companies (confidence < 0.5):")
                print(f"   Total: {quality['low']}")
                print("   (Details would show missing fields, data gaps)")

            elif command == "re-enrich low quality":
                print("⚠️  Re-enrichment not yet connected to workflow")
                print(f"💡 In production: would re-run enrichment for {quality['low']} companies")
                # In real implementation:
                # self._re_enrich_low_quality(gate_data)
                # quality = self._compute_quality_preview(updated_companies)

            elif command == "redo enrichment":
                print("⚠️  Redo not yet connected to workflow")
                print("💡 In production: would reset and restart enrichment phase")
                return False

            elif command == "abort":
                return False

            else:
                print(f"❌ Unknown command: '{command}'")
                print("💡 Try: approve, export csv, show low quality, re-enrich low quality, abort")

    # ============================================================
    # HELPER METHODS - Gate action implementations
    # ============================================================

    def _show_companies(self, companies: list[dict], start: int = 0, limit: int = 10):
        """Display companies with details."""
        print(f"\n📋 Companies {start + 1}-{min(start + limit, len(companies))}:")
        for i, company in enumerate(companies[start : start + limit], start + 1):
            print(f"   {i}. {company['name']} ({company.get('province', 'N/A')})")
            if "confidence" in company:
                print(f"      Confidence: {company['confidence']:.2f}")
            if "priority_score" in company:
                print(f"      Priority: {company['priority_score']:.1f}")

    def _show_quality_stats(self, quality: dict):
        """Display detailed quality statistics."""
        print("\n📊 Detailed Quality Statistics:")
        print(f"   High confidence (≥0.8): {quality['high']} ({quality['high_pct']:.1f}%)")
        print(f"   Medium confidence (0.5-0.8): {quality['medium']} ({quality['medium_pct']:.1f}%)")
        print(f"   Low confidence (<0.5): {quality['low']} ({quality['low_pct']:.1f}%)")
        print("\n💡 High confidence = verified from government sources")
        print("💡 Medium confidence = company website or association data")
        print("💡 Low confidence = estimates or incomplete data")
