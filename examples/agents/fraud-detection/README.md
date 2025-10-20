# Fraud Detection Application

A comprehensive fraud detection system built using the STAR agent architecture. This application demonstrates how to create a multi-agent system where each agent is forced via system prompt to call specific resources or workflows.

## Architecture Overview

The application follows a sequential pipeline pattern with 4 specialized agents:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Coordinator   │───▶│ DeepExtractor   │───▶│ FieldNormalizer │───▶│ FraudIndicator  │
│     Agent       │    │     Agent       │    │     Agent       │    │     Agent       │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       ▼                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │              │ DeepExtraction  │    │ Normalization   │    │ FraudDetection  │
         │              │    Resource     │    │    Resource     │    │    Resource     │
         │              └─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ FraudDetection  │
│    Workflow     │
└─────────────────┘
```

## Data Flow

The system processes documents through a clear data transformation pipeline:

```
PDF/Image File ──▶ Text ──▶ JSON ──▶ Fraud Result
     │              │        │           │
     ▼              ▼        ▼           ▼
DeepExtractor  FieldNormalizer  FraudIndicator
   Agent           Agent           Agent
```

### 1. DeepExtractor Agent
- **Input**: PDF or image file path
- **Output**: Extracted text string
- **Resource**: `DeepExtractionResource`
- **Method**: `extract(file_path)`

### 2. FieldNormalizer Agent  
- **Input**: Extracted text string
- **Output**: Structured JSON data
- **Resource**: `NormalizationResource`
- **Method**: `normalize(extracted_text)`

### 3. FraudIndicator Agent
- **Input**: Normalized JSON data
- **Output**: Fraud analysis result
- **Resource**: `FraudDetectionResource` 
- **Method**: `detect(normalized_data)`

### 4. Coordinator Agent
- **Input**: File path
- **Output**: Complete fraud analysis
- **Workflow**: `FraudDetectionWorkflow`
- **Method**: `execute(file_path)`

## Key Features

### Forced Resource/Workflow Calls
Each agent is configured with system prompts that **force** them to call specific resources or workflows:

- **DeepExtractor**: Must call `deep-extraction` resource
- **FieldNormalizer**: Must call `field-normalization` resource  
- **FraudIndicator**: Must call `fraud-detection` resource
- **Coordinator**: Must call `fraud-detection-pipeline` workflow

### System Prompt Pattern
```xml
<IDENTITY>
You MUST ALWAYS call [resource/workflow-id] with [method-name].
Pass the [parameter-name] parameter.
NEVER answer without calling this [resource/workflow].
</IDENTITY>
```

### Deterministic Execution
The pipeline ensures:
- Sequential agent execution (no parallel calls)
- Proper data flow between agents
- Error handling at each stage
- Comprehensive result aggregation

## Installation

### Prerequisites
```bash
# Install aicapture for VLM-based document processing
pip install aicapture

# Optional: Install traditional OCR dependencies for fallback
pip install PyPDF2 pytesseract pillow

# For OCR functionality (optional fallback)
# On Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# On macOS:
brew install tesseract

# On Windows:
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Environment Setup
Set your chosen VLM provider and API key:

```bash
# For Anthropic Claude (recommended)
export ANTHROPIC_API_KEY=your_anthropic_key

# For OpenAI
export OPENAI_API_KEY=your_openai_key

# For Google Gemini
export GEMINI_API_KEY=your_google_key
```

### Setup
```bash
# Navigate to the fraud detection directory
cd examples/agents/fraud-detection

# Ensure you have the dana_agent package in your Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/dana-internal"
```

## Usage

### Basic Usage
```python
from agents.coordinator_agent import CoordinatorAgent

# Initialize the coordinator
coordinator = CoordinatorAgent(
    agent_id="fraud-coordinator",
    llm_provider="anthropic",
    model="claude-3-5-sonnet-20241022"
)

# Analyze a document for fraud
result = coordinator.converse(
    initial_message="Analyze this document for fraud",
    file_path="invoice.pdf"
)

# Access results
extracted_text = result["extracted_text"]
normalized_data = result["normalized_data"] 
fraud_result = result["fraud_result"]
risk_score = fraud_result["risk_score"]
```

### Command Line Demo
```bash
# Run with a specific file
python demo.py invoice.pdf

# Run with sample data (creates temporary file)
python demo.py

# Verbose output
python demo.py invoice.pdf --verbose

# Custom LLM settings
python demo.py invoice.pdf --llm-provider openai --model gpt-4
```

## Example Output

### Extracted Text
```
INVOICE

Invoice #: INV-2024-001
Date: 2024-01-15
Amount: $15,000.00
Vendor: Tech Solutions Inc.
...
```

### Normalized Data
```json
{
  "invoice_id": "INV-2024-001",
  "date": "2024-01-15",
  "amount": 15000.0,
  "currency": "USD",
  "vendor_name": "Tech Solutions Inc.",
  "customer_name": "Acme Corporation",
  "total_amount": 16275.0,
  "tax_amount": 1275.0
}
```

### Fraud Analysis Result
```json
{
  "risk_score": 25,
  "fraud_indicators": [
    {
      "indicator": "Valid invoice format",
      "severity": "low",
      "description": "Document follows standard invoice structure",
      "confidence": 0.9
    }
  ],
  "anomalies": [],
  "recommendations": [
    "LOW RISK: Standard processing acceptable"
  ],
  "overall_confidence": 0.85
}
```

## Agent Responsibilities

### CoordinatorAgent
- Orchestrates the complete fraud detection pipeline
- Manages sequential execution of specialist agents
- Handles error propagation and result aggregation
- **Forced to call**: `fraud-detection-pipeline` workflow

### DeepExtractorAgent
- Extracts text from PDF and image files
- Handles multiple file formats (PDF, PNG, JPG, TIFF, BMP)
- Uses OCR for image processing
- **Forced to call**: `deep-extraction` resource

### FieldNormalizerAgent
- Converts unstructured text to structured JSON
- Normalizes data formats (dates, amounts, names)
- Uses LLM intelligence for field extraction
- **Forced to call**: `field-normalization` resource

### FraudIndicatorAgent
- Analyzes structured data for fraud patterns
- Calculates risk scores (0-100)
- Identifies anomalies and suspicious patterns
- **Forced to call**: `fraud-detection` resource

## Resource Capabilities

### DeepExtractionResource
- **VLM-Powered Processing**: Uses aicapture VisionParser for enhanced text extraction
- **PDF Processing**: VLM-based extraction with fallback to PyPDF2
- **Image Processing**: VLM-based extraction with fallback to pytesseract OCR
- **Error Handling**: Graceful fallback for unsupported formats and API failures
- **Output**: Clean, structured text data with improved accuracy

### NormalizationResource
- **LLM-Powered Extraction**: Uses `self.reason()` for intelligent field identification
- **Data Normalization**: Standardizes dates, currency, phone numbers
- **Pattern Recognition**: Identifies common document types
- **Output**: Structured JSON with normalized fields

### FraudDetectionResource
- **Multi-Dimensional Analysis**: Combines LLM reasoning with rule-based checks
- **Risk Scoring**: Calculates 0-100 risk scores based on indicators
- **Anomaly Detection**: Identifies data inconsistencies and suspicious patterns
- **Output**: Comprehensive fraud assessment with recommendations

## Error Handling

The system includes comprehensive error handling:

- **File Validation**: Checks file existence and format support
- **Agent Failures**: Graceful handling of agent communication errors
- **Resource Errors**: Fallback mechanisms for resource failures
- **Pipeline Errors**: Error propagation with detailed error messages

## Customization

### Adding New Fraud Patterns
Extend the `FraudDetectionResource` to add custom fraud detection rules:

```python
def _apply_custom_fraud_rules(self, data):
    indicators = []
    
    # Add custom fraud detection logic
    if self._detect_suspicious_pattern(data):
        indicators.append({
            "indicator": "Custom fraud pattern detected",
            "severity": "high",
            "description": "Specific fraud pattern explanation",
            "confidence": 0.9
        })
    
    return indicators
```

### Adding New Document Types
Extend the `NormalizationResource` to handle new document formats:

```python
def _extract_custom_fields(self, text, document_type):
    if document_type == "contract":
        return self._extract_contract_fields(text)
    elif document_type == "receipt":
        return self._extract_receipt_fields(text)
    # Add more document types...
```

## Performance Considerations

- **LLM Usage**: Resources use LLM calls for intelligent processing
- **File Size Limits**: Large files may need chunking for processing
- **OCR Performance**: Image processing can be slow for large images
- **Memory Usage**: Consider memory limits for very large documents

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install aicapture
   # Optional fallback dependencies
   pip install PyPDF2 pytesseract pillow
   ```

2. **API Key Issues**
   - Ensure the correct API key is set for your chosen provider
   - Check that the API key has vision model access
   - Verify the model name is supported by your provider

3. **LLM Provider Issues**
   - Verify API keys are set correctly
   - Check model availability and permissions

4. **File Format Issues**
   - Ensure file exists and is readable
   - Check supported formats (PDF, PNG, JPG, TIFF, BMP)

5. **VLM Fallback Issues**
   - If VLM extraction fails, the system will automatically fall back to traditional methods
   - Check that fallback dependencies (PyPDF2, pytesseract) are installed
   - Ensure tesseract is installed and in PATH for image OCR fallback

### Debug Mode
Run with verbose output to see detailed execution:
```bash
python demo.py invoice.pdf --verbose
```

## Contributing

To extend the fraud detection system:

1. **Add New Resources**: Create new resource classes inheriting from `BaseResource`
2. **Add New Agents**: Create new agent classes inheriting from `STARAgent`
3. **Add New Workflows**: Create new workflow classes inheriting from `BaseWorkflow`
4. **Update System Prompts**: Modify XML files to enforce new behaviors

## License

This fraud detection application is part of the Dana agent framework and follows the same licensing terms.
