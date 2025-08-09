# Dana Product Search - Consolidated Version

A streamlined, self-contained product search example demonstrating Dana's agent-native programming capabilities.

## Overview

This consolidated version eliminates Python dependencies and showcases pure Dana implementation of an intelligent product search system with:

- **Query Enhancement**: Uses `reason()` to extract structured information from user queries
- **Dual Search Strategy**: Combines part number matching with vector similarity search
- **Intelligent Ranking**: LLM-powered result ranking with confidence scoring
- **Self-Contained**: No external databases required - uses embedded CSV data

## Architecture

### Files Structure
```
11_single_search/
├── search.na              # Main consolidated implementation
├── config.na              # Configuration constants and settings
├── prompts.na             # Separated LLM prompts
├── data/
│   └── sample_products.csv # Sample product data
└── README.md              # This documentation
```

### Key Dana Features Demonstrated

1. **Agent-Native Programming**: Uses `reason()` for context-aware intelligence
2. **Resource Management**: `use()` for tabular_index data access
3. **Struct-Based Configuration**: Type-safe config using Dana structs
4. **Modular Prompts**: Separated prompt functions for easy tuning

## Usage

### Basic Usage
```dana
# Run the main demo
main()

# Test individual components  
test_enhancement()     # Test query enhancement
test_search()          # Test search functionality
test_full_pipeline()   # Test complete pipeline

# Direct access to configuration
from config import SEARCH_CONFIG, MODEL_CONFIG, DATA_CONFIG
print(f"Max results: {SEARCH_CONFIG.max_results}")
```

### Search Examples
```dana
product_search("Subaru sedan brake pads")
product_search("Honda oil filter")
product_search("LED headlight bulbs")
```

## Configuration

Edit `config.na` struct default values to modify:
```dana
struct SearchConfig:
    max_results: int = 5                    # Change this value
    confidence_threshold: float = 0.7       # 0.0-1.0 range
    part_search_limit: int = 3
    vector_search_limit: int = 3
    use_weighted_terms: bool = true
```

## Prompt Tuning

Edit `prompts.na` to customize:
- **Enhancement prompts**: Modify query analysis logic
- **Ranking prompts**: Adjust product matching criteria

## Sample Data

The `data/sample_products.csv` contains automotive parts with columns:
- `product_name`: Product description
- `mfr_part_num`: Manufacturer part number
- `mfr_brand`: Brand/manufacturer
- `source_category`: Product category
- `data_source`: Origin source identifier

## Benefits Over Original

1. **Pure Dana**: No Python dependencies - showcases Dana capabilities
2. **Simplified**: 4 files vs 10+ in original multi-stage version
3. **Self-Contained**: Embedded data vs external PostgreSQL requirement
4. **Educational**: Clear Dana patterns and best practices
5. **Maintainable**: Clean separation of config, prompts, and logic

## Extension Ideas

- Add more sophisticated part number matching patterns
- Implement category-based filtering
- Add price and availability data
- Create domain-specific search strategies
- Implement fuzzy string matching for product names

This example demonstrates Dana's power for building intelligent, self-improving systems with clean, maintainable code.
