# SmartResearchAgent - Design Document

**Status**: Implementation Ready
**Created**: October 2025
**Pattern**: Single Specialist Agent with Phased Orchestration
**Complexity**: Medium (4-6 hours implementation)

---

## Executive Summary

SmartResearchAgent is a transparent, adaptive research assistant that demonstrates the STAR framework's unique strengths. Unlike black-box AI research tools (ChatGPT, Perplexity), this agent makes its reasoning visible - users see the STAR loop in action: query analysis, strategy selection, parallel information gathering, synthesis, and confidence assessment.

**Key Differentiators:**
- **Transparent Reasoning**: Visible STAR loop (SEE → THINK → ACT → REFLECT)
- **Adaptive Strategy**: Different query types trigger different research approaches
- **Multi-dimensional Confidence**: Granular confidence scores with explanations
- **Gap Identification**: Explicitly identifies what's missing from research
- **Source Diversity**: Parallel gathering from academic, news, documentation, and code sources

---

## Phase 1: Problem Analysis

### 1.1 Problem Statement

**The Problem**: Existing AI research tools provide answers but hide their reasoning process. Users don't see:
- What search strategy was chosen and why
- Which sources were considered and how they were ranked
- What confidence the system has in different parts of the answer
- What knowledge gaps exist
- How findings were synthesized

**The Solution**: Make the STAR loop observable - show every step from query understanding to synthesis.

### 1.2 Target Users

- **Researchers**: Need to verify AI-generated information
- **Students**: Learning to research effectively
- **Knowledge Workers**: Making decisions based on current information
- **Developers**: Understanding technical topics quickly
- **Anyone**: Who wants to understand *how* the answer was derived, not just *what* the answer is

### 1.3 Success Criteria

**Functional:**
- ✅ Adapts search strategy based on query type
- ✅ Gathers from 3+ diverse source types in parallel
- ✅ Synthesizes findings with cross-referencing
- ✅ Identifies knowledge gaps explicitly
- ✅ Provides multi-dimensional confidence scores

**Quality:**
- ✅ 80%+ overall confidence on well-researched topics
- ✅ Correctly identifies query type >90% of time
- ✅ Detects knowledge gaps when coverage <80%
- ✅ Generates 3-5 relevant follow-up questions

**Performance:**
- ✅ Quick facts: <5 seconds
- ✅ Technical deep-dive: 15-25 seconds
- ✅ Comparative analysis: 20-35 seconds

**Experience:**
- ✅ STAR loop visibility (users see reasoning)
- ✅ Magic function interface works
- ✅ Conversational refinement supported

---

## Phase 2: Component Identification

### 2.1 Required Capabilities

| Capability | Type | Complexity | Reusability |
|-----------|------|------------|-------------|
| **Query Analysis** | Workflow | Low | High (any research agent) |
| **Strategy Selection** | Workflow | Medium | High (adaptive agents) |
| **Parallel Source Gathering** | Workflow | Medium | High (multi-source research) |
| **Source Ranking** | Resource | Medium | Very High (any source evaluation) |
| **Synthesis & Cross-Reference** | Workflow | High | High (any synthesis task) |
| **Gap Detection** | Workflow | Medium | High (quality assessment) |
| **Confidence Scoring** | Workflow | Low | Very High (any AI output) |

### 2.2 Existing Dana Resources (Reuse)

From `dana_agent/dana/lib/resources/`:

- ✅ **SearchResource** (`web_research/search.py`) - Web search via Google
- ✅ **FetchResource** (`web_research/web_fetcher.py`) - HTTP fetching and content retrieval
- ✅ **ExtractResource** (`web_research/extract.py`) - Content extraction from HTML
- ✅ **ConversationResource** (`conversation.py`) - LLM-powered analysis and reasoning

### 2.3 New Components Needed

#### Resources to Build

1. **SourceRankingResource** (domain-agnostic)
   - Purpose: Rank sources by relevance, authority, recency
   - Reusability: Any multi-source research or information gathering
   - Methods:
     - `rank_by_quality()`: Rank sources using multi-factor scoring
     - `assess_authority()`: Evaluate source credibility
     - `check_recency()`: Assess source freshness

#### Workflows to Build

1. **ResearchStrategyWorkflow**
   - Input: User query
   - Output: Selected strategy (QUICK_FACT, TECHNICAL_DEEP_DIVE, CURRENT_EVENTS, COMPARATIVE_ANALYSIS)
   - Logic: LLM analyzes query → classifies type → selects appropriate strategy

2. **ParallelGatheringWorkflow**
   - Input: Query + strategy
   - Output: Ranked list of sources with content
   - Logic: Parallel search across source types → rank by quality → fetch top sources

3. **SynthesisWorkflow**
   - Input: Sources + query
   - Output: Synthesized answer with confidence scores
   - Logic: Extract claims → cross-reference → identify themes → detect gaps → generate narrative

#### Agent to Build

1. **SmartResearchAgent**
   - Pattern: Single specialist
   - Role: Transparent research assistant
   - Workflows: 3 new workflows + GoogleLookupWorkflow (existing)
   - Resources: 1 new + 4 existing

---

## Phase 3: Specialization Decomposition

### 3.1 Agent Design

**Pattern**: Single Specialist (like WebResearchAgent)

**Why Single Specialist?**
- Single domain: Research and information synthesis
- Focused task: Query → Gather → Synthesize → Present
- No need for multiple agent perspectives
- Complexity comes from workflow orchestration, not agent hierarchy

**Agent Identity:**

```xml
<PUBLIC_DESCRIPTION>
SmartResearchAgent is a transparent research assistant that makes its reasoning visible.

I help you:
- Understand complex topics through multi-source research
- See exactly how I search, evaluate, and synthesize information
- Assess confidence in different parts of my answers
- Identify knowledge gaps and areas for deeper investigation

Unlike black-box AI, I show you my STAR loop:
- SEE: How I understand your question
- THINK: What research strategy I choose and why
- ACT: Where I search and how I evaluate sources
- REFLECT: How confident I am and what's missing

Use me when you need:
- Research with transparent reasoning
- Multi-source verification
- Confidence assessment
- Gap identification for thorough understanding
</PUBLIC_DESCRIPTION>

<IDENTITY>
You are a transparent research assistant who values intellectual honesty and thoroughness.

Your principles:
- **Transparency**: Always show your reasoning process
- **Adaptability**: Choose the right strategy for each query type
- **Rigor**: Cross-reference claims from multiple sources
- **Honesty**: Explicitly identify gaps and uncertainties
- **Clarity**: Present complex information accessibly

Your process:
1. **Understand** the query deeply (not just keywords)
2. **Strategize** based on query type and user needs
3. **Gather** from diverse, authoritative sources in parallel
4. **Synthesize** by cross-referencing and identifying themes
5. **Assess** confidence and identify knowledge gaps
6. **Present** findings with sources, confidence, and follow-ups

You are methodical but not slow, comprehensive but not overwhelming.
You celebrate intellectual curiosity and help users research effectively.
</IDENTITY>
```

### 3.2 Workflow Specialization

#### 3.2.1 ResearchStrategyWorkflow

**Purpose**: Analyze query and select optimal research strategy

**Strategy Types:**

```python
STRATEGIES = {
    "QUICK_FACT": {
        "description": "Simple factual lookup",
        "sources": ["google_search"],
        "depth": "shallow",
        "max_sources": 3,
        "time_estimate": "2-5s",
        "example": "What is quantum computing?"
    },

    "TECHNICAL_DEEP_DIVE": {
        "description": "Deep technical research",
        "sources": ["academic", "documentation", "technical_blogs"],
        "depth": "deep",
        "max_sources": 20,
        "time_estimate": "15-25s",
        "example": "Explain transformer architecture in detail"
    },

    "CURRENT_EVENTS": {
        "description": "Recent news and developments",
        "sources": ["news", "blogs", "announcements"],
        "depth": "medium",
        "max_sources": 15,
        "time_estimate": "8-15s",
        "example": "Latest quantum computing breakthroughs"
    },

    "COMPARATIVE_ANALYSIS": {
        "description": "Compare multiple options",
        "sources": ["reviews", "benchmarks", "documentation"],
        "depth": "deep",
        "max_sources": 20,
        "time_estimate": "20-35s",
        "example": "Compare React vs Vue in 2024"
    }
}
```

**Logic:**
```
1. Use ConversationResource to analyze query:
   - Query type (definition, explanation, comparison, current events)
   - Complexity level (simple, medium, complex)
   - Implicit requirements (recency, depth, breadth)

2. Map to strategy:
   - Definition query + simple → QUICK_FACT
   - Technical question + complex → TECHNICAL_DEEP_DIVE
   - "Latest" or date reference → CURRENT_EVENTS
   - "Compare" or "vs" → COMPARATIVE_ANALYSIS

3. Return strategy with reasoning
```

#### 3.2.2 ParallelGatheringWorkflow

**Purpose**: Gather information from diverse sources in parallel

**Responsibilities:**
- Execute searches across multiple source types simultaneously
- Rank results by quality (relevance, authority, recency)
- Fetch and extract content from top sources
- Track source metadata for provenance

**Logic:**
```
1. Based on strategy, determine source types to query

2. Parallel search phase:
   async def gather():
       searches = []
       if "academic" in sources:
           searches.append(search_academic(query))
       if "news" in sources:
           searches.append(search_news(query))
       if "documentation" in sources:
           searches.append(search_documentation(query))

       results = await asyncio.gather(*searches)
       return results

3. Ranking phase:
   - Use SourceRankingResource to score each source:
     score = (relevance * 0.4) + (authority * 0.3) + (recency * 0.3)
   - Sort and select top N sources per strategy

4. Fetching phase:
   - Parallel fetch of top sources
   - Extract main content using ExtractResource
   - Return structured source list with content

5. Return:
   {
       "sources": [list of source objects],
       "total_found": int,
       "total_fetched": int,
       "source_types": [types used],
       "metadata": {...}
   }
```

#### 3.2.3 SynthesisWorkflow

**Purpose**: Synthesize findings, cross-reference claims, identify gaps

**Responsibilities:**
- Extract factual claims from each source
- Cross-reference claims across sources
- Identify themes and organize findings
- Detect knowledge gaps
- Calculate multi-dimensional confidence
- Generate follow-up questions

**Logic:**
```
1. Claim Extraction:
   - Use LLM to extract factual claims from each source
   - Tag each claim with source URL and date

2. Cross-Referencing:
   - Group similar claims
   - verified_claims: claims appearing in 2+ sources
   - single_source_claims: claims from only 1 source
   - conflicting_claims: contradictory claims

3. Theme Identification:
   - Cluster claims by topic
   - Identify major themes (3-5 themes)
   - Assign findings to themes

4. Gap Detection:
   - What topics should the query cover? (use LLM)
   - What did we actually cover?
   - gaps = expected_topics - covered_topics
   - Analyze why each gap exists

5. Confidence Calculation:
   overall_confidence = (
       verification_score * 0.4 +    # How many claims are verified?
       recency_score * 0.3 +          # How recent are sources?
       completeness_score * 0.3       # How many gaps exist?
   )

6. Narrative Generation:
   - Generate overview paragraph
   - Present key findings with sources
   - Explain confidence and reasoning
   - List knowledge gaps
   - Suggest follow-up questions

7. Return structured synthesis
```

### 3.3 Resource Specialization

#### 3.3.1 SourceRankingResource

**Purpose**: Evaluate and rank sources by quality (domain-agnostic)

**Methods:**

```python
@tool_use
@observable
def rank_by_quality(
    self,
    sources: list,
    query: str,
    criteria: dict = None,
    **kwargs
) -> DictParams:
    """
    Rank sources by quality using multi-factor scoring.

    Scoring factors:
    - Relevance: How well does content match query?
    - Authority: How credible is the source?
    - Recency: How recent is the information?

    Returns: Ranked list of sources with scores
    """

@tool_use
@observable
def assess_authority(
    self,
    url: str,
    domain: str = None,
    **kwargs
) -> DictParams:
    """
    Assess source authority and credibility.

    Factors:
    - Domain reputation (academic, news, official)
    - Author credentials (if available)
    - Citation count (for academic)
    - Site authority metrics

    Returns: Authority score (0-1) with explanation
    """

@tool_use
@observable
def check_recency(
    self,
    date: str,
    content: str = None,
    **kwargs
) -> DictParams:
    """
    Assess information freshness.

    Returns: Recency score (0-1) based on date
    """
```

**Why domain-agnostic?**
Source quality assessment applies to any multi-source research task, not just general research.

---

## Phase 4: Composition Strategy

### 4.1 Component Hierarchy

```
SmartResearchAgent (STARAgent)
│
├─ Workflows:
│  ├─ ResearchStrategyWorkflow (NEW)
│  │  └─ Uses: ConversationResource
│  │
│  ├─ ParallelGatheringWorkflow (NEW)
│  │  └─ Uses: SearchResource, FetchResource, ExtractResource, SourceRankingResource
│  │
│  ├─ SynthesisWorkflow (NEW)
│  │  └─ Uses: ConversationResource, SourceRankingResource
│  │
│  └─ GoogleLookupWorkflow (EXISTING)
│     └─ Fallback for simple queries
│
└─ Resources:
   ├─ SearchResource (existing)
   ├─ FetchResource (existing)
   ├─ ExtractResource (existing)
   ├─ ConversationResource (existing)
   └─ SourceRankingResource (NEW)
```

### 4.2 Data Flow

```
User Query: "What are the latest advances in quantum computing?"
    │
    ▼
SmartResearchAgent (STAR Loop Begins)
    │
    ├─ SEE: Analyze query
    │   └─> Type: TECHNICAL + CURRENT_EVENTS
    │
    ├─ THINK: Select strategy
    │   └─ ResearchStrategyWorkflow
    │       └─> Strategy: TECHNICAL_DEEP_DIVE (with recency emphasis)
    │
    ├─ ACT: Execute research
    │   ├─ ParallelGatheringWorkflow
    │   │   ├─ Search academic sources (parallel)
    │   │   ├─ Search news sources (parallel)
    │   │   ├─ Search tech blogs (parallel)
    │   │   └─> 23 sources found, ranked, top 15 fetched
    │   │
    │   └─ SynthesisWorkflow
    │       ├─ Extract claims from 15 sources
    │       ├─ Cross-reference (found 12 verified, 3 conflicts)
    │       ├─ Identify themes (3 major themes)
    │       ├─ Detect gaps (3 gaps identified)
    │       ├─ Calculate confidence (85% overall)
    │       └─> Generate narrative with findings
    │
    └─ REFLECT: Quality assessment
        ├─> Overall confidence: 85%
        ├─> Knowledge gaps: 3 identified
        └─> Follow-up questions: 4 generated
```

### 4.3 Agent Implementation Pattern

```python
class SmartResearchAgent(STARAgent):
    """
    Transparent research assistant showing visible STAR loop.

    See design.md for complete specification.
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        super().__init__(
            agent_type="smart-research",
            agent_id=agent_id or "smart-research-001",
            **kwargs
        )

        # Compose resources
        self.with_resources(
            SearchResource(resource_id="web-search"),
            FetchResource(resource_id="web-fetch"),
            ExtractResource(resource_id="content-extract"),
            ConversationResource(resource_id="llm-reasoning"),
            SourceRankingResource(resource_id="source-ranking"),
        )

        # Compose workflows
        self.with_workflows(
            ResearchStrategyWorkflow(workflow_id="strategy-selection"),
            ParallelGatheringWorkflow(workflow_id="parallel-gather"),
            SynthesisWorkflow(workflow_id="synthesis"),
            GoogleLookupWorkflow(workflow_id="quick-lookup"),
        )

    def __getattr__(self, name: str):
        """Magic function support: agent.research_topic() works!"""
        def magic_method(*args, **kwargs):
            natural_language = name.replace("_", " ").strip()
            if args:
                natural_language += f" {' '.join(str(arg) for arg in args)}"
            return self.converse(initial_message=natural_language)
        return magic_method
```

### 4.4 Invocation Patterns

```python
agent = SmartResearchAgent()

# Pattern 1: Magic function (most natural)
agent.research_quantum_computing_advances()
agent.compare_react_vs_vue_2024()
agent.explain_transformer_architecture()

# Pattern 2: Conversational (interactive)
agent.converse("What are the latest advances in quantum computing?")

# Pattern 3: Programmatic (API-style)
result = agent.query(caller_message="research quantum computing advances")
confidence = result["confidence"]["overall"]
if confidence > 0.8:
    process_findings(result["key_findings"])
```

---

## Phase 5: Validation & Testing Strategy

### 5.1 Component Testing

```python
# Resource Tests
def test_source_ranking():
    resource = SourceRankingResource()

    sources = [
        {"url": "https://arxiv.org/...", "date": "2024-12-01", "content": "..."},
        {"url": "https://blog.example.com/...", "date": "2023-01-01", "content": "..."},
    ]

    result = resource.rank_by_quality(sources=sources, query="quantum computing")

    assert result["success"] == True
    assert len(result["ranked_sources"]) == 2
    assert result["ranked_sources"][0]["score"] > result["ranked_sources"][1]["score"]

# Workflow Tests
def test_research_strategy_selection():
    workflow = ResearchStrategyWorkflow()

    # Test 1: Quick fact
    result = workflow.execute(query="What is quantum computing?")
    assert result["result"]["strategy"]["type"] == "QUICK_FACT"

    # Test 2: Technical deep dive
    result = workflow.execute(query="Explain transformer architecture in detail")
    assert result["result"]["strategy"]["type"] == "TECHNICAL_DEEP_DIVE"

    # Test 3: Current events
    result = workflow.execute(query="Latest quantum computing breakthroughs")
    assert result["result"]["strategy"]["type"] == "CURRENT_EVENTS"
```

### 5.2 Integration Testing

```python
def test_end_to_end_research():
    """Test full research pipeline"""
    agent = SmartResearchAgent()

    result = agent.query(caller_message="What are the latest advances in quantum computing?")

    # Validate structure
    assert "summary" in result
    assert "key_findings" in result["summary"]
    assert "confidence" in result
    assert "knowledge_gaps" in result
    assert "follow_up_questions" in result

    # Validate content quality
    assert result["confidence"]["overall"] > 0.5  # At least medium confidence
    assert len(result["summary"]["key_findings"]) >= 3  # Found multiple findings
    assert len(result["sources"]) >= 5  # Used multiple sources
```

### 5.3 Success Criteria Validation

**Functional:**
- [ ] Correctly classifies query type (test with 20 diverse queries)
- [ ] Gathers from 3+ source types for deep-dive queries
- [ ] Synthesizes with cross-referencing (verify claims have 2+ sources)
- [ ] Identifies gaps when coverage < 80%
- [ ] Generates 3-5 relevant follow-up questions

**Quality:**
- [ ] 80%+ confidence on well-researched topics
- [ ] 90%+ query classification accuracy
- [ ] Gap detection works (manually verify on test set)

**Performance:**
- [ ] Quick facts: <5 seconds
- [ ] Technical deep-dive: <25 seconds
- [ ] All strategies complete within time estimates

---

## Phase 6: Implementation Plan

### 6.1 Implementation Order

**Day 1: Resources & Basic Workflows (3-4 hours)**
1. SourceRankingResource (1 hour)
2. ResearchStrategyWorkflow (1 hour)
3. ParallelGatheringWorkflow (1.5 hours)
4. Unit tests for above (0.5 hours)

**Day 2: Synthesis & Agent (3-4 hours)**
1. SynthesisWorkflow (2 hours)
2. SmartResearchAgent composition (0.5 hours)
3. Prompt file creation (0.5 hours)
4. Integration tests (1 hour)

**Day 3: Examples & Documentation (2-3 hours)**
1. Example runner scripts (1 hour)
2. README.md (0.5 hours)
3. Manual testing and refinement (1.5 hours)

**Total Estimate**: 8-11 hours (can be compressed to 4-6 hours for MVP)

### 6.2 MVP Scope

**Included in MVP:**
- ResearchStrategyWorkflow (all 4 strategies)
- ParallelGatheringWorkflow (academic + news sources)
- SynthesisWorkflow (basic cross-referencing + confidence)
- SourceRankingResource (relevance + recency only)
- SmartResearchAgent with magic function support

**Deferred to v2:**
- Advanced source types (GitHub, Stack Overflow, documentation sites)
- Authority scoring (complex domain reputation logic)
- Conflict resolution for contradictory claims
- Interactive refinement in conversational mode
- Export formats (markdown, PDF, citation formats)

### 6.3 File Structure

```
examples/agents/smart-research/
├── README.md (User guide + quick start)
├── specs/
│   ├── design.md (this file)
│   └── implementation_tracker.md (progress tracking)
├── resources/
│   ├── __init__.py
│   └── source_ranking.py (SourceRankingResource)
├── workflows/
│   ├── __init__.py
│   ├── research_strategy.py (ResearchStrategyWorkflow)
│   ├── parallel_gathering.py (ParallelGatheringWorkflow)
│   └── synthesis.py (SynthesisWorkflow)
├── agents/
│   ├── __init__.py
│   └── smart_research_agent.py (SmartResearchAgent)
├── prompts/
│   └── SmartResearchAgent.xml (Agent identity)
├── tests/
│   ├── test_resources.py
│   ├── test_workflows.py
│   └── test_agent_integration.py
└── examples/
    ├── run_simple_query.py (Quick demo)
    ├── run_technical_research.py (Deep dive demo)
    └── run_comparative_analysis.py (Comparison demo)
```

---

## Appendix A: Output Format Specification

### Structured Response Format

```python
{
    "query": str,                           # Original query
    "strategy_used": str,                   # Strategy name
    "processing_time": float,               # Seconds

    "summary": {
        "overview": str,                    # 2-3 paragraph summary

        "key_findings": [                   # Top findings
            {
                "finding": str,             # The finding
                "date": str,                # Publication date
                "significance": str,        # high/medium/low
                "sources": [str],           # Source URLs
                "confidence": float,        # 0-1
                "details": str              # Detailed explanation
            }
        ],

        "themes": [                         # Identified themes
            {
                "theme": str,
                "findings_count": int,
                "trend": str,               # accelerating/steady/emerging
                "description": str
            }
        ],

        "timeline": [...]                   # Chronological events
    },

    "knowledge_gaps": [
        {
            "gap": str,                     # What's missing
            "severity": str,                # high/medium/low
            "reason": str,                  # Why gap exists
            "suggested_followup": str       # Question to ask
        }
    ],

    "confidence": {
        "overall": float,                   # 0-1
        "dimensions": {
            "verification": float,          # Cross-reference score
            "recency": float,               # Source freshness
            "completeness": float           # Coverage score
        },
        "explanation": [str]                # Human-readable reasons
    },

    "follow_up_questions": [str],          # Suggested follow-ups

    "sources": [                            # All sources used
        {
            "url": str,
            "type": str,                    # academic/news/blog
            "authority": float,             # 0-1
            "date": str,
            "used_for": [str]               # Which findings
        }
    ],

    "metadata": {
        "sources_searched": int,
        "sources_used": int,
        "source_breakdown": {...},
        "search_queries_executed": int,
        "llm_calls": int
    }
}
```

---

## Appendix B: Design Patterns Used

This agent demonstrates the following patterns from `docs/ai-building-agents/`:

1. **Single Specialist Agent** (agent_design_patterns.md)
   - Focused domain (research)
   - 3-4 workflows
   - Minimal agent code (~60 lines)

2. **Phased Orchestration** (workflow_design_patterns.md)
   - Parallel gathering → Sequential synthesis
   - Optimal performance
   - Clear phase boundaries

3. **Magic Function Interface** (agent_interface_patterns.md)
   - `agent.research_topic()` natural syntax
   - Calls `converse()` internally

4. **Resource Reuse** (composition pattern)
   - 80% existing resources
   - 20% new functionality

5. **LLM-Powered Resource** (resource_design_patterns.md)
   - ConversationResource for analysis
   - Structured LLM output

6. **Parallel Execution** (workflow_design_patterns.md)
   - `asyncio.gather()` for source gathering
   - Significant performance gain

7. **Graceful Degradation** (resource_design_patterns.md)
   - Fallback to GoogleLookupWorkflow
   - Never fail completely

---

**Design Status**: ✅ Complete

**Next Steps**: See `implementation_tracker.md` for detailed implementation progress.
