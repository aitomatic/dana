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

<IDENTITY>
I am methodical and thorough in my research process. I maintain strict
data quality standards, distinguishing verified facts from estimates.
I work incrementally, providing checkpoints rather than waiting to
deliver everything at once. I track the provenance of every data point
I collect. When I encounter gaps in data, I explicitly flag them rather
than fabricating information. I understand the importance of MECE
compliance and actively work to prevent duplicates and ensure complete
coverage across provinces.
</IDENTITY>
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

**Enrichment Schema (Enhanced):**
```python
{
    # Core Identity
    "name": str,                    # Official company name
    "tax_id": str,                  # Vietnamese tax ID (required)
    "entity_type": str,             # "Private Roaster" | "Cooperative" | "SME/Farm" | "SME/Processor" | "Export Co"

    # Products & Markets
    "product_category": str,        # Detailed: "Robusta, Arabica (roasted, packaged)"
    "volume_tons": str,             # Production volume: "100-120" or "~35"
    "export_status": bool,          # Verified exporter (✅/❌)
    "key_markets": str | None,      # Export destinations: "US, KR, Middle East"

    # Financial
    "revenue": int | None,          # Annual revenue (USD)
    "revenue_source": str,          # "Financial Statement" | "Estimate" | "Media Disclosure"
    "years_incorporated": int,      # Years in business

    # Certifications & Compliance
    "certifications": List[str],    # ["Fair Trade", "Organic", "Rainforest Alliance"]

    # Location
    "address": str,                 # Street address (if available)
    "district": str | None,         # District/County
    "province": str,                # Province (required)

    # Contact & Relationships
    "pic": str | None,              # Person in charge name
    "pic_title": str | None,        # Title: "Sales Dir." | "Chair" | "Founder"
    "affiliate": str | None,        # Group/network: "MILANO Group" | "Fairtrade Coop Network"

    # Scoring & Analysis
    "priority_score": float,        # 0-5 scale (strategic importance)
    "notes": str,                   # Business intelligence commentary (1-2 sentences)
    "confidence": float,            # 0-1 (overall data quality)

    # Metadata
    "sources": Dict[str, str],      # Field -> Source URL mapping
    "field_confidences": Dict[str, float],  # Per-field confidence scores
}
```

**Logic (Enhanced):**
```
1. Fetch company website (if exists)
2. Fetch government registry page (by tax ID)
3. Extract fields in parallel:
   - Basic info (name, address) from registry
   - Entity type classification from company name/structure
   - Revenue from registry or company statements (convert to USD)
   - Production volume estimation from revenue/market data
   - Export status from customs database
   - Key export markets from trade records/company website
   - Certifications from company website or association lists
   - PIC name and title from company website/registry
   - Affiliate/group membership from association lists
4. Validate:
   - Required fields present (name, tax_id, province, entity_type)
   - Data consistency (e.g., years_incorporated <= 100, volume_tons reasonable)
   - Export markets only if export_status = true
5. Compute per-field confidence:
   - High (0.9+): Government-verified data
   - Medium (0.6-0.9): Company statement or association list
   - Low (<0.6): Estimate or inferred
6. Compute priority_score (0-5 scale):
   Score = min(5.0, (
       revenue_score * 0.40 +          # Revenue importance
       export_score * 0.30 +            # Export capability
       certification_score * 0.20 +     # Quality certifications
       volume_score * 0.10              # Production scale
   ))

   Where:
   - revenue_score: 0-5 based on revenue brackets
   - export_score: 5 if exports, 2.5 if license, 0 otherwise
   - certification_score: 1.0 per cert (FLO, Organic, etc.), max 5
   - volume_score: 0-5 based on production volume
7. Generate notes:
   - Summarize key differentiators (1-2 sentences)
   - Highlight: scale, certifications, market position, export strength
   - Example: "Leading roaster with strong branded presence and export B2B network."
8. Return enriched record
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
- Human approval gates (3 checkpoints)
- Progress tracking
- Resume from checkpoint on failure

**Logic (with Human-in-Loop Gates):**
```
Phase 1: Discovery (Parallel by Province)
├─ For each province in parallel:
│  ├─ Run CompanyDiscoveryWorkflow
│  └─ Collect all candidates
└─ Output: Master list of 1,000+ companies
    │
    ▼
>>> GATE 1: DISCOVERY APPROVAL <<<
    Show: Total discovered, sample companies, provinces covered
    User Action: APPROVE to proceed with enrichment / REJECT to abort
    Why critical: Prevents enriching bad candidates (discovery is cheap, enrichment is expensive)

Phase 2: Enrichment (Batched, Sequential)
├─ Split master list into batches of 10-15
├─ For each batch sequentially:
│  ├─ Run CompanyEnrichmentWorkflow on each company (parallel within batch)
│  ├─ Checkpoint: Save batch to cache
│  ├─ Output: Deliver enriched batch to user
│  └─ Every 5 batches (~50 companies):
│      │
│      ▼
    >>> GATE 2: ENRICHMENT PROGRESS REVIEW <<<
        Show: Companies enriched so far, quality preview (high/medium/low confidence)
        User Action: CONTINUE / ABORT (if quality is too low)
        Why valuable: Catch quality problems early before wasting 8 hours
└─ Output: Stream of batches

Phase 3: Validation (Once at end)
├─ Collect all enriched companies
├─ Run MECEValidationWorkflow
└─ Output: Validated dataset + MECE report
    │
    ▼
>>> GATE 3: FINAL APPROVAL <<<
    Show: Total companies, MECE compliance, quality distribution
    User Action: APPROVE final delivery / REQUEST re-enrichment for low-confidence
    Why essential: Final sanity check before stakeholder delivery

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

### 3.4 Human-in-Loop Architecture

**Design Decision**: Multiple approval gates instead of single end-of-pipeline review

**Rationale:**
- **Early abort**: Catch bad candidates after discovery (saves 8 hours of enrichment)
- **Mid-course correction**: Detect quality issues during enrichment (catch data source problems)
- **Final approval**: Sanity check before stakeholder delivery

**Gate Design Pattern:**

```python
# BatchOrchestrationWorkflow accepts optional approval callback
def __init__(self, approval_callback=None):
    """
    Args:
        approval_callback: Optional function(gate_data: dict) -> bool
            Returns True to proceed, False to abort
    """
    self.approval_callback = approval_callback

def execute(self, provinces, batch_size):
    # Phase 1: Discovery
    discovered = self._run_discovery(provinces)

    # Gate 1: Review discoveries
    if self.approval_callback:
        gate_data = {
            "gate": "discovery",
            "total_companies": len(discovered),
            "sample": discovered[:10]
        }
        if not self.approval_callback(gate_data):
            return {"success": False, "aborted_at": "discovery"}

    # Phase 2: Enrichment with periodic reviews
    # Gate 2: Every 5 batches

    # Phase 3: Validation
    # Gate 3: Final approval
```

**Agent-Level Implementation:**

The agent provides the approval callback that formats gate data and prompts user:

```python
class VietnamCoffeeResearchAgent:
    def research_companies(self, provinces, interactive=True):
        """Run research with optional interactive gates."""

        def approval_gate(gate_data: dict) -> bool:
            gate_name = gate_data["gate"]

            if gate_name == "discovery":
                # Display discovered companies
                print(f"Found {gate_data['total_companies']} companies")
                print(f"Sample: {gate_data['sample']}")

                if interactive:
                    response = input("Proceed with enrichment? (yes/no): ")
                    return response.lower() in ["yes", "y"]
                return True

            elif gate_name == "enrichment":
                # Display quality preview
                quality = gate_data['quality_preview']
                print(f"Enriched: {gate_data['enriched_so_far']}")
                print(f"Quality: {quality['high']} high, {quality['low']} low")

                if interactive:
                    response = input("Continue enrichment? (yes/no): ")
                    return response.lower() in ["yes", "y"]
                return True

            elif gate_name == "final":
                # Display final report
                print(f"Total: {gate_data['total_companies']}")
                print(f"MECE: {gate_data['mece_report']}")

                if interactive:
                    response = input("Approve final dataset? (yes/no): ")
                    return response.lower() in ["yes", "y"]
                return True

        # Pass approval callback to orchestration workflow
        return batch_workflow.execute(
            provinces,
            approval_callback=approval_gate if interactive else None
        )
```

**Why Not `.converse()`?**

The `.converse()` method is designed for ongoing conversational interactions, not mid-workflow checkpoints:
- Blocking input() calls don't fit batch processing
- Difficult to return structured approval/rejection to workflow
- Better suited for **review mode** after automated processing

**Recommendation**: Use callback pattern for approval gates, reserve `.converse()` for post-processing review sessions.

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

## Appendix A: Enrichment Field Definitions (Enhanced)

| Field | Type | Source Priority | Notes |
|-------|------|----------------|-------|
| `name` | str | Government registry > Company website | Official registered name |
| `tax_id` | str | Government registry (masothue.com) | Unique identifier |
| `entity_type` | str | Company structure in registry | "Private Roaster", "Cooperative", "SME/Farm", "SME/Processor", "Export Co" |
| `product_category` | str | Company website > Association list | Detailed format: "Robusta, Arabica (roasted, packaged)" |
| `volume_tons` | str | Estimate from revenue/market data | Range format: "100-120" or approximate: "~35" |
| `export_status` | bool | Customs database > Company statement | Verified exporter flag (display as ✅/❌) |
| `key_markets` | str | Trade records > Company website | Comma-separated: "US, KR, Middle East" |
| `revenue` | int | Government filing > Company statement > Estimate | Annual revenue in USD (converted from VND) |
| `revenue_source` | str | Literal source type | "Financial Statement", "Estimate", "Media Disclosure" |
| `years_incorporated` | int | Government registry | Years in business |
| `certifications` | List[str] | Company website > Association list | ["Fair Trade", "Organic", "Rainforest Alliance", "4C", "UTZ"] |
| `address` | str | Registry > Company website | Street-level if available |
| `district` | str | Parsed from address | District/County |
| `province` | str | User input or registry | Province (required) |
| `pic` | str | Company website > Registry | Person in charge name |
| `pic_title` | str | Company website | Title: "Sales Dir.", "Chair", "Founder", "CEO" |
| `affiliate` | str | Association list > Registry | Group/network: "MILANO Group", "Fairtrade Coop Network" |
| `priority_score` | float | Computed | 0-5 scale (strategic importance) |
| `notes` | str | Generated from enrichment data | 1-2 sentence business intelligence summary |
| `confidence` | float | Computed | 0-1 overall data quality |
| `sources` | Dict | Tracked per field | Field → Source URL mapping |
| `field_confidences` | Dict | Computed per field | Field → confidence (0-1) |

---

## Appendix A2: Output Format Specifications

### Table Format (Primary Output)

The enriched data should be output in a formatted table with the following columns:

| Column | Format | Example |
|--------|--------|---------|
| # | Sequential number | 1, 2, 3... |
| Company Name | Full official name | Công ty TNHH sản xuất Milano |
| Entity Type | Classification | Private Roaster, Cooperative, SME/Farm |
| Product Categories | Detailed description | Robusta, Arabica (roasted, packaged) |
| Est. Volume (tons) | Range or ~value | 100–120, ~35 |
| Est. Revenue (USD) | Number or range | 375,000 or 360,000–450,000 |
| Revenue Source | Source type | Financial Statement, Estimate |
| Years Incorporated | Integer | 11 |
| Export License | Checkbox | ✅ Yes / ❌ No |
| Key Markets | Comma-separated | US, KR, Middle East |
| Certifications | Comma-separated | HACCP, ISO, Fair Trade |
| PIC (Verified) | Name and title | Nguyễn Quốc Tuấn (Sales Dir.) |
| Affiliate / Group Tag | Group name or "None" | MILANO Group, Fairtrade Coop Network |
| Priority Score | 0-5 with decimal | 4.8, 4.6, 3.4 |
| Notes | 1-2 sentence commentary | Leading roaster with strong branded presence and export B2B network. |

### CSV Export Format

```csv
company_name,tax_id,entity_type,product_category,volume_tons,revenue_usd,revenue_source,years_incorporated,export_status,key_markets,certifications,pic_name,pic_title,affiliate,priority_score,notes,confidence
```

### JSON Format (for API/Database)

```json
{
  "companies": [
    {
      "name": "Công ty TNHH sản xuất Milano",
      "tax_id": "0123456789",
      "entity_type": "Private Roaster",
      "product_category": "Robusta, Arabica (roasted, packaged)",
      "volume_tons": "100-120",
      "revenue": 375000,
      "revenue_source": "Financial Statement",
      "years_incorporated": 11,
      "export_status": true,
      "key_markets": "US, KR, Middle East",
      "certifications": ["HACCP", "ISO"],
      "address": "...",
      "district": "...",
      "province": "Đắk Lắk",
      "pic": "Nguyễn Quốc Tuấn",
      "pic_title": "Sales Dir.",
      "affiliate": "MILANO Group",
      "priority_score": 4.8,
      "notes": "Leading roaster with strong branded presence and export B2B network.",
      "confidence": 0.92,
      "sources": {...},
      "field_confidences": {...}
    }
  ],
  "summary": {
    "total_companies": 20,
    "provinces": ["Đắk Lắk"],
    "mece_report": {...}
  }
}
```

### Display Priorities

**For Table View:**
- Sort by: Priority Score (descending)
- Group by: Province or Entity Type (configurable)
- Highlight: High-value exporters (priority_score > 4.5)
- Format: Export status as ✅/❌ for readability

**For CSV Export:**
- Include all fields (including metadata)
- Use UTF-8 encoding for Vietnamese characters
- Escape commas in text fields

**For Analysis/CRM Ingestion:**
- JSON format with full metadata
- Include source provenance and field-level confidence
- Add timestamp and agent version

---

## Appendix B: Entity Type Classification Rules

Entity types should be inferred from company name, structure, and business model:

| Entity Type | Identifying Patterns | Examples |
|-------------|---------------------|----------|
| **Private Roaster** | "Sản xuất" (production), sells packaged/branded coffee | Công ty TNHH sản xuất Milano |
| **Cooperative** | "HTX" (Hợp tác xã), member-based | HTX Ea Tân (Flo), HTX Cà phê Đăk Hà |
| **SME/Farm** | Farm or small-medium business, single origin | The Married Beans, Ama Farm Coffee |
| **SME/Processor** | Processing but not large scale | Công ty TNHH Đăk Mê Trang |
| **SME/Roaster** | Small-medium roasting operations | Cà Phê Bột Uy Tín |
| **Export Co** | Export company in name or primary business | VNCoffee Export Ltd |
| **SME/Trade** | Trading company | Công ty TNHH TM Gia Lộc (TM = Thương mại) |

**Classification Logic:**
1. If "HTX" or "Hợp tác xã" in name → **Cooperative**
2. If "Export" in name or primarily export → **Export Co**
3. If "Farm" or farm-direct model → **SME/Farm**
4. If large-scale roasting/branding → **Private Roaster**
5. If processing/manufacturing → **SME/Processor** or **SME/Roaster**
6. If trading → **SME/Trade**

---

## Appendix C: Vietnamese Data Sources

| Source | URL | Data Available | Access Method |
|--------|-----|----------------|---------------|
| **Government Registry** | masothue.com | Name, Tax ID, Address, Registration date | Web scraping (by tax ID or name search) |
| **VICOFA** | vicofa.org.vn | Member companies, Certifications | Association member list |
| **Vietnam Customs** | customs.gov.vn | Export records | Public database (by company name or tax ID) |
| **Company Websites** | Various | Products, Certifications, Contact | Google search → scrape |
| **Provincial Portals** | Various .gov.vn | Regional business listings | Province-specific portals |

---

## Appendix D: Scale & Performance Estimates

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

## Appendix E: Implementation Progress Tracker

### Current Implementation Status

**Overall**: MVP Implementation Complete with Enhanced Output Format

| Component | Status | Notes |
|-----------|--------|-------|
| **Design Document** | ✅ Complete | Enhanced with output formats, entity classification, 3-gate approval architecture |
| **Resources** | ⚠️ Simulated | Working but using mock data instead of real web resources |
| **Workflows** | ⚠️ Simulated | Working but return simulated data |
| **Agent** | ✅ Complete | Fully functional with enhanced schema |
| **Human-in-Loop Gates** | 📝 Designed | Architecture documented, not yet implemented |
| **Examples** | ✅ Complete | Three examples: basic, multi-province, enhanced formatting |
| **Testing** | ⚠️ Manual | Component tests exist but not integrated into test suite |

### Implementation Phases

#### Phase 1: MVP with Simulated Data ✅ COMPLETE
**Target**: Demonstrate full pipeline with mock data
**Duration**: Completed October 2025

- ✅ Resources (3 new + 4 existing composed)
  - ✅ VietnameseDataNormalizationResource
  - ✅ CompanyDataStructuringResource
  - ✅ SourceProvenanceResource
  - ✅ SearchResource, FetchResource, ExtractResource, ConversationResource (composed)

- ✅ Workflows (4 new)
  - ✅ CompanyDiscoveryWorkflow (returns simulated candidates)
  - ✅ CompanyEnrichmentWorkflow (enhanced schema with entity types, notes, 0-5 scoring)
  - ✅ MECEValidationWorkflow (basic deduplication)
  - ✅ BatchOrchestrationWorkflow (3-phase orchestration)

- ✅ Agent
  - ✅ VietnamCoffeeResearchAgent (single specialist pattern)
  - ✅ Enhanced enrichment schema (19 fields including entity_type, volume_tons, key_markets, pic_title, notes, priority_score 0-5)
  - ✅ Priority scoring on 0-5 scale with weighted components
  - ✅ Entity type classification (7 types)
  - ✅ Business intelligence notes generation

- ✅ Examples
  - ✅ run_single_province.py (basic MVP)
  - ✅ run_multi_province.py (production scale)
  - ✅ run_with_formatting.py (enhanced output matching ryan.md format)

- ✅ Documentation
  - ✅ Enhanced design.md with output formats and entity classification
  - ✅ README.md with quick start guide
  - ✅ implementation_pitfalls.md documenting lessons learned

#### Phase 2: Real Data Integration 📝 NEXT
**Target**: Replace simulated data with real Vietnamese web sources
**Duration**: Estimated 2-3 days

- [ ] Update CompanyDiscoveryWorkflow
  - [ ] `_query_government_registry()`: Use SearchResource + FetchResource to scrape masothue.com
  - [ ] `_query_association_lists()`: Fetch VICOFA member list
  - [ ] `_query_export_database()`: Scrape customs.gov.vn export records

- [ ] Update CompanyEnrichmentWorkflow
  - [ ] `_fetch_government_registry()`: Real tax ID lookup via FetchResource
  - [ ] `_fetch_company_website()`: Google search + scrape via SearchResource + FetchResource
  - [ ] Add error handling: retries, rate limiting, timeouts

- [ ] Add Caching Layer
  - [ ] Cache government registry responses (by tax ID)
  - [ ] Cache company website fetches (by URL)
  - [ ] Implement TTL and invalidation strategy

- [ ] Testing
  - [ ] Test with real Đắk Lắk province data
  - [ ] Validate data quality vs. simulated baseline
  - [ ] Benchmark performance (target: <2 hours for 100 companies)

#### Phase 3: Human-in-Loop Gates 📝 DESIGNED
**Target**: Add 3 approval checkpoints to BatchOrchestrationWorkflow
**Duration**: Estimated 1 day

- [ ] Update BatchOrchestrationWorkflow
  - [ ] Add `approval_callback` parameter to `__init__()`
  - [ ] Implement Gate 1 after discovery (show discovered companies, await approval)
  - [ ] Implement Gate 2 during enrichment (every 5 batches, show quality preview)
  - [ ] Implement Gate 3 after validation (show final report, await approval)
  - [ ] Add abort/resume logic for each gate

- [ ] Update VietnamCoffeeResearchAgent
  - [ ] Add `approval_gate()` method to format gate data and prompt user
  - [ ] Add `interactive` parameter to `research_companies()`
  - [ ] Pass approval callback to BatchOrchestrationWorkflow

- [ ] Add Quality Preview Helpers
  - [ ] `_compute_quality_preview()`: Calculate high/medium/low confidence distribution
  - [ ] `_compute_quality_report()`: Full quality metrics for final gate

- [ ] Testing
  - [ ] Test abort at each gate
  - [ ] Test resume after abort
  - [ ] Test non-interactive mode (skip all gates)

#### Phase 4: Production Hardening 🔮 FUTURE
**Target**: Scale to 1,000+ companies with resilience
**Duration**: Estimated 3-5 days

- [ ] Parallel Enrichment
  - [ ] Increase batch parallelism (10-20 concurrent enrichments)
  - [ ] Add rate limiting to avoid overwhelming sources

- [ ] Checkpoint/Resume
  - [ ] Persistent checkpoints (write to disk after each batch)
  - [ ] Resume logic: detect last checkpoint, continue from there
  - [ ] Idempotent batch processing (skip already-enriched companies)

- [ ] Error Resilience
  - [ ] Exponential backoff for failed fetches
  - [ ] Circuit breaker for consistently failing sources
  - [ ] Partial enrichment (save what's available, flag missing fields)

- [ ] Monitoring & Observability
  - [ ] Real-time progress tracking (companies/min, ETA)
  - [ ] Quality metrics dashboard (confidence distribution over time)
  - [ ] Source health tracking (success rate per data source)

- [ ] Output Formats
  - [ ] CSV export with all fields (UTF-8 encoded)
  - [ ] JSON export with full metadata
  - [ ] Database ingestion (PostgreSQL, CRM systems)

- [ ] Scale Testing
  - [ ] Test with 7 provinces, 1,000+ companies
  - [ ] Validate <8 hour completion time
  - [ ] Stress test with network failures, slow sources

### Known Gaps & Technical Debt

| Gap | Impact | Priority | Plan |
|-----|--------|----------|------|
| **Simulated data sources** | Can't validate real-world data quality | 🔴 High | Phase 2: Replace with real web scraping |
| **No human-in-loop gates** | Can't abort bad discoveries early | 🟡 Medium | Phase 3: Add 3 approval checkpoints |
| **No persistent checkpoints** | Lost work on failure | 🟡 Medium | Phase 4: Add disk-based checkpoints |
| **Sequential batch processing** | Slow at scale (8+ hours for 1,000 companies) | 🟡 Medium | Phase 4: Parallelize enrichment within batches |
| **No error retry logic** | Fails on transient network errors | 🟢 Low | Phase 4: Add exponential backoff |
| **No caching** | Re-fetches same URLs | 🟢 Low | Phase 2: Add HTTP cache layer |
| **Test coverage** | Manual testing only | 🟢 Low | Phase 2-3: Integrate pytest suite |

### Validation Metrics

**MVP Success Criteria** (as of October 2025):
- ✅ Discovers companies (simulated)
- ✅ Enriches with 19 fields (including enhanced schema)
- ✅ Delivers in batches (10-15 companies)
- ✅ MECE validated (deduplication working)
- ✅ Enhanced output format (table, CSV, JSON)
- ✅ Entity classification (7 types)
- ✅ Priority scoring on 0-5 scale
- ✅ Business intelligence notes
- ⏱️ Performance: ~instant (simulated data)

**Production Readiness Checklist** (Phase 4 target):
- [ ] Real data sources integrated
- [ ] <2 hours for 100 companies (single province)
- [ ] <8 hours for 1,000+ companies (7 provinces)
- [ ] Human-in-loop gates implemented
- [ ] Checkpoint/resume working
- [ ] ≥70% high-confidence enrichment
- [ ] ≥90% field population rate
- [ ] 0 duplicates in final dataset
- [ ] Test suite passing (unit + integration)

---

**Design Status**: ✅ Complete with Enhanced Output Format & 3-Gate Architecture

**Implementation Status**: ⚠️ MVP Complete (Simulated Data), Phase 2 (Real Data) Next

**Next Steps:**
1. ✅ Enhanced schema implementation (COMPLETE)
2. ✅ Output format specification (COMPLETE)
3. ✅ 3-gate approval architecture design (COMPLETE)
4. 📝 Phase 2: Replace simulated data with real web scraping (NEXT)
5. 📝 Phase 3: Implement human-in-loop gates
6. 🔮 Phase 4: Production hardening and scale testing
