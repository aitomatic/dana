# WebResearchAgent

Specialized agent for web research and information synthesis.

## Overview

WebResearchAgent provides comprehensive web research capabilities including single source analysis, multi-source synthesis, and structured data extraction. It uses a composition-based architecture with intelligent workflow selection powered by LLM reasoning.

**Architecture**: Single-Agent + Multi-Resource + Multi-Workflow + LLM-Augmented

## Quick Start

```python
from adana.lib.agents.web_research.web_research_agent import WebResearchAgent

# Create agent
agent = WebResearchAgent()

# Analyze a URL
result = agent.analyze_url(
    url="https://docs.python.org/3/library/asyncio.html",
    purpose="Learn about asyncio"
)

# Research a topic
result = agent.research(
    query="What is asyncio in Python?",
    max_sources=3
)

# Extract structured data
result = agent.extract_data(
    query="Python popular packages",
    max_pages=2
)
```

## Features

- ✅ **Single source deep dive analysis** - Thoroughly analyze one document
- ✅ **Multi-source research synthesis** - Synthesize information across 3-5 sources
- ✅ **Structured data extraction** - Extract tables/lists with pagination support
- ✅ **Intelligent workflow selection** - LLM-powered workflow selection with few-shot learning
- ✅ **Rate limiting** - 1 request/second per domain
- ✅ **Quality assessment** - LLM-based content quality evaluation
- ✅ **Citation management** - Numbered and author-date citation styles
- ✅ **Markdown formatting** - Professional formatted output

## Architecture

### Resources (3)
- **WebFetcherResource** - HTTP operations with rate limiting, DuckDuckGo search
- **ContentExtractorResource** - HTML parsing, table extraction, metadata extraction
- **WorkflowSelectorResource** - Intelligent workflow selection using LLM

### Components (6)
Composition-based reusable functional primitives:
- **SearchComponents** - Web searching, filtering, ranking
- **FetchComponents** - URL fetching, parallel fetching, validation
- **ExtractComponents** - Content extraction, tables, links, code blocks
- **ProcessComponents** - Quality assessment, key point extraction
- **SynthesizeComponents** - Multi-source synthesis, comparison, timeline
- **FormatComponents** - Citations, tables, markdown formatting

### Workflows (3 Core)
- **SingleSourceDeepDiveWorkflow** - UC1: Single URL analysis
- **ResearchSynthesisWorkflow** - UC2: Multi-source research
- **StructuredDataNavigationWorkflow** - UC3: Multi-page data extraction

## API Reference

### Main Methods

#### `agent.query(message=None, **kwargs) -> DictParams`
Main entry point - orchestrates STAR loop with automatic workflow selection.

#### `agent.analyze_url(url: str, **kwargs) -> DictParams`
Convenience method for single URL analysis.

**Parameters:**
- `url` (str): URL to analyze
- `purpose` (str, optional): Analysis purpose for quality assessment
- `extract_code` (bool, optional): Extract code blocks

**Returns:**
```python
{
    "success": bool,
    "workflow": str,
    "result": {
        "content": dict,
        "quality": dict,
        "key_points": list[str],
        "summary": str,
        "formatted_output": str,
        "metadata": dict
    }
}
```

#### `agent.research(query: str, **kwargs) -> DictParams`
Convenience method for multi-source research.

**Parameters:**
- `query` (str): Research query
- `max_sources` (int, optional): Maximum sources to analyze (default: 5)
- `require_recent` (bool, optional): Filter for recent sources
- `synthesis_type` (str, optional): themes|comparison|timeline

**Returns:**
```python
{
    "success": bool,
    "workflow": str,
    "sources_analyzed": int,
    "result": {
        "synthesis": dict,
        "summary": dict,
        "formatted_output": str,
        "sources": list[dict]
    }
}
```

#### `agent.extract_data(query=None, url=None, **kwargs) -> DictParams`
Convenience method for structured data extraction.

**Parameters:**
- `query` (str, optional): Search query
- `url` (str, optional): Starting URL
- `max_pages` (int, optional): Maximum pages to navigate (default: 10)
- `extract_tables` (bool, optional): Extract tables (default: True)
- `extract_lists` (bool, optional): Extract lists (default: True)

**Returns:**
```python
{
    "success": bool,
    "workflow": str,
    "result": {
        "pages_processed": int,
        "tables": list[dict],
        "lists": list[dict],
        "total_data_points": int,
        "formatted_output": str
    }
}
```

### Utility Methods

#### `agent.get_capabilities() -> list[str]`
Get list of agent capabilities.

#### `agent.get_available_workflows() -> list[str]`
Get list of available workflow names.

## Use Cases

### Use Case 1: Single URL Analysis (Simple)
```python
agent = WebResearchAgent()

result = agent.analyze_url(
    url="https://example.com/article",
    purpose="general analysis",
    extract_code=True
)

if result["success"]:
    print(result["result"]["summary"])
    print(f"Key points: {result['result']['key_points']}")
```

### Use Case 2: Multi-Source Research (Medium)
```python
agent = WebResearchAgent()

result = agent.research(
    query="What is asyncio in Python?",
    max_sources=5,
    synthesis_type="themes"
)

if result["success"]:
    print(f"Analyzed {result['sources_analyzed']} sources")
    print(result["result"]["formatted_output"])
```

### Use Case 3: Structured Data Extraction (Complex)
```python
agent = WebResearchAgent()

result = agent.extract_data(
    query="Top Python packages 2024",
    max_pages=5,
    extract_tables=True
)

if result["success"]:
    res = result["result"]
    print(f"Found {len(res['tables'])} tables")
    print(f"Total data points: {res['total_data_points']}")
```

## Requirements

### Dependencies
- `requests>=2.31.0` - HTTP client
- `beautifulsoup4>=4.12.0` - HTML parsing
- `lxml>=5.0.0` - XML/HTML parser
- `readability-lxml>=0.8.1` - Content extraction
- `html2text>=2024.2.26` - Markdown conversion

### Runtime Requirements
- Python 3.11+
- Network connectivity
- LLM API access (OpenAI or Anthropic) for BaseWAR.reason() calls

## Configuration

### Basic Configuration

The agent uses default configuration:
- Rate limiting: 1 request/second per domain
- Maximum page size: 5MB
- Timeout: 30 seconds per request

### Search Engine Setup

**Important**: DuckDuckGo actively blocks automated requests (even with browser-like headers). You must use a proper search API for production use.

#### **Option 1: Google Custom Search API** (Recommended)

1. Go to https://console.cloud.google.com/
2. Enable Custom Search API
3. Create credentials (API key)
4. Create Custom Search Engine at https://programmablesearchengine.google.com/
5. Set environment variables:
   ```bash
   export GOOGLE_API_KEY="your-api-key"
   export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
   ```
6. Use Google search:
   ```python
   # Agent will use Google if env vars are set
   agent.web_fetcher.search_web(query, search_engine="google")
   ```

#### **Option 2: Provide URLs Directly**

Skip search entirely by providing URLs:
```python
# Single URL analysis (no search needed)
result = agent.analyze_url(url="https://example.com")

# Multi-source with explicit URLs
# Implement custom search logic or manually select URLs
```

#### **Option 3: Use SerpAPI** (Future)

- https://serpapi.com/ - Aggregates multiple search engines
- Easier setup, paid service
- Not yet implemented

## Error Handling

All methods return a `DictParams` with:
```python
{
    "success": bool,
    "error": str | None,
    "workflow": str,
    # ... additional fields
}
```

Always check `result["success"]` before accessing other fields.

## Examples

See:
- `tmp/example_use_web_research_agent.py` - Comprehensive examples
- `tmp/quickstart_web_research_agent.py` - Quick start guide
- `tmp/test_web_research_agent.py` - Basic tests

## Design Documents

- **Specification**: `adana/specs/web_research_agent_spec.md`
- **Architecture**: Single-Agent + Multi-Resource + Multi-Workflow + LLM-Augmented
- **Pattern**: STAR (See-Think-Act-Reflect)

## Testing

```bash
# Basic tests
uv run python tmp/test_web_research_agent.py

# Run examples (requires network + LLM)
uv run python tmp/example_use_web_research_agent.py
```

## Implementation Stats

- **Resources**: ~1,180 lines (3 resources)
- **Components**: ~1,780 lines (6 component classes)
- **Workflows**: ~800 lines (3 core workflows)
- **Agent**: ~430 lines
- **Total**: ~4,190 lines of code

## Future Enhancements

- [ ] Additional 7 workflows (documentation_site, data_portal, news_site, fact_finding, comparison, trend_analysis, how_to)
- [ ] Comprehensive test suite
- [ ] API endpoint integration (GitHub, PyPI, etc.)
- [ ] Authentication support
- [ ] PDF/document parsing
- [ ] Image extraction
- [ ] Caching layer
- [ ] Result persistence

## License

Part of the Adana framework. See project LICENSE.