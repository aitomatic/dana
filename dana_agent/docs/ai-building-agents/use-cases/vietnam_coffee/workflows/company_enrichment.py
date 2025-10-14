"""
CompanyEnrichmentWorkflow - Enrich company data with all fields.

This workflow takes basic company information (name, province, tax ID) and
enriches it with 10+ additional fields by fetching from multiple sources
and extracting structured data.
"""

from dana.common.protocols.types import DictParams
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output


class CompanyEnrichmentWorkflow(BaseWorkflow):
    """
    Enrich a single company with comprehensive data.

    Takes basic company info and populates all enrichment fields:
    - Product category
    - Export status
    - Revenue (with source tracking)
    - Years incorporated
    - Certifications
    - Address (street, district, province)
    - Person in charge (PIC)
    - Affiliate/parent company
    - Priority score (computed)
    - Overall confidence (computed)

    For each field, tracks source and confidence level.
    """

    def __init__(self, workflow_id: str | None = None, **kwargs):
        """
        Initialize CompanyEnrichmentWorkflow.

        Args:
            workflow_id: Workflow identifier
            **kwargs: Additional arguments for BaseWorkflow
        """
        super().__init__(workflow_id=workflow_id or "company-enrichment", **kwargs)

        # Import resources
        from resources.company_data_structuring import CompanyDataStructuringResource
        from resources.source_provenance import SourceProvenanceResource
        from resources.vietnamese_data_normalization import VietnameseDataNormalizationResource

        from dana.lib.resources.web_research.fetch import FetchResource
        from dana.lib.resources.web_research.search import SearchResource

        self.fetch_resource = FetchResource()
        self.search_resource = SearchResource()
        self.structuring_resource = CompanyDataStructuringResource()
        self.provenance_resource = SourceProvenanceResource()
        self.vietnamese_norm = VietnameseDataNormalizationResource()

    @validate_input(
        company_name={"required": True, "type": str, "min_length": 2},
        tax_id={"required": True, "type": str, "min_length": 5},
        province={"required": True, "type": str},
    )
    @validate_output(
        success={"required": True, "type": bool},
        enriched_company={"required": True, "type": dict},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Enrich company with all fields.

        Args:
            company_name (str): Company name
            tax_id (str): Vietnamese tax ID
            province (str): Province
            **kwargs: Optional context

        Returns:
            {
                "success": bool,
                "enriched_company": {
                    "name": str,
                    "tax_id": str,
                    "product_category": str,
                    "export_status": bool,
                    "revenue": int | None,
                    "revenue_source": str,
                    "years_incorporated": int,
                    "certifications": [str],
                    "address": str,
                    "district": str,
                    "province": str,
                    "pic": str | None,
                    "affiliate": str | None,
                    "priority_score": float,
                    "confidence": float,
                    "sources": {field: url}
                },
                "fields_enriched": int,
                "processing_time": float
            }
        """
        import time

        start_time = time.time()

        company_name = kwargs["company_name"]
        tax_id = kwargs["tax_id"]
        province = kwargs["province"]

        try:
            # Step 1: Fetch company data from government registry
            registry_data, registry_url = self._fetch_government_registry(tax_id)

            # Step 2: Fetch company website (if exists)
            website_data, website_url = self._fetch_company_website(company_name)

            # Step 3: Extract structured fields
            enriched = self._extract_all_fields(
                company_name=company_name,
                tax_id=tax_id,
                province=province,
                registry_data=registry_data,
                registry_url=registry_url,
                website_data=website_data,
                website_url=website_url,
            )

            # Step 4: Compute derived fields
            enriched = self._compute_derived_fields(enriched)

            # Step 5: Track provenance for all fields
            self._record_provenance(enriched, tax_id)

            processing_time = time.time() - start_time

            return {
                "success": True,
                "enriched_company": enriched,
                "fields_enriched": self._count_populated_fields(enriched),
                "processing_time": processing_time,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "enriched_company": self._create_minimal_company(company_name, tax_id, province),
                "fields_enriched": 3,  # Only name, tax_id, province
                "processing_time": time.time() - start_time,
            }

    # ============================================================================
    # DATA FETCHING
    # ============================================================================

    def _fetch_government_registry(self, tax_id: str) -> tuple[str, str]:
        """
        Fetch company data from government registry.

        MVP: Returns simulated data. In production, would:
        1. Use FetchResource to query masothue.com by tax_id
        2. Parse HTML response
        3. Return extracted text + URL

        Returns:
            (data_text, source_url)
        """
        # MVP: Simulated registry data
        simulated_data = f"""
        Company Tax ID: {tax_id}
        Official Name: Công ty TNHH Cà phê Robusta
        Registration Date: 2015-03-15
        Address: 123 Đường Lê Duẩn, Thành phố Buôn Ma Thuột, Đắk Lắk
        Business Activities: Growing coffee; Processing coffee; Trading coffee
        Legal Representative: Nguyễn Văn A
        Registered Capital: 5,000,000,000 VND
        """

        source_url = f"https://masothue.com/{tax_id}"

        return simulated_data, source_url

    def _fetch_company_website(self, company_name: str) -> tuple[str, str]:
        """
        Fetch company website data.

        MVP: Returns simulated data. In production, would:
        1. Use SearchResource to find company website
        2. Use FetchResource to get homepage
        3. Return extracted text + URL

        Returns:
            (data_text, source_url)
        """
        # MVP: Simulated website data
        simulated_data = f"""
        {company_name}
        About Us: We are a leading coffee producer in Vietnam with over 500 hectares
        of Robusta and Arabica coffee plantations.

        Products: Green coffee beans, Roasted coffee, Instant coffee
        Certifications: Fair Trade, Organic, Rainforest Alliance
        Export Markets: Europe, USA, Japan, South Korea

        Annual Production: 2,000 tons of green coffee beans
        Established: 2015

        Contact: info@coffee-company.vn
        Director: Mr. Nguyễn Văn A
        """

        source_url = "https://www.example-coffee.vn"

        return simulated_data, source_url

    # ============================================================================
    # FIELD EXTRACTION
    # ============================================================================

    def _extract_all_fields(
        self, company_name: str, tax_id: str, province: str, registry_data: str, registry_url: str, website_data: str, website_url: str
    ) -> dict:
        """
        Extract all enrichment fields from fetched data.

        Uses CompanyDataStructuringResource to extract structured data
        from unstructured text.
        """
        # Define enrichment schema (enhanced)
        schema = {
            "product_category": {
                "type": "string",
                "description": "Detailed product categories: Robusta, Arabica (green, roasted, packaged)",
                "required": False,
            },
            "volume_tons": {
                "type": "string",
                "description": "Production volume in tons per year, format as range '100-120' or approximate '~35'",
                "required": False,
            },
            "export_status": {"type": "bool", "description": "Whether company exports (true/false)", "required": False},
            "key_markets": {
                "type": "string",
                "description": "Export destination markets (comma-separated): US, EU, KR, Japan, etc.",
                "required": False,
            },
            "revenue": {"type": "int", "description": "Annual revenue in VND (number only)", "required": False},
            "years_incorporated": {"type": "int", "description": "Number of years in business", "required": False},
            "certifications": {
                "type": "list",
                "description": "List of certifications: Fair Trade, Organic, Rainforest Alliance, 4C, UTZ, etc.",
                "required": False,
            },
            "full_address": {"type": "string", "description": "Complete street address", "required": False},
            "pic": {"type": "string", "description": "Person in charge / Director name", "required": False},
            "pic_title": {
                "type": "string",
                "description": "Title of person in charge: Sales Dir., Chair, Founder, CEO, Manager, etc.",
                "required": False,
            },
            "affiliate": {
                "type": "string",
                "description": "Parent company, group or network affiliation",
                "required": False,
            },
        }

        # Extract from registry data (higher confidence)
        registry_result = self.structuring_resource.structure_company_data(
            raw_text=registry_data, schema=schema, context=f"Government business registry for {company_name}"
        )

        # Extract from website (lower confidence but more detail)
        website_result = self.structuring_resource.structure_company_data(
            raw_text=website_data, schema=schema, context=f"Company website for {company_name}"
        )

        # Merge results (prefer registry data for conflicts, use website for additional info)
        merged = self._merge_extraction_results(registry_result, website_result, registry_url, website_url)

        # Parse address into components
        if merged.get("full_address"):
            address_result = self.vietnamese_norm.parse_address(merged["full_address"])
            if address_result["success"]:
                components = address_result["components"]
                merged["address"] = components.get("street") or merged["full_address"]
                merged["district"] = components.get("district")
                # Province from input (more reliable)

        # Classify entity type
        entity_type = self._classify_entity_type(company_name, merged.get("product_category"))

        # Convert revenue from VND to USD (approximate 1 USD = 25,000 VND)
        revenue_vnd = merged.get("revenue")
        revenue_usd = int(revenue_vnd / 25000) if revenue_vnd else None

        # Build enriched company record (enhanced)
        enriched = {
            "name": company_name,
            "tax_id": tax_id,
            "entity_type": entity_type,
            "product_category": merged.get("product_category"),
            "volume_tons": merged.get("volume_tons"),
            "export_status": merged.get("export_status"),
            "key_markets": merged.get("key_markets") if merged.get("export_status") else None,
            "revenue": revenue_usd,
            "revenue_source": merged.get("revenue_source", "Estimate"),
            "years_incorporated": merged.get("years_incorporated"),
            "certifications": merged.get("certifications") or [],
            "address": merged.get("address"),
            "district": merged.get("district"),
            "province": province,
            "pic": merged.get("pic"),
            "pic_title": merged.get("pic_title"),
            "affiliate": merged.get("affiliate"),
            "sources": merged.get("sources", {}),
            "field_confidences": merged.get("field_confidences", {}),
        }

        return enriched

    def _merge_extraction_results(self, registry_result: dict, website_result: dict, registry_url: str, website_url: str) -> dict:
        """
        Merge extraction results from multiple sources.

        Priority: Government registry > Company website
        """
        merged = {}
        sources = {}
        confidences = {}

        registry_data = registry_result.get("data", {}) if registry_result.get("success") else {}
        website_data = website_result.get("data", {}) if website_result.get("success") else {}

        registry_confidences = registry_result.get("field_confidences", {})
        website_confidences = website_result.get("field_confidences", {})

        # For each field, choose best source
        all_fields = set(registry_data.keys()) | set(website_data.keys())

        for field in all_fields:
            registry_value = registry_data.get(field)
            website_value = website_data.get(field)

            registry_conf = registry_confidences.get(field, 0.0) or 0.0
            website_conf = website_confidences.get(field, 0.0) or 0.0

            # Boost registry confidence (official source)
            registry_conf_boosted = min(1.0, registry_conf * 1.2)

            # Choose based on confidence
            if registry_value and registry_conf_boosted >= website_conf:
                merged[field] = registry_value
                sources[field] = registry_url
                confidences[field] = registry_conf_boosted
            elif website_value:
                merged[field] = website_value
                sources[field] = website_url
                confidences[field] = website_conf

        merged["sources"] = sources
        merged["field_confidences"] = confidences

        return merged

    # ============================================================================
    # DERIVED FIELDS
    # ============================================================================

    def _classify_entity_type(self, company_name: str, product_category: str | None) -> str:
        """
        Classify entity type based on company name and structure.

        Uses patterns from Appendix B of design.md.
        """
        name_lower = company_name.lower()

        # Cooperative
        if "htx" in name_lower or "hợp tác xã" in name_lower or "cooperative" in name_lower:
            return "Cooperative"

        # Export company
        if "export" in name_lower or "xuất khẩu" in name_lower:
            return "Export Co"

        # Farm
        if "farm" in name_lower or "nông trại" in name_lower:
            return "SME/Farm"

        # Trading company
        if "thương mại" in name_lower or " tm " in name_lower:
            return "SME/Trade"

        # Check product category for classification hints
        if product_category:
            product_lower = product_category.lower()

            # Private roaster (large scale, branded)
            if "sản xuất" in name_lower and ("roasted" in product_lower or "packaged" in product_lower):
                return "Private Roaster"

            # Processor
            if "processing" in product_lower or "chế biến" in product_lower:
                return "SME/Processor"

            # Roaster
            if "roasted" in product_lower or "rang" in product_lower:
                return "SME/Roaster"

        # Default: SME/Processor
        return "SME/Processor"

    def _compute_derived_fields(self, enriched: dict) -> dict:
        """
        Compute priority_score (0-5 scale), notes, and overall_confidence.

        Priority Score Components:
        - Revenue: 40% (0-5 based on brackets)
        - Export: 30% (5 if exports, 0 otherwise)
        - Certifications: 20% (1 point per cert, max 5)
        - Volume: 10% (0-5 based on production scale)
        """
        # Revenue score (0-5 scale)
        revenue_score = 0.0
        revenue_usd = enriched.get("revenue") or 0
        if revenue_usd > 0:
            # Revenue brackets (USD):
            # < 50k: 1, 50k-100k: 2, 100k-200k: 3, 200k-400k: 4, 400k+: 5
            if revenue_usd >= 400000:
                revenue_score = 5.0
            elif revenue_usd >= 200000:
                revenue_score = 4.0
            elif revenue_usd >= 100000:
                revenue_score = 3.0
            elif revenue_usd >= 50000:
                revenue_score = 2.0
            else:
                revenue_score = 1.0

        # Export score (0-5 scale)
        export_score = 5.0 if enriched.get("export_status") else 0.0

        # Certification score (0-5 scale)
        cert_count = len(enriched.get("certifications", []))
        cert_score = min(5.0, cert_count * 1.0)  # 1 point per cert, max 5

        # Volume score (0-5 scale)
        volume_score = self._score_volume(enriched.get("volume_tons"))

        # Weighted priority score (0-5 scale)
        priority_score = min(5.0, revenue_score * 0.40 + export_score * 0.30 + cert_score * 0.20 + volume_score * 0.10)

        enriched["priority_score"] = round(priority_score, 2)

        # Generate notes (business intelligence commentary)
        enriched["notes"] = self._generate_notes(enriched)

        # Overall confidence (average of field confidences)
        confidences = enriched.get("field_confidences", {})
        if confidences:
            conf_values = [c for c in confidences.values() if c is not None]
            overall_conf = sum(conf_values) / len(conf_values) if conf_values else 0.5
        else:
            overall_conf = 0.5

        enriched["confidence"] = round(overall_conf, 2)

        return enriched

    def _score_volume(self, volume_tons: str | None) -> float:
        """
        Score production volume on 0-5 scale.

        Handles ranges like "100-120" and approximates like "~35".
        """
        if not volume_tons:
            return 0.0

        # Extract numeric value
        import re

        numbers = re.findall(r"\d+", volume_tons)
        if not numbers:
            return 0.0

        # Use average of range or single value
        avg_volume = sum(int(n) for n in numbers) / len(numbers)

        # Volume brackets (tons):
        # < 20: 1, 20-50: 2, 50-100: 3, 100-200: 4, 200+: 5
        if avg_volume >= 200:
            return 5.0
        elif avg_volume >= 100:
            return 4.0
        elif avg_volume >= 50:
            return 3.0
        elif avg_volume >= 20:
            return 2.0
        elif avg_volume > 0:
            return 1.0
        else:
            return 0.0

    def _generate_notes(self, enriched: dict) -> str:
        """
        Generate 1-2 sentence business intelligence notes.

        Highlights: scale, certifications, market position, export strength.
        """
        notes_parts = []

        # Entity classification
        entity_type = enriched.get("entity_type", "Company")

        # Scale/Volume
        volume_tons = enriched.get("volume_tons")
        if volume_tons:
            notes_parts.append(f"{entity_type} with {volume_tons} tons production")
        else:
            notes_parts.append(entity_type)

        # Export capability
        if enriched.get("export_status"):
            markets = enriched.get("key_markets")
            if markets:
                notes_parts.append(f"exports to {markets}")
            else:
                notes_parts.append("active exporter")

        # Certifications
        certs = enriched.get("certifications", [])
        if len(certs) >= 3:
            notes_parts.append(f"highly certified ({len(certs)} certs)")
        elif len(certs) >= 1:
            notes_parts.append(f"certified ({', '.join(certs[:2])})")

        # Years in business (stability)
        years = enriched.get("years_incorporated")
        if years and years >= 15:
            notes_parts.append(f"established {years}+ years")
        elif years and years >= 10:
            notes_parts.append("strong track record")

        # Affiliate/Group membership
        affiliate = enriched.get("affiliate")
        if affiliate and affiliate.lower() != "none":
            notes_parts.append(f"member of {affiliate}")

        # Combine into 1-2 sentences
        if len(notes_parts) <= 3:
            return ". ".join(notes_parts[:3]) + "."
        else:
            # First sentence: type + scale/export
            sentence1 = ". ".join(notes_parts[:2])
            # Second sentence: certs + additional
            sentence2 = ". ".join(notes_parts[2:4])
            return f"{sentence1}. {sentence2}."

    def _record_provenance(self, enriched: dict, tax_id: str):
        """Record provenance for all fields."""
        sources = enriched.get("sources", {})
        confidences = enriched.get("field_confidences", {})

        for field, value in enriched.items():
            if field in ["sources", "field_confidences"]:
                continue

            source_url = sources.get(field, "computed")
            confidence = confidences.get(field, 0.5)

            self.provenance_resource.record_source(
                company_id=tax_id, field=field, value=value, source_url=source_url, confidence=confidence
            )

    def _count_populated_fields(self, enriched: dict) -> int:
        """Count non-null fields."""
        count = 0
        for key, value in enriched.items():
            if key in ["sources", "field_confidences"]:
                continue
            if value is not None and value != "":
                count += 1
        return count

    def _create_minimal_company(self, name: str, tax_id: str, province: str) -> dict:
        """Create minimal company record when enrichment fails."""
        return {
            "name": name,
            "tax_id": tax_id,
            "entity_type": "SME/Processor",  # Default classification
            "product_category": None,
            "volume_tons": None,
            "export_status": None,
            "key_markets": None,
            "revenue": None,
            "revenue_source": "Unknown",
            "years_incorporated": None,
            "certifications": [],
            "address": None,
            "district": None,
            "province": province,
            "pic": None,
            "pic_title": None,
            "affiliate": None,
            "priority_score": 0.0,
            "notes": "Limited data available.",
            "confidence": 0.2,
            "sources": {},
            "field_confidences": {},
        }
