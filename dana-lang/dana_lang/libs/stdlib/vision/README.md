# Vision Processing Module

The Vision Processing Module provides unified file processing capabilities for PDF documents, images, and videos using AI-powered vision analysis. This module integrates with the `aicapture` library to extract and analyze content from various file formats.

## Features

- **Multi-format Support**: Process PDFs, images, and videos with a single function
- **AI-Powered Analysis**: Uses advanced vision models for content extraction and understanding
- **Customizable Prompts**: Apply specific prompts for targeted content extraction
- **Caching System**: Built-in caching for improved performance and cost efficiency
- **Configurable Processing**: Fine-tune processing parameters for different use cases
- **Async Processing**: Non-blocking operations for better performance

## Supported File Types

### Documents
- **PDF** (`.pdf`): Extract text, structure, and content from PDF documents

### Images
- **JPEG** (`.jpg`, `.jpeg`): Process photographic and graphic content
- **PNG** (`.png`): Handle transparent images and graphics
- **TIFF** (`.tiff`, `.tif`): Process high-quality images and documents
- **WebP** (`.webp`): Modern web image format
- **BMP** (`.bmp`): Bitmap image format

### Videos
- **MP4** (`.mp4`): Most common video format
- **AVI** (`.avi`): Audio Video Interleave format
- **MOV** (`.mov`): QuickTime movie format
- **MKV** (`.mkv`): Matroska video format

## Quick Start

```python
from vision import vision_extract

# Process a PDF document
result = vision_extract("document.pdf")
print(f"Extracted {result['file_object']['total_pages']} pages")

# Process an image with custom prompt
result = vision_extract("diagram.png", prompt="Describe the technical details shown in this diagram")

# Process a video
result = vision_extract("presentation.mp4")
print(f"Video content: {result['file_object']['content']}")

# Configure processing with custom settings
config = {
    "cache_dir": "tmp/vision_cache",
    "invalidate_cache": True,
    "image_quality": "high",
}
result = vision_extract("document.pdf", config=config)

# Error Handling
try:
    result = vision_extract("document.pdf")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Unsupported file type: {e}")
except Exception as e:
    print(f"Processing error: {e}")
```

## API Reference

### `vision_extract(file_path, prompt=None, config=None)`

Unified function to process various file types supported by aicapture.

#### Parameters

- **file_path** (`str`): Path to the file to process
- **prompt** (`Optional[str]`): Custom prompt for processing. If `None`, uses default prompts
- **config** (`Optional[Dict]`): Configuration dictionary for the processors

#### Returns

Returns a dictionary with processing results. Structure varies by file type:

**For PDF/Images:**
```python
{
    "file_object": {
        "file_name": "document.pdf",
        "file_full_path": "/path/to/document.pdf",
        "total_pages": 5,
        "pages": [
            {
                "page_number": 1,
                "page_content": "Extracted text content...",
                "page_analysis": "AI analysis of the page..."
            }
        ]
    }
}
```

**For Videos:**
```python
{
    "file_object": {
        "file_name": "video.mp4",
        "file_full_path": "/path/to/video.mp4",
        "file_type": "video",
        "content": "AI-generated description of video content..."
    }
}
```

#### Raises

- **FileNotFoundError**: When the specified file doesn't exist
- **ValueError**: When an unsupported file type is provided

## Configuration Options

The `config` parameter accepts a dictionary with the following options:

### General Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cache_dir` | `str` | `None` | Directory for caching processed results |
| `invalidate_cache` | `bool` | `False` | Whether to ignore existing cache |
| `vision_model` | `str` | `None` | Specific vision model to use |
| `cloud_bucket` | `str` | `None` | Cloud storage bucket for caching |

### Image Processing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_quality` | `str` | `"default"` | Image quality setting (`"low"`, `"default"`, `"high"`) |
| `dpi` | `int` | `333` | DPI setting for image processing |
| `max_concurrent_tasks` | `int` | `4` | Maximum concurrent processing tasks |

### Video Processing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_duration_seconds` | `int` | `30` | Maximum video duration to process |
| `frame_rate` | `int` | `2` | Frames per second to extract |
| `target_frame_size` | `tuple` | `(768, 768)` | Target size for frame resizing |
| `resize_frames` | `bool` | `True` | Whether to resize video frames |


## Integration with AI Functions

The vision processing results can be seamlessly integrated with Dana's AI reasoning capabilities:

```python
from vision import vision_extract

# Process an image
vision_result = vision_extract("diagram.png")

# Extract content for AI analysis
if "file_object" in vision_result and "pages" in vision_result["file_object"]:
    content = vision_result["file_object"]["pages"][0]["page_content"]
    
    # Use AI to analyze the extracted content
    analysis = reason(f"Summarize this content in one sentence: {content[:500]}...")
    print(f"AI Analysis: {analysis}")
```

## Performance Considerations

- **Caching**: Enable caching for frequently processed files to improve performance
- **Image Quality**: Use appropriate image quality settings based on your needs
- **Video Duration**: Limit video processing duration for faster results
- **Concurrent Tasks**: Adjust `max_concurrent_tasks` based on your system resources

## Supported Models and Environment Configuration

The vision module supports multiple AI vision models through the `aicapture` library. You can configure which model to use and its settings through environment variables.

### Available Model Providers

| Provider | Environment Variable | Default Model | Description |
|----------|---------------------|---------------|-------------|
| **OpenAI** | `USE_VISION=openai` | `gpt-4.1-mini` | OpenAI's GPT-4 Vision models |
| **Anthropic Claude** | `USE_VISION=claude` | `claude-sonnet-4-20250514` | Anthropic's Claude Vision models |
| **Google Gemini** | `USE_VISION=gemini` | `gemini-2.5-flash-preview-04-17` | Google's Gemini Vision models |
| **Azure OpenAI** | `USE_VISION=azure-openai` | `gpt-4o` | Azure-hosted OpenAI models |
| **AWS Bedrock** | `USE_VISION=anthropic_bedrock` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | AWS Bedrock Claude models |

### Environment Configuration

Create a `.env` file in your project root or use environment variables to configure the vision models:

#### OpenAI Configuration
```bash
# Vision model selection
USE_VISION=openai

# OpenAI API credentials
OPENAI_VISION_API_KEY=your_openai_api_key
OPENAI_VISION_MODEL=gpt-4o-mini
OPENAI_VISION_BASE_URL=https://api.openai.com/v1

# Alternative: Use general OpenAI variables
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1

# Processing parameters
OPENAI_MAX_TOKENS=5000
OPENAI_TEMPERATURE=0.0
```

#### Anthropic Claude Configuration
```bash
# Vision model selection
USE_VISION=claude

# Anthropic API credentials
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022-v2:0
```

#### Google Gemini Configuration
```bash
# Vision model selection
USE_VISION=gemini

# Gemini API credentials
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-preview-04-17
```

#### Azure OpenAI Configuration
```bash
# Vision model selection
USE_VISION=azure-openai

# Azure OpenAI credentials
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_MODEL=gpt-4o
AZURE_OPENAI_API_URL=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-11-01-preview
```

#### AWS Bedrock Configuration
```bash
# Vision model selection
USE_VISION=anthropic_bedrock

# AWS credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Optional: VPC endpoint for private access
AWS_BEDROCK_VPC_ENDPOINT_URL=https://your-vpc-endpoint.bedrock.us-east-1.amazonaws.com

# Model configuration
ANTHROPIC_BEDROCK_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Global Configuration

```bash
# General vision processing settings
MAX_CONCURRENT_TASKS=20

# Cache configuration
VISION_CACHE_DIR=./cache/vision
VISION_INVALIDATE_CACHE=false

# Cloud storage (optional)
VISION_CLOUD_BUCKET=your-cloud-bucket
```

### Model-Specific Features

#### OpenAI Vision Models
- **Supported Models**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4-vision-preview`
- **Image Quality**: Configurable detail levels (`low`, `high`)
- **Token Limits**: Configurable via `max_tokens` parameter

#### Anthropic Claude Models
- **Supported Models**: `claude-3-5-sonnet-20241022-v2:0`, `claude-3-opus-20240229`, `claude-3-sonnet-20240229`

#### Google Gemini Models
- **Supported Models**: `gemini-2.5-flash-preview-04-17`, `gemini-1.5-pro`, `gemini-1.5-flash`
- **Image Quality**: High-quality processing
- **Compatibility**: Uses OpenAI-compatible API interface

#### Azure OpenAI Models
- **Supported Models**: Same as OpenAI, but hosted on Azure
- **Authentication**: Uses Azure API key and endpoint
- **Features**: Enterprise-grade security and compliance

#### AWS Bedrock Models
- **Supported Models**: Claude models through AWS Bedrock
- **Authentication**: Uses AWS credentials
- **Features**: VPC endpoint support for private access

### Configuration Priority

The module follows this configuration priority:

1. **Function Parameters**: Values passed directly to `vision_extract()`
2. **Environment Variables**: System environment variables
3. **Default Values**: Built-in defaults for each provider

### Example Configuration Usage

```python
from vision import vision_extract

# Use environment-configured model
result = vision_extract("image.jpg")

# Override with specific configuration
config = {
    "vision_model": "gpt-4o-mini",
    "cache_dir": "./custom_cache",
    "image_quality": "high"
}
result = vision_extract("image.jpg", config=config)
```

## Dependencies

This module depends on the `aicapture` library, which provides the underlying vision processing capabilities. The library is included in the module's `aicapture/` directory.

## Testing

The module includes comprehensive tests in `tests/test_na/03_ai_function/test_vision_extract.na` that cover:

- Basic file processing for all supported formats
- Custom prompt functionality
- Configuration options
- Error handling
- Cache behavior
- AI integration

Run the tests to verify the module is working correctly in your environment.

## Troubleshooting

### Common Issues

1. **File Not Found**: Ensure the file path is correct and the file exists
2. **Unsupported File Type**: Check that the file extension is in the supported list
3. **Processing Errors**: Verify the file is not corrupted and is in a valid format
4. **Cache Issues**: Use `invalidate_cache: True` to bypass cache problems

### Performance Tips

- Use appropriate image quality settings for your use case
- Enable caching for repeated processing
- Consider video duration limits for large files
- Monitor system resources during processing

## Contributing

When contributing to the vision module:

1. Follow the existing code structure and patterns
2. Add tests for new functionality
3. Update this documentation for any API changes
4. Ensure compatibility with the `aicapture` library

## License

This module is part of the Dana framework and follows the same licensing terms.
