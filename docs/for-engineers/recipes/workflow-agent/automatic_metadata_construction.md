# Automatic Workflow Metadata Construction

## Overview

The automatic workflow metadata construction feature eliminates the need for manual metadata definition by automatically extracting information from function docstrings and `poet()` decorator parameters. This significantly improves developer experience and reduces maintenance overhead.

## Problem Solved

### Before: Manual Metadata Definition

```python
# Poor design - manual metadata definition
def ingest_document(file_path):
    """Ingest document from file system with validation."""
    # ... implementation

# Manual metadata assignment
ingest_document.metadata = {"description": "Ingest and validate document", "retry_count": 3}
ingest_document.step_name = "ingest_document"

# Manual workflow metadata construction
workflow_metadata = {
    "workflow_id": "doc_processing_001",
    "description": "Enterprise document processing pipeline",
    "version": "1.0.0",
    "steps": [
        {"name": "ingest_document", "description": "Ingest and validate document", "retry_count": 3},
        {"name": "perform_ocr", "description": "Perform OCR processing", "timeout": 30},
        # ... more manual definitions
    ]
}
```

### After: Automatic Metadata Construction

```python
# Clean design - automatic metadata extraction
@poet(domain="document_processing", retries=3)
def ingest_document(file_path):
    """Ingest document from file system with validation."""
    # ... implementation

@poet(domain="ocr", timeout=30)
def perform_ocr(document):
    """Perform OCR on ingested document."""
    # ... implementation

# Automatic metadata construction
workflow_metadata = create_pipeline_metadata(
    document_processing_workflow,
    workflow_id="doc_processing_001",
    description="Enterprise document processing pipeline"
)
```

## Key Features

### 1. Automatic Function Name Extraction
- Function names are automatically extracted from `__name__` attribute
- No need to manually specify step names

### 2. Docstring Description Extraction
- First line of function docstring is automatically used as description
- Supports multi-line docstrings with automatic first-line extraction
- Fallback to function name if no docstring is provided

### 3. Poet Decorator Parameter Extraction
- `retries` parameter → `retry_count` in metadata
- `timeout` parameter → `timeout` in metadata
- `domain` parameter → `domain` in metadata
- Phase-specific parameters (operate, enforce, train) are extracted
- Additional parameters are preserved

### 4. Multiple Construction Methods

#### Method 1: Pipeline Metadata Extraction
```python
# From composed pipeline
workflow = step1 | step2 | step3
metadata = create_pipeline_metadata(workflow, workflow_id="example")
```

#### Method 2: Function List Metadata
```python
# From list of functions
functions = [step1, step2, step3]
metadata = create_workflow_metadata(functions, workflow_id="example")
```

#### Method 3: Convenience Decorators
```python
@workflow_step(name="custom", retry_count=5)
def my_function(data):
    """Custom function with metadata."""
    return data
```

## Implementation Details

### Core Components

1. **MetadataExtractor**: Extracts metadata from individual functions
2. **FunctionMetadata**: Dataclass representing extracted metadata
3. **Workflow Helpers**: High-level functions for metadata construction
4. **Poet Integration**: Enhanced poet decorator with metadata extraction

### Metadata Sources (in order of precedence)

1. `poet()` decorator parameters (`_poet_config` attribute)
2. Legacy metadata attributes (`metadata` attribute)
3. Function docstring
4. Function name

### Supported Parameters

| Parameter | Source | Description |
|-----------|--------|-------------|
| `name` | Function `__name__` | Function name |
| `description` | Docstring first line | Function description |
| `retry_count` | `poet(retries=N)` | Number of retry attempts |
| `timeout` | `poet(timeout=N)` | Timeout in seconds |
| `domain` | `poet(domain="...")` | Domain context |
| `model` | `poet(operate={"model": "..."})` | Model specification |
| `confidence_threshold` | `poet(enforce={"confidence_threshold": N})` | Confidence threshold |
| `format` | `poet(operate={"format": "..."})` | Output format |

## Usage Examples

### Basic Usage
```python
from dana.frameworks.poet.core.workflow_helpers import create_pipeline_metadata

@poet(domain="data_processing", retries=3)
def process_data(input_data):
    """Process input data with validation."""
    return processed_data

@poet(domain="analysis", timeout=60)
def analyze_data(data):
    """Analyze processed data for insights."""
    return analysis_results

# Create workflow
workflow = process_data | analyze_data

# Automatically construct metadata
metadata = create_pipeline_metadata(
    workflow,
    workflow_id="data_analysis_001",
    description="Data processing and analysis pipeline"
)
```

### Advanced Usage with Phase-Specific Parameters
```python
@poet(
    domain="llm_optimization",
    operate={"model": "gpt-4", "timeout": 30},
    enforce={"confidence_threshold": 0.9}
)
def enhanced_analysis(data):
    """Perform enhanced analysis using LLM."""
    return enhanced_results
```

### Backward Compatibility
```python
# Legacy functions still work
def legacy_function(data):
    """Legacy function without poet decorator."""
    return data

# Metadata is still extracted (name and description)
metadata = create_workflow_metadata([legacy_function])
```

## Benefits

### 1. Reduced Boilerplate
- No more manual metadata definition
- Automatic extraction from existing code
- Consistent metadata structure

### 2. Better Maintainability
- Single source of truth (function definition)
- Automatic updates when function changes
- Reduced potential for metadata drift

### 3. Improved Developer Experience
- Less code to write and maintain
- Natural integration with existing patterns
- Clear separation of concerns

### 4. Enhanced Consistency
- Standardized metadata structure
- Consistent parameter naming
- Unified extraction logic

## Migration Guide

### From Manual Metadata
```python
# Old approach
def my_function(data):
    return data

my_function.metadata = {"description": "My function", "retry_count": 3}

# New approach
@poet(retries=3)
def my_function(data):
    """My function."""
    return data
```

### From Manual Workflow Metadata
```python
# Old approach
workflow_metadata = {
    "workflow_id": "example",
    "steps": [
        {"name": "step1", "description": "Step 1", "retry_count": 3}
    ]
}

# New approach
@poet(retries=3)
def step1(data):
    """Step 1."""
    return data

workflow = step1 | step2
metadata = create_pipeline_metadata(workflow, workflow_id="example")
```

## Testing

The automatic metadata construction is thoroughly tested with:

- Basic metadata extraction
- Poet decorator parameter extraction
- Legacy metadata compatibility
- Pipeline metadata extraction
- Edge cases and error handling

Run tests with:
```bash
python -m pytest tests/unit/frameworks/test_metadata_extractor.py -v
```

## Future Enhancements

1. **Type Annotation Extraction**: Extract parameter types from type hints
2. **Validation Rules**: Extract validation rules from function annotations
3. **Performance Metrics**: Automatic performance tracking integration
4. **Documentation Generation**: Auto-generate workflow documentation
5. **Visualization**: Generate workflow diagrams from metadata 