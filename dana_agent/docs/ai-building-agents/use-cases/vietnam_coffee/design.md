# Vietnam Coffee Research Agent - Design Document

**Status**: Draft MVP
**Created**: October 2025
**Scope**: 1,000+ Vietnamese coffee producers across multiple provinces
**Pattern**: Single Specialist Agent with Phased Orchestration

---

## Executive Summary

This agent automates the research and enrichment of Vietnamese coffee producers, cooperatives, and processors to create a **Mutually Exclusive, Collectively Exhaustive (MECE)** dataset ranked by strategic value. The system addresses the scalability challenges discovered in the manual process (described in ryan.md) where a 45-company single-province effort revealed the need for automated orchestration across 1,000+ entities.

**Key Requirements:**
- Scale: 1,000+ companies across multiple provinces
- Enrichment: 10+ fields per company (revenue, export status, certifications, addresses, etc.)
- Quality: Source tracking, confidence scoring, MECE validation
- Delivery: Incremental checkpoints (10-15 companies per batch)
- Resilience: Resume from failure, cache web results

---

## Phase 1: Problem Analysis

### 1.1 Business Context

**Goal**: Build comprehensive dataset for supply chain risk assessment and lead generation in Vietnamese coffee industry.

**Stakeholders:**
- **Primary User**: Supply chain analysts, business development teams
- **Data Sources**: Vietnamese government portals (masothue.com), industry associations, company websites
- **Output Consumers**: Risk models, CRM systems, export analysis tools

**Success Metrics:**
- **Completeness**: All companies in target provinces discovered
- **Accuracy**: >90% fields verified (not estimated)
- **MECE Compliance**: No duplicates, no gaps in coverage
- **Throughput**: Process 1,000+ companies in <8 hours
- **Transparency**: Every field tracks source + confidence

### 1.2 Problem Decomposition

#### Core Challenges from Manual Process (ryan.md)

| Challenge | Impact | Technical Root Cause |
|-----------|--------|---------------------|
| **Delayed Delivery** | Missed deadlines, no intermediate outputs | No incremental checkpointing |
| **Data Completeness** | Address fields discovered late | No schema validation upfront |
| **Communication Gaps** | Promises without execution | No observable state |
| **All-or-Nothing Model** | Lost work on failure | No batch persistence |
| **Scale Bottleneck** | 45 companies manageable, 1,000+ requires automation | Manual research doesn't scale |

#### Technical Requirements

**Scale:**
- 1,000+ companies across 7+ provinces
- Each company: 10-15 enrichment fields
- ~10,000+ data points to collect
- Multi-day execution expected

**Data Quality:**
- **Verified > Estimated**: Flag confidence per field
- **Source Provenance**: Track origin of each data point
- **MECE Enforcement**: Deduplicate, prevent overlaps
- **Address Hierarchy**: Province → District → Commune fallback

**Operational:**
- **Incremental Delivery**: Output every 10-15 companies
- **Resumability**: Continue from last checkpoint on failure
- **Caching**: Don't re-fetch same websites
- **Observable**: Progress tracking visible to user

### 1.3 Success Criteria

**MVP Success (single province, 45-100 companies):**
- ✅ Discover all registered coffee producers in target province
- ✅ Enrich 100% with core fields (name, product, revenue estimate)
- ✅ Enrich 80%+ with extended fields (address, certifications, export status)
- ✅ Deliver incrementally (10-company batches)
- ✅ MECE validated (no duplicates)
- ✅ Complete in <2 hours

**Production Success (multi-province, 1,000+ companies):**
- ✅ All MVP criteria at scale
- ✅ Parallel province processing
- ✅ Resume from failure without data loss
- ✅ <8 hours for 1,000 companies
- ✅ Output ready for CRM/analysis ingestion

---

## Phase 2: Component Identification

### 2.1 Required Capabilities

#### Capability Map

| Capability | Type | Complexity | Reusability |
|-----------|------|------------|-------------|
| **Vietnamese Web Search** | Resource | Medium | High (other Vietnam research) |
| **Government Registry Extraction** | Resource | High | Medium (Vietnam-specific) |
| **Company Data Structuring** | Resource | Medium | High (any company research) |
| **Address Normalization** | Resource | Low | High (any geographic data) |
| **Source Provenance Tracking** | Resource | Low | Very High (all research) |
| **Company Discovery** | Workflow | Medium | Medium |
| **Field Enrichment** | Workflow | High | Medium |
| **MECE Validation** | Workflow | Medium | High (any MECE dataset) |
| **Batch Orchestration** | Workflow | Low | Very High (all batch jobs) |
| **Research Coordination** | Agent | Medium | Low (coffee-specific) |

### 2.2 Existing Dana Resources (Can Reuse)

From `dana/lib/resources/`:

- ✅ **SearchResource** (`web_research/search.py`) - Web search
- ✅ **FetchResource** (`web_research/fetch.py`) - HTTP fetching
- ✅ **ExtractResource** (`web_research/extract.py`) - Content extraction
- ✅ **ConversationResource** (`conversation.py`) - LLM reasoning

### 2.3 New Components Needed

#### Resources to Build

1. **VietnameseDataNormalizationResource** (domain-agnostic)
   - Purpose: Handle Vietnamese encoding, name variations
   - Reusability: Any Vietnamese data project

2. **CompanyDataStructuringResource** (domain-agnostic)
   - Purpose: Structure extracted data into standard schema
   - Reusability: Any company research

3. **SourceProvenanceResource** (domain-agnostic)
   - Purpose: Track origin + confidence of each field
   - Reusability: All research projects

#### Workflows to Build

1. **CompanyDiscoveryWorkflow**
   - Input: Province name, industry keywords
   - Output: List of candidate companies
   - Logic: Query government portals → association lists → deduplicate

2. **CompanyEnrichmentWorkflow**
   - Input: Company basic info (name, province)
   - Output: Fully enriched company record
   - Logic: Fetch company website → extract fields → validate → score confidence

3. **MECEValidationWorkflow**
   - Input: List of enriched companies
   - Output: Validated MECE dataset
   - Logic: Deduplicate → detect gaps → ensure unique placement

4. **BatchOrchestrationWorkflow**
   - Input: Province list, batch size
   - Output: Stream of batches
   - Logic: Discover → enrich in batches → validate → output incrementally

#### Agent to Build

1. **VietnamCoffeeResearchAgent**
   - Pattern: Single specialist
   - Role: Coffee producer research coordinator
   - Workflows: 4 workflows above
   - Resources: 7 resources (3 new + 4 existing)

---

## Phase 3: Specialization Decomposition

### 3.1 Agent Design

**Pattern**: Single Specialist (like WebResearchAgent)

**Why Single Specialist?**
- Single domain: Vietnamese coffee industry research
- Focused task: Discovery + enrichment
- No need for coordinator (no cross-domain synthesis)
- Scales through workflow orchestration, not agent hierarchy

**Agent Identity:**

```xml
<PUBLIC_DESCRIPTION>
I am a research specialist focused on the Vietnamese coffee industry.
I discover and enrich datasets of coffee producers, cooperatives, and
processors with comprehensive business intelligence including revenue,
export activity, certifications, and geographic data. I ensure complete
coverage (MECE compliance) and provide transparent source tracking for
all data points.
</PUBLIC_DESCRIPTION>

<PRIVATE_IDENTITY>
I am methodical and thorough in my research process. I maintain strict
data quality standards, distinguishing verified facts from estimates.
I work incrementally, providing checkpoints rather than waiting to
deliver everything at once. I track the provenance of every data point
I collect. When I encounter gaps in data, I explicitly flag them rather
than fabricating information. I understand the importance of MECE
compliance and actively work to prevent duplicates and ensure complete
coverage across provinces.
</PRIVATE_IDENTITY>
```

### 3.2 Workflow Specialization

#### 3.2.1 CompanyDiscoveryWorkflow

**Purpose**: Find all coffee companies in target provinces

**Responsibilities:**
- Query government business registries (masothue.com)
- Search industry association lists
- Cross-reference with export databases
- Deduplicate across sources
- Return candidate list with basic info (name, province, tax ID)

**Success Criteria:**
- Recall: Found ≥95% of registered companies
- Precision: ≥90% are actual coffee producers (not false positives)
- No duplicates in output

**Logic:**
```
1. Parallel fetch from 3 sources:
   - Government registry (filter by province + industry code)
   - Vietnam Coffee & Cocoa Association (VICOFA) member list
   - Export database (coffee HS codes)

2. Normalize names (Vietnamese encoding, variations)

3. Deduplicate by tax ID (primary) or name+province (fallback)

4. Return structured list:
   {name, tax_id, province, sources[], confidence}
```

#### 3.2.2 CompanyEnrichmentWorkflow

**Purpose**: Populate all enrichment fields for a single company

**Responsibilities:**
- Fetch company website/documents
- Extract 10+ enrichment fields
- Validate and cross-check data
- Track source for each field
- Compute confidence score

**Enrichment Schema:**
```python
{
    "name": str,                    # Official company name
    "tax_id": str,                  # Vietnamese tax ID (required)
    "product_category": str,        # e.g., "Green coffee beans, Roasted coffee"
    "export_status": bool,          # Verified exporter
    "revenue": int | None,          # Annual revenue (VND)
    "revenue_source": str,          # "Government filing" | "Estimate" | "Company statement"
    "years_incorporated": int,      # Years in business
    "certifications": List[str],    # e.g., ["Fair Trade", "Organic"]
    "address": str,                 # Street address (if available)
    "district": str,                # District/County
    "province": str,                # Province (required)
    "pic": str | None,              # Person in charge (if available)
    "affiliate": str | None,        # Parent company (if applicable)
    "priority_score": float,        # 0-100 (based on revenue, export, certifications)
    "confidence": float,            # 0-1 (overall data quality)
    "sources": Dict[str, str],      # Field -> Source URL mapping
}
```

**Logic:**
```
1. Fetch company website (if exists)
2. Fetch government registry page (by tax ID)
3. Extract fields in parallel:
   - Basic info (name, address) from registry
   - Revenue from registry or company statements
   - Export status from customs database
   - Certifications from company website or association lists
4. Validate:
   - Required fields present (name, tax_id, province)
   - Data consistency (e.g., years_incorporated <= 100)
5. Compute confidence:
   - High (0.9+): Government-verified data
   - Medium (0.6-0.9): Company statement or association list
   - Low (<0.6): Estimate or inferred
6. Compute priority_score:
   - Revenue weight: 50%
   - Export status: 30%
   - Certifications: 20%
7. Return enriched record
```

**Error Handling:**
- Missing fields: Set to `None`, don't fabricate
- Website unavailable: Use only government data, flag low confidence
- Conflicting data: Prefer government source, note discrepancy

#### 3.2.3 MECEValidationWorkflow

**Purpose**: Ensure dataset is Mutually Exclusive, Collectively Exhaustive

**Responsibilities:**
- Detect duplicates (same company, different names)
- Identify gaps (missing provinces or industry segments)
- Enforce single placement (each company in exactly one category)
- Generate MECE compliance report

**Logic:**
```
1. Deduplication:
   - Primary: Match by tax_id
   - Secondary: Fuzzy match on name+province (>90% similarity)
   - Action: Merge duplicates, keep highest-confidence data

2. Gap Detection:
   - Expected: All target provinces have ≥1 company
   - Validate: No province returns 0 results (likely data issue)

3. Mutual Exclusivity:
   - Check: No company appears in multiple provinces
   - Check: Cooperatives listed separately from member companies

4. Completeness Check:
   - Compare count vs. government statistics (if available)
   - Flag if <80% of expected count

5. Return:
   - Validated dataset
   - MECE report: {duplicates_removed, gaps_found, confidence}
```

#### 3.2.4 BatchOrchestrationWorkflow

**Purpose**: Coordinate full research process across provinces

**Responsibilities:**
- Orchestrate discovery → enrichment → validation pipeline
- Batch processing (10-15 companies per batch)
- Incremental output delivery
- Progress tracking
- Resume from checkpoint on failure

**Logic:**
```
Phase 1: Discovery (Parallel by Province)
├─ For each province in parallel:
│  ├─ Run CompanyDiscoveryWorkflow
│  └─ Collect all candidates
└─ Output: Master list of 1,000+ companies

Phase 2: Enrichment (Batched, Sequential)
├─ Split master list into batches of 10-15
├─ For each batch sequentially:
│  ├─ Run CompanyEnrichmentWorkflow on each company (parallel within batch)
│  ├─ Checkpoint: Save batch to cache
│  └─ Output: Deliver enriched batch to user
└─ Output: Stream of batches

Phase 3: Validation (Once at end)
├─ Collect all enriched companies
├─ Run MECEValidationWorkflow
└─ Output: Final validated dataset + MECE report

Recovery:
├─ If interrupted, read last checkpoint
└─ Resume from next batch
```

**Observability:**
```python
# Progress tracking
{
    "phase": "enrichment",
    "provinces_completed": 3,
    "provinces_total": 7,
    "companies_enriched": 247,
    "companies_total": 1043,
    "batches_completed": 16,
    "current_batch": 17,
    "estimated_time_remaining": "4.2 hours"
}
```

### 3.3 Resource Specialization

#### 3.3.1 VietnameseDataNormalizationResource

**Purpose**: Handle Vietnamese language data (domain-agnostic)

**Methods:**
```python
@tool_use
def normalize_company_name(self, name: str, **kwargs) -> DictParams:
    """
    Normalize Vietnamese company names for deduplication.

    Handles:
    - UTF-8 encoding variations (á, à, ả, ã, ạ)
    - Common abbreviations (TNHH, CP, etc.)
    - Punctuation variations
    - Whitespace normalization
    """

@tool_use
def normalize_address(self, address: str, **kwargs) -> DictParams:
    """
    Parse and normalize Vietnamese addresses into hierarchy.

    Returns: {street, district, province, confidence}
    """
```

**Why domain-agnostic?** Same logic applies to any Vietnamese company data, not coffee-specific.

#### 3.3.2 CompanyDataStructuringResource

**Purpose**: Structure extracted web data into schema (domain-agnostic)

**Methods:**
```python
@tool_use
def structure_company_data(
    self,
    raw_text: str,
    schema: Dict,
    **kwargs
) -> DictParams:
    """
    Use LLM to extract structured fields from unstructured text.

    Input: Raw HTML/text from company website or registry
    Output: Dictionary matching provided schema

    Handles:
    - Field extraction (revenue, certifications, etc.)
    - Type validation (dates, numbers, booleans)
    - Confidence scoring per field
    """
```

**Why domain-agnostic?** Uses generic LLM extraction, schema is passed as parameter.

#### 3.3.3 SourceProvenanceResource

**Purpose**: Track data lineage for all fields (domain-agnostic)

**Methods:**
```python
@tool_use
def record_source(
    self,
    field: str,
    value: Any,
    source_url: str,
    confidence: float,
    **kwargs
) -> DictParams:
    """Track where a data point came from"""

@tool_use
def get_provenance_report(self, company_id: str, **kwargs) -> DictParams:
    """Generate source report for all fields of a company"""
```

**Why domain-agnostic?** Provenance tracking is universal to all research.

---

## Phase 4: Composition Strategy

### 4.1 Component Hierarchy

```
VietnamCoffeeResearchAgent (STARAgent)
│
├─ Workflows:
│  ├─ BatchOrchestrationWorkflow (main entry point)
│  │  └─ Uses: Discovery, Enrichment, Validation workflows
│  │
│  ├─ CompanyDiscoveryWorkflow
│  │  └─ Uses: Search, Fetch, VietnameseNormalization resources
│  │
│  ├─ CompanyEnrichmentWorkflow
│  │  └─ Uses: Fetch, Extract, CompanyStructuring, SourceProvenance resources
│  │
│  └─ MECEValidationWorkflow
│     └─ Uses: VietnameseNormalization, SourceProvenance resources
│
└─ Resources (all domain-agnostic except agent context):
   ├─ SearchResource (existing, from dana/lib)
   ├─ FetchResource (existing)
   ├─ ExtractResource (existing)
   ├─ ConversationResource (existing)
   ├─ VietnameseDataNormalizationResource (new)
   ├─ CompanyDataStructuringResource (new)
   └─ SourceProvenanceResource (new)
```

### 4.2 Data Flow

```
User Input: {provinces: ["Đắk Lắk", "Gia Lai"], batch_size: 15}
    │
    ▼
BatchOrchestrationWorkflow
    │
    ├─ Phase 1: Discovery (Parallel)
    │   ├─ CompanyDiscoveryWorkflow(province="Đắk Lắk")
    │   │   └─> [Company1, Company2, ..., Company500]
    │   │
    │   └─ CompanyDiscoveryWorkflow(province="Gia Lai")
    │       └─> [Company501, Company502, ..., Company1000]
    │
    ├─ Phase 2: Enrichment (Batched)
    │   ├─ Batch 1 (Companies 1-15)
    │   │   ├─ CompanyEnrichmentWorkflow(Company1) ──┐
    │   │   ├─ CompanyEnrichmentWorkflow(Company2)   │ Parallel
    │   │   └─ ...                                    │ within
    │   │   └─> Output: [Enriched1-15]              ┘ batch
    │   │
    │   ├─ Batch 2 (Companies 16-30)
    │   │   └─> Output: [Enriched16-30]
    │   │
    │   └─ ... (repeat for all batches)
    │
    └─ Phase 3: Validation
        └─ MECEValidationWorkflow(all_companies)
            └─> {validated_dataset, mece_report}
```

### 4.3 Agent Implementation Pattern

```python
class VietnamCoffeeResearchAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>...</PUBLIC_DESCRIPTION>
    <PRIVATE_IDENTITY>...</PRIVATE_IDENTITY>
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        super().__init__(
            agent_type="vietnam-coffee-research",
            agent_id=agent_id or "vietnam-coffee-research-001",
            **kwargs
        )

        # Compose resources
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
```

### 4.4 Invocation Pattern

```python
# User invokes agent
agent = VietnamCoffeeResearchAgent()

# Execute research (streaming batches)
async for batch in agent.execute(
    provinces=["Đắk Lắk", "Gia Lai", "Lâm Đồng"],
    batch_size=15,
    enrichment_fields=["all"]  # or specify subset
):
    print(f"Batch {batch['number']}: {batch['companies']}")
    # User can save batch to CSV/DB here

# Get final validation report
final_result = agent.get_final_result()
print(f"MECE Report: {final_result['mece_report']}")
```

---

## Phase 5: Validation & Testing Strategy

### 5.1 Component Testing

#### Resource Tests
```python
def test_vietnamese_normalization():
    resource = VietnameseDataNormalizationResource()

    # Test encoding variations
    assert resource.normalize_company_name("Công ty Cổ phần") == \
           resource.normalize_company_name("Cong ty Co phan")

    # Test abbreviation handling
    assert "TNHH" in resource.normalize_company_name("TNHH An Giang Coffee")

def test_company_structuring():
    resource = CompanyDataStructuringResource()
    raw_html = "<html>... revenue: 50 billion VND ...</html>"

    result = resource.structure_company_data(
        raw_text=raw_html,
        schema={"revenue": int}
    )

    assert result["revenue"] == 50_000_000_000
    assert result["confidence"] > 0.7
```

#### Workflow Tests
```python
def test_company_discovery():
    workflow = CompanyDiscoveryWorkflow()

    result = workflow.execute(
        province="Đắk Lắk",
        industry="coffee"
    )

    assert len(result["companies"]) > 0
    assert all(c["province"] == "Đắk Lắk" for c in result["companies"])
    assert len(result["companies"]) == len(set(c["tax_id"] for c in result["companies"]))  # No duplicates

def test_mece_validation():
    workflow = MECEValidationWorkflow()

    # Create test data with duplicates
    companies = [
        {"name": "Company A", "tax_id": "123", "province": "Đắk Lắk"},
        {"name": "Cong ty A", "tax_id": "123", "province": "Đắk Lắk"},  # Duplicate
    ]

    result = workflow.execute(companies=companies)

    assert len(result["validated_companies"]) == 1  # Duplicate removed
    assert result["mece_report"]["duplicates_removed"] == 1
```

### 5.2 Integration Testing

```python
def test_end_to_end_single_province():
    """Test full pipeline on small dataset"""
    agent = VietnamCoffeeResearchAgent()

    result = agent.execute(
        provinces=["Đắk Lắk"],
        batch_size=10,
        limit=20  # MVP: test with 20 companies
    )

    # Collect all batches
    all_companies = []
    for batch in result:
        all_companies.extend(batch["companies"])

    # Validation
    assert len(all_companies) == 20
    assert all(c["province"] == "Đắk Lắk" for c in all_companies)
    assert all("confidence" in c for c in all_companies)
    assert len(set(c["tax_id"] for c in all_companies)) == 20  # MECE: no duplicates
```

### 5.3 Production Validation

#### Data Quality Metrics
```python
def validate_production_dataset(companies: List[Dict]) -> Dict:
    """Run after full execution"""

    metrics = {
        "total_companies": len(companies),
        "provinces": len(set(c["province"] for c in companies)),

        # Completeness
        "with_revenue": sum(1 for c in companies if c["revenue"] is not None),
        "with_export_status": sum(1 for c in companies if c["export_status"] is not None),
        "with_address": sum(1 for c in companies if c["address"] is not None),

        # Quality
        "high_confidence": sum(1 for c in companies if c["confidence"] > 0.8),
        "medium_confidence": sum(1 for c in companies if 0.5 < c["confidence"] <= 0.8),
        "low_confidence": sum(1 for c in companies if c["confidence"] <= 0.5),

        # MECE
        "unique_tax_ids": len(set(c["tax_id"] for c in companies)),
        "duplicates": len(companies) - len(set(c["tax_id"] for c in companies)),
    }

    # Validation checks
    assert metrics["duplicates"] == 0, "MECE violation: duplicates found"
    assert metrics["high_confidence"] / metrics["total_companies"] > 0.7, "Quality too low"

    return metrics
```

### 5.4 MVP Success Criteria

**For MVP (single province, 45-100 companies):**

✅ **Functional:**
- [ ] Discovers all companies in target province
- [ ] Enriches 100% with core fields (name, product, revenue estimate)
- [ ] Delivers in 10-company batches
- [ ] Validates MECE compliance
- [ ] Completes in <2 hours

✅ **Quality:**
- [ ] ≥70% high-confidence data (>0.8)
- [ ] ≥90% fields populated (not None)
- [ ] 0 duplicates in final dataset
- [ ] Source tracked for ≥95% of fields

✅ **Operational:**
- [ ] Observable progress throughout execution
- [ ] Resumes from checkpoint on failure
- [ ] Outputs ready for CSV export

---

## Phase 6: Implementation Plan

### 6.1 MVP Scope (Iteration 1)

**Target**: Single province (Đắk Lắk), 45-100 companies, core enrichment only

**Build Order:**
1. **Resources** (Day 1)
   - VietnameseDataNormalizationResource
   - CompanyDataStructuringResource
   - SourceProvenanceResource

2. **Workflows** (Day 2-3)
   - CompanyDiscoveryWorkflow (simplified: single source)
   - CompanyEnrichmentWorkflow (core fields only)
   - MECEValidationWorkflow (basic dedup)
   - BatchOrchestrationWorkflow (no resume logic yet)

3. **Agent** (Day 3)
   - VietnamCoffeeResearchAgent (basic composition)
   - Integration testing

4. **Testing & Refinement** (Day 4)
   - Run on Đắk Lắk province
   - Validate data quality
   - Fix bugs, refine extraction logic

### 6.2 Production Scope (Iteration 2)

**Target**: Multi-province (7 provinces), 1,000+ companies, full enrichment

**Enhancements:**
1. **Resources**
   - Add caching to all web resources
   - Add retry logic with exponential backoff

2. **Workflows**
   - CompanyDiscoveryWorkflow: Add all 3 data sources
   - CompanyEnrichmentWorkflow: Add all enrichment fields
   - BatchOrchestrationWorkflow: Add checkpoint/resume logic
   - Add parallel province processing

3. **Agent**
   - Add configuration for batch size, parallelism
   - Add monitoring/logging
   - Add output formats (CSV, JSON, database)

### 6.3 File Structure

```
docs/ai-building-agents/use-cases/
└── vietnam_coffee_research_agent_design.md (this file)

contrib/vietnam_coffee_research/  (implementation)
├── README.md
├── resources/
│   ├── __init__.py
│   ├── vietnamese_data_normalization.py
│   ├── company_data_structuring.py
│   └── source_provenance.py
├── workflows/
│   ├── __init__.py
│   ├── company_discovery.py
│   ├── company_enrichment.py
│   ├── mece_validation.py
│   └── batch_orchestration.py
├── agents/
│   ├── __init__.py
│   └── vietnam_coffee_research.py
├── prompts/
│   └── VietnamCoffeeResearchAgent.prt
├── tests/
│   ├── test_resources.py
│   ├── test_workflows.py
│   └── test_agent_integration.py
└── examples/
    ├── run_single_province.py
    └── run_multi_province.py
```

---

## Appendix A: Enrichment Field Definitions

| Field | Type | Source Priority | Notes |
|-------|------|----------------|-------|
| `name` | str | Government registry > Company website | Official registered name |
| `tax_id` | str | Government registry (masothue.com) | Unique identifier |
| `product_category` | str | Company website > Association list | Comma-separated if multiple |
| `export_status` | bool | Customs database > Company statement | Verified exporter flag |
| `revenue` | int | Government filing > Company statement > Estimate | Annual revenue in VND |
| `revenue_source` | str | Literal source type | For transparency |
| `years_incorporated` | int | Government registry | Years in business |
| `certifications` | List[str] | Company website > Association list | Fair Trade, Organic, etc. |
| `address` | str | Registry > Company website | Street-level if available |
| `district` | str | Parsed from address | District/County |
| `province` | str | User input or registry | Province (required) |
| `pic` | str | Company website | Person in charge (optional) |
| `affiliate` | str | Registry | Parent company if applicable |
| `priority_score` | float | Computed | 0-100 based on revenue/export/certs |
| `confidence` | float | Computed | 0-1 overall data quality |
| `sources` | Dict | Tracked per field | Field → URL mapping |

---

## Appendix B: Vietnamese Data Sources

| Source | URL | Data Available | Access Method |
|--------|-----|----------------|---------------|
| **Government Registry** | masothue.com | Name, Tax ID, Address, Registration date | Web scraping (by tax ID or name search) |
| **VICOFA** | vicofa.org.vn | Member companies, Certifications | Association member list |
| **Vietnam Customs** | customs.gov.vn | Export records | Public database (by company name or tax ID) |
| **Company Websites** | Various | Products, Certifications, Contact | Google search → scrape |
| **Provincial Portals** | Various .gov.vn | Regional business listings | Province-specific portals |

---

## Appendix C: Scale & Performance Estimates

**MVP (Single Province, 100 companies):**
- Discovery: ~5 minutes (1 province, 100 companies)
- Enrichment: ~90 minutes (100 companies × ~50s avg)
- Validation: ~5 minutes
- **Total: ~1.7 hours**

**Production (7 Provinces, 1,000 companies):**
- Discovery: ~15 minutes (7 provinces parallel, 1,000 companies)
- Enrichment: ~8 hours (1,000 companies × ~30s avg, with parallelism)
- Validation: ~10 minutes
- **Total: ~8.5 hours**

**Optimization Opportunities:**
- Increase batch parallelism (currently 15 per batch)
- Cache common lookups (province codes, certifications)
- Pre-fetch government data in bulk
- Target: <4 hours for 1,000 companies

---

**Design Status**: ✅ Ready for review and implementation

**Next Steps:**
1. Review this design document
2. Validate against ai-building-agents/design/agent_team_design_guide.md
3. Proceed with MVP implementation (Day 1-4)
4. Iterate based on real data from Đắk Lắk province
