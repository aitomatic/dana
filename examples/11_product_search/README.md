# Dana Product Search Example

A modular, intelligent product search system demonstrating Dana's agent-native programming capabilities with AI-enhanced query processing and ranking.

## What It Does

This example showcases a **4-step intelligent search pipeline** that transforms natural language queries into precise product matches:

1. **Query Enhancement**: Uses `reason()` to extract structured information (part numbers, keywords, specifications)
2. **Dual Search**: Combines exact part number matching with vector similarity search  
3. **AI Ranking**: LLM-powered result selection with confidence scoring
4. **Response Assembly**: Returns best match with reasoning and metadata

**Example Query**: `"Subaru sedan brake pads"` → Finds specific brake pad products for Subaru sedans with confidence scores and detailed reasoning.

## Features

- **Agent-Native Design**: Uses Dana's `reason()` for context-aware intelligence
- **Modular Architecture**: Clean separation of concerns across focused modules
- **Self-Contained**: No external databases - uses embedded CSV data via `tabular_index`
- **Configurable**: Easily adjust search parameters, confidence thresholds, and prompts
- **Educational**: Clear demonstration of Dana best practices and patterns

## Quick Start

### Run the Example
```bash
./bin/dana examples/11_product_search/search.na
```

### Test Individual Components
```bash
# Test query enhancement only
./bin/dana -c "from examples.11_product_search.modules.query_enhancement import enhance_query; print(enhance_query('brake pads'))"

# Test search functionality  
./bin/dana -c "from examples.11_product_search.search import test_search; test_search()"

# Test full pipeline
./bin/dana -c "from examples.11_product_search.search import test_full_pipeline; test_full_pipeline()"
```

## File Structure

```
examples/11_product_search/
├── search.na                   # Main orchestrator (79 lines)
├── modules/
│   ├── query_enhancement.na    # Query processing with LLM
│   ├── product_search.na       # Search implementation  
│   ├── result_ranking.na       # AI-powered ranking
│   └── data_access.na         # Data utilities
├── config.na                  # Configuration structs
├── prompts.na                 # LLM prompts
├── data/sample_products.csv   # Sample automotive parts data
└── README.md                  # This file
```

## Configuration

Edit values in `config.na`:

```dana
struct SearchConfig:
    max_results: int = 5                    # Maximum results returned
    confidence_threshold: float = 0.7       # Minimum confidence for best match
    part_search_limit: int = 3              # Part number search limit
    vector_search_limit: int = 15           # Vector similarity limit
    use_weighted_terms: bool = true         # Use keyword weighting
```

## Example Usage

```dana
# Basic search
response = product_search("Honda oil filter")

# Check results
print(f"Found {response['total_results']} results")
print(f"Confidence: {response['confidence']}")
if response['best_match']:
    print(f"Best: {response['best_match']['product_name']}")
    print(f"Part#: {response['best_match']['mfr_part_num']}")
```

## Sample Queries

- `"Subaru sedan brake pads"` - Specific vehicle and part type
- `"LED headlight bulbs"` - Generic part category  
- `"Honda Civic brake pads"` - Vehicle model specific
- `"Phillips screwdriver IRDV-BA/CA"` - Part number extraction

## Key Dana Patterns Demonstrated

1. **Modular Imports**: Clean module organization with focused responsibilities
2. **Context-Aware Reasoning**: `reason()` calls that adapt based on context
3. **Resource Management**: `use("tabular_index")` for data access
4. **Struct Configuration**: Type-safe configuration management
5. **Pipeline Composition**: Orchestrated function composition
