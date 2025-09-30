# GoogleSearchService Architecture Documentation

## Overview

The GoogleSearchService implements the SearchService protocol to provide web search capabilities using Google Custom Search API combined with web content extraction. This service bridges Google's search results with content scraping to deliver comprehensive search results for product research.

## Architecture Components

### Core Service Structure

```python
class GoogleSearchService(SearchService):
    """
    Google Custom Search + Web Scraping implementation.

    Combines Google Custom Search API with BeautifulSoup-based content extraction
    to provide comprehensive search results with actual page content.
    """

    async def search(self, request: SearchRequest) -> SearchResults:
        """Main entry point implementing SearchService protocol"""
```

### Component Hierarchy

```
GoogleSearchService
├── GoogleSearchEngine     # Google Custom Search API integration
├── WebContentExtractor    # BeautifulSoup-based web scraping
├── ResultProcessor        # Search result scoring and filtering
└── ConfigManager         # API keys and settings management
```

## Implementation Details

### 1. GoogleSearchEngine

**Purpose**: Interface with Google Custom Search API to get search results

**Key Features**:
- Async HTTP client with proper timeout handling
- Query optimization for technical product searches
- Result scoring based on domain relevance and content type
- Automatic URL filtering (skip social media, irrelevant sites)

**API Integration**:
```python
class GoogleSearchEngine:
    def __init__(self, api_key: str, cse_id: str):
        self.api_key = api_key
        self.cse_id = cse_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str, max_results: int) -> List[GoogleResult]:
        # Construct Google Custom Search API request
        # Handle pagination if needed
        # Score and filter results
        # Return structured results
```

**Search Parameters**:
- Language: English (`lr=lang_en`)
- Location: US-focused (`gl=us`, `hl=en`)
- Results per page: Up to 10 (API limitation)
- Query optimization for technical content

### 2. WebContentExtractor

**Purpose**: Extract and clean content from web pages

**Key Features**:
- Async context manager for resource management
- BeautifulSoup-based HTML parsing and cleaning
- Content filtering (remove scripts, ads, navigation)
- Text extraction with structure preservation
- Error handling for failed extractions

**Content Processing Pipeline**:
```python
class WebContentExtractor:
    async def extract_content(self, url: str) -> ContentResult:
        # 1. Fetch HTML content with proper headers
        # 2. Parse HTML with BeautifulSoup
        # 3. Remove unwanted elements (scripts, ads, nav)
        # 4. Extract and clean text content
        # 5. Return structured content result
```

**Content Cleaning Strategy**:
- Remove: `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>`, `<aside>`
- Preserve: `<p>`, `<div>`, `<span>`, `<table>`, `<ul>`, `<ol>`, `<h1-h6>`
- Extract: Product specifications, technical data, structured information

### 3. ResultProcessor

**Purpose**: Score, filter, and rank search results for relevance

**Relevance Scoring Algorithm**:
```python
def calculate_relevance_score(url: str, title: str, snippet: str) -> int:
    score = 0

    # High-priority content types
    if is_technical_document(url):          # +5 points
        score += 5
    if contains_specifications(title):       # +4 points
        score += 4
    if is_distributor_site(url):            # +3 points
        score += 3
    if contains_product_info(snippet):      # +2 points
        score += 2
    if has_technical_keywords(title):       # +1 point
        score += 1

    return score
```

**Filtering Rules**:
- **Skip domains**: Social media, forums, marketplaces
- **Prioritize**: Manufacturer sites, distributors, technical documentation
- **Content types**: PDFs, datasheets, specification pages

### 4. ConfigManager

**Purpose**: Handle configuration, API keys, and environment settings

**Configuration Schema**:
```python
@dataclass
class GoogleSearchConfig:
    api_key: str
    cse_id: str
    max_results: int = 10
    timeout_seconds: int = 30
    enable_content_extraction: bool = True

    # Content extraction settings
    max_content_length: int = 50000
    enable_pdf_extraction: bool = True

    # Result filtering settings
    skip_domains: List[str] = field(default_factory=lambda: [
        'youtube.com', 'facebook.com', 'twitter.com', 'pinterest.com'
    ])
```

## Data Flow Architecture

### Request Processing Flow

```
SearchRequest → GoogleSearchService.search()
    ↓
1. Query Optimization
    ↓
2. Google Custom Search API Call
    ↓
3. Result Scoring & Filtering
    ↓
4. Content Extraction (parallel)
    ↓
5. SearchResults Assembly
    ↓
SearchResults (with content)
```

### Detailed Processing Steps

#### Step 1: Query Optimization
```python
def optimize_query(self, request: SearchRequest) -> str:
    query = request.query

    # Add search depth modifiers
    if request.search_depth == "extensive":
        query += " specifications datasheet technical"
    elif request.search_depth == "standard":
        query += " specifications"
    # basic: use query as-is

    return query
```

#### Step 2: Google Search Execution
- Make async HTTP request to Google Custom Search API
- Handle rate limiting and API errors
- Parse JSON response and extract relevant fields
- Return structured search results

#### Step 3: Result Processing
- Score each result using relevance algorithm
- Filter out irrelevant domains and content types
- Sort by relevance score (highest first)
- Limit to requested number of results

#### Step 4: Content Extraction (Parallel)
```python
async def extract_all_content(self, urls: List[str]) -> List[SearchSource]:
    # Create extraction tasks for all URLs
    tasks = [self.extract_single_url(url) for url in urls]

    # Execute all extractions in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter successful extractions and handle errors
    return [result for result in results if isinstance(result, SearchSource)]
```

#### Step 5: Response Assembly
- Combine search metadata with extracted content
- Create SearchSource objects for each successful extraction
- Build final SearchResults with success/error information

## Error Handling Strategy

### API Error Handling
```python
async def handle_google_api_errors(self, response: httpx.Response):
    if response.status_code == 429:  # Rate limit exceeded
        raise RateLimitError("Google API rate limit exceeded")
    elif response.status_code == 403:  # API key invalid/quota exceeded
        raise APIKeyError("Google API authentication failed")
    elif response.status_code >= 500:  # Server errors
        raise ServiceUnavailableError("Google API temporarily unavailable")
    else:
        response.raise_for_status()
```

### Content Extraction Error Handling
- **Connection failures**: Log error, continue with other URLs
- **Parsing failures**: Return empty content, log warning
- **Timeout errors**: Cancel extraction, return partial results
- **Rate limiting**: Implement exponential backoff

### Fallback Strategy
1. **Primary**: Google Custom Search + content extraction
2. **Fallback 1**: Google search only (no content extraction)
3. **Fallback 2**: Return empty results with error message

## Performance Considerations

### Optimization Strategies

#### 1. Concurrent Processing
- Search API call and content extraction run in parallel when possible
- Multiple URL extractions happen concurrently
- Use asyncio.gather() for coordinated async operations

#### 2. Request Optimization
- Connection pooling with httpx.AsyncClient
- Proper timeout configuration (30s for search, 15s per content extraction)
- Keep-alive connections for multiple requests

#### 3. Resource Management
- Async context managers for proper cleanup
- Connection limits to avoid overwhelming target servers
- Memory-efficient content processing

### Performance Targets
- **Search API response**: < 2 seconds
- **Content extraction per URL**: < 10 seconds
- **Total service response**: < 30 seconds
- **Concurrent URL limit**: 10 simultaneous extractions

## Security Considerations

### API Key Management
- Store API keys in environment variables
- Never log or expose API keys in error messages
- Validate API key format before making requests


### Input Validation
```python
def validate_search_request(self, request: SearchRequest) -> None:
    if not request.query.strip():
        raise ValueError("Search query cannot be empty")

    if len(request.query) > 1000:
        raise ValueError("Search query too long (max 1000 characters)")

    if request.search_depth not in {"basic", "standard", "extensive"}:
        raise ValueError("Invalid search depth")
```

## Configuration Requirements

### Environment Variables
```bash
# Required
GOOGLE_SEARCH_API_KEY=your_google_custom_search_api_key
GOOGLE_SEARCH_CX=your_custom_search_engine_id

# Optional
GOOGLE_SEARCH_MAX_RESULTS=10
GOOGLE_SEARCH_TIMEOUT=30
ENABLE_CONTENT_EXTRACTION=true
```

### Google Custom Search Setup
1. Create Google Custom Search Engine at [cse.google.com](https://cse.google.com)
2. Configure search engine to search entire web
3. Get Custom Search Engine ID (CX)
4. Enable Custom Search API in Google Cloud Console
5. Create API key with Custom Search API access

## Integration with WebResearch Architecture

### SearchService Protocol Compliance
```python
# Our service implements this exact interface
class SearchService(Protocol):
    async def search(self, request: SearchRequest) -> SearchResults

# GoogleSearchService implementation
class GoogleSearchService(SearchService):
    async def search(self, request: SearchRequest) -> SearchResults:
        # Implementation that returns SearchResults with:
        # - success: bool
        # - sources: List[SearchSource] (with URL + content)
        # - raw_data: str (Google API response)
        # - error_message: str (if failed)
```

### Data Model Mapping
```python
# Input: SearchRequest
SearchRequest:
    query: str                    → Google Custom Search query
    search_depth: str            → Query optimization modifier
    with_full_content: bool      → Enable/disable content extraction

# Output: SearchResults
SearchResults:
    success: bool                → Overall operation success
    sources: List[SearchSource]  → URLs + extracted content
    raw_data: str               → Google API JSON response
    error_message: str          → Error details if failed

SearchSource:
    url: str                    → Google search result URL
    content: str                → BeautifulSoup extracted text
    full_content: str           → Raw HTML (if requested)
```
