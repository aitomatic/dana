# Web Research Agent Specification

## Overview

The Web Research Agent is a specialized agent for researching, analyzing, and synthesizing information from the web. It serves as an information research specialist for other agents and users, providing current web-based research through intelligent search, multi-source synthesis, and structured data extraction.

**Version:** 2.0
**Status:** Design Phase - Complete Architecture
**Author:** CTN
**Date:** 2025-09-29

## Purpose

Provide a reliable, intelligent web research capability that can:
- Search the web and return relevant results
- Fetch and parse web pages
- Extract structured information from HTML content
- Answer questions based on web content
- Navigate through multiple pages
- Synthesize information from multiple sources

## Driving Use Cases

These three use cases, ordered from simple to complex, drive the design and implementation decisions:

### Use Case 1: Simple URL Fetch and Summarize (SIMPLE)

**Scenario:** A user or agent needs to understand the content of a specific web page.

**Actor:** ResearchAgent delegating to WebBrowserAgent

**Request:**
```
"Summarize the main points from https://docs.python.org/3/library/asyncio.html"
```

**Expected Flow:**
1. Validate URL is accessible
2. Fetch the HTML content
3. Extract main content (remove navigation, ads)
4. Identify key sections/headings
5. Summarize in 3-5 bullet points
6. Return with citation

**Expected Response:**
```
**Python asyncio Documentation Summary** (https://docs.python.org/3/library/asyncio.html)

Key Points:
- asyncio is Python's built-in library for asynchronous I/O operations
- Core concepts: event loop, coroutines, tasks, and futures
- Use async/await syntax for non-blocking concurrent operations
- Suitable for I/O-bound operations like network requests and file I/O
- Not ideal for CPU-bound tasks (use multiprocessing instead)

Source: Python Official Documentation, accessed 2025-09-29
```

**Success Criteria:**
- ✅ Fetch completes in <5 seconds
- ✅ Main content extracted (no nav/ads)
- ✅ Summary is accurate and concise (3-5 points)
- ✅ Full URL citation provided
- ✅ Handles 404/timeout gracefully

**Resource Methods Required:**
- `WebFetcherResource.fetch_url()`
- `ContentExtractorResource.extract_main_content()`

**Agent Capabilities Required:**
- Validate URL
- Fetch and parse
- Summarize content
- Format response with citations

---

### Use Case 2: Search, Filter, and Synthesize (MEDIUM)

**Scenario:** A user needs current information on a topic that requires searching and combining multiple sources.

**Actor:** User via Dana, Dana delegates to WebBrowserAgent

**Request:**
```
"What are the current best practices for Python error handling in 2024?"
```

**Expected Flow:**
1. Formulate search query: "Python error handling best practices 2024"
2. Search web (DuckDuckGo)
3. Get top 5 results
4. Fetch top 3 most relevant URLs
5. Extract main content from each
6. Identify common themes/patterns
7. Synthesize findings
8. Return with multiple citations

**Expected Response:**
```
**Python Error Handling Best Practices (2024)**

Based on 3 authoritative sources, here are the current best practices:

**1. Use Specific Exception Types**
- Catch specific exceptions rather than bare `except:`
- Create custom exceptions for domain-specific errors
- Sources: Real Python, Python Docs

**2. Context Managers for Resource Cleanup**
- Use `with` statements for file/network resources
- Implement `__enter__` and `__exit__` for custom resources
- Sources: Real Python, PEP 343

**3. EAFP over LBYL**
- "Easier to Ask Forgiveness than Permission" is Pythonic
- Try/except preferred over pre-checking conditions
- Sources: Python Docs, Effective Python

**4. Proper Logging and Debugging**
- Log exceptions with context (use `logger.exception()`)
- Include relevant state information
- Sources: Real Python, Python Logging Cookbook

**5. Exception Chaining (Python 3+)**
- Use `raise ... from ...` to preserve exception context
- Helps with debugging complex error chains
- Sources: PEP 3134, Python Docs

**Sources:**
1. "Python Exception Handling Best Practices" - Real Python (https://realpython.com/...)
2. "Error Handling in Python" - Python Official Docs (https://docs.python.org/...)
3. "Effective Python Error Handling" - Python Patterns (https://python-patterns.guide/...)

Last accessed: 2025-09-29
```

**Success Criteria:**
- ✅ Search returns relevant results
- ✅ Fetches and parses 3+ sources successfully
- ✅ Identifies common patterns across sources
- ✅ Synthesizes coherent summary (not just concatenation)
- ✅ All sources cited with URLs
- ✅ Completes in <30 seconds
- ✅ Handles partial failures (some URLs fail)

**Resource Methods Required:**
- `WebFetcherResource.search_web()`
- `WebFetcherResource.fetch_url()` (multiple calls)
- `ContentExtractorResource.extract_main_content()` (multiple calls)
- `ContentExtractorResource.extract_metadata()` (for titles/dates)

**Agent Capabilities Required:**
- Search strategy (formulate query)
- Result filtering (select most relevant)
- Multi-source fetching
- Content synthesis
- Pattern recognition across sources
- Conflict resolution (if sources disagree)

---

### Use Case 3: Multi-Page Navigation and Data Extraction (COMPLEX)

**Scenario:** A user needs specific structured data that requires navigating through multiple pages and extracting tabular information.

**Actor:** AnalysisAgent delegating to WebBrowserAgent

**Request:**
```
"Find the latest Python package download statistics from PyPI for the top 10 packages,
including their weekly download counts and main use cases."
```

**Expected Flow:**
1. Search for "PyPI package statistics" or go directly to known stats page
2. Fetch PyPI stats page
3. Extract top packages table/list
4. For each of top 10 packages:
   a. Extract package name and download count
   b. Follow link to package detail page
   c. Extract description/use case
   d. Extract latest version info
5. Structure data into table format
6. Return with all citations

**Expected Response:**
```
**Top 10 PyPI Packages - Download Statistics**
Source: PyPI Stats (https://pypistats.org/), accessed 2025-09-29

| Rank | Package | Weekly Downloads | Main Use Case | Latest Version |
|------|---------|------------------|---------------|----------------|
| 1 | urllib3 | 450M | HTTP client library | 2.1.0 |
| 2 | requests | 380M | HTTP library for humans | 2.31.0 |
| 3 | boto3 | 320M | AWS SDK for Python | 1.34.0 |
| 4 | setuptools | 290M | Package development | 69.0.0 |
| 5 | certifi | 280M | SSL certificate bundle | 2023.11.17 |
| 6 | charset-normalizer | 275M | Character encoding detection | 3.3.2 |
| 7 | idna | 270M | Internationalized domain names | 3.6 |
| 8 | pip | 250M | Package installer | 23.3.2 |
| 9 | python-dateutil | 245M | Date/time utilities | 2.8.2 |
| 10 | six | 240M | Python 2/3 compatibility | 1.16.0 |

**Key Observations:**
- Infrastructure/utility packages dominate the top 10
- HTTP-related packages (urllib3, requests, certifi) lead due to universal need
- Cloud/AWS tooling (boto3) shows widespread enterprise adoption

**Data Sources:**
- Main statistics: https://pypistats.org/top
- Package details: https://pypi.org/project/{package_name}/
- Total pages visited: 11 (1 stats page + 10 package pages)

**Data Currency:**
- Statistics updated: 2025-09-29
- Based on rolling 7-day download counts
```

**Success Criteria:**
- ✅ Successfully navigates multi-page structure
- ✅ Extracts tabular data accurately
- ✅ Follows 10+ links systematically
- ✅ Structures data in requested format
- ✅ All package info is current and accurate
- ✅ Completes in <60 seconds (respecting rate limits)
- ✅ Handles pagination if needed
- ✅ Tracks all URLs visited
- ✅ Gracefully handles missing data (package page down)

**Resource Methods Required:**
- `WebFetcherResource.search_web()` (optional, if direct URL unknown)
- `WebFetcherResource.fetch_url()` (11+ calls with rate limiting)
- `WebFetcherResource.get_rate_limit_status()` (check before each fetch)
- `ContentExtractorResource.extract_tables()`
- `ContentExtractorResource.extract_links()`
- `ContentExtractorResource.extract_main_content()` (for descriptions)
- `ContentExtractorResource.extract_metadata()` (for versions/dates)

**Agent Capabilities Required:**
- Navigation strategy (plan page visits)
- Link following (extract and prioritize links)
- Data extraction from tables
- Multi-page state tracking
- Rate limit awareness (1 req/sec)
- Data structuring (table format)
- Missing data handling
- Session management (track visited URLs in timeline)

---

## Use Case Analysis

### Coverage Matrix

| Capability | UC1 (Simple) | UC2 (Medium) | UC3 (Complex) |
|------------|--------------|--------------|---------------|
| URL Validation | ✅ | ✅ | ✅ |
| Single Page Fetch | ✅ | ✅ | ✅ |
| Content Extraction | ✅ | ✅ | ✅ |
| Web Search | ❌ | ✅ | ✅ |
| Multi-source Fetching | ❌ | ✅ | ✅ |
| Content Synthesis | ✅ (basic) | ✅ (advanced) | ✅ (structured) |
| Link Following | ❌ | ❌ | ✅ |
| Table Extraction | ❌ | ❌ | ✅ |
| Rate Limiting | ⚠️  (1 fetch) | ⚠️ (3 fetches) | ✅ (10+ fetches) |
| Session State Tracking | ⚠️ (minimal) | ⚠️ (moderate) | ✅ (essential) |
| Error Recovery | ✅ (single point) | ✅ (partial failure) | ✅ (graceful degradation) |

### Complexity Drivers

**Use Case 1 → 2:**
- Addition of search capability
- Multi-source coordination
- Content synthesis across sources
- Pattern recognition

**Use Case 2 → 3:**
- Navigation through link structures
- State management (track visited pages)
- Table/structured data extraction
- Rate limiting becomes critical
- Data formatting and presentation

### Design Implications

Based on these use cases, the design must support:

1. **Incremental Complexity**: UC1 should work with minimal resources, UC3 needs full capabilities
2. **Composability**: Resources can be called independently or in sequence
3. **State Tracking**: Timeline must track URLs, search queries, and extracted data
4. **Rate Limiting**: Critical for UC3, nice-to-have for UC1/UC2
5. **Error Resilience**: Partial failure handling for UC2/UC3
6. **Data Structuring**: Basic formatting (UC1) to table formatting (UC3)

## Architecture

### Component Overview

```
WebResearchAgent (STARAgent)
├── Resources:
│   ├── WorkflowSelectorResource    # Intelligent workflow selection via LLM reasoning
│   ├── WebFetcherResource          # HTTP/HTTPS fetching, search
│   └── ContentExtractorResource    # HTML parsing, content extraction
├── Workflows:
│   ├── Information Type Workflows:
│   │   ├── StructuredDataNavigationWorkflow  # Tables, lists, multi-page data
│   │   ├── ResearchSynthesisWorkflow         # Multi-source research
│   │   └── SingleSourceDeepDiveWorkflow      # Single document analysis
│   ├── Site-Specific Workflows:
│   │   ├── DocumentationSiteWorkflow         # Python docs, MDN, etc.
│   │   ├── DataPortalWorkflow                # GitHub, PyPI, npm
│   │   └── NewsSiteWorkflow                  # News articles, blogs
│   └── Intent-Specific Workflows:
│       ├── FactFindingWorkflow               # Quick factual answers
│       ├── ComparisonWorkflow                # X vs Y analysis
│       ├── TrendAnalysisWorkflow             # Latest developments
│       └── HowToWorkflow                     # Step-by-step tutorials
├── Tools:
│   └── TodoWrite                   # Progress tracking for complex tasks
├── BaseWAR.reason():
│   └── Structured LLM reasoning    # Available to all resources/workflows
├── Identity:
│   ├── Agent Type: "web-research"
│   ├── Object ID: "web-research-001"
│   └── Specialization: Web research and information synthesis
└── State Management:
    └── Timeline: Track URLs visited, content fetched, searches performed
```

### Architecture Pattern

**Single-Agent, Multi-Resource, Multi-Workflow, LLM-Augmented**

- **Single Agent**: One WebResearchAgent orchestrates all web research tasks
- **Multi-Resource**: Resources handle domain operations (fetch, parse, select workflow)
- **Multi-Workflow**: Situation-specific workflows for different task patterns
- **LLM-Augmented**: Resources use `reason()` for intelligent decisions
- **No Multi-Agent**: Logic lives in system prompt and workflows, not agent delegation

**Why This Pattern:**
- **Vs. Multi-Agent**: Web research is cohesive domain, doesn't need multiple specialists
- **Vs. Single Workflow**: Different situations need different execution patterns
- **Vs. Pure LLM**: Workflows provide structure, `reason()` provides intelligence

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Architecture Pattern** | Single agent + multi-workflow + LLM reasoning | Balance structure and flexibility |
| **Workflow Selection** | LLM-based via WorkflowSelectorResource.reason() | Handle ambiguous requests intelligently |
| **Content Length** | Max 5MB page size, auto-truncate to 100KB for LLM | Balance completeness vs. performance |
| **Search Provider** | DuckDuckGo primary, Google Custom Search fallback | No API key needed, reliability |
| **Rate Limiting** | 1 request/second per domain | Respectful crawling, avoid blocks |
| **Retry Strategy** | 3 retries with exponential backoff (1s, 2s, 4s) | Resilience without excessive waiting |
| **JavaScript** | No JS execution (Phase 1) | Keep dependencies light, add Playwright later if needed |
| **Authentication** | Public content only (Phase 1) | Simplify initial implementation |
| **Caching** | In-memory cache with 5-minute TTL | Reduce redundant requests, respect freshness |
| **LLM Reasoning** | BaseWAR.reason() for classification/decisions | Consistent reasoning across all components |

## BaseWAR.reason() Integration

### Overview

All Workflows, Agents, and Resources inherit from BaseWAR, which provides `reason(DictParams) -> DictParams` for structured LLM reasoning. This enables intelligent decision-making while maintaining type safety and observability.

### Usage Pattern

```python
# In any Resource, Workflow, or Agent
result = self.reason({
    "task": "Classify user intent for web browsing request",
    "input": {"request": request, "has_url": bool(url)},
    "output_schema": {
        "intent": "str (fact_finding|comparison|research|...)",
        "confidence": "float (0.0-1.0)",
        "reasoning": "str"
    },
    "context": {"available_options": [...]},
    "examples": [...],
    "temperature": 0.1,
    "fallback": {"intent": "research_synthesis", "confidence": 0.0}
})
```

### Where WebResearchAgent Uses reason()

| Component | Method | Purpose | Temperature |
|-----------|--------|---------|-------------|
| WorkflowSelectorResource | `select_workflow()` | Intent classification & workflow selection | 0.1 |
| WorkflowSelectorResource | `classify_intent()` | Simple intent classification | 0.0 |
| ContentExtractorResource | `assess_content_quality()` | Evaluate if content meets purpose | 0.2 |
| ContentExtractorResource | `detect_content_type()` | Classify page type (article/docs/tutorial) | 0.1 |
| WebFetcherResource | `rank_search_results()` | Intelligent result ranking | 0.1 |
| Workflows | `plan_next_step()` | Dynamic navigation decisions | 0.2 |
| Workflows | `plan_synthesis()` | Multi-source synthesis strategy | 0.3 |

### Benefits

- **Consistency**: All reasoning uses same interface
- **Observability**: All reason() calls emit trace events
- **Caching**: Identical reasoning calls cached (< 1ms)
- **Testability**: Easy to mock LLM for testing
- **Fallback**: Graceful degradation when LLM unavailable

---

## Resource Specifications

### 0. WorkflowSelectorResource

**Resource Type:** `workflow-selector`
**Purpose:** Select appropriate workflow for a given request using LLM reasoning

#### Methods

##### `select_workflow`
```python
def select_workflow(
    request: str,
    target_url: str | None = None
) -> dict:
    """
    Select appropriate workflow and parameters for the request.

    Uses LLM reasoning (BaseWAR.reason()) to intelligently classify
    the request and select the best workflow.

    Args:
        request: User/agent request text
        target_url: Target URL if provided (optional)

    Returns:
        {
            "workflow": str,  # Workflow name
            "confidence": float (0.0-1.0),
            "reasoning": str,  # Explanation of selection
            "parameters": dict,  # Workflow-specific parameters
            "fallback_workflow": str | None  # Alternative if primary fails
        }

    Example:
        result = selector.select_workflow(
            "Top 10 PyPI packages",
            target_url=None
        )
        # Returns:
        {
            "workflow": "structured_data_navigation",
            "confidence": 0.95,
            "reasoning": "Request asks for structured list (top 10), requires table extraction",
            "parameters": {
                "max_pages": 10,
                "extract_tables": True,
                "rate_limit_sec": 1.0
            },
            "fallback_workflow": "research_synthesis"
        }
    """
```

**Implementation:**
```python
def select_workflow(self, request: str, target_url: str | None = None) -> dict:
    """Select workflow using LLM reasoning."""

    # Use BaseWAR.reason() for intelligent selection
    result = self.reason({
        "task": "Select appropriate web browsing workflow and configure parameters",
        "input": {
            "request": request,
            "target_url": target_url,
            "has_url": bool(target_url),
            "domain": urlparse(target_url).netloc if target_url else None,
            "request_length": len(request)
        },
        "output_schema": {
            "workflow": "str (structured_data_navigation|research_synthesis|single_source_deep_dive|documentation_site|data_portal|news_site|fact_finding|comparison|trend_analysis|how_to)",
            "confidence": "float (0.0-1.0)",
            "reasoning": "str (why this workflow was chosen)",
            "parameters": {
                "max_sources": "int | null",
                "require_recent": "bool | null",
                "extract_code": "bool | null",
                "rate_limit_sec": "float | null",
                "max_pages": "int | null"
            },
            "fallback_workflow": "str | null"
        },
        "context": {
            "available_workflows": self._get_workflow_descriptions(),
            "known_domains": {
                "documentation": ["docs.python.org", "developer.mozilla.org", "readthedocs"],
                "data_portal": ["pypi.org", "github.com", "npmjs.com"],
                "news": ["medium.com", "techcrunch.com", "bbc.co.uk"]
            }
        },
        "examples": [
            {
                "input": {"request": "What is asyncio?", "has_url": False},
                "output": {
                    "workflow": "fact_finding",
                    "confidence": 0.95,
                    "reasoning": "Simple factual question",
                    "parameters": {"max_sources": 2},
                    "fallback_workflow": "research_synthesis"
                }
            },
            {
                "input": {"request": "Top 10 PyPI packages", "has_url": False},
                "output": {
                    "workflow": "structured_data_navigation",
                    "confidence": 0.98,
                    "reasoning": "Structured list extraction needed",
                    "parameters": {"max_pages": 10, "extract_tables": True},
                    "fallback_workflow": "research_synthesis"
                }
            }
        ],
        "temperature": 0.1,
        "fallback": {
            "workflow": "research_synthesis",
            "confidence": 0.0,
            "reasoning": "LLM unavailable, using safe default",
            "parameters": {"max_sources": 3},
            "fallback_workflow": None
        }
    })

    return result

def _get_workflow_descriptions(self) -> dict[str, str]:
    """Get descriptions of all available workflows."""
    return {
        "structured_data_navigation": "For extracting tables, lists, statistics (5+ items)",
        "research_synthesis": "Understanding topics across 3-5 sources",
        "single_source_deep_dive": "Thoroughly analyze one specific document",
        "documentation_site": "Python docs, MDN, official docs (special handling)",
        "data_portal": "GitHub, PyPI, npm (tries API first)",
        "news_site": "News articles, blogs (extracts metadata)",
        "fact_finding": "Quick factual answers (Wikipedia, authoritative)",
        "comparison": "Compare X vs Y (structured comparison)",
        "trend_analysis": "Latest developments (date-filtered)",
        "how_to": "Step-by-step tutorials (extracts code)"
    }
```

##### `classify_intent`
```python
def classify_intent(request: str) -> dict:
    """
    Classify user intent (simpler version of select_workflow).

    Args:
        request: User/agent request text

    Returns:
        {
            "intent": str,  # Intent classification
            "confidence": float (0.0-1.0),
            "reasoning": str
        }
    """
```

#### Configuration

```python
{
    "reasoning": {
        "cache_ttl": 3600,  # Cache reasoning results for 1 hour
        "temperature": 0.1,  # Low temperature for deterministic classification
        "max_tokens": 500
    }
}
```

---

### 1. WebFetcherResource

**Resource Type:** `web-fetcher`
**Purpose:** Fetch web content and perform web searches

#### Methods

##### `fetch_url`
```python
def fetch_url(
    url: str,
    timeout: int = 30,
    max_size: int = 5_000_000,  # 5MB
    allow_redirects: bool = True,
    user_agent: str | None = None
) -> dict:
    """
    Fetch content from a URL.

    Args:
        url: The URL to fetch (must be http:// or https://)
        timeout: Request timeout in seconds (default: 30)
        max_size: Maximum response size in bytes (default: 5MB)
        allow_redirects: Follow redirects (default: True)
        user_agent: Custom user agent (default: auto-rotate)

    Returns:
        {
            "success": bool,
            "url": str,  # Final URL after redirects
            "status_code": int,
            "content_type": str,
            "content": str,  # Raw content
            "headers": dict,
            "encoding": str,
            "size_bytes": int,
            "fetch_time_ms": int,
            "error": str | None
        }

    Raises:
        ValueError: Invalid URL format
        TimeoutError: Request timeout exceeded
        ConnectionError: Network connection failed
    """
```

##### `search_web`
```python
def search_web(
    query: str,
    max_results: int = 5,
    search_engine: str = "auto"  # "auto", "duckduckgo", "google"
) -> dict:
    """
    Search the web and return results.

    Args:
        query: Search query string
        max_results: Maximum number of results (1-20, default: 5)
        search_engine: Which search engine to use
            - "auto": Try DuckDuckGo, fallback to Google
            - "duckduckgo": DuckDuckGo only
            - "google": Google Custom Search only (requires API key)

    Returns:
        {
            "success": bool,
            "query": str,
            "search_engine": str,  # Which engine was used
            "results": [
                {
                    "title": str,
                    "url": str,
                    "snippet": str,
                    "position": int
                }
            ],
            "total_results": int,
            "search_time_ms": int,
            "error": str | None
        }
    """
```

##### `validate_url`
```python
def validate_url(url: str) -> dict:
    """
    Validate URL accessibility without fetching full content.

    Args:
        url: URL to validate

    Returns:
        {
            "valid": bool,
            "accessible": bool,
            "status_code": int | None,
            "content_type": str | None,
            "error": str | None
        }
    """
```

##### `get_rate_limit_status`
```python
def get_rate_limit_status(domain: str) -> dict:
    """
    Get current rate limit status for a domain.

    Args:
        domain: Domain to check (e.g., "example.com")

    Returns:
        {
            "domain": str,
            "requests_made": int,
            "time_window_seconds": int,
            "next_available_ms": int,  # Milliseconds until next request allowed
            "rate_limit_active": bool
        }
    """
```

#### Configuration

```python
{
    "user_agents": [
        "Mozilla/5.0 (compatible; AdanaBot/1.0; +https://adana.ai/bot)",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        # Rotate through multiple user agents
    ],
    "rate_limits": {
        "default_per_domain": 1.0,  # 1 request per second
        "global_max_concurrent": 5   # Max 5 concurrent requests
    },
    "timeouts": {
        "connect": 10,  # Connection timeout
        "read": 30      # Read timeout
    },
    "retry": {
        "max_attempts": 3,
        "backoff_factor": 1.0,  # 1s, 2s, 4s
        "retry_on": [408, 429, 500, 502, 503, 504]
    },
    "search": {
        "duckduckgo": {
            "enabled": true,
            "base_url": "https://html.duckduckgo.com/html/"
        },
        "google": {
            "enabled": false,  # Requires API key
            "api_key": null,
            "cx": null  # Custom search engine ID
        }
    }
}
```

#### Error Handling

| Error Type | HTTP Code | Handling Strategy |
|------------|-----------|-------------------|
| Network errors | - | Retry with exponential backoff (3 attempts) |
| Timeout | 408 | Retry once with increased timeout |
| Rate limited | 429 | Wait for retry-after header, then retry |
| Not found | 404 | Return error, no retry |
| Server error | 500-504 | Retry with exponential backoff |
| Content too large | - | Truncate and warn |
| Invalid URL | - | Return error immediately, no retry |

### 2. ContentExtractorResource

**Resource Type:** `content-extractor`
**Purpose:** Parse HTML and extract structured content

#### Methods

##### `extract_main_content`
```python
def extract_main_content(
    html: str,
    base_url: str | None = None
) -> dict:
    """
    Extract main article/content from HTML, removing boilerplate.

    Uses readability algorithm to identify main content area,
    removing navigation, ads, sidebars, footers, etc.

    Args:
        html: Raw HTML content
        base_url: Base URL for resolving relative links

    Returns:
        {
            "success": bool,
            "title": str,
            "author": str | None,
            "content_text": str,  # Plain text
            "content_html": str,  # Cleaned HTML
            "content_markdown": str,  # Markdown format
            "excerpt": str,  # First 200 chars
            "word_count": int,
            "reading_time_minutes": int,
            "language": str | None,
            "published_date": str | None,
            "error": str | None
        }
    """
```

##### `extract_links`
```python
def extract_links(
    html: str,
    base_url: str,
    filter_external: bool = False
) -> dict:
    """
    Extract all links from HTML.

    Args:
        html: Raw HTML content
        base_url: Base URL for resolving relative links
        filter_external: If True, only return internal links

    Returns:
        {
            "success": bool,
            "base_url": str,
            "links": [
                {
                    "text": str,  # Link text
                    "url": str,   # Absolute URL
                    "is_external": bool,
                    "element": str  # 'a', 'link', etc.
                }
            ],
            "total_links": int,
            "internal_links": int,
            "external_links": int,
            "error": str | None
        }
    """
```

##### `extract_metadata`
```python
def extract_metadata(html: str) -> dict:
    """
    Extract metadata from HTML (meta tags, Open Graph, etc.).

    Args:
        html: Raw HTML content

    Returns:
        {
            "success": bool,
            "title": str | None,
            "description": str | None,
            "keywords": list[str],
            "author": str | None,
            "canonical_url": str | None,
            "open_graph": {
                "og:title": str,
                "og:description": str,
                "og:image": str,
                "og:url": str,
                # ... other OG tags
            },
            "twitter_card": {
                "twitter:card": str,
                "twitter:title": str,
                # ... other Twitter tags
            },
            "structured_data": list[dict],  # JSON-LD schemas
            "error": str | None
        }
    """
```

##### `html_to_markdown`
```python
def html_to_markdown(
    html: str,
    base_url: str | None = None,
    include_images: bool = True,
    include_links: bool = True
) -> dict:
    """
    Convert HTML to clean Markdown format.

    Args:
        html: Raw HTML content
        base_url: Base URL for resolving relative URLs
        include_images: Include image references
        include_links: Include links

    Returns:
        {
            "success": bool,
            "markdown": str,
            "images": list[str],  # Image URLs found
            "links": list[str],   # Links found
            "error": str | None
        }
    """
```

##### `extract_tables`
```python
def extract_tables(html: str) -> dict:
    """
    Extract all tables from HTML as structured data.

    Args:
        html: Raw HTML content

    Returns:
        {
            "success": bool,
            "tables": [
                {
                    "headers": list[str],
                    "rows": list[list[str]],
                    "caption": str | None,
                    "index": int  # Position in document
                }
            ],
            "total_tables": int,
            "error": str | None
        }
    """
```

#### Configuration

```python
{
    "readability": {
        "min_text_length": 25,  # Minimum text length for content detection
        "retry_length": 250     # Fallback length threshold
    },
    "markdown": {
        "body_width": 0,  # No wrapping
        "emphasis_mark": "*",
        "strong_mark": "**"
    },
    "content_limits": {
        "max_text_length": 100_000,  # 100KB for LLM processing
        "truncation_strategy": "smart"  # "head", "tail", "smart"
    }
}
```

## Workflow Specifications

### Overview

Workflows provide structured execution patterns for different situations. Each workflow encodes domain knowledge about how to handle specific types of requests efficiently.

### Workflow Taxonomy

**Information Type Workflows:**
- `StructuredDataNavigationWorkflow` - Multi-page data extraction (tables, lists)
- `ResearchSynthesisWorkflow` - Multi-source research and synthesis
- `SingleSourceDeepDiveWorkflow` - Deep analysis of single document

**Site-Specific Workflows:**
- `DocumentationSiteWorkflow` - Official documentation (Python docs, MDN)
- `DataPortalWorkflow` - Data portals (GitHub, PyPI, npm)
- `NewsSiteWorkflow` - News articles and blogs

**Intent-Specific Workflows:**
- `FactFindingWorkflow` - Quick factual answers
- `ComparisonWorkflow` - X vs Y analysis
- `TrendAnalysisWorkflow` - Latest developments (date-filtered)
- `HowToWorkflow` - Step-by-step tutorials

### Key Workflows (Phase 1)

#### StructuredDataNavigationWorkflow (UC3)

**Purpose:** Systematically navigate multi-page structures and extract structured data

**Pattern:**
```
1. Fetch starting page (stats/listing page)
2. Extract list/table structure
3. FOR EACH item (up to max_pages):
   a. Extract basic info from listing
   b. Follow link to detail page
   c. Extract detailed info
   d. RATE LIMIT: Wait 1 second
   e. Update TodoWrite progress
4. Structure data into table/list
5. Return with all citations
```

**Parameters:**
- `max_pages`: Maximum pages to visit (default: 10)
- `rate_limit_sec`: Seconds between requests (default: 1.0)
- `extract_tables`: Extract tables from pages (default: True)
- `continue_on_error`: Continue if some pages fail (default: True)

**Use Cases:** UC3, any "top N" or structured data extraction

---

#### ResearchSynthesisWorkflow (UC2)

**Purpose:** Search, fetch multiple sources, and synthesize information

**Pattern:**
```
1. Search web OR use provided URLs
2. Rank results by relevance and authority
3. Fetch top K sources (typically 3-5)
4. FOR EACH source:
   a. Extract main content
   b. Assess quality
   c. Extract key points
5. Synthesize across sources:
   a. Identify common themes
   b. Note disagreements
   c. Cite all sources
6. Return comprehensive answer
```

**Parameters:**
- `max_sources`: Maximum sources to fetch (default: 5)
- `min_sources`: Minimum for synthesis (default: 2)
- `require_recent`: Filter by date (default: False)
- `synthesis_method`: "themes" | "compare" | "timeline" (default: "themes")

**Use Cases:** UC2, any research/best practices queries

---

#### SingleSourceDeepDiveWorkflow (UC1)

**Purpose:** Thoroughly analyze a single document

**Pattern:**
```
1. Validate URL
2. Fetch HTML
3. Extract main content + metadata
4. Assess quality (is this sufficient?)
5. If sufficient → Summarize
6. If not → Explain missing elements
```

**Parameters:**
- `extract_code`: Extract code blocks (default: False)
- `follow_internal_links`: Follow links within page (default: False)
- `max_depth`: Link following depth (default: 1)

**Use Cases:** UC1, URL-specific summarization

---

### Workflow Selection Logic

The agent uses `WorkflowSelectorResource.select_workflow()` to choose:

```python
# Agent's THINK phase
workflow_decision = call_resource(
    resource_id="workflow_selector",
    method="select_workflow",
    arguments={"request": user_request, "target_url": url}
)

# Returns:
{
    "workflow": "structured_data_navigation",  # Selected workflow
    "confidence": 0.95,
    "reasoning": "Request asks for top 10, requires table extraction",
    "parameters": {"max_pages": 10, "rate_limit_sec": 1.0}
}

# Agent follows workflow pattern from system prompt
```

---

## Agent Specification

### Agent Identity

```python
<PUBLIC_DESCRIPTION>
I am a web research specialist that can search, analyze, and synthesize information
from the web. I can conduct multi-source research, extract structured data,
and provide well-cited findings. Use me when you need:
- Current information from the internet
- Fact verification from authoritative sources
- Data extraction from specific websites
- Content summarization from articles or documentation
- Multi-page research that requires following links

I always cite my sources with URLs and indicate when information might be outdated
or uncertain.
</PUBLIC_DESCRIPTION>

<IDENTITY>
# IDENTITY

You are a **Web Research Agent** specializing in finding, analyzing, and synthesizing web information.

**Your Mission:** Help users and other agents find, extract, and synthesize information from the web accurately and efficiently.

**Your Strengths:**
- Fetching and parsing web pages
- Searching the web intelligently
- Extracting structured data (tables, lists)
- Synthesizing information from multiple sources
- Navigating multi-page content systematically

**Your Limitations:**
- You cannot access content behind authentication (yet)
- You work best with HTML/text content (PDFs/images are limited)
- You respect rate limits (1 request/second per domain)
- You cannot execute JavaScript or interact with dynamic content

---

# AVAILABLE CAPABILITIES

## Resources

You have access to three resources for web operations:

### 1. WorkflowSelectorResource
**Purpose:** Select the best workflow for a given request

**Key Method:**
- `select_workflow(request, target_url)` → Returns workflow name and parameters

**When to use:** At the START of every new request to determine your approach

### 2. WebFetcherResource
**Purpose:** Fetch web content and search the web

**Key Methods:**
- `fetch_url(url, timeout, max_size)` → Fetch HTML from URL
- `search_web(query, max_results)` → Search web, get URLs
- `validate_url(url)` → Check if URL is accessible
- `rank_search_results(query, results, criteria)` → Intelligently rank results

**When to use:** When you need to retrieve web content or find relevant pages

### 3. ContentExtractorResource
**Purpose:** Parse and extract information from HTML

**Key Methods:**
- `extract_main_content(html, base_url)` → Get main content (no ads/nav)
- `extract_links(html, base_url)` → Get all links from page
- `extract_metadata(html)` → Get title, author, date, description
- `extract_tables(html)` → Extract all tables as structured data
- `html_to_markdown(html)` → Convert HTML to readable markdown
- `assess_content_quality(html, url, purpose)` → Check if content is sufficient

**When to use:** After fetching HTML to extract useful information

## Workflows

You have access to **situation-specific workflows** for complex multi-step tasks:

### Information Type Workflows

**structured_data_navigation** - For extracting lists, tables, statistics
- Use when: Request asks for "top N", "list of", tables, structured data
- Capabilities: Systematic multi-page navigation, table extraction, rate limiting
- Example: "Get top 10 PyPI packages with download stats"

**research_synthesis** - For understanding topics across multiple sources
- Use when: Request needs comprehensive understanding, multiple perspectives
- Capabilities: Multi-source fetching, quality filtering, intelligent synthesis
- Example: "What are Python error handling best practices?"

**single_source_deep_dive** - For thoroughly analyzing one document
- Use when: Request specifies a URL or asks to summarize specific content
- Capabilities: Deep content extraction, metadata analysis, internal link following
- Example: "Summarize this documentation page"

### Site-Specific Workflows

**documentation_site** - For official documentation (Python docs, MDN, etc.)
- Use when: Target domain is docs.python.org, developer.mozilla.org, readthedocs.io, etc.
- Special handling: Uses site search, extracts code blocks, follows "Next" links
- Example: "Find asyncio examples in Python docs"

**data_portal** - For structured data sites (GitHub, PyPI, npm)
- Use when: Target domain is github.com, pypi.org, npmjs.com, etc.
- Special handling: Tries API first, then HTML scraping, extracts structured data
- Example: "Get package info from PyPI"

**news_site** - For news articles and blog posts
- Use when: Target domain is news/media sites or blogs
- Special handling: Extracts author/date, filters ads aggressively, checks freshness
- Example: "Summarize this tech news article"

### Intent-Specific Workflows

**fact_finding** - Quick factual answers
- Use when: Simple "What is X?" or "Who is Y?" questions
- Strategy: Fetch 1-2 authoritative sources (Wikipedia, official sites), extract definition
- Example: "What is asyncio?"

**comparison** - Compare X vs Y
- Use when: Request explicitly asks to compare options
- Strategy: Fetch balanced sources for each option, extract pros/cons, synthesize
- Example: "Compare React vs Vue"

**trend_analysis** - Latest developments, current state
- Use when: Request asks for "latest", "recent", "current", or specific year
- Strategy: Filter by date (past 6-12 months), synthesize temporal trends
- Example: "Current state of Python packaging in 2024"

**how_to** - Step-by-step tutorials
- Use when: Request asks "how to" or wants tutorial/guide
- Strategy: Extract steps, code examples, prerequisites, structured output
- Example: "How to use asyncio for web scraping"

## Tools

**TodoWrite** - Track progress through multi-step tasks
- Use when: Working on complex tasks with 5+ steps (especially UC2, UC3)
- Benefits: Helps you (and user) track what's done and what's remaining
- Example: When fetching 10 package pages, track "Fetched 3/10"

---

# DECISION LOGIC: How to Approach Each Request

## Step 1: Analyze the Request

**Ask yourself:**
1. What is the user really asking for? (fact, comparison, data, summary)
2. Do they want breadth (multiple sources) or depth (single source)?
3. Is there a target URL provided, or do I need to search?
4. How complex is this task? (simple: 1-3 steps, complex: 5+ steps)

## Step 2: Select Workflow

**Use WorkflowSelectorResource to classify the request:**

```
workflow_decision = call_resource(
    resource_id="workflow_selector",
    method="select_workflow",
    arguments={
        "request": <user request>,
        "target_url": <url if provided, else null>
    }
)
```

**The WorkflowSelectorResource will return:**
- `workflow`: Which workflow to use
- `confidence`: How confident it is (0.0-1.0)
- `reasoning`: Why this workflow was chosen
- `parameters`: Workflow-specific parameters (max_sources, rate_limit, etc.)

**Trust the WorkflowSelectorResource** - it uses LLM reasoning to make intelligent decisions.

## Step 3: Execute Workflow

**For each workflow type, follow its specific pattern (see Workflows section above)**

## Step 4: Quality Assurance

**Before responding to user, check:**
- ✅ Did I answer the user's question?
- ✅ Are all sources cited with URLs?
- ✅ Is the information current (if recency matters)?
- ✅ Did I handle errors gracefully?
- ✅ Is the output well-structured?

## Step 5: Error Recovery

**If a fetch fails:**
1. Log the failure clearly
2. Try alternative source if available
3. Continue with partial results if possible
4. Explain to user what succeeded and what failed

---

# QUALITY STANDARDS

## What Makes a Good Result?

### For Summaries/Synthesis:
- **Accurate**: Information matches sources (no hallucination)
- **Concise**: 3-5 bullet points for simple requests, 1-2 paragraphs for complex
- **Cited**: Every claim has source URL
- **Current**: Recent sources when recency matters
- **Structured**: Use headings, bullets, tables for readability

### For Structured Data:
- **Complete**: All requested items extracted (or explain what's missing)
- **Consistent**: Same fields for all items
- **Accurate**: Data matches source pages exactly
- **Cited**: Source URL for each item
- **Formatted**: Table or structured list format

---

# RATE LIMITING & ETHICS

## Rate Limiting Rules

**ALWAYS respect rate limits:**
- **1 request per second per domain** (strictly enforced)
- For multi-page navigation (10+ pages), this is CRITICAL
- Use TodoWrite to track progress during long operations

**Why this matters:**
- Prevents overloading websites
- Avoids getting blocked/banned
- Ethical web scraping behavior

## Ethical Guidelines

**DO:**
- Respect robots.txt (checked automatically by WebFetcherResource)
- Cite all sources with full URLs
- Explain when content is insufficient
- Handle failures gracefully

**DON'T:**
- Hammer websites with rapid requests
- Scrape content behind authentication
- Present scraped content as your own
- Access content you're not authorized to see

---

# FINAL CHECKLIST

Before responding to user, verify:

- [ ] Did I use workflow_selector to pick the right workflow?
- [ ] Did I follow the workflow's specific pattern?
- [ ] Did I respect rate limits (1 req/sec per domain)?
- [ ] Did I cite ALL sources with URLs?
- [ ] Did I check content quality before using it?
- [ ] Did I handle errors gracefully?
- [ ] Did I use TodoWrite for complex tasks (5+ steps)?
- [ ] Is my output well-structured and readable?
- [ ] Did I answer the user's actual question?
- [ ] Did I explain my process (thinking out loud)?

---

**Remember:** You are a specialized web browsing agent. Your job is to be **thorough, accurate, and transparent** about what you find, what you can't find, and how you're approaching each task.
</IDENTITY>
```

### Agent Capabilities

#### Core Workflows

**1. Search and Summarize**
```
User/Agent request → Search web → Fetch top N results → Extract content →
Summarize findings → Return with citations
```

**2. Fetch and Extract**
```
User/Agent request with URL → Validate URL → Fetch content → Extract main content →
Parse specific data → Return structured results
```

**3. Multi-page Research**
```
User/Agent request → Search → Fetch → Extract links → Follow relevant links →
Synthesize multi-page content → Return comprehensive summary
```

**4. Data Extraction**
```
User/Agent request for specific data → Fetch page → Extract tables/lists →
Parse structured data → Return in requested format
```

#### Tool Usage Patterns

The agent has access to:
- `call_resource`: WebFetcherResource (search_web, fetch_url, validate_url)
- `call_resource`: ContentExtractorResource (extract_main_content, extract_links, etc.)
- Timeline: Track browsing history, cache content

Example tool call sequences:

**Search workflow:**
```xml
<tool_call>
  <function>call_resource</function>
  <arguments>
    <resource_id>web-fetcher</resource_id>
    <method>search_web</method>
    <parameters>
      <query>latest developments in AI agents 2025</query>
      <max_results>5</max_results>
    </parameters>
  </arguments>
</tool_call>

<!-- Then for each promising result: -->
<tool_call>
  <function>call_resource</function>
  <arguments>
    <resource_id>web-fetcher</resource_id>
    <method>fetch_url</method>
    <parameters>
      <url>https://example.com/article</url>
    </parameters>
  </arguments>
</tool_call>

<tool_call>
  <function>call_resource</function>
  <arguments>
    <resource_id>content-extractor</resource_id>
    <method>extract_main_content</method>
    <parameters>
      <html>[fetched HTML]</html>
      <base_url>https://example.com/article</base_url>
    </parameters>
  </arguments>
</tool_call>
```

### Response Patterns

**Successful Response:**
```
Based on my web search, here's what I found:

**[Article Title]** (https://example.com/article)
Published: [date]
Summary: [2-3 sentence summary]

**Key Points:**
- Point 1 with specific data
- Point 2 with quotes/citations
- Point 3 with analysis

**Sources:**
1. [Title] - https://url1.com
2. [Title] - https://url2.com

[Optional: Confidence assessment, conflicts between sources, limitations]
```

**Partial Success:**
```
I found some information, but encountered issues:

**What I found:**
[Summary with citations]

**Limitations:**
- Could not access [URL] (404 error)
- [Website] blocked automated access
- Information on [topic] appears outdated (last updated [date])

**Suggestions:**
- Try searching for [alternative query]
- Check [alternative source]
```

**Error Response:**
```
I was unable to complete the web search/fetch because:
[Clear explanation of error]

**What I tried:**
- Searched for "[query]" on DuckDuckGo
- Attempted to fetch [URL]
- Retried [N] times

**Suggestions:**
- [Alternative approach]
- [Check if URL is correct]
- [Try again later if rate limited]
```

## State Management

### Timeline Tracking

The agent tracks in its timeline:
```python
{
    "entry_type": "MY_THOUGHTS",
    "content": "Searching for: [query]"
}

{
    "entry_type": "TOOL_CALL",
    "content": "web-fetcher.search_web(query='...', max_results=5)"
}

{
    "entry_type": "TOOL_RESULT",
    "content": {
        "search_results": [...],
        "selected_urls": [...]
    }
}

{
    "entry_type": "MY_THOUGHTS",
    "content": "Found [N] relevant results. Fetching top 3..."
}

{
    "entry_type": "TOOL_CALL",
    "content": "web-fetcher.fetch_url(url='...')"
}

{
    "entry_type": "TOOL_RESULT",
    "content": {
        "url": "...",
        "title": "...",
        "excerpt": "..."
    }
}

{
    "entry_type": "MY_RESPONSE",
    "content": "[Final synthesized response with citations]"
}
```

### Session Metadata

```python
{
    "session_start": "2025-09-29T10:00:00Z",
    "urls_visited": ["url1", "url2", ...],
    "searches_performed": [
        {"query": "...", "engine": "duckduckgo", "timestamp": "..."}
    ],
    "content_cached": {
        "url1": {"title": "...", "excerpt": "...", "cached_at": "..."},
        # In-memory cache for session
    },
    "rate_limit_state": {
        "example.com": {"last_request": "...", "requests_count": 3}
    }
}
```

## Dependencies

### Python Packages

```toml
[tool.poetry.dependencies]
# Core dependencies
requests = "^2.31.0"           # HTTP client
beautifulsoup4 = "^4.12.0"     # HTML parsing
lxml = "^5.1.0"                # Fast XML/HTML parser
readability-lxml = "^0.8.1"    # Content extraction
html2text = "^2020.1.16"       # HTML to Markdown
urllib3 = "^2.1.0"             # URL handling

# Optional (for future enhancements)
# playwright = "^1.40.0"       # JavaScript rendering (Phase 2)
# selenium = "^4.15.0"         # Alternative browser automation (Phase 2)
```

### System Requirements

- Python 3.12+
- Network access (HTTP/HTTPS)
- No browser installation needed (Phase 1)
- Memory: ~100MB for typical operation

## Testing Strategy

### Unit Tests

**WebFetcherResource:**
```python
- test_fetch_url_success()
- test_fetch_url_timeout()
- test_fetch_url_invalid_url()
- test_fetch_url_too_large()
- test_fetch_url_rate_limited()
- test_search_web_duckduckgo()
- test_search_web_fallback()
- test_validate_url()
- test_rate_limiting()
```

**ContentExtractorResource:**
```python
- test_extract_main_content()
- test_extract_main_content_with_noise()
- test_extract_links()
- test_extract_metadata()
- test_html_to_markdown()
- test_extract_tables()
- test_content_truncation()
```

**WebBrowserAgent:**
```python
- test_search_and_summarize()
- test_fetch_specific_url()
- test_multi_page_research()
- test_data_extraction()
- test_error_handling()
- test_rate_limit_respect()
```

### Integration Tests (Use Case-Driven)

**Use Case 1 Integration:**
```python
- test_use_case_1_simple_fetch_and_summarize()
  # Given: A valid documentation URL
  # When: Agent is asked to summarize it
  # Then: Returns 3-5 bullet point summary with citation
  # Validates: fetch_url + extract_main_content + agent summarization
```

**Use Case 2 Integration:**
```python
- test_use_case_2_search_and_synthesize()
  # Given: A search query about a technical topic
  # When: Agent searches and fetches top 3 results
  # Then: Returns synthesized summary with multiple citations
  # Validates: search_web + multiple fetch_url + content synthesis
```

**Use Case 3 Integration:**
```python
- test_use_case_3_multi_page_navigation()
  # Given: A request for tabular data from a stats page
  # When: Agent navigates to stats page, extracts table, follows links
  # Then: Returns structured table with data from 10+ pages
  # Validates: extract_tables + extract_links + rate limiting + data structuring
```

**Additional Integration:**
```python
- test_agent_to_agent_delegation()
  # Dana → WebBrowserAgent delegation
- test_partial_failure_handling()
  # Some URLs fail, agent continues with available data
- test_rate_limit_enforcement()
  # Respects 1 req/sec across multiple calls
```

### Mock Strategy

- Mock HTTP requests in unit tests
- Use real (but controlled) URLs for integration tests
- Create fixture HTML files for parsing tests
- Test with various content types and edge cases

## Security & Ethics

### Security Considerations

1. **URL Validation**: Strict validation to prevent SSRF attacks
   - Only allow http:// and https:// schemes
   - Block internal/private IP ranges
   - Block localhost and 127.0.0.1

2. **Content Sanitization**:
   - Parse HTML safely (no code execution)
   - Sanitize extracted content
   - Limit content size

3. **Rate Limiting**: Prevent abuse and respect server resources

4. **User Agent**: Clearly identify as bot, provide contact info

### Ethical Guidelines

1. **Respect robots.txt**: Check and honor robots.txt directives
2. **Rate limiting**: Default 1 req/sec per domain (configurable)
3. **User agent**: Honest identification as Adana bot
4. **Copyright**: Don't copy/reproduce full articles, only summarize
5. **Privacy**: Don't scrape personal data or private information
6. **Attribution**: Always cite sources

## Implementation Phases

### Use Case-Driven Implementation Strategy

Implementation will be incremental, with each phase enabling specific use cases:

**Phase 1a: Use Case 1 Support (Simple Fetch)**
- Priority: HIGH
- Timeline: Week 1
- Deliverables:
  - ✅ WebFetcherResource.fetch_url()
  - ✅ WebFetcherResource.validate_url()
  - ✅ ContentExtractorResource.extract_main_content()
  - ✅ ContentExtractorResource.extract_metadata()
  - ✅ Basic WebBrowserAgent workflow (fetch → extract → summarize)
  - ✅ Unit tests for resources
  - ✅ Integration test for UC1

**Validation:** Can execute Use Case 1 end-to-end successfully

**Phase 1b: Use Case 2 Support (Search & Synthesize)**
- Priority: HIGH
- Timeline: Week 2
- Deliverables:
  - ✅ WebFetcherResource.search_web() (DuckDuckGo)
  - ✅ Multi-source fetching in agent
  - ✅ Content synthesis logic
  - ✅ Search tests
  - ✅ Integration test for UC2

**Validation:** Can execute Use Case 2 end-to-end successfully

**Phase 1c: Use Case 3 Support (Multi-Page Navigation)**
- Priority: MEDIUM
- Timeline: Week 3
- Deliverables:
  - ✅ ContentExtractorResource.extract_links()
  - ✅ ContentExtractorResource.extract_tables()
  - ✅ Rate limiting per domain (enforced)
  - ✅ Link following logic in agent
  - ✅ Session state tracking
  - ✅ Integration test for UC3

**Validation:** Can execute Use Case 3 end-to-end successfully

**Phase 1d: Robustness & Polish**
- Priority: MEDIUM
- Timeline: Week 4
- Deliverables:
  - ✅ Retry logic with exponential backoff
  - ✅ Comprehensive error handling
  - ✅ Caching (in-memory, 5-min TTL)
  - ✅ Google Custom Search fallback
  - ✅ ContentExtractorResource.html_to_markdown()
  - ✅ All regression tests
  - ✅ Documentation and examples

**Validation:** All use cases work reliably with graceful degradation

### Phase 2: Enhanced Capabilities (Future)
- JavaScript rendering with Playwright
- Google Custom Search API integration
- Caching with persistence (Redis/SQLite)
- PDF content extraction
- Image analysis/OCR
- Form filling capabilities
- Cookie/session management

### Phase 3: Advanced Features (Future)
- Authentication support (OAuth, API keys)
- Screenshot capture
- Web scraping workflows
- Structured data extraction (JSON-LD, microdata)
- Competitive intelligence gathering
- Website change monitoring

## Success Criteria

### Use Case-Based Validation

**Phase 1a Complete (Use Case 1 Working):**
1. ✅ User/Agent can provide a URL and get a summary
2. ✅ Main content extracted (no navigation/ads)
3. ✅ Summary is accurate and concise (3-5 bullet points)
4. ✅ Full citation provided with URL
5. ✅ Handles 404/timeout errors gracefully
6. ✅ Completes in <5 seconds for typical page
7. ✅ Unit tests for fetch_url() and extract_main_content() pass
8. ✅ Integration test for UC1 passes

**Phase 1b Complete (Use Case 2 Working):**
1. ✅ Can search web and get relevant results
2. ✅ Fetches and parses 3+ sources successfully
3. ✅ Synthesizes coherent summary (not just concatenation)
4. ✅ All sources cited with URLs
5. ✅ Handles partial failures (some URLs fail)
6. ✅ Completes in <30 seconds
7. ✅ Unit tests for search_web() pass
8. ✅ Integration test for UC2 passes

**Phase 1c Complete (Use Case 3 Working):**
1. ✅ Can navigate multi-page structures
2. ✅ Extracts tabular data accurately
3. ✅ Follows 10+ links systematically
4. ✅ Structures data in requested format (tables/lists)
5. ✅ Respects rate limits (1 req/sec per domain)
6. ✅ Tracks all URLs in timeline
7. ✅ Handles missing pages gracefully
8. ✅ Completes in <60 seconds with 10 fetches
9. ✅ Unit tests for extract_links() and extract_tables() pass
10. ✅ Integration test for UC3 passes

**Phase 1d Complete (Production Ready):**
1. ✅ Retry logic with exponential backoff works
2. ✅ All error scenarios handled gracefully
3. ✅ Caching reduces redundant requests
4. ✅ Google Custom Search fallback functional (if API key present)
5. ✅ Markdown conversion works for all content types
6. ✅ All unit tests pass (>80% coverage)
7. ✅ All integration tests pass
8. ✅ Successfully integrates with Dana coordinator
9. ✅ Documentation complete with examples
10. ✅ All three use cases demonstrate in examples/

### Overall Success Metrics

**Performance:**
- UC1: <5 seconds average
- UC2: <30 seconds average
- UC3: <60 seconds average (10 fetches)

**Reliability:**
- 95%+ success rate on valid URLs
- Graceful degradation on failures
- No crashes or unhandled exceptions

**Quality:**
- Content extraction accuracy >90%
- Summary quality (human evaluation)
- Proper citation in 100% of responses

## Open Questions

1. **Caching persistence**: Should cache persist across agent restarts, or in-memory only?
   - **Recommendation**: Start in-memory, add persistence in Phase 2

2. **Content length for LLM**: What's the optimal truncation strategy?
   - **Recommendation**: Smart truncation - keep beginning and end, note truncation

3. **Search result ranking**: Should agent re-rank results based on relevance?
   - **Recommendation**: No, trust search engine ranking initially

4. **Robots.txt checking**: Should we implement robots.txt parsing?
   - **Recommendation**: Yes, add in Phase 1 with simple parser

5. **API keys management**: How to handle Google Custom Search API keys?
   - **Recommendation**: Environment variables, graceful fallback if not present

## References

- [Adana Resource Specification](./resource_spec.md)
- [Adana Agent Specification](./core_agent_spec.md)
- [Readability Algorithm](https://github.com/mozilla/readability)
- [DuckDuckGo HTML Search](https://html.duckduckgo.com/)
- [robots.txt Specification](https://www.robotstxt.org/)

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-09-29 | Claude + CTN | Initial specification |
| 1.1 | 2025-09-29 | Claude + CTN | Added 3 driving use cases (simple to complex), use case coverage matrix, use case-driven implementation phases, and use case-based success criteria |
| 2.0 | 2025-09-29 | Claude + CTN | **Complete architecture**: Added situation-specific workflows, BaseWAR.reason() integration, WorkflowSelectorResource, complete system prompt (IDENTITY), LLM reasoning patterns, and workflow taxonomy. Changed from single-resource to multi-resource + multi-workflow + LLM-augmented pattern. |

---

## Architecture Summary (v2.0)

**Key Design Principles:**
1. **Situation-Specific Workflows**: Different execution patterns for different request types (10 workflows across 3 categories)
2. **LLM-Augmented Resources**: Resources use `BaseWAR.reason()` for intelligent decisions (workflow selection, content quality assessment, result ranking)
3. **Declarative Orchestration**: System prompt (IDENTITY) provides high-level logic, Python code provides STAR loop and capabilities
4. **Hybrid Intelligence**: Workflows provide structure, LLM provides flexibility, rules provide fallback

**Architecture Pattern:**
```
Single Agent + Multi-Resource + Multi-Workflow + LLM Reasoning

Agent (orchestration) → Resources (capabilities + reasoning) → Workflows (patterns) → LLM (decisions)
```

**What's New in v2.0:**
- WorkflowSelectorResource for intelligent workflow selection
- 10 situation-specific workflows (information type, site-specific, intent-specific)
- BaseWAR.reason() integration for all intelligent decisions
- Complete system prompt with workflow selection logic
- TodoWrite tool integration for progress tracking
- Use of reason() for: workflow selection, content quality, result ranking, synthesis planning

---

**Next Steps:**
1. **Implement BaseWAR.reason()** (framework-level, you will implement)
2. Review and approve specification v2.0
3. Implement WorkflowSelectorResource
4. Implement WebFetcherResource (with rank_search_results using reason())
5. Implement ContentExtractorResource (with assess_content_quality using reason())
6. Implement situation-specific workflows (Phase 1: 3 workflows for UC1, UC2, UC3)
7. Implement WebBrowserAgent with complete system prompt
8. Create comprehensive tests (unit + integration for each UC)
9. Integrate with Dana coordinator (war.py)
