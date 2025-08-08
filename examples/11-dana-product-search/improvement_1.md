# Product Search Architecture Refactor Plan

## Current State Analysis

### 🔍 **Current Issues**
1. **Monolithic main() function** - 100+ lines with mixed concerns
2. **No clear data flow visualization** - hard to follow the pipeline
3. **Mixed abstraction levels** - low-level operations mixed with high-level orchestration
4. **Configuration scattered** - some hardcoded values, some in config files
5. **Limited reusability** - difficult to run individual pipeline stages
6. **Poor debugging experience** - all-or-nothing execution
7. **Junior analyst barriers** - requires understanding entire codebase to make simple changes

### 🎯 **Target Architecture Goals**
1. **Declarative Pipeline** - Clear, readable data flow using Dana pipes
2. **Modular Stages** - Each pipeline step as independent, testable function
3. **Configuration-Driven** - All tunable parameters centralized and documented
4. **Self-Documenting** - Code structure explains the business logic
5. **Junior-Friendly** - Easy to modify prompts, tune parameters, add logging
6. **Debugging-Friendly** - Run individual stages, inspect intermediate results

## Proposed Refactor Architecture

### 📁 **New File Structure**
```
examples/11-dana-product-search/
├── pipeline.na               # Main entry point with declarative pipeline
├── stages/
│   ├── enhance.na           # Query enhancement stage
│   ├── part_search.na       # Part number search stage  
│   ├── vector_search.na     # Vector similarity search stage
│   ├── extract_related.na   # Related result extraction stage
│   ├── merge_results.na     # Result merging and deduplication
│   ├── rank_results.na      # LLM ranking stage
│   └── assemble_response.na # Final response assembly
├── config/
│   ├── settings.na          # All tunable parameters
│   ├── prompts.na           # All LLM prompts (existing, enhanced)
│   └── data_sources.na      # Data source configurations
├── py/                      # Python modules (existing, enhanced)
│   ├── standardize.py       # Result standardization (existing)
│   ├── part_search_bridge.py # Part search bridge (existing)
│   └── utils.py             # Common utilities
└── docs/
    ├── analyst_guide.md     # Junior analyst tuning guide
    └── architecture.md      # Technical architecture docs
```

### 🔄 **Pipeline Flow Using Dana Pipes**

**Target Syntax (Declarative & Readable):**
```dana
def product_search(query: str) -> dict:
    return query 
        | enhance_query
        | search_parts_if_needed  
        | search_vectors
        | extract_related_results
        | merge_and_dedupe
        | rank_with_llm
        | assemble_final_response
```

### 🧩 **Individual Stage Design**

#### **1. Enhanced Query Stage (`stages/enhance.na`)**
```dana
from config.prompts import get_enhancement_prompt
from config.settings import get_enhancement_settings

def enhance_query(query: str) -> dict:
    settings = get_enhancement_settings()
    prompt = get_enhancement_prompt(query, settings)
    
    enhanced = reason(prompt, format="json") or fallback_enhancement(query)
    
    return {
        "original_query": query,
        "enhanced": enhanced,
        "settings_used": settings
    }

def fallback_enhancement(query: str) -> dict:
    return {
        "refined_query": query,
        "most_weighted_keyword": "",
        "mfr_part_num": ""
    }
```

#### **2. Conditional Part Search (`stages/part_search.na`)**
```dana
import part_search_bridge.py as bridge
from config.settings import get_part_search_settings

def search_parts_if_needed(context: dict) -> dict:
    settings = get_part_search_settings()
    enhanced = context["enhanced"]
    mfr_part_num = enhanced.get("mfr_part_num", "")
    
    if mfr_part_num == "":
        return context | {"part_results": [], "part_search_used": false}
    
    results = bridge.part_search_smart(mfr_part_num, settings["limit"])
    
    return context | {
        "part_results": results,
        "part_search_used": true,
        "part_strategy": results.get("strategy_used", "none")
    }
```

#### **3. Vector Search Stage (`stages/vector_search.na`)**
```dana
from config.data_sources import get_vector_index
from config.settings import get_vector_search_settings

def search_vectors(context: dict) -> dict:
    settings = get_vector_search_settings()
    enhanced = context["enhanced"]
    
    search_query = build_search_query(enhanced, settings)
    index = get_vector_index()
    
    vector_results = index.retrieve(search_query, top_k=settings["top_k"])
    
    return context | {
        "vector_results": vector_results,
        "search_query_used": search_query,
        "vector_settings": settings
    }

def build_search_query(enhanced: dict, settings: dict) -> str:
    refined = enhanced.get("refined_query", "")
    weighted = enhanced.get("most_weighted_keyword", "")
    
    if settings["use_weighted_terms"] and weighted:
        return f"{refined} {weighted}"
    return refined
```

### 📊 **Configuration System (`config/settings.na`)**
```dana
def get_pipeline_settings() -> dict:
    return {
        "enhancement": get_enhancement_settings(),
        "part_search": get_part_search_settings(), 
        "vector_search": get_vector_search_settings(),
        "ranking": get_ranking_settings(),
        "general": get_general_settings()
    }

def get_enhancement_settings() -> dict:
    return {
        "model": "openai:gpt-4.1-mini",
        "temperature": 0.1,
        "max_retries": 2,
        "fallback_enabled": true
    }

def get_vector_search_settings() -> dict:
    return {
        "top_k": 3,
        "use_weighted_terms": true,
        "similarity_threshold": 0.7,
        "max_results": 5
    }

def get_ranking_settings() -> dict:
    return {
        "model": "openai:gpt-4.1-mini", 
        "temperature": 0.2,
        "confidence_threshold": 0.5,
        "explanation_required": true
    }
```

### 🎨 **Main Pipeline (`pipeline.na`)**
```dana
from stages.enhance import enhance_query
from stages.part_search import search_parts_if_needed
from stages.vector_search import search_vectors
from stages.extract_related import extract_related_results
from stages.merge_results import merge_and_dedupe
from stages.rank_results import rank_with_llm
from stages.assemble_response import assemble_final_response
from config.settings import get_pipeline_settings
from time.py import time

def product_search(query: str) -> dict:
    start_time = time()
    settings = get_pipeline_settings()
    
    result = query 
        | enhance_query
        | search_parts_if_needed  
        | search_vectors
        | extract_related_results
        | merge_and_dedupe
        | rank_with_llm
        | assemble_final_response
    
    return result | {"processing_time": time() - start_time, "settings": settings}

def main():
    query = "Subaru sedan with good fuel economy"  # TODO: Make configurable
    response = product_search(query)
    
    print("=== PRODUCT SEARCH RESULT ===")
    print(f"Query: {response['original_query']}")
    print(f"Best Match: {response['best_match']['product_name']}")
    print(f"Confidence: {response['best_match']['confidence_score']:.2f}")
    print(f"Processing Time: {response['processing_time']:.2f}s")
    
    return response

main()
```

## Benefits of This Architecture

### 🎯 **For Junior Data Analysts**
1. **Easy Prompt Tuning** - All prompts in `config/prompts.na` with clear documentation
2. **Parameter Adjustment** - All tunable values in `config/settings.na` 
3. **Individual Stage Testing** - Run each pipeline stage independently
4. **Clear Data Flow** - Pipe syntax shows exactly how data flows
5. **Self-Documenting** - Function names and structure explain the process

### 🔧 **For Developers**
1. **Modular Testing** - Test each stage in isolation
2. **Easy Extension** - Add new stages without touching existing code
3. **Debugging** - Insert logging/inspection at any pipe stage
4. **Reusability** - Stages can be reused in different pipelines
5. **Maintainability** - Small, focused modules vs. monolithic code

### ⚡ **For Operations**
1. **Configuration Management** - Centralized, version-controlled settings
2. **Performance Tuning** - Easy to adjust timeouts, limits, thresholds
3. **Data Source Swapping** - Change data sources without code changes
4. **A/B Testing** - Easy to compare different configurations

## Implementation Plan

### Phase 1: Core Refactor
1. Create new file structure
2. Extract individual pipeline stages
3. Implement pipe-based main pipeline
4. Migrate existing functionality

### Phase 2: Configuration Enhancement  
1. Centralize all settings
2. Create comprehensive prompt management
3. Add data source configuration
4. Document all tunable parameters

### Phase 3: Junior Analyst Experience
1. Create analyst guide documentation
2. Add parameter validation and helpful errors
3. Create example configuration variations
4. Add debug/inspection utilities

### Phase 4: Advanced Features
1. Add pipeline caching
2. Implement A/B testing framework
3. Add performance monitoring
4. Create configuration UI/tools

## Migration Strategy

1. **Maintain backwards compatibility** - Keep existing `product_search.na` working
2. **Parallel development** - Build new architecture alongside existing code
3. **Gradual migration** - Move stages one by one to new architecture
4. **Comprehensive testing** - Ensure identical results before switching
5. **Documentation first** - Create analyst guide before final migration

This refactor transforms the codebase from a **monolithic script** into a **professional, maintainable architecture** that empowers junior analysts to confidently tune and extend the system.
