# Product Search System Design

## Architecture Overview

The product search system implements a **4-stage intelligent pipeline** that transforms natural language queries into ranked product results using Dana's agent-native capabilities.

```
User Query → Enhancement → Search → Ranking → Response
     ↓           ↓          ↓         ↓         ↓
  "brake pads" → Structured → Results → Best Match → Confident Result
```

## Core Features

### 1. Query Enhancement
**Module**: `query_enhancement.na`
- **Purpose**: Extract structured information from natural language
- **Technology**: Dana `reason()` with specialized prompts
- **Output**: Refined query, weighted keywords, part numbers

**Example Transformation**:
```
Input:  "Subaru sedan brake pads"
Output: {
  "refined_query": "Subaru sedan brake pads",
  "most_weighted_keyword": "brake pads", 
  "mfr_part_num": ""
}
```

### 2. Dual Search Strategy  
**Module**: `product_search.na`
- **Part Number Search**: Exact matching for precise part lookups
- **Vector Similarity**: Semantic search for fuzzy matching
- **Data Source**: CSV via Dana `tabular_index` resource
- **Deduplication**: Part number-based result consolidation

### 3. AI-Powered Ranking
**Module**: `result_ranking.na`  
- **Technology**: Dana `reason()` for intelligent selection
- **Criteria**: Product type relevance, brand matching, specification alignment
- **Output**: Confidence scores, best match selection, reasoning

### 4. Result Assembly
**Module**: `data_access.na`
- **Standardization**: Consistent result format across search types
- **Metadata**: Search strategy, confidence levels, data sources
- **Performance**: Processing time tracking

## Component Details

### Configuration System
**File**: `config.na`
- **Struct-Based**: Type-safe configuration with Dana structs
- **Separation**: Model, search, data, and vector store configs
- **Modularity**: Independent configuration constructors

### Prompt Engineering
**File**: `prompts.na`
- **Enhancement Prompts**: Query analysis and normalization
- **Ranking Prompts**: Product matching and confidence scoring
- **Maintainability**: Separated from business logic for easy tuning

### Data Management
- **Source**: `sample_products.csv` with automotive parts
- **Fields**: product_name, mfr_part_num, mfr_brand, source_category, data_source
- **Access**: Dana `tabular_index` for embedding and retrieval

## Search Flow

### Stage 1: Query Enhancement
1. Receive natural language query
2. Apply enhancement prompt via `reason()`
3. Extract: refined query, keywords, part numbers
4. Return structured context object

### Stage 2: Product Search  
1. Initialize `tabular_index` with CSV data
2. **If part number exists**: Direct part number search
3. **Always**: Vector similarity search with enhanced query
4. Merge and deduplicate results

### Stage 3: Ranking & Selection
1. Format results for ranking prompt
2. Apply ranking logic via `reason()`
3. Validate confidence against threshold
4. Select best match if confidence sufficient

### Stage 4: Response Assembly
1. Combine search results with ranking decision  
2. Add metadata (processing time, confidence, reasoning)
3. Return comprehensive response object

## Key Design Decisions

### Modular Architecture
- **Separation of Concerns**: Each module handles single responsibility
- **Testability**: Independent testing of components  
- **Maintainability**: Focused files reduce complexity
- **Reusability**: Components can be used in other systems

### Dana-Native Implementation
- **No Python Dependencies**: Pure Dana showcasing language capabilities
- **Agent-Native Patterns**: `reason()`, `use()`, struct configs
- **Resource Management**: Proper resource lifecycle management
- **Type Safety**: Explicit type hints and structured data

### Configuration Strategy
- **Struct-Based**: Type-safe, IDE-friendly configuration
- **Layered**: Model, search, data separation
- **Extensible**: Easy addition of new configuration categories

### Error Handling Philosophy
- **Graceful Degradation**: System continues with reduced functionality
- **Transparent Failures**: Clear error messages and fallback strategies
- **Confidence-Based**: Quality gating via confidence thresholds

## Performance Characteristics

- **Latency**: ~2-3 seconds for complete pipeline (includes 2 LLM calls)
- **Throughput**: Limited by LLM API rate limits  
- **Memory**: Minimal - CSV data loaded via tabular_index
- **Scalability**: Horizontal via stateless design

## Extension Points

1. **Search Strategies**: Add fuzzy matching, category filters
2. **Ranking Algorithms**: Implement learning-based ranking
3. **Data Sources**: Support multiple data formats and sources  
4. **Caching**: Add intelligent caching for frequently queried items
5. **Feedback Loop**: Implement user feedback for continuous improvement

This design balances simplicity with functionality, demonstrating Dana's capabilities while maintaining clean, maintainable architecture.
