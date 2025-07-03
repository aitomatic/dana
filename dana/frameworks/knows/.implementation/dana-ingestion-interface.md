# Dana Language Interface: OpenDXA KNOWS Knowledge Ingestion

## Simple User Interface

### 1. Knowledge Pack Creation
```dana
# One line to create knowledge pack from documents
private:kb = create_knowledge_pack("path/to/documents", "path/to/output/knowledge_pack")
```

### 2. Common Usage Patterns

#### Pattern 1: Basic Knowledge Pack Creation
```dana
# Create knowledge pack from documents
private:kb = create_knowledge_pack("path/to/documents", "path/to/output/knowledge_pack")
```

#### Pattern 2: Error Handling
```dana
try:
    private:kb = create_knowledge_pack("path/to/documents", "path/to/output/knowledge_pack")
except InvalidDocuments:
    log("Invalid documents found", "error")
except StorageError:
    log("Failed to create knowledge pack", "error")
```

## Under the Hood

The system automatically handles:

1. **Document Processing**
   - Loads documents from input folder
   - Extracts text and metadata
   - Validates document format

2. **Knowledge Extraction**
   - Extracts meta-level knowledge
   - Expands context using similarity
   - Validates knowledge correctness

3. **Knowledge Organization**
   - Creates knowledge pack structure
   - Organizes workflows and semantic data
   - Generates metadata

## Knowledge Pack Structure
```
knowledge_pack/
├── vector_db/           # LlamaIndex vector database
├── workflows/          # Structured workflow data
└── metadata.json      # Pack metadata and configuration
```

## Best Practices

1. **Document Organization**
   - Keep documents organized by domain
   - Use descriptive filenames
   - Maintain consistent format

2. **Output Management**
   - Use descriptive knowledge pack names
   - Keep output paths organized
   - Monitor disk space

3. **Error Handling**
   - Always use try-catch for ingestion
   - Check document validity
   - Monitor ingestion progress

## Implementation Notes

### Knowledge Pack Creation
```dana
struct KnowledgePack:
    path: str
    vector_db: any
    workflows: dict
    metadata: dict
```

### Error Types
```dana
struct InvalidDocuments:
    message: str
    details: dict

struct StorageError:
    message: str
    details: dict
```

## Example Usage Scenarios

### Scenario 1: Basic Ingestion
```dana
# Create knowledge pack from documents
private:kb = create_knowledge_pack("path/to/documents", "path/to/output/knowledge_pack")
```

### Scenario 2: Error Handling
```dana
try:
    private:kb = create_knowledge_pack("path/to/documents", "path/to/output/knowledge_pack")
except InvalidDocuments:
    log("Invalid documents found", "error")
except StorageError:
    log("Failed to create knowledge pack", "error")
```

### Scenario 3: Batch Processing
```dana
# Process multiple document folders
for folder in document_folders:
    try:
        private:kb = create_knowledge_pack(folder, f"output/{folder.name}")
    except InvalidDocuments:
        log(f"Invalid documents in {folder}", "warn")
        continue
``` 