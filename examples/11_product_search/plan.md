# Consolidation Plan: Dana Product Search - Compact Version

## Executive Summary

This plan outlines the consolidation of the multi-stage `11-dana-product-search-v2` example into a streamlined, self-contained version in `11_single_search` that eliminates Python dependencies and embraces pure Dana programming patterns.

## Understanding the Current Architecture

### What is Dana?
Dana is an **agent-native programming language** that bridges AI development with autonomous execution through:
- **Agent-first design**: `agent` primitives instead of classes
- **Context-aware reasoning**: `reason()` calls that adapt output types automatically
- **Self-improving pipelines**: Functions that learn through POET in production
- **Transparent execution**: Every step is visible and debuggable
- **Built-in AI integration**: First-class LLM integration with structured reasoning

### Current Example Analysis
The `11-dana-product-search-v2` example implements a **4-stage product search pipeline**:

1. **Query Enhancement** (`stages/enhance.na`) - Uses `reason()` to extract structured information from user queries
2. **Product Search** (`stages/search.na`) - Combines part number search + vector similarity search  
3. **Result Ranking** (`stages/rank.na`) - Uses `reason()` to intelligently rank and select best matches
4. **Response Assembly** (`stages/result.na`) - Formats final response with metadata

**Key Dependencies to Remove:**
- `py/part_search_bridge.py` - Python-based database part number search
- `py/standardize.py` - Python-based result formatting and standardization
- Complex configuration system with multiple files
- External database dependencies

## Consolidation Goals

### Primary Objectives
1. **Eliminate Python Dependencies**: Replace all `py/` module imports with pure Dana implementations
2. **Simplify Architecture**: Reduce from 4 separate stage files to 1-2 focused files
3. **Self-Contained Operation**: Remove external database requirements where possible
4. **Preserve Core Functionality**: Maintain the intelligent query enhancement and ranking capabilities
5. **Embrace Dana Patterns**: Use native Dana features like `reason()`, `use()`, and resource management

### Secondary Objectives
1. **Improve Maintainability**: Reduce complexity while preserving functionality
2. **Better Documentation**: Clear inline documentation for Dana-specific patterns
3. **Enhanced Testability**: Simple functions that can be tested individually
4. **Educational Value**: Serve as a clean example of Dana best practices

## Proposed Architecture

### File Structure (Streamlined)
```
examples/11_single_search/
├── search.na              # Main search implementation (consolidated)
├── config.json            # Configuration settings (JSON format)
├── prompts.na             # LLM prompts separated for easy tuning
├── data/
│   └── sample_products.csv # Embedded test product data
└── plan.md                # This document
```

### Core Design Principles

#### 1. Pure Dana Implementation
Replace Python bridge functions with native Dana capabilities:
- Use Dana's `use()` resource system for data access
- Leverage `reason()` for intelligent processing
- Implement standardization logic directly in Dana

#### 2. Simplified Data Flow
```
User Query → Enhancement (reason) → Search (native) → Ranking (reason) → Response
```

#### 3. Self-Contained Search Logic
Instead of external database dependency:
- Use embedded test data or CSV files via `tabular_index`
- Implement simplified part number matching in Dana
- Focus on the AI-enhanced search and ranking logic

#### 4. Consolidated Functions
Merge related functionality:
- Combine search strategies into unified functions
- Integrate result standardization with search logic
- Streamline configuration into single source

## Implementation Strategy

### Phase 1: Core Search Function (Priority 1)
Create `search.na` with:
```dana
def product_search(query: str) -> dict:
    # Step 1: Query Enhancement with reason()
    enhanced = enhance_query(query)
    
    # Step 2: Search with native Dana
    results = search_products(enhanced)
    
    # Step 3: Intelligent ranking with reason()
    ranked = rank_results(query, results)
    
    return ranked
```

### Phase 2: Native Data Access (Priority 2)
Replace Python database bridge with:
- Dana `tabular_index` for CSV-based product data
- Simple in-memory product database for demonstration
- Native Dana string matching and filtering

### Phase 3: Enhanced AI Integration (Priority 3)
Optimize Dana-specific features:
- Context-aware `reason()` calls with proper type hints
- Structured prompt engineering for consistent outputs
- Error handling and fallback strategies

### Phase 4: Configuration Simplification (Priority 4)
Consolidate configuration:
- Single `config.na` file with essential settings
- Embed prompts directly in functions for clarity
- Remove unnecessary abstraction layers

## Key Implementation Details

### 1. Query Enhancement (Pure Dana)
```dana
from prompts import get_enhancement_prompt

def enhance_query(query: str) -> dict:
    prompt = get_enhancement_prompt(query)
    enhanced: dict = reason(prompt)
    
    return {
        "original_query": query,
        "enhanced": enhanced
    }
```

### 2. Native Search Implementation
```dana
def search_products(context: dict) -> list:
    search_config = get_search_config()
    data_config = get_data_config()
    enhanced = context["enhanced"]
    
    # Initialize tabular_index with CSV data
    tabular_index_config = {
        "source": data_config["csv_file_path"],
        "force_reload": data_config["force_reload"],
        "cache_dir": data_config["cache_dir"]
    }
    product_data = use("tabular_index", tabular_index_config=tabular_index_config)
    
    results = []
    
    # Part number search (if available)
    if enhanced.get("mfr_part_num"):
        part_results = search_by_part_number(
            enhanced["mfr_part_num"], 
            product_data, 
            search_config["part_search_limit"]
        )
        results.extend(part_results)
    
    # Vector similarity search
    search_query = build_search_query(enhanced, search_config)
    vector_results = product_data.retrieve(
        search_query, 
        top_k=search_config["vector_search_limit"]
    )
    results.extend(standardize_vector_results(vector_results))
    
    return dedupe_results(results, search_config["max_results"])
```

### 3. Intelligent Ranking (Enhanced Dana)
```dana
from prompts import get_ranking_prompt

def rank_results(query: str, results: list) -> dict:
    search_config = get_search_config()
    
    if not results:
        return {
            "query": query,
            "best_match": None,
            "total_results": 0,
            "confidence": 0.0
        }
    
    formatted = format_results_for_ranking(results)
    prompt = get_ranking_prompt(query, formatted)
    
    ranking: dict = reason(prompt)
    
    # Validate confidence against threshold
    confidence = ranking.get("confidence_score", 0.0)
    meets_threshold = confidence >= search_config["confidence_threshold"]
    
    return {
        "query": query,
        "results": results,
        "best_match": results[ranking["item_index"] - 1] if meets_threshold else None,
        "total_results": len(results),
        "confidence": confidence,
        "meets_threshold": meets_threshold,
        "reasoning": ranking.get("notes", "")
    }
```

### 4. Improved Configuration Architecture

#### JSON Configuration (`config.json`)
```json
{
  "model": {
    "provider": "openai:gpt-4o-mini",
    "temperature": 0.1,
    "max_tokens": 1000
  },
  "search": {
    "max_results": 5,
    "confidence_threshold": 0.7,
    "part_search_limit": 3,
    "vector_search_limit": 3,
    "use_weighted_terms": true
  },
  "data": {
    "csv_file_path": "data/sample_products.csv",
    "cache_dir": ".cache/single_search",
    "force_reload": false
  },
  "debug": {
    "enabled": false,
    "log_level": "info"
  }
}
```

#### Configuration Loading in Dana (`search.na`)
```dana
# Load configuration as a default struct/constant
CONFIG = use("json", file="config.json")

def get_search_config() -> dict:
    return CONFIG["search"]

def get_model_config() -> dict:
    return CONFIG["model"]

def get_data_config() -> dict:
    return CONFIG["data"]
```

#### Separated Prompts (`prompts.na`)
```dana
def get_enhancement_prompt(query: str) -> str:
    return f"""You are a query enhancement specialist for product searches.

Extract structured information from user queries for database search optimization.

ANALYSIS REQUIREMENTS:
1. REFINED QUERY: Normalize technical terms and measurements
   - Replace " with "in" (inches), ' with "ft" (feet)  
   - Expand abbreviations (WD → WD-40, SS → stainless steel)
   - Keep all original specifications

2. MOST WEIGHTED KEYWORD: Primary product type
   - Specific part names (e.g., "brake pad", "spark plug")
   - Product categories (e.g., "sensor", "filter")
   - Brand names only if no product type exists

3. MFR_PART_NUM: Extract manufacturer part numbers/model codes

USER QUERY: {query}

Return ONLY valid JSON: {{"refined_query": "", "most_weighted_keyword": "", "mfr_part_num": ""}}"""

def get_ranking_prompt(query: str, formatted_results: str) -> str:
    return f"""You are an expert product matching specialist.

Select the best match from search results based on query relevance.

SCORING PRINCIPLES:
- Product type match is critical
- Consider part numbers, brands, specs only if mentioned in query
- Don't penalize for extra features not requested

USER QUERY: {query}

SEARCH RESULTS:
{formatted_results}

Return ONLY JSON: {{"item_index": 1, "confidence_score": 0.90, "notes": "reasoning"}}"""
```

## Benefits of This Approach

### For Dana Language Showcase
1. **Pure Dana Implementation**: Demonstrates Dana's capabilities without Python crutches
2. **Agent-Native Patterns**: Shows proper use of `reason()`, `use()`, and resource management
3. **Simplified Mental Model**: Easy to understand and modify for learning Dana

### For Practical Usage
1. **Reduced Dependencies**: No external Python modules or databases required
2. **Self-Contained**: Can run immediately with Dana installation
3. **Educational**: Clear example of AI-enhanced search in pure Dana
4. **Extensible**: Easy to add new features or modify behavior

### For Maintenance
1. **Single Language**: No context switching between Dana and Python
2. **Fewer Files**: Consolidated logic reduces complexity
3. **Native Debugging**: Use Dana's built-in debugging capabilities
4. **Clear Data Flow**: Easier to trace execution and identify issues

## Testing Strategy

### Simple Test Functions
```dana
def test_enhancement():
    result = enhance_query("Phillips screwdriver IRDV-BA/CA 1/4in")
    print(f"Enhancement result: {result}")
    return result

def test_search():
    enhanced = enhance_query("automotive brake pad")
    results = search_products(enhanced)
    print(f"Search found {len(results)} results")
    return results

def test_full_pipeline():
    return product_search("Subaru sedan brake pads")
```

### Data Requirements
- Small embedded CSV file with sample product data including columns:
  - `product_name`: Description of the product
  - `mfr_part_num`: Manufacturer part number
  - `mfr_brand`: Brand/manufacturer name
  - `source_category`: Product category
  - `data_source`: Origin of the data (e.g., "supplier_catalog", "manufacturer_db", "parts_database")
- Focus on automotive parts to match current test queries
- Include varied part numbers, brands, and categories for comprehensive testing

## Migration Steps

1. **Create base structure** in `11_single_search/`
   - Create `search.na` (main implementation)
   - Create `prompts.na` (separated prompt functions)
   - Create `config.json` (JSON configuration)
   - Create `data/` directory with sample CSV

2. **Extract and consolidate core logic**
   - Move enhancement logic from `stages/enhance.na`
   - Combine search logic from `stages/search.na` 
   - Integrate ranking from `stages/rank.na`
   - Merge result assembly from `stages/result.na`

3. **Replace Python dependencies**
   - Remove `py/part_search_bridge.py` dependency
   - Replace `py/standardize.py` with native Dana functions
   - Implement part number search using `tabular_index` filtering

4. **Implement configuration system**
   - Use `use("json", file="config.json")` for settings
   - Separate prompts into `prompts.na` for easy tuning
   - Load configuration as default struct/constant

5. **Test and validate**
   - Create simple test functions for each component
   - Validate against original functionality
   - Test with sample automotive parts data

6. **Documentation and examples**
   - Add inline documentation for Dana patterns
   - Create usage examples and test functions
   - Document configuration options

## Success Criteria

- [ ] Runs entirely in Dana without Python dependencies
- [ ] Provides equivalent search functionality to original
- [ ] Uses native Dana features (reason, use, resources)
- [ ] Self-contained with embedded test data
- [ ] Clear, maintainable code structure
- [ ] Comprehensive inline documentation
- [ ] Simple test functions for validation
- [ ] Serves as good Dana programming example

This consolidation will result in a clean, educational, and practical example of Dana's capabilities for AI-enhanced product search, while removing complexity and external dependencies.
