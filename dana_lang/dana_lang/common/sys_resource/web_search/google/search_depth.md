# Search Depth Configuration

**Google Web Search Module - Search Depth Documentation**

## Overview

The Google web search module supports three levels of search depth configuration that control the thoroughness and performance characteristics of search operations. Search depth affects query optimization, reference link extraction, and result processing behavior.

## Search Depth Levels

### 1. BASIC (`"basic"`)
- **Purpose**: Fast, lightweight searches with minimal processing
- **Use Case**: Quick lookups, initial exploration, performance-critical scenarios
- **Characteristics**:
  - No query optimization - uses original query as-is
  - **Zero reference links** extracted
  - Minimal processing overhead
  - Fastest response time

### 2. STANDARD (`"standard"`) - **Default**
- **Purpose**: Balanced search with moderate depth and performance
- **Use Case**: Most common searches, production usage
- **Characteristics**:
  - Query enhanced with `"with all specifications"`
  - **Up to 5 reference links** extracted
  - Standard relevance scoring
  - Good balance of completeness vs performance

### 3. EXTENSIVE (`"extensive"`)
- **Purpose**: Comprehensive, thorough searches for complete information gathering
- **Use Case**: Research tasks, detailed analysis, when completeness is prioritized over speed
- **Characteristics**:
  - Query enhanced with `"with all specifications and relevant information"`
  - **Up to 15 reference links** extracted
  - **20% relevance score boost** for more inclusive results
  - Highest processing time and resource usage

## Implementation Details

### Query Optimization (`search_engine.py`)

```python
def optimize_query(self, query: str, search_depth: str = "standard") -> str:
    if search_depth == "extensive":
        return f"{query} with all specifications and relevant information"
    elif search_depth == "standard":
        return f"{query} with all specifications"
    else:  # basic
        return query  # Use original query unchanged
```

**Examples**:
- Original: `"Intel Core i7 specifications"`
- BASIC: `"Intel Core i7 specifications"` (unchanged)
- STANDARD: `"Intel Core i7 specifications with all specifications"`
- EXTENSIVE: `"Intel Core i7 specifications with all specifications and relevant information"`

### Reference Link Extraction (`reference_extractor.py`)

#### Processing Behavior by Depth:

| Depth | Max Links | Processing | Score Multiplier | Performance |
|-------|-----------|------------|------------------|-------------|
| BASIC | 0 | Skipped entirely | N/A | Fastest |
| STANDARD | 5 | Full processing | 1.0x | Moderate |
| EXTENSIVE | 15 | Enhanced processing | 1.2x | Slowest |

#### Reference Link Scoring System:

**Base Scoring Criteria**:
- **+10 points per match**: Query terms found in URL, text, or context
- **+8 points**: Authority domains (`.gov`, `.edu`, `official`, `docs`, `support`)
- **+7 points**: Technical file types (`.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`)
- **+5 points**: Technical indicators (`spec`, `manual`, `datasheet`, `documentation`, etc.)

**Search Depth Modifiers**:
- **BASIC**: No reference processing
- **STANDARD**: Standard scoring (1.0x multiplier)
- **EXTENSIVE**: Enhanced scoring (1.2x multiplier) for more inclusive results

**Minimum Threshold**: Links must score e5 points to be included

## Configuration Usage

### SearchRequest Model

```python
from dana.common.sys_resource.web_search.core.models import SearchRequest, SearchDepth

# Using enum values (recommended)
request = SearchRequest(
    query="Intel Core i7 specifications",
    search_depth=SearchDepth.STANDARD
)

# Using string values (also supported)
request = SearchRequest(
    query="Intel Core i7 specifications", 
    search_depth="extensive"
)
```

### Available Values

```python
class SearchDepth(str, Enum):
    BASIC = "basic"        # Quick search with minimal results
    STANDARD = "standard"  # Balanced search with moderate depth
    EXTENSIVE = "extensive" # Comprehensive search including reference links
```

## Performance Characteristics

### Resource Usage Comparison

| Depth | Query Processing | Link Extraction | Network Requests | Response Time |
|-------|------------------|-----------------|------------------|---------------|
| BASIC | Minimal | None | Lowest | ~1-2s |
| STANDARD | Moderate | Up to 5 links | Moderate | ~3-5s |
| EXTENSIVE | Enhanced | Up to 15 links | Highest | ~5-10s |

### Memory and CPU Impact

- **BASIC**: Minimal HTML parsing, no link processing
- **STANDARD**: Full HTML parsing + moderate link scoring
- **EXTENSIVE**: Full HTML parsing + comprehensive link analysis + enhanced scoring

## Use Case Guidelines

### When to Use BASIC
-  Quick information lookups
-  Performance-critical applications
-  Initial exploration/validation
-  Limited bandwidth scenarios
- L Comprehensive research needs

### When to Use STANDARD (Default)
-  Most production use cases
-  Balanced completeness vs performance
-  General product research
-  Automated processing pipelines
-  When reference links add value but aren't critical

### When to Use EXTENSIVE
-  Detailed research tasks
-  Academic or technical analysis
-  When completeness is prioritized over speed
-  Manual/interactive research sessions
- L High-frequency automated queries
- L Real-time applications

## Best Practices

### 1. **Choose Appropriate Depth**
```python
# For quick validation
search_request = SearchRequest(query="product exists?", search_depth="basic")

# For standard research  
search_request = SearchRequest(query="product specifications", search_depth="standard")

# For comprehensive analysis
search_request = SearchRequest(query="detailed technical analysis", search_depth="extensive")
```

### 2. **Consider Performance Impact**
- Use BASIC for high-frequency queries
- Use STANDARD as default for most cases
- Reserve EXTENSIVE for when thoroughness is essential

### 3. **Monitor Resource Usage**
- Track response times across different depths
- Consider caching for EXTENSIVE searches
- Implement timeout handling for comprehensive searches

### 4. **Validate Results Quality**
- BASIC may miss important reference materials
- STANDARD provides good coverage for most cases
- EXTENSIVE may include some lower-relevance links

## Error Handling

Search depth validation occurs at the model level:

```python
# Valid values
valid_depths = ["basic", "standard", "extensive"]

# Invalid depth will raise validation error
try:
    request = SearchRequest(query="test", search_depth="invalid")
except ValueError as e:
    print(f"Invalid search depth: {e}")
```

## Configuration Examples

### Production Configuration
```python
# Default production setup
config = {
    "search_depth": "standard",  # Balanced performance
    "max_results": 10,
    "enable_content_extraction": True
}
```

### Research Configuration  
```python
# Comprehensive research setup
config = {
    "search_depth": "extensive",  # Maximum thoroughness
    "max_results": 10,
    "enable_content_extraction": True,
    "max_concurrent_extractions": 5  # Lower concurrency for complex processing
}
```

### High-Performance Configuration
```python
# Speed-optimized setup
config = {
    "search_depth": "basic",     # Minimal processing
    "max_results": 5,            # Fewer results
    "enable_content_extraction": False  # Skip content extraction
}
```

## Integration Notes

### With Content Processor
Search depth affects the content that gets processed:
- BASIC: Only main search results
- STANDARD: Main results + up to 5 reference sources
- EXTENSIVE: Main results + up to 15 reference sources

### With Result Scoring
Reference links contribute to overall result quality:
- More reference links = better cross-validation
- Higher relevance scores = more authoritative sources
- Enhanced scoring in EXTENSIVE mode finds more marginal but relevant content

## Monitoring and Debugging

### Logging Output Examples

```bash
# BASIC depth
=Ë Skipping reference extraction for basic search depth

# STANDARD depth  
= Found 3 relevant links from 45 total links

# EXTENSIVE depth
= Extracting reference links from: https://example.com (depth: extensive)
= Found 12 relevant links from 67 total links
```

### Performance Metrics to Track
- Average response time by depth
- Reference link extraction success rate
- Content extraction completion rate
- Memory usage patterns
- Error rates by depth level

---

**Last Updated**: 2025-01-11  
**Module Version**: Google Web Search v1.0  
**Related Files**: 
- `search_engine.py` - Query optimization
- `reference_extractor.py` - Link extraction logic
- `core/models.py` - SearchRequest and SearchDepth definitions