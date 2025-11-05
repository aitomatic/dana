# Tabular Analysis Workflow

## Overview

The `TabularAnalysisWorkflow` orchestrates a complete data analysis pipeline that combines semantic search with metadata extraction to help answer questions about tabular data.

## Workflow Architecture

```
User Query
    ↓
┌─────────────────────────────────────┐
│ Step 1: Semantic Search             │
│ (DataFrameIndexerResource)          │
│ - Search data rows                  │
│ - Search column values              │
│ - Identify relevant files           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Step 2: Metadata Extraction         │
│ (MetadataExtractorResource)         │
│ - Get file statistics               │
│ - Column details                    │
│ - Data types & counts               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Step 3: LLM Reasoning               │
│ - Analyze data availability         │
│ - Suggest approach                  │
│ - Identify limitations              │
└─────────────────────────────────────┘
    ↓
Analysis Result
```

## Components

### 1. DataFrameIndexerResource
- **Purpose**: Indexes tabular data for semantic search
- **Document Types**:
  - `data_rows`: Actual data in markdown tables
  - `column_values`: Unique values per column
- **Key Methods**:
  - `index_file(file_path, sheet_name, force_reload)`: Index single file
  - `index_workspace(force_reload)`: Index all files in workspace
  - `search_all(query, top_k, file_filter)`: Search both doc types

### 2. MetadataExtractorResource
- **Purpose**: Extract structured metadata from files
- **Information Extracted**:
  - File type, size, row count
  - Column names, data types
  - Unique value counts
  - Sample values for string columns
- **Key Method**:
  - `extract_metadata(file_path)`: Get comprehensive file metadata

### 3. TabularAnalysisWorkflow
- **Purpose**: Coordinate resources and LLM reasoning
- **Inputs**:
  - `user_query`: Question about the data
  - `top_k`: Number of search results (default: 5)
- **Outputs**:
  - `relevant_files`: Files that match the query
  - `relevant_columns`: Key columns identified
  - `metadata_results`: Detailed file metadata
  - `llm_analysis`: Reasoning about how to answer

## Usage

### Quick Start

```python
from pathlib import Path
from tabular_workflows.tabular_analysis_workflow import TabularAnalysisWorkflow
from resources.dataframe_indexer_resource import DataFrameIndexerResource
from resources.metadata_extractor_resource import MetadataExtractorResource

# Initialize resources
dataset_dir = Path("path/to/data")

indexer = DataFrameIndexerResource(
    workspace_root=str(dataset_dir),
    cache_dir="/tmp/tabular_cache"  # Optional
)

metadata_extractor = MetadataExtractorResource(
    workspace_root=str(dataset_dir)
)

# Create workflow
workflow = TabularAnalysisWorkflow(
    dataframe_indexer=indexer,
    metadata_extractor=metadata_extractor,
    llm_agent=None  # Or provide agent for LLM reasoning
)

# Index files (one-time setup)
indexer.index_workspace()

# Execute workflow
response = workflow.execute(
    user_query="Find sales data for California customers",
    top_k=5
)

result = response.get('result', response)

if result['success']:
    print(f"Relevant Files: {result['relevant_files']}")
    print(f"Key Columns: {result['relevant_columns']}")
    print(f"\nAnalysis:\n{result['llm_analysis']}")
```

### Running the Demo

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the demo script
python tabular_analysis/demo_workflow.py
```

The demo will:
1. Index a sample CSV file
2. Execute a workflow with a test query
3. Display relevant files, columns, and analysis

## Workflow Output Structure

```python
{
    "success": bool,
    "search_results": {
        "data_rows_results": [
            {
                "doc_type": "data_rows",
                "file_name": str,
                "content": str,  # Markdown table
                "score": float,
                "metadata": dict
            }
        ],
        "column_values_results": [
            {
                "doc_type": "column_values",
                "file_name": str,
                "content": str,  # Column values
                "score": float,
                "metadata": dict
            }
        ]
    },
    "metadata_results": {
        "file_name.csv": {
            "file_type": "csv",
            "row_count": int,
            "columns": [...]
        }
    },
    "llm_analysis": str,  # Detailed analysis
    "relevant_files": [str],
    "relevant_columns": {
        "file.csv": ["col1", "col2"]
    },
    "error": str | None
}
```

## LLM Analysis

When an LLM agent is provided, the workflow generates a comprehensive prompt that includes:

1. **Relevant Data Rows**: Top matching data samples
2. **Relevant Columns**: Columns with matching values
3. **File Metadata**: Complete file structure
4. **Key Columns**: Most relevant columns identified

The LLM analyzes this to provide:
- Whether the query can be answered
- Which files/columns to use
- Step-by-step approach
- Limitations and assumptions

## Fallback Mode

Without an LLM agent, the workflow provides a basic analysis listing:
- Number of relevant files found
- File statistics (rows, columns)
- Key columns identified
- Recommendation to review files

## Configuration Options

### DataFrameIndexerResource

```python
DataFrameIndexerResource(
    workspace_root=str,         # Directory containing data files
    resource_id=str,            # Unique identifier (default: "dataframe-indexer")
    cache_dir=str | None,       # Cache directory (default: ~/.dana/.cache/tabular_rag)
    max_rows=int,               # Max rows to index per file (default: 10000)
    chunk_size=int,             # Rows per document chunk (default: 512)
    max_unique_values=int,      # Max unique values to index (default: 10000)
    index_only_str_object=bool, # Index only string columns (default: True)
    dimension=int,              # Embedding dimension (default: 1024)
    force_reload=bool,          # Re-index even if cached (default: False)
    debug=bool                  # Enable debug output (default: False)
)
```

### MetadataExtractorResource

```python
MetadataExtractorResource(
    resource_id=str | None,     # Unique identifier
    workspace_root=str | None   # Root directory (default: cwd)
)
```

## Performance Considerations

1. **Initial Indexing**: First-time indexing can take time depending on:
   - Number of files
   - File sizes
   - Number of columns

2. **Caching**: Files are tracked by hash and not re-indexed unless:
   - File content changes
   - `force_reload=True` is set

3. **Sampling**: Large datasets are automatically sampled:
   - DataFrames > 10,000 rows are uniformly sampled
   - Columns with > 10,000 unique values are sampled

4. **Token Limits**: Large markdown tables may occasionally exceed token limits:
   - These batches are skipped with a warning
   - Processing continues with remaining batches

## Testing

Run the test suite:

```bash
# Test the workflow
pytest tabular_analysis/tests/test_tabular_analysis_workflow.py -v

# Test individual resources
pytest tabular_analysis/tests/test_dataframe_indexer_resource.py -v
pytest tabular_analysis/tests/test_metadata_extractor_resource.py -v
```

## File Structure

```
tabular_analysis/
├── tabular_workflows/
│   ├── __init__.py
│   └── tabular_analysis_workflow.py
├── resources/
│   ├── dataframe_indexer_resource.py
│   └── metadata_extractor_resource.py
├── agents/
│   └── tabular_analysis_agent.py
├── tests/
│   ├── test_tabular_analysis_workflow.py
│   ├── test_dataframe_indexer_resource.py
│   └── test_metadata_extractor_resource.py
├── dataset/
│   └── *.csv, *.xlsx files
├── demo_workflow.py
└── WORKFLOW_README.md
```

## Troubleshooting

### "Module not found: workflows.context"
- **Cause**: Name conflict with LlamaIndex internal modules
- **Fix**: Ensure the old `workflows/` directory is deleted, only `tabular_workflows/` should exist

### "Conflicting lock on file" (DuckDB)
- **Cause**: Multiple processes accessing the same cache
- **Fix**: Use separate cache directories for parallel tests

### "Requested X tokens, max 300000"
- **Cause**: Large markdown tables exceed embedding API limits
- **Fix**: Reduce `chunk_size` parameter or increase sampling

### Files not being re-indexed
- **Cause**: Hash-based caching prevents duplicate indexing
- **Fix**: Use `force_reload=True` or delete cache directory

## Next Steps

1. **Integrate with Agent**: Register resources in `TabularAnalysisAgent`
2. **Add LLM**: Provide an LLM agent for intelligent analysis
3. **Custom Queries**: Experiment with different query types
4. **Production Use**: Adjust parameters for your dataset size
5. **Extend Functionality**: Add more resources or workflow steps

## Related Files

- **Agent Prompt**: `prompts/TabularAnalysisAgent.xml`
- **Plan Document**: `metadata-extraction-resource.plan.md`
- **Dataset**: `dataset/NL2SQL_Query_Dataset.csv`

