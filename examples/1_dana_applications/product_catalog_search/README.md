# Dana Product Search Use Case - Complete Tutorial

This tutorial provides a comprehensive step-by-step guide for understanding and running the Dana Product Search example, which demonstrates an intelligent 4-stage search pipeline using Dana's agent-native programming capabilities. It includes both practical usage instructions and deep technical insights into how the `tabular_index` resource works internally.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Understanding the Architecture](#understanding-the-architecture)
4. [File Structure](#file-structure)
5. [Configuration Setup](#configuration-setup)
6. [Running the Example](#running-the-example)
7. [Understanding the Code](#understanding-the-code)
8. [Testing Individual Components](#testing-individual-components)
9. [Technical Deep Dive: How tabular_index Works](#technical-deep-dive-how-tabular_index-works)
10. [Customization Guide](#customization-guide)
11. [Troubleshooting](#troubleshooting)

## Overview

The Dana Product Search system transforms natural language queries into precise product matches using a **4-stage intelligent pipeline**:

1. **Query Enhancement**: Extract structured information using `reason()`
2. **Dual Search**: Combine exact part number matching with vector similarity search
3. **AI Ranking**: LLM-powered result selection with confidence scoring
4. **Response Assembly**: Return best match with reasoning and metadata

### Example Flow
```
"Subaru sedan brake pads" → Enhanced Query → Search Results → Best Match → Final Response
```

## Prerequisites

Before running this example, ensure you have:

1. **Dana Framework**: Installed and configured
2. **LLM Access**: OpenAI API key
3. **Python Environment**: Python 3.8+ (for time utilities)
4. **Data Files**: Sample product CSV data (included)

### Environment Setup

```bash
# Navigate to the workspace
cd /Users/hungvu/Workspace/dana

# Ensure Dana environment is activated
source bin/activate_env.sh  # if using virtual environment

# Verify Dana installation
./bin/dana --version
```

## Understanding the Architecture

### Core Components

The system implements a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Query           │    │ Dual Search     │    │ AI Ranking      │    │ Response        │
│ Enhancement     │───▶│ (Part# + Vector)│───▶│ & Selection     │───▶│ Assembly        │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Technologies Used

- **Dana `reason()`**: AI-powered query enhancement and ranking
- **Dana `use("tabular_index")`**: Vector search and data access
- **Dana Structs**: Type-safe configuration management
- **Dana Workflows**: Functional pipeline composition

## File Structure

```
examples/11_product_search/
├── main.na                    # Single search entry point
├── main_batch.na             # Batch processing example
├── workflows.na              # Pipeline workflow definitions
├── methods.na                # Core functional methods
├── config.na                 # Configuration structs and defaults
├── common.na                 # Utility functions
├── prompts.na                # LLM prompts for enhancement and ranking
├── data/
│   ├── sample_products_15.csv   # Small dataset for testing
│   └── sample_products_1000.csv # Larger dataset for production
├── README.md                 # Basic usage information
├── design.md                 # Architecture documentation
└── TUTORIAL.md               # This comprehensive tutorial
```

## Configuration Setup

### 1. Understanding the Data Pipeline: CSV → tabular_index → Search

Before diving into configuration, it's essential to understand how data flows through the system:

```
CSV Data → tabular_index Resource → Vector Embeddings → Search Results
```

This pipeline involves three interconnected components that must be configured together:

#### **Step 1: Understanding CSV Data Structure**

The system works with two different CSV formats. Understanding this is crucial for proper configuration:

**Small Dataset (`sample_products_15.csv`):**
```csv
product_name,mfr_part_num,mfr_brand,source_category,data_source
"Subaru Legacy Brake Pads - Front","BP-SL-001","Subaru","Brake System","manufacturer_db"
"Automotive Brake Pad Set - Universal","BP-UNI-2024","AutoZone","Brake System","supplier_catalog"
```

**Large Dataset (`sample_products_1000.csv`):**
```csv
mfr_part_num,mfr,mfr_brand,mfr_desc_Short,mfr_desc_long,...,ProductName,...
M-5-PN-6-DN-LX-AQ-GCC-CUT REEL,Prysmian Group,Prysmian Group,,,...,"BL0061PNU-ClearCurve® OM4, Tight Buffer Distribution Plenum Cable, 6 Fiber, Aqua",...
```

**Key Differences:**
- **Small dataset**: Uses `product_name` column
- **Large dataset**: Uses `ProductName` column (note the capitalization!)

**Decide Critical Columns for Search:**
- `product_name` / `ProductName`: Main product description (used for vector embeddings)
- `mfr_part_num`: Manufacturer part number (for exact matching)
- `mfr_brand`: Brand/manufacturer name
- `source_category` / inferred category: Product category

#### **Step 2: tabular_index Configuration Functions**

In `config.na`, two critical functions define how CSV data is processed. **These must match your CSV column names exactly:**

```dana
# Tells tabular_index what text to embed for similarity search
def embedding_field_constructor(row: dict) -> str:
    return str(row.get("ProductName", ""))  # For sample_products_1000.csv
    # return str(row.get("product_name", ""))  # For sample_products_15.csv

# Defines what metadata to store with each embedding
def metadata_constructor(row: dict) -> dict:
    metadata = {
        "data_source": row.get("data_source", ""),
        "source_category": row.get("source_category", ""),
        "mfr_brand": row.get("mfr_brand", ""),
        "mfr_part_num": row.get("mfr_part_num", ""),
    }
    return metadata
```

**Critical Configuration Points:**

1. **Column Name Matching**: The `row.get("ProductName", "")` must exactly match your CSV header
2. **Embedding Field**: This determines what text gets converted to vector embeddings
3. **Metadata Storage**: This defines what additional information is stored with each embedding
4. **Missing Values**: The empty string `""` provides fallback for missing data

#### **Step 3: Complete tabular_index Configuration**

The `get_tabular_index_config()` function ties everything together:

```dana
def get_tabular_index_config() -> dict:
    return {
        "source": DATA_CONFIG.csv_file_path,           # Path to CSV file
        "force_reload": DATA_CONFIG.force_reload,       # Rebuild embeddings?
        "table_name": DATA_CONFIG.table_name,          # Unique identifier
        "cache_dir": DATA_CONFIG.cache_dir,            # Where to store embeddings
        "embedding_field_constructor": embedding_field_constructor,  # What to embed
        "metadata_constructor": metadata_constructor,   # What metadata to store
        "excluded_embed_metadata_keys": []             # Metadata keys to exclude from embedding
    }
```

### 2. Step-by-Step Configuration Process

#### **Step A: Choose Your Dataset**

Two datasets are provided:

```dana
# Option 1: Small dataset for testing (15 products)
DATA_CONFIG = DataConfig(
    csv_file_path="examples/11_product_search/data/sample_products_15.csv"
)

# Option 2: Larger dataset for production (1000 products)
DATA_CONFIG = DataConfig(
    csv_file_path="examples/11_product_search/data/sample_products_1000.csv"
)
```

#### **Step B: Configure Cache Behavior**

```dana
DATA_CONFIG = DataConfig(
    csv_file_path="examples/11_product_search/data/sample_products_15.csv",
    cache_dir=".cache/product_search",      # Where embeddings are stored
    force_reload=false,                     # Set to true to rebuild embeddings
    table_name="product_search_example"     # Unique identifier for this dataset
)
```

**Important Notes:**
- `force_reload=true`: Rebuilds embeddings (use when CSV data changes)
- `force_reload=false`: Uses cached embeddings (faster startup)
- `cache_dir`: Directory where vector embeddings are stored locally

#### **Step C: Configure for Your Dataset**

**For Small Dataset (15 products):**
```dana
# In config.na
DATA_CONFIG = DataConfig(
    csv_file_path="examples/11_product_search/data/sample_products_15.csv",
    force_reload=true  # First time setup
)

# Update embedding_field_constructor:
def embedding_field_constructor(row: dict) -> str:
    return str(row.get("product_name", ""))  # Note: lowercase
```

**For Large Dataset (1000 products) - Default:**
```dana
# In config.na (already configured)
DATA_CONFIG = DataConfig(
    csv_file_path="examples/11_product_search/data/sample_products_1000.csv",
    force_reload=false  # Use cached embeddings
)

# Current embedding_field_constructor:
def embedding_field_constructor(row: dict) -> str:
    return str(row.get("ProductName", ""))  # Note: PascalCase
```

**For Custom CSV Files:**
```dana
# Step 1: Analyze your CSV headers
# Step 2: Update DATA_CONFIG path
DATA_CONFIG = DataConfig(
    csv_file_path="path/to/your/products.csv",
    force_reload=true,  # Rebuild embeddings for new data
    table_name="your_custom_table_name"  # Unique identifier
)

# Step 3: Update column mapping functions
def embedding_field_constructor(row: dict) -> str:
    return str(row.get("your_product_column", ""))

def metadata_constructor(row: dict) -> dict:
    metadata = {
        "data_source": row.get("your_source_column", ""),
        "source_category": row.get("your_category_column", ""),
        "mfr_brand": row.get("your_brand_column", ""),
        "mfr_part_num": row.get("your_partnum_column", ""),
    }
    return metadata
```

#### **Step D: Understanding the tabular_index Resource Lifecycle**

When you run the search system, here's what happens with the tabular_index:

```
1. Check if cached embeddings exist in cache_dir
2. If force_reload=true OR no cache exists:
   a. Read CSV file
   b. Apply embedding_field_constructor to each row
   c. Generate vector embeddings using the LLM
   d. Apply metadata_constructor to each row
   e. Store embeddings + metadata in cache_dir
3. Load cached embeddings for search
```

**Important Timing:**
- **First run**: Takes 2-5 minutes to generate embeddings (depends on CSV size)
- **Subsequent runs**: Starts in seconds using cached embeddings
- **After CSV changes**: Set `force_reload=true` to regenerate

### 3. Key Configuration Structs

The system uses structured configuration with clear defaults:

```dana
# Model configuration
struct ModelConfig:
    model_name: str = "openai:gpt-4.1-mini"

# Search behavior configuration
struct SearchConfig:
    max_results: int = 5
    confidence_threshold: float = 0.7
    part_search_limit: int = 3
    vector_search_limit: int = 15
    use_weighted_terms: bool = true

# Data and caching configuration
struct DataConfig:
    csv_file_path: str = "examples/11_product_search/data/sample_products_1000.csv"
    cache_dir: str = ".cache/product_search"
    force_reload: bool = false
    table_name: str = "product_search_example"
```

### 2. Model Configuration


```dana
# In config.na, ensure:
MODEL_CONFIG = ModelConfig(model_name="openai:gpt-4.1-mini")
```

### 3. Data Configuration

The system uses the smaller dataset by default. To switch to the larger dataset:

```dana
# In config.na, modify DATA_CONFIG:
DATA_CONFIG = DataConfig(
    csv_file_path="examples/11_product_search/data/sample_products_1000.csv"
)
```

### 4. Environment Variables

Ensure your environment has necessary API keys:

```bash
# For OpenAI
export OPENAI_API_KEY="your-api-key-here"

# For other providers, set appropriate environment variables
```

## Running the Example

### 1. Basic Single Search

Run the main search example:

```bash
cd /Users/hungvu/Workspace/dana
./bin/dana examples/11_product_search/main.na
```

**Expected Output:**
```
=== DANA PRODUCT SEARCH RESULT ===
Query: Wire Mesh Cable Tray
Total Results: 5
Confidence Score: 0.85
Processing Time: 2.3s
Best Match: Industrial Wire Mesh Cable Tray - 12"
Part Number: WMT-12-IND
Brand: CableTech
Reasoning: Strong match for wire mesh cable tray with specific sizing and industrial grade specifications.
```

### 2. Batch Processing Example

For processing multiple queries simultaneously:

```bash
./bin/dana examples/11_product_search/main_batch.na
```

This will process the predefined batch of queries:
- "Ammonia Hydroxide concentrated x 500ml"
- "Fiberglass Wax"
- "Silicone Sealant"
- "Copper Wire 18 gauge"
- "LED Light Bulb 60W equivalent"

### 3. Custom Query Execution

To test with your own query:

```bash
# Modify the query in main.na
# Change line 13: query = "Your custom search term here"
# Then run: ./bin/dana examples/11_product_search/main.na
```

## Understanding the Code

### 1. Workflow Pipeline (`workflows.na`)

The core workflow is elegantly simple:

```dana
def product_search_workflow(query) =
    reserve_param as original_query |
    enhance_query |
    search_products as matched_products |
    rank_results(original_query, matched_products)
```

This functional pipeline:
1. Preserves the original query
2. Enhances the query for better search
3. Searches for matching products
4. Ranks and selects the best results

### 2. Query Enhancement (`methods.na`)

```dana
def enhance_query(query: str) -> EnhanceQueryResults:
    """Extract structured information from user query using LLM"""
    prompt = get_enhancement_prompt(query)
    enhanced: EnhanceQuery = reason(prompt)
    return EnhanceQueryResults(original_query=query, enhanced=enhanced)
```

**Key Features:**
- Normalizes technical terms and measurements
- Extracts manufacturer part numbers
- Identifies primary product keywords
- Uses structured prompts for consistent results

### 3. Product Search (`methods.na`)

The search combines two strategies:

```dana
def search_products(enhance_query: EnhanceQueryResults) -> list:
    # Initialize tabular_index
    product_data = use("tabular_index", tabular_index_config=tabular_index_config)

    # Part number search (exact matches)
    if enhanced_query.mfr_part_num:
        part_results = search_by_part_number(...)

    # Vector similarity search
    vector_results = product_data.retrieve(search_query, top_k=...)

    # Combine and deduplicate
    return dedupe_results(results, max_results)
```

### 4. AI-Powered Ranking (`methods.na`)

```dana
def rank_results(query: str, results: list) -> RankResults:
    formatted = format_results_for_ranking(results)
    prompt = get_ranking_prompt(query, formatted)
    ranking: Ranking = reason(prompt)

    # Validate confidence against threshold
    meets_threshold = ranking.confidence_score >= SEARCH_CONFIG.confidence_threshold
    return comprehensive_response_object
```

### 3. Interactive Testing

For hands-on exploration, use the Dana REPL:

```bash
./bin/dana-repl
```

Then execute:
```dana
from workflows import product_search_workflow
result = product_search_workflow("LED headlights")
print(result)
```

## Technical Deep Dive: How tabular_index Works

Understanding the internal architecture of the `tabular_index` resource provides insights into Dana's sophisticated data processing capabilities and helps optimize performance for your specific use cases.

### Architecture Overview

The `tabular_index` resource implements a **3-layer architecture** with dependency injection:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TabularIndexResource                         │
│                    (Public API Layer)                           │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       TabularIndex                              │
│                   (Core Processing Layer)                       │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────┐  ┌───────────────────┐  ┌──────────────────┐
│  EmbeddingFactory│  │ VectorStoreFactory│  │   Configuration  │
│    (Dependency)  │  │    (Dependency)   │  │     (Config)     │
└──────────────────┘  └───────────────────┘  └──────────────────┘
```

### Component Breakdown

#### **1. TabularIndexResource (Orchestrator)**

**Location**: `dana/common/sys_resource/tabular_index/tabular_index_resource.py`

**Responsibilities:**
- **Configuration Management**: Validates and structures all configuration data
- **Dependency Creation**: Uses factories to create embedding models and vector stores
- **Resource Lifecycle**: Manages initialization, cleanup, and state
- **Public API**: Provides clean interface for Dana applications

**Key Methods:**
```python
def __init__(self, source: str, embedding_field_constructor: Callable, ...):
    # 1. Create configuration objects
    self._tabular_config = self._create_tabular_config(...)
    self._embedding_config = self._create_embedding_config(...)

    # 2. Create dependencies using factories
    self._embedding_model, self._embed_dim = self._create_embedding_component()
    self._vector_store_provider = self._create_vector_store_component()

    # 3. Inject dependencies into core processor
    self._tabular_index = TabularIndex(
        config=self._tabular_config,
        embedding_model=self._embedding_model,
        provider=self._vector_store_provider
    )
```

#### **2. TabularIndex (Core Processor)**

**Location**: `dana/common/sys_resource/tabular_index/tabular_index.py`

**Responsibilities:**
- **Data Processing**: Loads CSV/Parquet files and converts them to embeddings
- **Index Management**: Decides when to rebuild vs. load existing indices
- **Search Operations**: Handles vector similarity searches and result ranking

**Critical Decision Logic (ADR-001 Architecture):**
```python
def _should_rebuild(self) -> bool:
    # Core decision logic for performance optimization
    if self.config.force_reload:
        return True  # Explicit rebuild request

    if not self._vector_store_exists():
        return True  # First time setup

    if not self._vector_store_has_data():
        return True  # Empty or corrupted store

    return False  # Use existing cached embeddings
```

#### **3. EmbeddingFactory (Dependency)**

**Location**: `dana/common/sys_resource/embedding/embedding_integrations.py`

**Responsibilities:**
- **Model Creation**: Creates embedding models from various providers (OpenAI, HuggingFace, etc.)
- **Dimension Detection**: Automatically determines embedding dimensions
- **Configuration Resolution**: Handles default model selection from `dana_config.json`

**Factory Pattern Implementation:**
```python
@staticmethod
def create_from_dict(config: dict | None = None) -> tuple[Any, int]:
    if not config:
        # Use defaults from dana_config.json
        return EmbeddingFactory.create_from_config()

    model_name = config.get("model_name")  # e.g., "openai:text-embedding-3-large"
    dimensions = config.get("dimensions")   # e.g., 3072 or None for auto-detect

    embedding_resource = LlamaIndexEmbeddingResource()
    embedding_model = embedding_resource.get_embedding_model(model_name, dimensions)
    actual_dimensions = EmbeddingFactory._extract_dimensions(embedding_model)

    return embedding_model, actual_dimensions
```

#### **4. VectorStoreFactory (Dependency)**

**Location**: `dana/common/sys_resource/vector_store/factory.py`

**Responsibilities:**
- **Storage Backend Creation**: Creates DuckDB or PostgreSQL vector stores
- **Provider Abstraction**: Provides unified interface across different storage backends
- **Lifecycle Management**: Handles database connections, table creation, data cleanup

**Provider Pattern Implementation:**
```python
@staticmethod
def create_with_provider(config: VectorStoreConfig, embed_dim: int) -> VectorStoreProviderProtocol:
    if config.provider == "duckdb":
        # Create local file-based storage
        vector_store = DuckDBProvider.create(config.duckdb, embed_dim)
        provider = DuckDBProvider(vector_store)
        return provider
    elif config.provider == "pgvector":
        # Create PostgreSQL-based storage
        vector_store = PGVectorProvider.create(config.pgvector, embed_dim)
        provider = PGVectorProvider(vector_store)
        return provider
```

### Data Processing Pipeline

When you call `use("tabular_index", tabular_index_config=config)`, here's the complete technical flow:

#### **Phase 1: Initialization and Validation**
```python
# 1. TabularIndexResource.__init__()
# - Validates CSV path and column names
# - Creates structured configuration objects
# - Initializes embedding and vector store factories

# 2. Component Creation
embedding_model, dimensions = EmbeddingFactory.create_from_dict(embedding_config)
vector_store_provider = VectorStoreFactory.create_with_provider(vector_store_config, dimensions)

# 3. Dependency Injection
tabular_index = TabularIndex(config, embedding_model, vector_store_provider)
```

#### **Phase 2: Index Decision Logic**
```python
# TabularIndex.initialize()
if self._should_rebuild():
    # Path A: Build from scratch
    self._validate_rebuild_preconditions()  # Check file accessibility, model availability
    self.index = await self._rebuild_index()
else:
    # Path B: Load existing
    self.index = await self._load_existing_index()
```

#### **Phase 3: Data Processing (Rebuild Path)**
```python
# TabularIndex._build_index()
# 1. Load data
df = pd.read_csv(self.config.source)  # or pd.read_parquet()

# 2. Create documents
documents = []
for _, row in df.iterrows():
    # Apply user-defined embedding field constructor
    embedding_text = self.config.embedding_field_constructor(row.to_dict())

    # Apply user-defined metadata constructor
    metadata = self.config.metadata_constructor(row.to_dict()) if self.config.metadata_constructor else {}

    # Create LlamaIndex document
    doc = Document(
        text=str(embedding_text).strip(),
        metadata=metadata,
        excluded_embed_metadata_keys=self.config.excluded_embed_metadata_keys
    )
    documents.append(doc)

# 3. Generate embeddings and build index
storage_context = StorageContext.from_defaults(vector_store=self.provider.vector_store)
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    embed_model=self.embedding_model
)
```

#### **Phase 4: Vector Storage (Storage Backend)**

**DuckDB Implementation:**
```sql
-- Automatic table creation
CREATE TABLE {table_name} (
    node_id VARCHAR PRIMARY KEY,
    text VARCHAR,
    embedding FLOAT[{embed_dim}],
    metadata_ JSON
);

-- Insertion during indexing
INSERT INTO {table_name} VALUES (?, ?, ?, ?);
```

**PostgreSQL Implementation:**
```sql
-- Extension and table setup
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE {table_name} (
    node_id VARCHAR PRIMARY KEY,
    text TEXT,
    embedding vector({embed_dim}),
    metadata_ JSONB
);
```

### Performance Optimization Strategies

#### **1. Caching Architecture**

The system implements **multi-level caching**:

```
Level 1: Configuration Cache
├── Embedding model instances (in-memory)
├── Vector store connections (persistent)
└── Table schema validation (one-time)

Level 2: Data Cache
├── CSV parsing results (temporary)
├── Document objects (temporary)
└── Embedding generation (temporary)

Level 3: Vector Store Cache
├── Embeddings (persistent in DuckDB/PostgreSQL)
├── Metadata (persistent)
└── Index structures (persistent)
```

#### **2. Rebuild vs. Load Decision Matrix**

| Scenario | `force_reload` | Vector Store Exists | Has Data | Action | Reason |
|----------|---------------|---------------------|----------|--------|--------- |
| First run | `false` | ❌ | ❌ | **Rebuild** | No cache exists |
| Data changed | `true` | ✅ | ✅ | **Rebuild** | Explicit refresh |
| Normal run | `false` | ✅ | ✅ | **Load** | Use cached embeddings |
| Corrupted cache | `false` | ✅ | ❌ | **Rebuild** | Cache invalid |

#### **3. Memory Management**

```python
# Streaming processing for large datasets
for _, row in df.iterrows():  # Process one row at a time
    embedding_text = self.config.embedding_field_constructor(row.to_dict())
    if not embedding_text:
        continue  # Skip empty rows to save memory

    # Create document immediately
    doc = Document(text=embedding_text, metadata=metadata)
    documents.append(doc)

    # Batch processing for efficiency
    if len(documents) >= batch_size:
        self._process_batch(documents)
        documents.clear()  # Free memory
```

### Key Takeaways

This technical architecture enables the Dana Product Search to efficiently process CSV data, generate vector embeddings, and perform fast similarity searches while maintaining clean separation of concerns and high performance through intelligent caching strategies.

### Embedding and Chunking Strategy

The `tabular_index` resource uses a **unique Row-Based Embedding Strategy** specifically designed for tabular data, which differs significantly from traditional document chunking approaches.

#### **Row-Based Document Creation (No Traditional Chunking)**

Unlike typical RAG systems that chunk large documents, `tabular_index` treats **each CSV row as a single document**:

```python
# From tabular_index.py - _create_documents()
for _, row in df.iterrows():
    # Each CSV row becomes exactly one document
    row_dict = row.to_dict()
    embedding_text = self.config.embedding_field_constructor(row_dict)

    # Single document per row - no chunking
    doc = Document(
        text=str(embedding_text).strip(),
        metadata=metadata,
        excluded_embed_metadata_keys=self.config.excluded_embed_metadata_keys
    )
    documents.append(doc)
```

**Key Characteristics:**
- **1 CSV Row = 1 Document = 1 Embedding Vector**
- **No text chunking** - entire row content is embedded together
- **User-controlled text composition** via `embedding_field_constructor`
- **Rich metadata preservation** via `metadata_constructor`

#### **Embedding Strategy Details**

**1. Text Composition Strategy:**
```python
# Product search example - config.na
def embedding_field_constructor(row: dict) -> str:
    return str(row.get("ProductName", ""))  # Single field embedding

# Advanced composition example
def advanced_embedding_constructor(row: dict) -> str:
    product_name = row.get("ProductName", "")
    description = row.get("Description", "")
    specs = row.get("Specifications", "")

    # Weighted text combination
    return f"{product_name} {description} {specs}"
```

**2. Supported Embedding Models:**
```python
# Default preferred models from dana_config.json
preferred_models = [
    "openai:text-embedding-3-small",     # 1536 dimensions
    "openai:text-embedding-3-large",     # 3072 dimensions
    "huggingface:BAAI/bge-small-en-v1.5", # 384 dimensions
    "huggingface:sentence-transformers/all-MiniLM-L6-v2", # 384 dimensions
    "cohere:embed-english-v3.0"          # 1024 dimensions
]
```

**3. Dimension Auto-Detection:**
```python
# EmbeddingFactory automatically detects dimensions
def _extract_dimensions(embedding_model) -> int:
    # Strategy 1: Check model attributes
    if hasattr(embedding_model, "dimensions"):
        return embedding_model.dimensions

    # Strategy 2: Generate test embedding
    test_embedding = embedding_model.get_text_embedding("test")
    return len(test_embedding)  # Auto-detect from actual output
```

#### **Chunking Strategy Comparison**

| Approach | Traditional RAG | tabular_index Strategy |
|----------|----------------|------------------------|
| **Input** | Large documents | Structured CSV rows |
| **Chunking** | Text splitting (1000-2000 chars) | Row-based (no splitting) |
| **Documents** | Many chunks per document | One document per row |
| **Embedding Scope** | Text fragment | Complete row context |
| **Metadata** | Document-level | Row-level (rich) |
| **Search Granularity** | Chunk-level matches | Row-level matches |

#### **Performance Characteristics**

**1. Memory Efficiency:**
```python
# Streaming row processing - efficient for large CSV files
for _, row in df.iterrows():  # One row at a time
    embedding_text = construct_embedding_text(row)
    if not embedding_text:
        continue  # Skip empty rows

    doc = Document(text=embedding_text, metadata=metadata)
    documents.append(doc)

    # No chunking overhead - direct document creation
```

**2. Embedding Generation:**
- **Batch Processing**: Multiple rows embedded together for efficiency
- **Provider Support**: OpenAI, HuggingFace, Cohere with automatic failover
- **Dimension Flexibility**: Auto-detection or explicit configuration
- **Error Handling**: Graceful handling of empty/invalid rows

**3. Vector Storage:**
```sql
-- DuckDB storage schema
CREATE TABLE {table_name} (
    node_id VARCHAR PRIMARY KEY,     -- Unique document ID
    text VARCHAR,                   -- Full embedding text
    embedding FLOAT[{embed_dim}],   -- Vector (1536/3072/384 dims)
    metadata_ JSON                  -- Row metadata
);
```



#### **When to Use Row-Based vs. Traditional Chunking**

**Use Row-Based Strategy (tabular_index) When:**
- ✅ **Structured Data**: CSV/Parquet files with meaningful rows
- ✅ **Product Catalogs**: Each row represents a distinct item
- ✅ **Entity Search**: Looking for specific records/entities
- ✅ **Metadata Rich**: Need to preserve row-level attributes
- ✅ **Exact Matches**: Part numbers, SKUs, identifiers

**Use Traditional Chunking When:**
- ❌ **Long Documents**: PDFs, articles, books
- ❌ **Narrative Text**: Stories, explanations, guides
- ❌ **Contextual Search**: Need surrounding context
- ❌ **Document Sections**: Searching within document parts

This row-based embedding strategy makes `tabular_index` exceptionally well-suited for structured data search applications like product catalogs, inventory systems, and entity databases where each row represents a meaningful, searchable unit.

## Single Search vs Batch Search Use Cases

The Dana Product Search system supports two primary search modes: **Single Search** for individual queries and **Batch Search** for processing multiple queries efficiently. Understanding when and how to use each approach is crucial for optimal performance.

### Single Search Use Cases

**Single Search** is ideal for interactive applications where users submit one query at a time and expect immediate results.

#### **1. Interactive Product Search (main.na)**

**Use Case**: Real-time product lookup in web applications or customer service tools.

```dana
# Single search implementation - main.na
from workflows import product_search_workflow
from config import MODEL_CONFIG
from time.py import time

set_model(MODEL_CONFIG.model_name)

# Execute single search
query = "Wire Mesh Cable Tray"
start_time = time()
response = product_search_workflow(query)
end_time = time()

# Display results
print("=== DANA PRODUCT SEARCH RESULT ===")
print(f"Query: {response['query']}")
print(f"Total Results: {response['total_results']}")
print(f"Confidence Score: {response['confidence']}")
print(f"Processing Time: {end_time - start_time}s")

if response['best_match']:
    print(f"Best Match: {response['best_match']['product_name']}")
    print(f"Part Number: {response['best_match']['mfr_part_num']}")
    print(f"Brand: {response['best_match']['mfr_brand']}")
else:
    print("No suitable match found")

print(f"Reasoning: {response['reasoning']}")
```

**Expected Output:**
```
=== DANA PRODUCT SEARCH RESULT ===
Query: Wire Mesh Cable Tray
Total Results: 5
Confidence Score: 0.85
Processing Time: 2.3s
Best Match: Industrial Wire Mesh Cable Tray - 12"
Part Number: WMT-12-IND
Brand: CableTech
Reasoning: Strong match for wire mesh cable tray with specific sizing and industrial grade specifications.
```

#### **2. Direct tabular_index Single Search**

**Use Case**: When you need more control over search parameters or want to bypass the product search workflow.

```dana
# Direct tabular_index usage
from config import get_tabular_index_config

# Initialize tabular_index
tabular_index_config = get_tabular_index_config()
product_data = use("tabular_index", tabular_index_config=tabular_index_config)

# Single search with custom parameters
result = await product_data.single_search(
    query="brake pads",
    top_k=15,  # Return more results
    callback=lambda query, results: print(f"Found {len(results)} matches for '{query}'")
)

print(f"Query: {result['query']}")
print(f"Results count: {len(result['results'])}")
for i, item in enumerate(result['results'][:3]):
    print(f"{i+1}. {item['text']} (Score: {item.get('score', 'N/A')})")
```

#### **3. Single Search Performance Characteristics**

| Metric | Typical Value | Notes |
|--------|---------------|-------|
| **Response Time** | 1.5-3.0 seconds | Includes LLM reasoning + vector search |
| **Vector Search** | 50-200ms | Pure similarity search time |
| **LLM Processing** | 1-2 seconds | Query enhancement + ranking |
| **Memory Usage** | Low | Stateless operation |
| **Concurrency** | High | Multiple users can search simultaneously |

### Batch Search Use Cases

**Batch Search** is designed for processing multiple queries efficiently, with built-in parallelization and optimized resource usage.

#### **1. Application-Level Batch Processing (main_batch.na)**

**Use Case**: Processing multiple customer queries, bulk data analysis, or system integration tasks.

```dana
# Batch search implementation - main_batch.na
def single_search(query: str) -> any:
    return product_search_workflow(query)

def get_successful_results(single_search_result: list[any]) -> list[any]:
    """Extract and format results from single search"""
    response = single_search_result
    summary = {
        "query": response['query'],
        "total_results": response['total_results'],
        "confidence": response['confidence'],
        "reasoning": response['reasoning'],
    }
    if response['best_match']:
        summary["best_match"] = {
            "product_name": response['best_match']['product_name'],
            "mfr_part_num": response['best_match']['mfr_part_num'],
            "mfr_brand": response['best_match']['mfr_brand'],
        }
    else:
        summary["best_match"] = None
    return [summary]

def batch_search(queries: list[str], batch_size: int) -> list[any]:
    """Process multiple queries in batches with performance monitoring"""
    batch_results = []
    n = len(queries)
    i = 0
    start_time = time()

    while i < n:
        stop = i + batch_size
        if stop > n:
            stop = n

        print(f"Processing batch from {i} to {stop}")
        print(f"Batch size: {stop - i}")
        batch = queries[i:stop]

        # Initialize all searches concurrently
        batch_start_time = time()
        task_batch = []
        for query in batch:
            task_batch.append(single_search(query))

        batch_concurrency_time = time()
        print(f"Batch initialization time: {batch_concurrency_time - batch_start_time}s")

        # Process results
        for task in task_batch:
            result = get_successful_results(task)
            batch_results.append(result)

        batch_end_time = time()
        print(f"Batch result processing time: {batch_end_time - batch_concurrency_time}s")
        i += batch_size

    end_time = time()
    print(f"Total time: {end_time - start_time}s")
    return batch_results

# Execute batch search
queries = [
    "Ammonia Hydroxide concentrated x 500ml",
    "Fiberglass Wax",
    "Silicone Sealant",
    "Copper Wire 18 gauge",
    "LED Light Bulb 60W equivalent"
]

batch_size = 10
results = batch_search(queries, batch_size)
```

**Expected Output:**
```
Processing batch from 0 to 5
Batch size: 5
Batch initialization time: 0.05s
Batch result processing time: 8.2s
Total time: 8.25s
[
  [{"query": "Ammonia Hydroxide concentrated x 500ml", "confidence": 0.82, ...}],
  [{"query": "Fiberglass Wax", "confidence": 0.91, ...}],
  ...
]
```

#### **2. Native tabular_index Batch Search**

**Use Case**: High-performance batch processing with optimized async execution.

```dana
# Direct tabular_index batch search
from config import get_tabular_index_config, BatchSearchConfig

# Initialize tabular_index
tabular_index_config = get_tabular_index_config()
product_data = use("tabular_index", tabular_index_config=tabular_index_config)

# Configure batch search parameters
batch_config = {
    "batch_size": 20,           # Process 20 queries per batch
    "pre_filter_top_k": 100,    # Initial retrieval limit
    "post_filter_top_k": 20,    # Post-processing limit
    "top_k": 10                 # Final results per query
}

# Execute batch search
queries = [
    "industrial cable management",
    "automotive brake components",
    "electrical connectors waterproof",
    "stainless steel fasteners",
    "LED lighting fixtures"
]

# Progress callback function
def progress_callback(query: str, results: list[dict]):
    print(f"✓ Completed search for '{query}' - {len(results)} results")

# Execute batch search with async optimization
results = await product_data.batch_search(
    queries=queries,
    batch_search_config=batch_config,
    callback=progress_callback
)

# Process results
for i, result in enumerate(results):
    print(f"\n--- Query {i+1}: {result['query']} ---")
    for j, item in enumerate(result['results'][:3]):
        print(f"  {j+1}. {item['text']}")
```

#### **3. Batch Search Performance Optimization**

**Concurrency Strategies:**

```python
# Strategy 1: Async Gather (tabular_index native)
async def native_batch_search(queries: list[str]) -> list[dict]:
    tasks = []
    for query in queries:
        tasks.append(self.single_search(query, top_k, callback))

    # Execute all searches concurrently
    results = await asyncio.gather(*tasks)
    return results

# Strategy 2: Application-level Batching (main_batch.na)
def application_batch_search(queries: list[str], batch_size: int) -> list[dict]:
    # Process in smaller chunks to manage memory and resources
    for i in range(0, len(queries), batch_size):
        batch = queries[i:i + batch_size]
        # Process batch with controlled concurrency
        process_batch(batch)
```

### Performance Comparison

| Aspect | Single Search | Batch Search |
|--------|---------------|--------------|
| **Latency** | 1.5-3.0s per query | 0.8-1.5s per query |
| **Throughput** | 1-2 queries/second | 5-10 queries/second |
| **Resource Usage** | Low, stateless | Higher during processing |
| **Memory Efficiency** | Excellent | Good (batched) |
| **Concurrency** | High | Controlled |
| **Use Case** | Interactive search | Bulk processing |

### When to Use Each Approach

#### **Use Single Search For:**

✅ **Interactive Applications**
- Web search interfaces
- Customer service tools
- Real-time product lookups
- API endpoints with immediate response needs

✅ **Low Volume Scenarios**
- Individual customer queries
- Manual product research
- Troubleshooting specific items
- Ad-hoc searches

#### **Use Batch Search For:**

✅ **Bulk Processing Tasks**
- Data migration and validation
- Catalog synchronization
- Automated inventory updates
- System integration workflows

✅ **Analytics and Reporting**
- Market research analysis
- Competitive product mapping
- Search performance testing
- Data quality assessment

#### **Advanced Batch Search Patterns**

**1. Priority-Based Batch Processing:**
```dana
def priority_batch_search(priority_queries: dict[str, int]):
    # Sort by priority (higher number = higher priority)
    sorted_queries = sorted(priority_queries.keys(),
                          key=lambda q: priority_queries[q],
                          reverse=True)

    return batch_search(sorted_queries, batch_size=10)
```

**2. Error-Resilient Batch Processing:**
```dana
def resilient_batch_search(queries: list[str]):
    successful_results = []
    failed_queries = []

    for query in queries:
        try:
            result = single_search(query)
            successful_results.append(result)
        except Exception as e:
            failed_queries.append((query, str(e)))

    return successful_results, failed_queries
```

Both single and batch search modes leverage the same underlying `tabular_index` infrastructure while providing optimal performance characteristics for their respective use cases.

## Customization Guide

### 1. Modify Search Parameters

Edit `config.na` to adjust search behavior:

```dana
SEARCH_CONFIG = SearchConfig(
    max_results=10,                    # More results
    confidence_threshold=0.6,          # Lower threshold
    vector_search_limit=20,            # Broader search
    use_weighted_terms=false           # Disable term weighting
)
```

### 2. Add Custom Product Data

Replace or extend the CSV data:

```csv
product_name,mfr_part_num,mfr_brand,source_category,data_source
"Your Product Name","YPN-001","YourBrand","Category","your_source"
```

Update the data path in `config.na`:
```dana
DATA_CONFIG = DataConfig(
    csv_file_path="path/to/your/products.csv"
)
```

### 3. Customize Prompts

Modify prompts in `prompts.na` for different domains:

```dana
def get_enhancement_prompt(query: str) -> str:
    return f"""You are a specialist for [YOUR DOMAIN] product searches.

    [Custom instructions for your use case]

    USER QUERY: {query}
    """
```

### 4. Add New Search Strategies

Extend `methods.na` with additional search methods:

```dana
def search_by_category(category: str, product_data, limit: int) -> list:
    """Search by product category"""
    # Your implementation
    pass

def search_by_brand(brand: str, product_data, limit: int) -> list:
    """Search by manufacturer brand"""
    # Your implementation
    pass
```

## Troubleshooting

### CSV and tabular_index Issues

1. **"CSV file not found" Error**
   ```
   Problem: Cannot locate the specified CSV file
   Solution:
   - Verify the csv_file_path in DATA_CONFIG points to correct file
   - Use absolute paths: "/full/path/to/your/file.csv"
   - Ensure the data files exist: ls examples/11_product_search/data/
   ```

2. **"KeyError" or Empty Results from CSV**
   ```
   Problem: Column name mismatch in embedding_field_constructor
   Solution:
   - Check your CSV headers: head -1 your_file.csv
   - Update embedding_field_constructor to match exactly
   - For large dataset: row.get("ProductName", "")
   - For small dataset: row.get("product_name", "")
   ```

3. **Embeddings Taking Forever to Generate**
   ```
   Problem: Large CSV file processing
   Solution:
   - Start with sample_products_15.csv for testing
   - Check your OpenAI API rate limits
   - Monitor progress in logs with log_level("info")
   - First run with 1000 products takes 3-5 minutes
   ```

4. **"No embeddings found" or Cache Issues**
   ```
   Problem: tabular_index cache problems
   Solution:
   - Delete cache directory: rm -rf .cache/product_search
   - Set force_reload=true in DATA_CONFIG
   - Verify cache_dir path is writable
   - Check disk space for embedding storage
   ```

5. **Inconsistent Search Results**
   ```
   Problem: Using wrong dataset or configuration mismatch
   Solution:
   - Verify which CSV file is being used in DATA_CONFIG
   - Check that embedding_field_constructor matches CSV headers
   - Ensure table_name is unique for differ
     Clear cache when switching between datasets
   ```

### General System Issues

6. **"Model not found" Error**
   ```
   Solution: Check your model configuration in config.na
   Verify API keys are set in environment variables
   For OpenAI: export OPENAI_API_KEY="your-key"
   ```

7. **Low Confidence Scores**
   ```
   Solution: Lower confidence_threshold in SEARCH_CONFIG
   Improve query enhancement prompts
   Add more relevant training data
   Test with simpler, more direct queries first
   ```

8. **Slow Performance**
   ```
   Solution: Reduce vector_search_limit in SEARCH_CONFIG
   Use smaller model (e.g., gpt-3.5-turbo)
   Implement result caching
   Use cached embeddings (force_reload=false)
   ```

9. **No Results Found**
   ```
   Solution: Check if product data loaded correctly
   Verify tabular_index configuration
   Test with broader, simpler queries
   Check that CSV has data and proper headers
   ```

### Debug Mode

Enable debug logging for detailed information:

```dana
# In main.na, change:
log_level("info")  # Instead of log_level("warn")
```

## Performance Expectations

### Typical Performance Metrics

- **Single Query**: 2-3 seconds (includes 2 LLM calls)
- **Batch Processing**: Scales with concurrent LLM calls
- **Memory Usage**: Minimal (CSV data loaded via tabular_index)
- **Accuracy**: 80-90% for well-formed queries

### Optimization Tips

1. **Use Smaller Models**: For faster response times
2. **Batch Similar Queries**: Leverage concurrent processing
3. **Cache Frequent Queries**: Implement intelligent caching
4. **Tune Search Limits**: Balance speed vs. thoroughness
5. **Optimize Prompts**: Reduce token usage while maintaining quality

## Next Steps

### Extending the System

1. **Add More Data Sources**: Integrate multiple CSV files or databases
2. **Implement Learning**: Use feedback to improve ranking algorithms
3. **Add Filters**: Support category, price range, or brand filtering
4. **Build APIs**: Create RESTful endpoints for web integration
5. **Add UI**: Build a web interface for interactive searching

### Production Considerations

1. **Error Handling**: Add comprehensive error handling and fallbacks
2. **Monitoring**: Implement logging and metrics collection
3. **Security**: Add input validation and rate limiting
4. **Scalability**: Consider distributed processing for large datasets
5. **Testing**: Add comprehensive unit and integration tests

---

This tutorial provides a complete foundation for understanding and extending the Dana Product Search example. The modular design makes it easy to adapt for different domains and requirements while demonstrating best practices for Dana development.
