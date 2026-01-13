# LLM Provider Live Tests

This directory contains comprehensive live tests for all LLM providers in the Adana library.

## Running Tests

### All Live Tests
```bash
# Run all live tests
python run_live_tests.py

# Or with pytest directly
uv run pytest adana/common/llm/tests/ -v -m live
```

### Specific Provider Tests
```bash
# Test specific provider
python run_live_tests.py openai
python run_live_tests.py anthropic
python run_live_tests.py deepseek
```

### Test Categories
```bash
# Test only provider creation (no API calls)
uv run pytest adana/common/llm/tests/ -v -k "creation"

# Test only chat functionality
uv run pytest adana/common/llm/tests/ -v -k "chat" -m live

# Test specific functionality
uv run pytest adana/common/llm/tests/ -v -k "conversation" -m live
```

## Test Structure

- `test_providers_live.py` - Comprehensive tests for all providers
- `test_openai.py` - OpenAI-specific tests
- `test_anthropic.py` - Anthropic-specific tests
- `test_groq.py` - Groq-specific tests
- `test_deepseek.py` - DeepSeek-specific tests
- `conftest.py` - Pytest configuration and fixtures

## Test Results Summary

### ✅ Working Providers
- **DeepSeek**: Full functionality working
- **HuggingFace**: Full functionality working
- **Azure**: Provider creation working
- **All Providers**: Creation and configuration working

### ⚠️ Provider-Specific Issues
- **OpenAI**: Geographic restrictions (Vietnam not supported)
- **Anthropic**: API key or permission issues
- **Groq**: API endpoint or model issues
- **Ollama**: Local server not running
- **Moonshot**: Authentication issues
- **OpenRouter**: Depends on underlying providers

### 🔧 Fixed Issues
- ✅ LLMResponse constructor (removed invalid `provider` parameter)
- ✅ Azure provider (removed `api_version` from AsyncOpenAI constructor)
- ✅ HuggingFace provider (added response format handling)
- ✅ Pydantic deprecation warnings (updated to `model_dump()`)

## Environment Setup

To run tests successfully, you need API keys for the providers you want to test:

```bash
# Add to .env file
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROQ_API_KEY=your-groq-key
DEEPSEEK_API_KEY=your-deepseek-key
HF_TOKEN=your-huggingface-token
# ... etc
```

## Test Markers

- `@pytest.mark.live` - Tests that make real API calls
- `@pytest.mark.slow` - Tests that may take longer to run
- `@pytest.mark.provider("name")` - Tests for specific providers

## Notes

- Tests are designed to be resilient to missing API keys
- Geographic restrictions are handled gracefully
- Connection issues are expected for local services like Ollama
- Tests provide detailed output for debugging

