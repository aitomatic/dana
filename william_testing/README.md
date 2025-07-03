# OpenDXA KNOWS Human Testing Suite

This directory contains scripts and documents for manually testing the OpenDXA KNOWS knowledge ingestion system phases.

## Directory Structure

```
william_testing/
├── README.md                          # This file
├── docs/                              # Test documents directory
│   ├── sample_text.txt               # Text document (backup best practices)
│   ├── network_troubleshooting.md    # Markdown document (network guide)
│   ├── server_metrics.json           # JSON document (server performance data)
│   └── incident_log.csv              # CSV document (incident tracking)
├── test_phase1_document_processing.py # Phase 1 testing script
├── test_phase2_meta_extraction.py     # Phase 2 testing script
└── test_phase3_similarity_context.py  # Phase 3 testing script (coming next)
```

## Phase 1: Document Processing Testing

### What Phase 1 Tests
- **DocumentLoader**: Loading documents from various formats (txt, md, json, csv)
- **DocumentParser**: Parsing document structure and extracting metadata
- **TextExtractor**: Extracting clean text content from parsed documents
- **Error Handling**: Testing edge cases and invalid inputs

### Test Documents Provided
1. **sample_text.txt** - Data backup best practices guide
2. **network_troubleshooting.md** - Network troubleshooting procedures with markdown formatting
3. **server_metrics.json** - Server performance metrics in JSON format
4. **incident_log.csv** - Incident tracking data in CSV format

### How to Run Phase 1 Testing

```bash
# Navigate to the testing directory
cd /Users/aitomatic/Project/opendxa/william_testing

# Run the Phase 1 testing script
uv run python test_phase1_document_processing.py
```

### Interactive Testing Menu

The script provides an interactive menu with these options:

1. **List available documents** - Shows all documents in the docs/ directory
2. **Test individual document** - Test the complete pipeline on a specific document
3. **Test document loading only** - Test just the loading functionality
4. **Test error handling scenarios** - Test error conditions and edge cases
5. **Test all documents (batch)** - Run tests on all available documents
6. **Exit** - Exit the testing interface

### What to Look For During Testing

#### ✅ Successful Loading
- Document ID is generated
- Source path is correct
- Format is detected properly
- Content length is reasonable
- Metadata contains expected fields

#### ✅ Successful Parsing
- Text content is extracted
- Structured data is populated (for JSON/CSV)
- Metadata includes parsing information
- No data loss occurs

#### ✅ Successful Text Extraction
- Clean text is produced
- Word/line counts are reasonable
- Text preview shows readable content
- No formatting artifacts remain

#### ❌ Error Handling
- Invalid files are rejected gracefully
- Meaningful error messages are provided
- System doesn't crash on bad input
- Proper logging occurs

### Expected Results

For the provided test documents:

- **sample_text.txt**: ~1,700 characters, plain text about backup practices
- **network_troubleshooting.md**: ~2,500 characters, markdown with headers, code blocks, tables
- **server_metrics.json**: ~2,000 characters, structured JSON with metrics and alerts
- **incident_log.csv**: ~800 characters, tabular data with incident records

## Adding Your Own Test Documents

You can add your own documents to the `docs/` directory. Supported formats:
- `.txt` - Plain text files
- `.md` - Markdown files
- `.json` - JSON data files
- `.csv` - CSV data files

The testing script will automatically detect and include any new documents you add.

## Phase 2: Meta Knowledge Extraction Testing

### What Phase 2 Tests
- **MetaKnowledgeExtractor**: Extracting structured knowledge from text content
- **KnowledgeCategorizer**: Categorizing knowledge into different types
- **Integration**: End-to-end pipeline from document to categorized knowledge
- **Quality Analysis**: Confidence metrics and knowledge distribution analysis

### How to Run Phase 2 Testing

```bash
# Navigate to the testing directory
cd /Users/aitomatic/Project/opendxa/william_testing

# Run the Phase 2 testing script
uv run python test_phase2_meta_extraction.py
```

### Interactive Testing Menu

The Phase 2 script provides these testing options:

1. **List available documents** - Shows all documents in the docs/ directory
2. **Test individual document** - Complete Phase 2 pipeline on a specific document
3. **Test meta knowledge extraction only** - Test just the knowledge extraction
4. **Test knowledge categorization only** - Test just the categorization
5. **Test knowledge quality analysis** - Analyze confidence and distribution metrics
6. **Test error handling scenarios** - Test error conditions and edge cases
7. **Test all documents (batch)** - Run tests on all available documents
8. **Exit** - Exit the testing interface

### What to Look For During Testing

#### ✅ Successful Meta Knowledge Extraction
- Knowledge points are generated from text content
- Different knowledge types are identified (facts, procedures, concepts, etc.)
- Confidence scores are reasonable (0.0-1.0 range)
- Content is meaningful and relevant to source document

#### ✅ Successful Knowledge Categorization
- Knowledge points are grouped into logical categories
- Categories reflect the document content appropriately
- No knowledge points are lost during categorization
- Category distribution makes sense for the document type

#### ✅ Quality Analysis
- Confidence scores show reasonable distribution
- High-confidence knowledge is accurate and relevant
- Content lengths are appropriate for knowledge type
- Knowledge type distribution reflects document content

#### ❌ Error Handling
- Empty or invalid inputs are handled gracefully
- Meaningful error messages are provided
- System doesn't crash on bad input
- Proper logging occurs for debugging

### Expected Results

For the provided test documents, you should see:

- **Text documents**: Procedural knowledge, best practices, guidelines
- **Technical documents**: Technical facts, procedures, troubleshooting steps
- **Data documents**: Structured information, metrics, categorical data
- **Research papers**: Concepts, methodologies, findings, technical details

## Phase 3 Testing (Coming Next)

Phase 3 testing script will be created to test:
- **Phase 3**: Similarity search and context expansion

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running from the project root with `uv run python`
2. **Documents not found**: Verify the docs/ directory exists and contains files
3. **Permission errors**: Check file permissions on the test documents

### Getting Help

If you encounter issues:
1. Check the console output for detailed error messages
2. Verify all test documents are readable
3. Ensure the OpenDXA environment is properly set up
4. Contact the development team if problems persist

## Next Steps

After successfully testing Phase 1:
1. Verify all document types load correctly
2. Check that text extraction produces clean, readable output
3. Confirm error handling works for edge cases
4. Move on to Phase 2 testing when ready 