# Document Processor Recipe

*Build intelligent document processing systems with OpenDXA*

---

## Overview

This recipe demonstrates how to build a comprehensive document processing system using OpenDXA. Learn to extract information, summarize content, classify documents, and generate insights from various document types.

## 🎯 What You'll Build

A complete document processing pipeline that can:
- **Extract** key information from documents
- **Classify** documents by type and content
- **Summarize** lengthy documents intelligently
- **Generate** actionable insights and recommendations
- **Process** multiple document formats (PDF, Word, text)

## 🚀 Quick Start

### Basic Document Processor

```dana
# Configure document processing resources
llm = create_llm_resource(provider="openai", model="gpt-4")
kb = create_kb_resource()

# Simple document processing function
def process_document(document_path):
    # Load document content
    content = load_document(document_path)
    
    # Extract key information
    key_info = reason(f"""
    Extract key information from this document:
    {content}
    
    Focus on:
    - Main topics and themes
    - Important dates and numbers
    - Key people and organizations
    - Action items or decisions
    """)
    
    # Generate summary
    summary = reason(f"""
    Provide a concise summary of this document:
    {content}
    
    Keep it under 200 words and focus on the most important points.
    """)
    
    return {
        "key_info": key_info,
        "summary": summary,
        "document_path": document_path
    }

# Process a single document
result = process_document("./sample_document.pdf")
log(f"Processed document: {result['summary']}", level="INFO")
```

### Advanced Document Pipeline

```dana
# Advanced document processing with classification and insights
def advanced_document_processor(documents):
    results = []
    
    for doc_path in documents:
        # Load and preprocess
        content = load_document(doc_path)
        
        # Classify document type
        doc_type = reason(f"""
        Classify this document type:
        {content[:1000]}...
        
        Categories: contract, report, email, proposal, manual, invoice, other
        Return only the category name.
        """)
        
        # Extract information based on type
        if doc_type == "contract":
            extraction = extract_contract_info(content)
        elif doc_type == "report":
            extraction = extract_report_info(content)
        elif doc_type == "invoice":
            extraction = extract_invoice_info(content)
        else:
            extraction = extract_general_info(content)
        
        # Generate insights
        insights = reason(f"""
        Based on this {doc_type} document analysis:
        {extraction}
        
        Provide:
        1. Key insights
        2. Potential issues or concerns
        3. Recommended actions
        """)
        
        # Store in knowledge base for future reference
        kb.store({
            "content": content,
            "type": doc_type,
            "extraction": extraction,
            "insights": insights,
            "source": doc_path
        })
        
        results.append({
            "document": doc_path,
            "type": doc_type,
            "extraction": extraction,
            "insights": insights
        })
        
        log(f"Processed {doc_type}: {doc_path}", level="INFO")
    
    return results

# Helper functions for specific document types
def extract_contract_info(content):
    return reason(f"""
    Extract contract-specific information:
    {content}
    
    Focus on:
    - Parties involved
    - Contract dates (start, end, renewal)
    - Key terms and conditions
    - Payment terms
    - Obligations and responsibilities
    - Termination clauses
    """)

def extract_report_info(content):
    return reason(f"""
    Extract report-specific information:
    {content}
    
    Focus on:
    - Report purpose and scope
    - Key findings and results
    - Methodology used
    - Recommendations
    - Data and statistics
    - Conclusions
    """)

def extract_invoice_info(content):
    return reason(f"""
    Extract invoice-specific information:
    {content}
    
    Focus on:
    - Invoice number and date
    - Vendor and customer information
    - Line items and quantities
    - Amounts and totals
    - Payment terms
    - Due dates
    """)

# Process multiple documents
document_list = [
    "./contracts/service_agreement.pdf",
    "./reports/quarterly_report.docx",
    "./invoices/inv_001.pdf"
]

results = advanced_document_processor(document_list)
log(f"Processed {len(results)} documents", level="INFO")
```

## 📋 Implementation Steps

### Step 1: Environment Setup

```bash
# Install required dependencies
pip install opendxa python-docx PyPDF2 python-magic

# Set up project structure
mkdir document_processor
cd document_processor
mkdir documents outputs configs
```

### Step 2: Document Loading Functions

```dana
# Document loading utilities
def load_document(file_path):
    """Load document content based on file type."""
    file_extension = get_file_extension(file_path)
    
    if file_extension == ".pdf":
        return load_pdf(file_path)
    elif file_extension in [".docx", ".doc"]:
        return load_word_document(file_path)
    elif file_extension == ".txt":
        return load_text_file(file_path)
    else:
        log(f"Unsupported file type: {file_extension}", level="WARNING")
        return None

def load_pdf(file_path):
    """Extract text from PDF files."""
    # Implementation would use PyPDF2 or similar
    pass

def load_word_document(file_path):
    """Extract text from Word documents."""
    # Implementation would use python-docx
    pass

def load_text_file(file_path):
    """Load plain text files."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
```

### Step 3: Document Analysis Pipeline

```dana
# Comprehensive document analysis
def analyze_document_batch(documents, analysis_config=None):
    """Analyze a batch of documents with configurable options."""
    
    config = analysis_config or {
        "extract_entities": True,
        "generate_summary": True,
        "classify_sentiment": True,
        "identify_topics": True,
        "extract_keywords": True
    }
    
    batch_results = []
    
    for doc_path in documents:
        try:
            content = load_document(doc_path)
            if not content:
                continue
            
            analysis = {}
            
            # Entity extraction
            if config["extract_entities"]:
                analysis["entities"] = extract_entities(content)
            
            # Document summarization
            if config["generate_summary"]:
                analysis["summary"] = generate_summary(content)
            
            # Sentiment analysis
            if config["classify_sentiment"]:
                analysis["sentiment"] = analyze_sentiment(content)
            
            # Topic identification
            if config["identify_topics"]:
                analysis["topics"] = identify_topics(content)
            
            # Keyword extraction
            if config["extract_keywords"]:
                analysis["keywords"] = extract_keywords(content)
            
            batch_results.append({
                "document": doc_path,
                "analysis": analysis,
                "processing_time": get_current_time()
            })
            
        except Exception as e:
            log(f"Error processing {doc_path}: {e}", level="ERROR")
            batch_results.append({
                "document": doc_path,
                "error": str(e)
            })
    
    return batch_results

# Individual analysis functions
def extract_entities(content):
    return reason(f"""
    Extract named entities from this text:
    {content}
    
    Identify:
    - People (names, titles)
    - Organizations (companies, institutions)
    - Locations (addresses, cities, countries)
    - Dates and times
    - Monetary amounts
    - Products or services
    
    Return as structured data.
    """)

def generate_summary(content, max_length=200):
    return reason(f"""
    Create a {max_length}-word summary of this document:
    {content}
    
    Focus on the most important information and main points.
    """)

def analyze_sentiment(content):
    return reason(f"""
    Analyze the sentiment of this document:
    {content}
    
    Determine:
    - Overall sentiment (positive, negative, neutral)
    - Confidence level (0-1)
    - Key emotional indicators
    """)

def identify_topics(content):
    return reason(f"""
    Identify the main topics discussed in this document:
    {content}
    
    List 3-5 primary topics with confidence scores.
    """)

def extract_keywords(content):
    return reason(f"""
    Extract important keywords and phrases from this document:
    {content}
    
    Focus on:
    - Domain-specific terminology
    - Key concepts
    - Important phrases
    - Technical terms
    """)
```

### Step 4: Output Generation

```dana
# Generate comprehensive reports
def generate_document_report(analysis_results, output_format="markdown"):
    """Generate a comprehensive report from document analysis results."""
    
    # Aggregate statistics
    total_docs = len(analysis_results)
    successful_analyses = len([r for r in analysis_results if "analysis" in r])
    
    # Generate report content
    report = reason(f"""
    Generate a comprehensive document analysis report based on these results:
    {analysis_results}
    
    Include:
    1. Executive summary
    2. Processing statistics
    3. Key findings across all documents
    4. Common themes and patterns
    5. Recommendations for action
    6. Individual document summaries
    
    Format: {output_format}
    """)
    
    # Save report
    timestamp = get_current_timestamp()
    output_path = f"./outputs/document_report_{timestamp}.{output_format}"
    save_to_file(report, output_path)
    
    log(f"Report generated: {output_path}", level="INFO")
    return report

# Export results in various formats
def export_results(results, format="json"):
    """Export analysis results in specified format."""
    
    timestamp = get_current_timestamp()
    
    if format == "json":
        output_path = f"./outputs/analysis_results_{timestamp}.json"
        save_json(results, output_path)
    elif format == "csv":
        output_path = f"./outputs/analysis_results_{timestamp}.csv"
        save_csv(results, output_path)
    elif format == "excel":
        output_path = f"./outputs/analysis_results_{timestamp}.xlsx"
        save_excel(results, output_path)
    
    log(f"Results exported: {output_path}", level="INFO")
    return output_path
```

## 🔍 Advanced Features

### Document Comparison

```dana
# Compare multiple documents
def compare_documents(doc_paths, comparison_criteria=None):
    """Compare multiple documents across various dimensions."""
    
    criteria = comparison_criteria or [
        "content_similarity",
        "topic_overlap", 
        "sentiment_difference",
        "entity_overlap"
    ]
    
    # Load and analyze all documents
    documents = []
    for path in doc_paths:
        content = load_document(path)
        analysis = analyze_document_content(content)
        documents.append({
            "path": path,
            "content": content,
            "analysis": analysis
        })
    
    # Perform comparisons
    comparison_results = reason(f"""
    Compare these documents based on the following criteria:
    {criteria}
    
    Documents:
    {documents}
    
    Provide detailed comparison analysis including:
    - Similarity scores for each criterion
    - Key differences and similarities
    - Recommendations based on comparison
    """)
    
    return comparison_results
```

### Intelligent Document Routing

```dana
# Route documents based on content
def route_documents(documents, routing_rules):
    """Automatically route documents to appropriate handlers based on content."""
    
    routing_results = []
    
    for doc_path in documents:
        content = load_document(doc_path)
        
        # Classify document for routing
        classification = reason(f"""
        Analyze this document and determine the best routing based on these rules:
        {routing_rules}
        
        Document content:
        {content[:1000]}...
        
        Return the routing decision with confidence score.
        """)
        
        routing_results.append({
            "document": doc_path,
            "classification": classification,
            "routing_decision": classification["route"],
            "confidence": classification["confidence"]
        })
        
        log(f"Routed {doc_path} to {classification['route']}", level="INFO")
    
    return routing_results
```

## 🧪 Testing and Validation

### Test Document Processing

```dana
# Test the document processor with sample documents
def test_document_processor():
    """Test the document processing pipeline with sample data."""
    
    # Test data
    test_documents = [
        "./test_data/sample_contract.pdf",
        "./test_data/sample_report.docx",
        "./test_data/sample_email.txt"
    ]
    
    # Run processing
    results = advanced_document_processor(test_documents)
    
    # Validate results
    for result in results:
        assert "type" in result
        assert "extraction" in result
        assert "insights" in result
        log(f"Test passed for {result['document']}", level="INFO")
    
    log("All document processing tests passed", level="INFO")
    return True

# Run tests
test_result = test_document_processor()
```

## 📊 Monitoring and Analytics

### Performance Tracking

```dana
# Monitor processing performance
def track_processing_metrics(results):
    """Track and log processing performance metrics."""
    
    total_docs = len(results)
    successful = len([r for r in results if "error" not in r])
    error_rate = (total_docs - successful) / total_docs * 100
    
    metrics = {
        "total_documents": total_docs,
        "successful_processing": successful,
        "error_rate": error_rate,
        "processing_time": calculate_total_time(results),
        "average_time_per_doc": calculate_average_time(results)
    }
    
    log(f"Processing metrics: {metrics}", level="INFO")
    return metrics
```

## 🎯 Next Steps

### Enhancements
- Add OCR capabilities for scanned documents
- Implement real-time document monitoring
- Create web interface for document upload
- Add batch processing capabilities
- Integrate with cloud storage services

### Integration
- Connect to document management systems
- Integrate with email systems for automatic processing
- Add workflow automation triggers
- Create API endpoints for external access

---

*Ready to process your documents? Try the [Quick Start](#quick-start) example or explore more [OpenDXA Recipes](../README.md).*